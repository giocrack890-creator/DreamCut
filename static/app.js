const $ = (id) => document.getElementById(id);

let currentUrl = "";
let profiles = [];
let queuePoll = null;

function getOpts() {
  const langs = [];
  if ($("subs-es").checked) langs.push("es");
  if ($("subs-en").checked) langs.push("en");
  return {
    trim_start: $("trim-start").value.trim() || undefined,
    trim_end: $("trim-end").value.trim() || undefined,
    subtitle_langs: langs,
    move_to_imports: $("move-imports-once").checked,
  };
}

function buildDownloadUrl(formatId, kind, extra = {}) {
  const p = new URLSearchParams({ url: currentUrl, format_id: formatId, kind });
  const o = { ...getOpts(), ...extra };
  if (o.trim_start) p.set("trim_start", o.trim_start);
  if (o.trim_end) p.set("trim_end", o.trim_end);
  if (o.subtitle_langs?.includes("es")) p.set("subs_es", "true");
  if (o.subtitle_langs?.includes("en")) p.set("subs_en", "true");
  if (o.quick_mp3) p.set("quick_mp3", "true");
  if (o.profile_id) p.set("profile_id", o.profile_id);
  if (o.move_to_imports) p.set("move_to_imports", "true");
  return `/api/download?${p}`;
}

function showErr(el, msg) {
  el.textContent = msg;
  el.classList.remove("hidden");
}
function hideErr(el) {
  el.classList.add("hidden");
}

function formatDuration(sec) {
  if (!sec) return "";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

// Tabs
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $(`panel-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "history") loadHistory();
    if (btn.dataset.tab === "queue") pollQueue();
  });
});

async function loadProfiles() {
  const res = await fetch("/api/profiles");
  profiles = await res.json();
  for (const sel of [$("profile-select"), $("queue-profile")]) {
    const first = sel.id === "queue-profile" ? '<option value="">Formato cola por defecto</option>' : '<option value="">Perfil…</option>';
    sel.innerHTML = first + profiles.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
  }
}

async function loadSettings() {
  const s = await (await fetch("/api/settings")).json();
  $("output-dir").value = s.output_dir || "";
  $("move-imports").checked = !!s.move_to_imports;
}

$("btn-save-settings").addEventListener("click", async () => {
  const res = await fetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      output_dir: $("output-dir").value,
      move_to_imports: $("move-imports").checked,
    }),
  });
  const s = await res.json();
  $("settings-msg").textContent = `Guardado: ${s.output_dir}`;
});

function qualityChipClass(label, kind) {
  if (kind === "mp3") return "chip chip-blue";
  const m = (label || "").match(/(\d+)p/i);
  if (m) return parseInt(m[1], 10) >= 1080 ? "chip chip-purple" : "chip chip-green";
  return "chip chip-muted";
}

function renderFormats(listEl, items, kind) {
  listEl.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    const left = document.createElement("div");
    left.innerHTML = `
      <div>${item.label}</div>
      <div class="format-meta">
        <span class="${qualityChipClass(item.label, kind)}">${kind.toUpperCase()}</span>
        ${item.size ? `<span class="meta">${item.size}</span>` : ""}
      </div>
    `;
    const a = document.createElement("a");
    a.href = buildDownloadUrl(item.format_id, kind);
    a.textContent = "Descargar";
    a.setAttribute("download", "");
    li.append(left, a);
    listEl.appendChild(li);
  }
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideErr($("error"));
  $("result").classList.add("hidden");
  const url = $("url").value.trim();
  const btn = $("btn-analyze");
  btn.disabled = true;
  btn.textContent = "Analizando…";
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(120000),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error");
    currentUrl = url;
    $("title").textContent = data.title;
    $("meta").textContent = [data.uploader, data.duration && formatDuration(data.duration)].filter(Boolean).join(" · ");
    const tags = $("result-tags");
    if (tags) {
      tags.innerHTML = "";
      if (data.uploader) {
        const c = document.createElement("span");
        c.className = "chip chip-muted";
        c.textContent = data.uploader;
        tags.appendChild(c);
      }
      if (data.duration) {
        const c = document.createElement("span");
        c.className = "chip chip-green";
        c.textContent = formatDuration(data.duration);
        tags.appendChild(c);
      }
    }
    const thumb = $("thumb");
    if (data.thumbnail) {
      thumb.src = data.thumbnail;
      thumb.classList.remove("hidden");
    } else thumb.classList.add("hidden");
    renderFormats($("mp4-list"), data.mp4 || [], "mp4");
    renderFormats($("mp3-list"), data.mp3 || [], "mp3");
    $("result").classList.remove("hidden");
  } catch (err) {
    showErr($("error"), err.message || "Error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Analizar";
  }
});

$("btn-quick-mp3").addEventListener("click", () => {
  const url = $("url").value.trim();
  if (!url) return showErr($("error"), "Pega un enlace primero");
  currentUrl = url;
  window.location.href = buildDownloadUrl("bestaudio/best", "mp3", { quick_mp3: true });
});

$("btn-profile-dl").addEventListener("click", () => {
  const pid = $("profile-select").value;
  const url = $("url").value.trim();
  if (!pid || !url) return showErr($("error"), "Elige perfil y enlace");
  currentUrl = url;
  const p = profiles.find((x) => x.id === pid);
  window.location.href = buildDownloadUrl(p.format_id, p.kind, { profile_id: pid });
});

// Canal
let channelVideos = [];

$("btn-channel-load").addEventListener("click", async () => {
  hideErr($("channel-error"));
  const url = $("channel-url").value.trim();
  const limit = parseInt($("channel-limit").value, 10) || 15;
  $("btn-channel-load").disabled = true;
  try {
    const res = await fetch("/api/channel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, limit }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error");
    channelVideos = data.videos || [];
    $("channel-name").textContent = data.channel;
    const ul = $("channel-list");
    ul.innerHTML = "";
    channelVideos.forEach((v, i) => {
      const li = document.createElement("li");
      li.innerHTML = `<label><input type="checkbox" data-i="${i}" checked /> ${v.title}</label>`;
      ul.appendChild(li);
    });
    $("btn-channel-queue").classList.toggle("hidden", !channelVideos.length);
  } catch (err) {
    showErr($("channel-error"), err.message);
  } finally {
    $("btn-channel-load").disabled = false;
  }
});

$("btn-channel-queue").addEventListener("click", async () => {
  const checked = [...document.querySelectorAll("#channel-list input:checked")].map((el) =>
    channelVideos[parseInt(el.dataset.i, 10)]
  );
  const profile = $("queue-profile").value;
  const items = checked.map((v) => ({
    url: v.url,
    kind: "mp4",
    format_id: "bestvideo+bestaudio/best",
    profile_id: profile || undefined,
  }));
  await fetch("/api/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
  document.querySelector('.tab[data-tab="queue"]').click();
  pollQueue();
});

// Cola
$("btn-queue-add").addEventListener("click", async () => {
  const lines = $("queue-urls").value.split("\n").map((l) => l.trim()).filter(Boolean);
  const profile = $("queue-profile").value;
  const kind = $("queue-kind").value;
  const items = lines.map((url) => ({
    url,
    kind,
    format_id: kind === "mp3" ? "bestaudio/best" : "bestvideo+bestaudio/best",
    quick_mp3: kind === "mp3",
    profile_id: profile || undefined,
  }));
  await fetch("/api/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
  $("queue-urls").value = "";
  pollQueue();
});

function renderQueue(jobs) {
  const ul = $("queue-jobs");
  ul.innerHTML = "";
  for (const j of jobs) {
    const li = document.createElement("li");
    const pct = Math.round(j.progress || 0);
    li.innerHTML = `
      <div><strong>${j.status}</strong> · ${j.kind} · ${j.url.slice(0, 50)}…</div>
      <div class="bar"><span style="width:${pct}%"></span></div>
      <small>${j.message || ""} ${j.output_path ? "→ " + j.output_path : ""}</small>
      ${j.error ? `<div class="err">${j.error}</div>` : ""}
    `;
    ul.appendChild(li);
  }
}

async function pollQueue() {
  if (queuePoll) clearInterval(queuePoll);
  const tick = async () => {
    const jobs = await (await fetch("/api/queue")).json();
    renderQueue(jobs);
    const pending = jobs.some((j) => j.status === "pending" || j.status === "running");
    if (!pending && queuePoll) {
      clearInterval(queuePoll);
      queuePoll = null;
    }
  };
  await tick();
  queuePoll = setInterval(tick, 1500);
}

// Historial
async function loadHistory() {
  const rows = await (await fetch("/api/history")).json();
  const ul = $("history-list");
  ul.innerHTML = rows.length
    ? ""
    : "<li>Sin descargas aún</li>";
  for (const r of rows) {
    const li = document.createElement("li");
    li.innerHTML = `<span>${r.title || r.url} <small class="meta">${r.created_at?.slice(0, 19)}</small></span>`;
    if (r.file_path) {
      const a = document.createElement("a");
      a.href = `file://${r.file_path}`;
      a.textContent = "Ruta";
      a.title = r.file_path;
      li.appendChild(a);
    }
    ul.appendChild(li);
  }
}

$("btn-refresh-history").addEventListener("click", loadHistory);

loadProfiles();
loadSettings();

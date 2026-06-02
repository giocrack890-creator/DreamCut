const DEFAULT_API = "http://127.0.0.1:8765";

const form = document.getElementById("form");
const urlInput = document.getElementById("url");
const btnAnalyze = document.getElementById("btn-analyze");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");
const thumbEl = document.getElementById("thumb");
const titleEl = document.getElementById("title");
const metaEl = document.getElementById("meta");
const resultTags = document.getElementById("result-tags");
const resultDate = document.getElementById("result-date");
const mp4List = document.getElementById("mp4-list");
const mp3List = document.getElementById("mp3-list");
const serverStatus = document.getElementById("server-status");
const profileSelect = document.getElementById("profile-select");

let currentUrl = "";
let apiBase = DEFAULT_API;
let profiles = [];

const HOST_RE =
  /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|tiktok\.com|instagram\.com|twitter\.com|x\.com|twitch\.tv|clips\.twitch\.tv)/i;

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove("hidden");
}
function clearError() {
  errorEl.classList.add("hidden");
}

function formatDuration(sec) {
  if (!sec) return "";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function qualityChipClass(label, kind) {
  if (kind === "mp3") return "chip chip-blue";
  const m = (label || "").match(/(\d+)p/i);
  if (m) {
    const h = parseInt(m[1], 10);
    if (h >= 1080) return "chip chip-purple";
    return "chip chip-green";
  }
  return "chip chip-muted";
}

function isSupportedUrl(url) {
  return HOST_RE.test(url || "");
}

function extraParams() {
  const p = new URLSearchParams();
  if (document.getElementById("subs-es").checked) p.set("subs_es", "true");
  if (document.getElementById("subs-en").checked) p.set("subs_en", "true");
  return p;
}

async function loadApiBase() {
  const stored = await chrome.storage.local.get(["apiBase", "savedProfile"]);
  apiBase = (stored.apiBase || DEFAULT_API).replace(/\/$/, "");
  if (stored.savedProfile) profileSelect.value = stored.savedProfile;
}

async function loadProfiles() {
  try {
    const res = await fetch(`${apiBase}/api/profiles`);
    profiles = await res.json();
    profileSelect.innerHTML =
      '<option value="">Elegir perfil…</option>' +
      profiles.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
    const { savedProfile } = await chrome.storage.local.get(["savedProfile"]);
    if (savedProfile) profileSelect.value = savedProfile;
  } catch {
    /* offline */
  }
}

profileSelect.addEventListener("change", () => {
  chrome.storage.local.set({ savedProfile: profileSelect.value });
});

async function checkServer() {
  try {
    const res = await fetch(`${apiBase}/api/health`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) throw new Error("offline");
    serverStatus.textContent = "En línea";
    serverStatus.className = "chip chip-green";
    return true;
  } catch {
    serverStatus.textContent = "Sin servidor";
    serverStatus.className = "chip chip-red";
    return false;
  }
}

function buildDownloadUrl(formatId, kind, opts = {}) {
  const params = new URLSearchParams({
    url: currentUrl,
    format_id: formatId,
    kind,
  });
  if (opts.quick_mp3) params.set("quick_mp3", "true");
  if (opts.profile_id) params.set("profile_id", opts.profile_id);
  extraParams().forEach((v, k) => params.set(k, v));
  return `${apiBase}/api/download?${params}`;
}

async function startDownload(url, label, ext) {
  const safe = (label || "video").replace(/[^\w\s.-]/g, "").trim().slice(0, 80) || "video";
  await chrome.downloads.download({
    url,
    filename: `descargas/${safe}.${ext}`,
    saveAs: false,
  });
}

function renderOptions(listEl, items, kind) {
  listEl.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    const info = document.createElement("div");
    info.className = "format-info";
    const chipClass = qualityChipClass(item.label, kind);
    info.innerHTML = `
      <span class="format-label">${item.label}</span>
      <div class="format-meta">
        <span class="${chipClass}">${kind.toUpperCase()}</span>
        ${item.size ? `<span class="size-text">${item.size}</span>` : ""}
      </div>
    `;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-primary";
    btn.textContent = "Descargar";
    btn.addEventListener("click", () =>
      startDownload(buildDownloadUrl(item.format_id, kind), item.label, kind)
    );
    li.append(info, btn);
    listEl.appendChild(li);
  }
}

document.getElementById("btn-quick-mp3").addEventListener("click", async () => {
  const url = urlInput.value.trim();
  if (!url || !(await checkServer())) return showError("Enlace y servidor requeridos");
  currentUrl = url;
  await startDownload(buildDownloadUrl("bestaudio/best", "mp3", { quick_mp3: true }), "audio", "mp3");
});

document.getElementById("btn-profile").addEventListener("click", async () => {
  const pid = profileSelect.value;
  const url = urlInput.value.trim();
  if (!pid || !url || !(await checkServer())) return showError("Perfil, enlace y servidor");
  const p = profiles.find((x) => x.id === pid);
  currentUrl = url;
  await startDownload(buildDownloadUrl(p.format_id, p.kind, { profile_id: pid }), p.name, p.kind);
});

document.getElementById("btn-open-web").addEventListener("click", () => {
  chrome.tabs.create({ url: `${apiBase}/` });
});

async function prefillFromTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.url && isSupportedUrl(tab.url)) urlInput.value = tab.url;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();
  resultEl.classList.add("hidden");
  const url = urlInput.value.trim();
  if (!(await checkServer())) return showError("Inicia ./run.sh en el proyecto");
  btnAnalyze.disabled = true;
  try {
    const res = await fetch(`${apiBase}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(120000),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error");
    currentUrl = url;
    resultDate.textContent = new Date().toLocaleString("es", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
    titleEl.textContent = data.title;
    metaEl.textContent = [data.uploader, data.duration && formatDuration(data.duration)]
      .filter(Boolean)
      .join(" · ");
    resultTags.innerHTML = "";
    if (data.uploader) {
      const c = document.createElement("span");
      c.className = "chip chip-muted";
      c.textContent = data.uploader;
      resultTags.appendChild(c);
    }
    if (data.duration) {
      const c = document.createElement("span");
      c.className = "chip chip-green";
      c.textContent = formatDuration(data.duration);
      resultTags.appendChild(c);
    }
    if (data.thumbnail) {
      thumbEl.src = data.thumbnail;
      thumbEl.classList.remove("hidden");
    } else thumbEl.classList.add("hidden");
    renderOptions(mp4List, data.mp4 || [], "mp4");
    renderOptions(mp3List, data.mp3 || [], "mp3");
    resultEl.classList.remove("hidden");
  } catch (err) {
    showError(err.message || "Error");
  } finally {
    btnAnalyze.disabled = false;
  }
});

(async () => {
  await loadApiBase();
  await checkServer();
  await loadProfiles();
  await prefillFromTab();
})();

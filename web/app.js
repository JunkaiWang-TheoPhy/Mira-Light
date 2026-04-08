const sceneGrid = document.getElementById("scene-grid");
const baseUrlInput = document.getElementById("base-url");
const dryRunInput = document.getElementById("dry-run");

const runtimeRunning = document.getElementById("runtime-running");
const runtimeScene = document.getElementById("runtime-scene");
const runtimeStep = document.getElementById("runtime-step");
const runtimeDevice = document.getElementById("runtime-device");
const runtimeError = document.getElementById("runtime-error");
const runtimeBaseUrl = document.getElementById("runtime-base-url");

const summarySceneTitle = document.getElementById("summary-scene-title");
const summarySceneId = document.getElementById("summary-scene-id");
const summaryCurrentStep = document.getElementById("summary-current-step");
const summaryStepCounter = document.getElementById("summary-step-counter");
const summaryHostCue = document.getElementById("summary-host-cue");
const summaryRequirements = document.getElementById("summary-requirements");
const summaryFallback = document.getElementById("summary-fallback");
const summaryShowcaseLink = document.getElementById("summary-showcase-link");
const readinessGrid = document.getElementById("readiness-grid");

const statusOutput = document.getElementById("status-output");
const ledOutput = document.getElementById("led-output");
const actionsOutput = document.getElementById("actions-output");
const profileOutput = document.getElementById("profile-output");
const profileMeta = document.getElementById("profile-meta");
const servoSummary = document.getElementById("servo-summary");
const poseSummary = document.getElementById("pose-summary");
const logOutput = document.getElementById("log-output");
const mockMode = document.getElementById("mock-mode");
const mockModeHint = document.getElementById("mock-mode-hint");
const mockLedMode = document.getElementById("mock-led-mode");
const mockLedMeta = document.getElementById("mock-led-meta");
const mockServoGrid = document.getElementById("mock-servo-grid");
const mockPixelStrip = document.getElementById("mock-pixel-strip");
const mockLedNote = document.getElementById("mock-led-note");
const mockColorSwatch = document.getElementById("mock-color-swatch");

let scenes = [];
let selectedSceneId = null;
let runtimeState = null;
let statusState = null;
let ledState = null;
let actionsState = null;

const DIRECTOR_SCENE_IDS = [
  "wake_up",
  "curious_observe",
  "touch_affection",
  "cute_probe",
  "daydream",
  "standup_reminder",
  "track_target",
  "celebrate",
  "farewell",
  "sleep",
];

const SHOWCASE_PAGES = {
  standup_reminder: "/06_standup_reminder/index.html",
  track_target: "/07_track_target/index.html",
  celebrate: "/08_celebrate/index.html",
  farewell: "/09_farewell/index.html",
  sleep: "/10_sleep/index.html",
};

const ATTACHMENT_DEFS = [
  { id: "base_calibrated", label: "基础姿态已校准", hint: "neutral / sleep / extend 等关键 pose 已调好" },
  { id: "touch_ready", label: "手部互动就绪", hint: "手部接近或触摸演示条件具备" },
  { id: "tracking_ready", label: "目标跟踪就绪", hint: "书本 / 目标跟踪逻辑可用" },
  { id: "camera_ready", label: "摄像头在线", hint: "摄像头与视觉链路工作正常" },
  { id: "offer_ready", label: "Offer 页面已准备", hint: "庆祝段落需要假邮件或展示页" },
  { id: "audio_ready", label: "音频素材已准备", hint: "跳舞段落所需音乐可播放" },
  { id: "sleep_calibrated", label: "睡姿已校准", hint: "sleep pose 可安全回落" },
  { id: "mic_ready", label: "麦克风 / 语音输入可用", hint: "语音或叹气类场景需要音频输入" },
];

function readAttachmentState() {
  try {
    return JSON.parse(localStorage.getItem("mira-light-attachments") || "{}");
  } catch {
    return {};
  }
}

function writeAttachmentState(state) {
  localStorage.setItem("mira-light-attachments", JSON.stringify(state));
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(`Invalid JSON from ${url}`);
  }

  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }

  return data;
}

function sceneById(sceneId) {
  return scenes.find((item) => item.id === sceneId) || null;
}

function formatDuration(durationMs) {
  if (!durationMs) return "TBD";
  return `${(durationMs / 1000).toFixed(1)}s`;
}

function readinessLabel(value) {
  return value || "prototype";
}

function renderRuntime(runtime) {
  runtimeState = runtime;
  runtimeRunning.textContent = runtime.running ? "RUNNING" : "IDLE";
  runtimeScene.textContent = runtime.runningScene || runtime.lastFinishedScene || "-";
  runtimeStep.textContent = runtime.currentStepLabel || runtime.lastCommand || "-";
  runtimeDevice.textContent =
    runtime.deviceOnline === true ? "ONLINE" : runtime.deviceOnline === false ? "OFFLINE" : "UNKNOWN";
  runtimeError.textContent = runtime.lastError || "-";
  runtimeBaseUrl.textContent = runtime.baseUrl || "-";

  baseUrlInput.value = runtime.baseUrl || "";
  dryRunInput.checked = Boolean(runtime.dryRun);

  document.body.classList.toggle("is-running", Boolean(runtime.running));
  document.body.classList.toggle("is-error", Boolean(runtime.lastError));

  renderSceneGrid();
  renderDirectorSummary();
  updateSceneAccent();
  renderMockOverview();
}

function buildTag(text, tone = "default") {
  const span = document.createElement("span");
  span.className = `tag tone-${tone}`;
  span.textContent = text;
  return span;
}

function renderSceneGrid() {
  sceneGrid.innerHTML = "";
  const readinessState = readAttachmentState();

  scenes.forEach((scene) => {
    const isSelected = selectedSceneId === scene.id;
    const isRunning = runtimeState?.runningScene === scene.id;
    const card = document.createElement("button");
    card.type = "button";
    card.className = "scene-card";
    if (isSelected) card.classList.add("is-selected");
    if (isRunning) card.classList.add("is-running");
    card.dataset.readiness = scene.readiness || "prototype";
    card.dataset.priority = scene.priority || "P2";
    card.dataset.accent = scene.accent || "prototype";

    const emotionTags = (scene.emotionTags || []).slice(0, 3);
    const requirements = (scene.requirements || []).slice(0, 2);
    const unmetCount = (scene.requirementIds || []).filter((id) => readinessState[id] !== true).length;

    const halo = document.createElement("div");
    halo.className = "scene-halo";

    const badges = document.createElement("div");
    badges.className = "scene-badges";
    badges.appendChild(buildTag(scene.priority || "P2", "priority"));
    badges.appendChild(buildTag(readinessLabel(scene.readiness), scene.readiness || "prototype"));
    badges.appendChild(buildTag(formatDuration(scene.durationMs), "duration"));
    if (unmetCount > 0) {
      badges.appendChild(buildTag(`${unmetCount} 项未就绪`, "warning"));
    }

    const title = document.createElement("strong");
    title.textContent = scene.title;

    const id = document.createElement("span");
    id.className = "scene-id";
    id.textContent = scene.id;

    const host = document.createElement("p");
    host.className = "scene-host";
    host.textContent = scene.hostLine || "";

    const emotions = document.createElement("div");
    emotions.className = "tag-list";
    emotionTags.forEach((tag) => emotions.appendChild(buildTag(tag, "emotion")));

    const needs = document.createElement("div");
    needs.className = "scene-needs";
    requirements.forEach((item) => needs.appendChild(buildTag(item, "need")));

    card.appendChild(halo);
    card.appendChild(badges);
    card.appendChild(title);
    card.appendChild(id);
    card.appendChild(host);
    card.appendChild(emotions);
    card.appendChild(needs);

    card.addEventListener("click", async () => {
      selectedSceneId = scene.id;
      renderSceneGrid();
      renderDirectorSummary();
      try {
        await fetchJson(`/api/run/${encodeURIComponent(scene.id)}`, { method: "POST" });
        await refreshRuntime();
        await refreshLogs();
      } catch (error) {
        appendLocalLog(`[ui-error] ${error.message}`);
      }
    });

    sceneGrid.appendChild(card);
  });
}

function renderDirectorSummary() {
  const activeSceneId = runtimeState?.runningScene || selectedSceneId || runtimeState?.lastFinishedScene || scenes[0]?.id;
  const scene = sceneById(activeSceneId);
  const readinessState = readAttachmentState();

  if (!scene) {
    summarySceneTitle.textContent = "-";
    summarySceneId.textContent = "-";
    summaryCurrentStep.textContent = "-";
    summaryStepCounter.textContent = "-";
    summaryHostCue.textContent = "-";
    summaryFallback.textContent = "-";
    summaryRequirements.innerHTML = "";
    return;
  }

  summarySceneTitle.textContent = scene.title;
  summarySceneId.textContent = `${scene.id} · ${readinessLabel(scene.readiness)}`;
  summaryCurrentStep.textContent = runtimeState?.currentStepLabel || "等待触发";

  const currentIndex = runtimeState?.currentStepIndex;
  const currentTotal = runtimeState?.currentStepTotal;
  if (currentIndex && currentTotal) {
    summaryStepCounter.textContent = `${currentIndex} / ${currentTotal}`;
  } else {
    summaryStepCounter.textContent = `预计 ${formatDuration(scene.durationMs)}`;
  }

  summaryHostCue.textContent = scene.operatorCue || scene.hostLine || "-";
  summaryFallback.textContent = scene.fallbackHint || "-";

  const showcaseHref = SHOWCASE_PAGES[scene.id];
  if (showcaseHref) {
    summaryShowcaseLink.textContent = "打开当前场景展示页";
    summaryShowcaseLink.href = showcaseHref;
    summaryShowcaseLink.classList.remove("is-disabled");
    summaryShowcaseLink.removeAttribute("aria-disabled");
  } else {
    summaryShowcaseLink.textContent = "当前场景暂无单独展示页";
    summaryShowcaseLink.href = "#";
    summaryShowcaseLink.classList.add("is-disabled");
    summaryShowcaseLink.setAttribute("aria-disabled", "true");
  }

  summaryRequirements.innerHTML = "";
  (scene.requirements || []).forEach((item, index) => {
    const requirementId = (scene.requirementIds || [])[index];
    const ready = requirementId ? readinessState[requirementId] === true : true;
    summaryRequirements.appendChild(buildTag(item, ready ? "need" : "warning"));
  });
}

function renderReadinessPanel() {
  const state = readAttachmentState();
  readinessGrid.innerHTML = "";

  ATTACHMENT_DEFS.forEach((item) => {
    const card = document.createElement("label");
    card.className = "readiness-card";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = state[item.id] === true;
    checkbox.addEventListener("change", () => {
      const nextState = readAttachmentState();
      nextState[item.id] = checkbox.checked;
      writeAttachmentState(nextState);
      renderReadinessPanel();
      renderSceneGrid();
      renderDirectorSummary();
    });

    const copy = document.createElement("div");
    copy.className = "readiness-copy";
    copy.innerHTML = `<strong>${item.label}</strong><small>${item.hint}</small>`;

    card.appendChild(checkbox);
    card.appendChild(copy);
    readinessGrid.appendChild(card);
  });
}

function renderJson(target, data) {
  target.textContent = JSON.stringify(data, null, 2);
}

function normalizeServoStatus(data) {
  if (!data || !Array.isArray(data.servos)) return [];
  return data.servos
    .map((item) => ({
      name: item.name || `servo${item.id || "?"}`,
      angle: typeof item.angle === "number" ? item.angle : null,
      pin: item.pin ?? "-",
    }))
    .filter((item) => item.name);
}

function normalizePixel(pixel) {
  if (pixel && typeof pixel === "object" && !Array.isArray(pixel)) {
    return {
      r: Number(pixel.r ?? 0),
      g: Number(pixel.g ?? 0),
      b: Number(pixel.b ?? 0),
    };
  }
  if (Array.isArray(pixel) && pixel.length === 3) {
    return {
      r: Number(pixel[0] ?? 0),
      g: Number(pixel[1] ?? 0),
      b: Number(pixel[2] ?? 0),
    };
  }
  return { r: 0, g: 0, b: 0 };
}

function rgbToCss(pixel) {
  const { r, g, b } = normalizePixel(pixel);
  return `rgb(${r}, ${g}, ${b})`;
}

function inferDeviceMode() {
  if (!runtimeState) return { title: "-", hint: "-" };
  if (runtimeState.dryRun) {
    return { title: "Dry Run", hint: "当前不访问任何设备，只验证调度链路。" };
  }
  if ((runtimeState.baseUrl || "").includes("127.0.0.1:9791")) {
    return { title: "Mock Lamp", hint: "bridge 正在对接本地假设备，可排练完整闭环。" };
  }
  return { title: "Live Lamp", hint: `当前目标：${runtimeState.baseUrl || "-"}` };
}

function renderMockOverview() {
  if (!mockMode) return;

  const deviceMode = inferDeviceMode();
  mockMode.textContent = deviceMode.title;
  mockModeHint.textContent = deviceMode.hint;

  if (!ledState) {
    mockLedMode.textContent = "-";
    mockLedMeta.textContent = "等待 LED 状态";
    mockLedNote.textContent = "等待 LED 状态";
    mockColorSwatch.style.background = "linear-gradient(135deg, rgba(255,255,255,0.9), rgba(220,224,255,0.7))";
    mockServoGrid.innerHTML = "";
    mockPixelStrip.innerHTML = "";
    return;
  }

  mockLedMode.textContent = ledState.mode || "-";
  const ledCount = ledState.led_count || (Array.isArray(ledState.pixels) ? ledState.pixels.length : 0) || 0;
  mockLedMeta.textContent = `brightness ${ledState.brightness ?? "-"} · ${ledCount} px`;

  const servos = normalizeServoStatus(statusState);
  mockServoGrid.innerHTML = "";
  servos.forEach((servo) => {
    const card = document.createElement("div");
    card.className = "mock-servo-card";

    const angle = typeof servo.angle === "number" ? servo.angle : 0;
    const fill = document.createElement("div");
    fill.className = "mock-servo-fill";
    fill.style.width = `${Math.max(0, Math.min(100, (angle / 180) * 100))}%`;

    card.innerHTML = `
      <div class="mock-servo-head">
        <strong>${servo.name}</strong>
        <small>pin ${servo.pin}</small>
      </div>
      <div class="mock-servo-angle">${servo.angle ?? "-"}°</div>
      <div class="mock-servo-track"></div>
    `;
    card.querySelector(".mock-servo-track").appendChild(fill);
    mockServoGrid.appendChild(card);
  });

  let pixels = [];
  if (ledState.mode === "vector" && Array.isArray(ledState.pixels)) {
    pixels = ledState.pixels.map((pixel) => normalizePixel(pixel));
    mockLedNote.textContent = `当前为 vector 模式，预览 ${pixels.length} 个像素。`;
  } else {
    const ledCountForFill = ledCount || 40;
    const color = normalizePixel(ledState.color || { r: 255, g: 255, b: 255 });
    pixels = Array.from({ length: ledCountForFill }, () => color);
    mockLedNote.textContent = `当前为 ${ledState.mode || "solid"} 模式，整条使用统一色。`;
  }

  const swatchColor = ledState.mode === "vector" ? normalizePixel(pixels[0]) : normalizePixel(ledState.color);
  mockColorSwatch.style.background = rgbToCss(swatchColor);

  mockPixelStrip.innerHTML = "";
  pixels.forEach((pixel, index) => {
    const dot = document.createElement("span");
    dot.className = "mock-pixel";
    dot.style.background = rgbToCss(pixel);
    dot.title = `${index + 1}: ${rgbToCss(pixel)}`;
    mockPixelStrip.appendChild(dot);
  });
}

function renderLogs(items) {
  logOutput.innerHTML = "";

  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "log-row";
    row.textContent = `[${item.ts}] ${item.text}`;
    if (item.text.includes("[runtime-error]") || item.text.includes("[ui-error]")) {
      row.classList.add("is-error");
    } else if (item.text.includes("[scene-done]")) {
      row.classList.add("is-scene");
    } else if (item.text.includes("[pose]") || item.text.includes("[action]")) {
      row.classList.add("is-step");
    }
    logOutput.appendChild(row);
  });

  logOutput.scrollTop = logOutput.scrollHeight;
}

function appendLocalLog(message) {
  const row = document.createElement("div");
  row.className = "log-row is-error";
  row.textContent = `[local] ${message}`;
  logOutput.prepend(row);
}

function renderProfile(profile) {
  renderJson(profileOutput, profile);

  profileMeta.innerHTML = "";
  [
    ["Profile Path", profile.info?.path || "-"],
    ["Loaded", profile.info?.loaded ? "yes" : "no"],
    ["Exists", profile.info?.exists ? "yes" : "no"],
    ["Pose Count", Object.keys(profile.poses || {}).length],
  ].forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "meta-card";
    card.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    profileMeta.appendChild(card);
  });

  servoSummary.innerHTML = "";
  Object.entries(profile.servoCalibration || {}).forEach(([servoName, data]) => {
    const row = document.createElement("div");
    row.className = "servo-row";
    row.innerHTML = `
      <div>
        <strong>${servoName}</strong>
        <small>${data.label || "-"}</small>
      </div>
      <div class="servo-values">
        <span>N ${data.neutral ?? "-"}</span>
        <span>R ${(data.rehearsal_range || []).join(" ~ ") || "-"}</span>
        <span>${data.verified ? "verified" : "draft"}</span>
      </div>
    `;
    servoSummary.appendChild(row);
  });

  poseSummary.innerHTML = "";
  Object.entries(profile.poses || {}).slice(0, 8).forEach(([poseName, data]) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "pose-card";
    card.innerHTML = `
      <strong>${poseName}</strong>
      <small>${data.verified ? "verified" : "draft"}</small>
      <span>s1 ${data.angles?.servo1 ?? "-"} · s2 ${data.angles?.servo2 ?? "-"}</span>
      <span>s3 ${data.angles?.servo3 ?? "-"} · s4 ${data.angles?.servo4 ?? "-"}</span>
    `;
    card.addEventListener("click", () => applyPose(poseName));
    poseSummary.appendChild(card);
  });
}

function updateSceneAccent() {
  const activeSceneId = runtimeState?.runningScene || selectedSceneId || runtimeState?.lastFinishedScene;
  const scene = sceneById(activeSceneId);
  document.body.dataset.scene = scene?.accent || "default";
}

async function refreshRuntime() {
  const data = await fetchJson("/api/runtime");
  renderRuntime(data.runtime);
}

async function refreshScenes() {
  const data = await fetchJson("/api/scenes");
  const sceneMap = new Map((data.items || []).map((item) => [item.id, item]));
  scenes = DIRECTOR_SCENE_IDS.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);
  if (!selectedSceneId && scenes.length > 0) {
    selectedSceneId = scenes[0].id;
  }
  renderSceneGrid();
  renderDirectorSummary();
}

async function refreshStatus() {
  const data = await fetchJson("/api/status");
  statusState = data.data;
  renderJson(statusOutput, data.data);
  renderMockOverview();
}

async function refreshLed() {
  const data = await fetchJson("/api/led");
  ledState = data.data;
  renderJson(ledOutput, data.data);
  renderMockOverview();
}

async function refreshActions() {
  const data = await fetchJson("/api/actions");
  actionsState = data.data;
  renderJson(actionsOutput, data.data);
}

async function refreshProfile() {
  const data = await fetchJson("/api/profile");
  renderProfile(data.profile);
}

async function refreshLogs() {
  const data = await fetchJson("/api/logs");
  renderLogs(data.items);
}

async function saveConfig() {
  try {
    const data = await fetchJson("/api/config", {
      method: "POST",
      body: JSON.stringify({
        baseUrl: baseUrlInput.value.trim(),
        dryRun: dryRunInput.checked,
      }),
    });
    renderRuntime(data.runtime);
    appendLocalLog(`config updated: baseUrl=${data.runtime.baseUrl} dryRun=${data.runtime.dryRun}`);
  } catch (error) {
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function stopScene() {
  try {
    await fetchJson("/api/stop", { method: "POST" });
    await refreshRuntime();
    await refreshLogs();
  } catch (error) {
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function operatorAction(endpoint) {
  try {
    await fetchJson(endpoint, { method: "POST" });
    await Promise.all([refreshRuntime(), refreshStatus(), refreshLed(), refreshLogs()]);
  } catch (error) {
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function resetLamp() {
  try {
    await fetchJson("/api/reset", { method: "POST" });
    await Promise.all([refreshStatus(), refreshLed(), refreshLogs(), refreshRuntime()]);
  } catch (error) {
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function applyPose(name) {
  try {
    await fetchJson("/api/apply-pose", {
      method: "POST",
      body: JSON.stringify({ pose: name }),
    });
    await Promise.all([refreshStatus(), refreshLogs(), refreshRuntime()]);
  } catch (error) {
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

document.getElementById("save-config").addEventListener("click", saveConfig);
document.getElementById("refresh-status").addEventListener("click", refreshStatus);
document.getElementById("refresh-led").addEventListener("click", refreshLed);
document.getElementById("refresh-actions").addEventListener("click", refreshActions);
document.getElementById("apply-neutral").addEventListener("click", () => applyPose("neutral"));
document.getElementById("apply-sleep").addEventListener("click", () => applyPose("sleep"));
document.getElementById("stop-scene").addEventListener("click", stopScene);
document.getElementById("stop-neutral").addEventListener("click", () => operatorAction("/api/operator/stop-to-neutral"));
document.getElementById("stop-sleep").addEventListener("click", () => operatorAction("/api/operator/stop-to-sleep"));
document.getElementById("reset-lamp").addEventListener("click", resetLamp);

async function bootstrap() {
  try {
    renderReadinessPanel();
    await refreshRuntime();
    await refreshScenes();
    await refreshStatus();
    await refreshLed();
    await refreshActions();
    await refreshProfile();
    await refreshLogs();
  } catch (error) {
    appendLocalLog(`[bootstrap-error] ${error.message}`);
  }

  setInterval(async () => {
    try {
      await Promise.all([refreshRuntime(), refreshLogs(), refreshStatus(), refreshLed(), refreshActions()]);
    } catch (error) {
      appendLocalLog(`[poll-error] ${error.message}`);
    }
  }, 2500);
}

bootstrap();

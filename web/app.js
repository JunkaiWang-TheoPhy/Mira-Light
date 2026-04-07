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
const readinessGrid = document.getElementById("readiness-grid");

const statusOutput = document.getElementById("status-output");
const ledOutput = document.getElementById("led-output");
const actionsOutput = document.getElementById("actions-output");
const profileOutput = document.getElementById("profile-output");
const profileMeta = document.getElementById("profile-meta");
const servoSummary = document.getElementById("servo-summary");
const poseSummary = document.getElementById("pose-summary");
const logOutput = document.getElementById("log-output");

let scenes = [];
let selectedSceneId = null;
let runtimeState = null;

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
  scenes = data.items;
  if (!selectedSceneId && scenes.length > 0) {
    selectedSceneId = scenes[0].id;
  }
  renderSceneGrid();
  renderDirectorSummary();
}

async function refreshStatus() {
  const data = await fetchJson("/api/status");
  renderJson(statusOutput, data.data);
}

async function refreshLed() {
  const data = await fetchJson("/api/led");
  renderJson(ledOutput, data.data);
}

async function refreshActions() {
  const data = await fetchJson("/api/actions");
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
      await refreshRuntime();
      await refreshLogs();
      await refreshStatus();
    } catch (error) {
      appendLocalLog(`[poll-error] ${error.message}`);
    }
  }, 2500);
}

bootstrap();

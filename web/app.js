const sceneGrid = document.getElementById("scene-grid");
const baseUrlInput = document.getElementById("base-url");
const dryRunInput = document.getElementById("dry-run");
const cueModeDirectorInput = document.getElementById("cue-mode-director");
const farewellDirectionInput = document.getElementById("farewell-direction");

const runtimeRunning = document.getElementById("runtime-running");
const runtimeScene = document.getElementById("runtime-scene");
const runtimeStep = document.getElementById("runtime-step");
const runtimeDevice = document.getElementById("runtime-device");
const runtimeError = document.getElementById("runtime-error");
const runtimeBaseUrl = document.getElementById("runtime-base-url");
const visionTargetTitle = document.getElementById("vision-target-title");
const visionTargetSubtitle = document.getElementById("vision-target-subtitle");
const visionZone = document.getElementById("vision-zone");
const visionDistance = document.getElementById("vision-distance");
const visionDetector = document.getElementById("vision-detector");
const visionConfidence = document.getElementById("vision-confidence");
const visionLastTrigger = document.getElementById("vision-last-trigger");
const visionOperatorLock = document.getElementById("vision-operator-lock");
const visionOperatorNote = document.getElementById("vision-operator-note");
const visionTrackList = document.getElementById("vision-track-list");

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
const capturePoseNameInput = document.getElementById("capture-pose-name");
const capturePoseNotesInput = document.getElementById("capture-pose-notes");
const capturePoseVerifiedInput = document.getElementById("capture-pose-verified");
const profileFlash = document.getElementById("profile-flash");
const logOutput = document.getElementById("log-output");
const mockMode = document.getElementById("mock-mode");
const mockModeHint = document.getElementById("mock-mode-hint");
const mockLedMode = document.getElementById("mock-led-mode");
const mockLedMeta = document.getElementById("mock-led-meta");
const mockHeadCapacitiveValue = document.getElementById("mock-head-capacitive-value");
const mockHeadCapacitiveHint = document.getElementById("mock-head-capacitive-hint");
const mockPixelSignalSummary = document.getElementById("mock-pixel-signal-summary");
const mockPixelSignalHint = document.getElementById("mock-pixel-signal-hint");
const mockHeadCapacitiveToggle = document.getElementById("mock-head-capacitive-toggle");
const mockSensorBadge = document.getElementById("mock-sensor-badge");
const mockTouchVisual = document.getElementById("mock-touch-visual");
const mockTouchCaption = document.getElementById("mock-touch-caption");
const mockServoGrid = document.getElementById("mock-servo-grid");
const mockPixelRing = document.getElementById("mock-pixel-ring");
const mockPixelRingActive = document.getElementById("mock-pixel-ring-active");
const mockPixelRingCaption = document.getElementById("mock-pixel-ring-caption");
const mockPixelStrip = document.getElementById("mock-pixel-strip");
const mockLedNote = document.getElementById("mock-led-note");
const mockColorSwatch = document.getElementById("mock-color-swatch");
const visionTrackCount = document.getElementById("vision-track-count");
const visionTrackNote = document.getElementById("vision-track-note");
const visionSelectedTrack = document.getElementById("vision-selected-track");
const visionSelectedNote = document.getElementById("vision-selected-note");
const visionSceneHint = document.getElementById("vision-scene-hint");
const visionSceneReason = document.getElementById("vision-scene-reason");
const visionTrackingActive = document.getElementById("vision-tracking-active");
const visionDistanceBand = document.getElementById("vision-distance-band");
const visionTracks = document.getElementById("vision-tracks");
const visionLockFlash = document.getElementById("vision-lock-flash");
const pageShell = document.querySelector(".page");
const sceneDecorLeft = document.querySelector(".scene-decor-left");
const sceneDecorRight = document.querySelector(".scene-decor-right");
const sceneDecorLeftIcon = document.getElementById("scene-decor-left-icon");
const sceneDecorLeftLabel = document.getElementById("scene-decor-left-label");
const sceneDecorRightIcon = document.getElementById("scene-decor-right-icon");
const sceneDecorRightLabel = document.getElementById("scene-decor-right-label");
const sceneSparkLayer = document.getElementById("scene-spark-layer");

let scenes = [];
let selectedSceneId = null;
let runtimeState = null;
let statusState = null;
let ledState = null;
let actionsState = null;
let visionOperatorState = null;
let visionState = null;
let sensorsState = null;
let sceneDecorFrame = 0;

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

const SCENE_DECOR = {
  wake_up: {
    left: { icon: "☀", label: "日光" },
    right: { icon: "✦", label: "苏醒" },
  },
  curious_observe: {
    left: { icon: "◔", label: "观察" },
    right: { icon: "✧", label: "试探" },
  },
  touch_affection: {
    left: { icon: "♡", label: "贴贴" },
    right: { icon: "✿", label: "亲近" },
  },
  cute_probe: {
    left: { icon: "☺", label: "卖萌" },
    right: { icon: "✦", label: "小心试探" },
  },
  daydream: {
    left: { icon: "☁", label: "发呆" },
    right: { icon: "✦", label: "走神" },
  },
  standup_reminder: {
    left: { icon: "↗", label: "起身" },
    right: { icon: "♪", label: "动一动" },
  },
  track_target: {
    left: { icon: "◎", label: "锁定" },
    right: { icon: "⌁", label: "跟随" },
  },
  celebrate: {
    left: { icon: "✺", label: "烟花" },
    right: { icon: "✦", label: "高光时刻" },
  },
  farewell: {
    left: { icon: "〰", label: "挥手" },
    right: { icon: "✧", label: "送别" },
  },
  sleep: {
    left: { icon: "☾", label: "月亮" },
    right: { icon: "Zz", label: "晚安" },
  },
};

const SCENE_BURSTS = {
  wake_up: {
    left: ["🌞", "🌤️", "🌼", "🌱"],
    right: ["☕", "✨", "🕊️", "🍯"],
  },
  curious_observe: {
    left: ["👀", "🔎", "🫧", "🪶"],
    right: ["🧠", "🪞", "🐾", "✨"],
  },
  touch_affection: {
    left: ["🫶", "💗", "🌷", "🎀"],
    right: ["🧸", "💌", "🌸", "🫧"],
  },
  cute_probe: {
    left: ["🐥", "🎀", "🧁", "🍮"],
    right: ["😊", "🐾", "💫", "🍓"],
  },
  daydream: {
    left: ["☁️", "💭", "🫧", "🪁"],
    right: ["🌙", "🕊️", "✨", "🫖"],
  },
  standup_reminder: {
    left: ["⏰", "🌞", "👟", "🌿"],
    right: ["🧃", "🎵", "🪴", "🪑"],
  },
  track_target: {
    left: ["🎯", "👁️", "📘", "🧭"],
    right: ["🛰️", "📡", "🔵", "🪐"],
  },
  celebrate: {
    left: ["🎆", "🎉", "🏆", "🍾"],
    right: ["🎇", "🎊", "💎", "🎈"],
  },
  farewell: {
    left: ["👋", "🌆", "🍃", "🚪"],
    right: ["🧳", "💌", "🕊️", "🌙"],
  },
  sleep: {
    left: ["🌙", "🛏️", "⭐", "🕯️"],
    right: ["💤", "☁️", "🧸", "🌌"],
  },
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

function readCueMode() {
  return localStorage.getItem("mira-light-cue-mode") === "scene" ? "scene" : "director";
}

function writeCueMode(mode) {
  localStorage.setItem("mira-light-cue-mode", mode === "scene" ? "scene" : "director");
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

function currentSceneForPresentation() {
  const activeSceneId =
    runtimeState?.runningScene ||
    (runtimeState?.trackingActive ? "track_target" : null) ||
    selectedSceneId ||
    runtimeState?.lastFinishedScene ||
    scenes[0]?.id;
  return sceneById(activeSceneId);
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
  runtimeRunning.textContent = runtime.running ? "RUNNING" : runtime.trackingActive ? "TRACKING" : "IDLE";
  runtimeScene.textContent = runtime.runningScene || (runtime.trackingActive ? "track_target" : runtime.lastFinishedScene) || "-";
  runtimeStep.textContent =
    runtime.currentStepLabel ||
    (runtime.trackingActive ? `tracking ${runtime.trackingTarget?.horizontalZone || "-"}` : runtime.lastCommand) ||
    "-";
  runtimeDevice.textContent =
    runtime.deviceOnline === true ? "ONLINE" : runtime.deviceOnline === false ? "OFFLINE" : "UNKNOWN";
  runtimeError.textContent = runtime.lastError || "-";
  runtimeBaseUrl.textContent = runtime.baseUrl || "-";

  baseUrlInput.value = runtime.baseUrl || "";
  dryRunInput.checked = Boolean(runtime.dryRun);
  cueModeDirectorInput.checked = readCueMode() === "director";

  document.body.classList.toggle("is-running", Boolean(runtime.running));
  document.body.classList.toggle("is-error", Boolean(runtime.lastError));

  renderSceneGrid();
  renderDirectorSummary();
  renderVisionSummary();
  updateSceneAccent();
  renderMockOverview();
}

function renderVisionSummary() {
  const target = runtimeState?.trackingTarget || {};
  const targetActive = Boolean(runtimeState?.trackingActive);
  const targetCount = target.targetCount ?? "-";
  const trackId = target.trackId ?? "-";
  const lockState = target.selectedLockState || (targetActive ? "tracking" : "-");
  const horizontal = target.horizontalZone || "-";
  const vertical = target.verticalZone || "-";
  const distanceBand = target.distanceBand || "-";
  const detector = target.detector || "-";
  const confidence = typeof target.confidence === "number" ? target.confidence.toFixed(2) : "-";
  const lastTrigger = runtimeState?.lastTrigger;

  visionTargetTitle.textContent = targetActive ? `track ${trackId} · ${lockState}` : "无 live tracking";
  visionTargetSubtitle.textContent = `targets ${targetCount} · class ${target.targetClass || "-"}`;
  visionZone.textContent = `${horizontal} / ${vertical}`;
  visionDistance.textContent = `${distanceBand} · ${target.approachState || "-"}`;
  visionDetector.textContent = detector;
  visionConfidence.textContent = confidence;
  if (lastTrigger?.event) {
    visionLastTrigger.textContent = `${lastTrigger.event} -> ${lastTrigger.scene || "-"}`;
  } else {
    visionLastTrigger.textContent = "-";
  }

  const lockedTrackId = visionOperatorState?.lockSelectedTrackId;
  visionOperatorLock.textContent = lockedTrackId ? `track ${lockedTrackId}` : "未锁定";
  visionOperatorNote.textContent = visionOperatorState?.note || (lockedTrackId ? "导演台手动锁定中" : "跟随当前自动选择");

  const latestEvent = visionState?.latestEvent || {};
  const selectedTarget = latestEvent.selected_target || null;
  const tracks = Array.isArray(latestEvent.tracks) ? latestEvent.tracks : [];
  const sceneHint = latestEvent.scene_hint || {};

  if (selectedTarget) {
    visionTargetTitle.textContent = `track ${selectedTarget.track_id} · ${selectedTarget.lock_state || "selected"}`;
    visionTargetSubtitle.textContent = `${selectedTarget.target_class || "-"} · ${sceneHint.name || "-"}`;
    visionZone.textContent = `${selectedTarget.horizontal_zone || "-"} / ${selectedTarget.vertical_zone || "-"}`;
    visionDistance.textContent = `${selectedTarget.distance_band || "-"} · ${selectedTarget.approach_state || "-"}`;
    visionDetector.textContent = selectedTarget.detector || detector;
    visionConfidence.textContent =
      typeof selectedTarget.confidence === "number" ? selectedTarget.confidence.toFixed(2) : confidence;
  }

  renderVisionTrackList(tracks, selectedTarget, sceneHint);
}

function renderVisionTrackList(tracks, selectedTarget, sceneHint) {
  if (!visionTrackList) return;
  visionTrackList.innerHTML = "";

  const summary = document.createElement("div");
  summary.className = "vision-track-empty";
  const trackCount = tracks?.length || 0;
  summary.textContent = `tracks ${trackCount} · scene_hint ${sceneHint?.name || "-"} · ${sceneHint?.reason || "-"}`;
  visionTrackList.appendChild(summary);

  if (!tracks || tracks.length === 0) {
    const empty = document.createElement("div");
    empty.className = "vision-track-empty";
    empty.textContent = "当前没有可视目标。";
    visionTrackList.appendChild(empty);
    return;
  }

  tracks
    .slice()
    .sort((a, b) => (b.selection_score || 0) - (a.selection_score || 0))
    .forEach((track) => {
      const card = document.createElement("div");
      card.className = "vision-track-card";
      if (selectedTarget && track.track_id === selectedTarget.track_id) {
        card.classList.add("is-selected");
      }

      const confidence = typeof track.confidence === "number" ? track.confidence.toFixed(2) : "-";
      const score = typeof track.selection_score === "number" ? track.selection_score.toFixed(2) : "-";
      const chip =
        selectedTarget && track.track_id === selectedTarget.track_id
          ? selectedTarget.lock_state || "selected"
          : "candidate";

      card.innerHTML = `
        <div class="vision-track-head">
          <strong>#${track.track_id}</strong>
          <span class="vision-track-chip">${chip}</span>
        </div>
        <div class="vision-track-meta">
          <span>${track.target_class || "-"}</span>
          <span>${track.detector || "-"}</span>
          <span>conf ${confidence}</span>
        </div>
        <div class="vision-track-meta">
          <span>${track.horizontal_zone || "-"}</span>
          <span>${track.vertical_zone || "-"}</span>
          <span>${track.distance_band || "-"}</span>
          <span>score ${score}</span>
        </div>
      `;

      const actions = document.createElement("div");
      actions.className = "vision-track-actions";
      const lockButton = document.createElement("button");
      lockButton.type = "button";
      lockButton.textContent = "锁定";
      lockButton.addEventListener("click", () => {
        setVisionOperatorLock(track.track_id, `lock track ${track.track_id} from director console`);
      });
      actions.appendChild(lockButton);
      card.appendChild(actions);
      visionTrackList.appendChild(card);
    });
}

function setProfileFlash(message, tone = "default") {
  if (!profileFlash) return;
  profileFlash.textContent = message;
  profileFlash.dataset.tone = tone;
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
    card.disabled = Boolean(runtimeState?.running || runtimeState?.trackingActive);
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
      triggerSceneBurst(scene.id);
      try {
        const payload = { cueMode: readCueMode() };
        if (scene.id === "farewell") {
          payload.context = { departureDirection: farewellDirectionInput.value };
        }
        await fetchJson(`/api/run/${encodeURIComponent(scene.id)}`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
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
  const scene = currentSceneForPresentation();
  const readinessState = readAttachmentState();

  if (!scene) {
    summarySceneTitle.textContent = "-";
    summarySceneId.textContent = "-";
    summaryCurrentStep.textContent = "-";
    summaryStepCounter.textContent = "-";
    summaryHostCue.textContent = "-";
    summaryFallback.textContent = "-";
    summaryRequirements.innerHTML = "";
    updateSceneAccent();
    return;
  }

  summarySceneTitle.textContent = scene.title;
  summarySceneId.textContent = `${scene.id} · ${readinessLabel(scene.readiness)}`;
  summaryCurrentStep.textContent =
    runtimeState?.currentStepLabel ||
    (runtimeState?.trackingActive ? `live tracking · ${runtimeState?.trackingTarget?.horizontalZone || "-"}` : "等待触发");

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

  updateSceneAccent();
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

function setVisionFlash(message, tone = "default") {
  if (!visionLockFlash) return;
  visionLockFlash.textContent = message;
  visionLockFlash.dataset.tone = tone;
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

function clampByte(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.max(0, Math.min(255, Math.round(numeric)));
}

function normalizePixelSignal(pixel, fallbackBrightness = 255) {
  if (pixel && typeof pixel === "object" && !Array.isArray(pixel)) {
    return {
      r: clampByte(pixel.r),
      g: clampByte(pixel.g),
      b: clampByte(pixel.b),
      brightness: clampByte(pixel.brightness ?? fallbackBrightness),
    };
  }
  if (Array.isArray(pixel) && pixel.length >= 3) {
    return {
      r: clampByte(pixel[0]),
      g: clampByte(pixel[1]),
      b: clampByte(pixel[2]),
      brightness: clampByte(pixel[3] ?? fallbackBrightness),
    };
  }
  return { r: 0, g: 0, b: 0, brightness: clampByte(fallbackBrightness) };
}

function derivePixelSignals(led) {
  if (!led) return [];

  if (Array.isArray(led.pixelSignals) && led.pixelSignals.length > 0) {
    return led.pixelSignals.map((pixel) => normalizePixelSignal(pixel, led.brightness ?? 255));
  }

  if (Array.isArray(led.pixels) && led.pixels.length > 0) {
    return led.pixels.map((pixel) => normalizePixelSignal(pixel, led.brightness ?? 255));
  }

  const ledCount = led.led_count || led.ledCount || 40;
  const color = normalizePixel(led.color || { r: 255, g: 255, b: 255 });
  const brightness = clampByte(led.brightness ?? 255);
  return Array.from({ length: ledCount }, () => ({
    ...color,
    brightness,
  }));
}

function rgbToCss(pixel) {
  const { r, g, b } = normalizePixel(pixel);
  return `rgb(${r}, ${g}, ${b})`;
}

function renderPixelRing(pixelSignals, activeCount, averageBrightness, mode) {
  if (!mockPixelRing) return;

  mockPixelRing.innerHTML = "";
  if (!Array.isArray(pixelSignals) || pixelSignals.length === 0) {
    if (mockPixelRingActive) mockPixelRingActive.textContent = "-";
    if (mockPixelRingCaption) mockPixelRingCaption.textContent = "等待 LED 状态";
    return;
  }

  const fragment = document.createDocumentFragment();
  pixelSignals.forEach((pixel, index) => {
    const node = document.createElement("div");
    node.className = "mock-ring-pixel";
    node.title = `#${index + 1} [${pixel.r}, ${pixel.g}, ${pixel.b}, ${pixel.brightness}]`;
    node.style.setProperty("--angle", `${(360 / pixelSignals.length) * index}deg`);
    node.style.setProperty("--pixel-color", rgbToCss(pixel));
    node.style.setProperty("--pixel-brightness", `${Math.max(14, Math.round((pixel.brightness / 255) * 100))}%`);
    node.style.setProperty("--pixel-alpha", `${0.24 + (pixel.brightness / 255) * 0.76}`);
    if (pixel.brightness > 0) {
      node.dataset.active = "true";
    }
    fragment.appendChild(node);
  });
  mockPixelRing.appendChild(fragment);

  if (mockPixelRingActive) {
    mockPixelRingActive.textContent = `${activeCount}/${pixelSignals.length}`;
  }
  if (mockPixelRingCaption) {
    mockPixelRingCaption.textContent = `${mode || "solid"} · avg ${averageBrightness}`;
  }
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

  const headCapacitive =
    sensorsState?.headCapacitive ??
    sensorsState?.sensors?.headCapacitive ??
    statusState?.sensors?.headCapacitive ??
    null;
  const headCapacitiveKnown = headCapacitive === 0 || headCapacitive === 1;
  if (mockHeadCapacitiveValue) {
    mockHeadCapacitiveValue.textContent = headCapacitiveKnown ? `${headCapacitive}` : "-";
  }
  if (mockHeadCapacitiveHint) {
    mockHeadCapacitiveHint.textContent =
      headCapacitive === 1 ? "已触发触摸 / 接近状态" : headCapacitive === 0 ? "当前为空闲 / 未触摸" : "等待传感器状态";
  }
  if (mockSensorBadge) {
    mockSensorBadge.textContent = headCapacitive === 1 ? "TOUCH" : headCapacitive === 0 ? "IDLE" : "UNKNOWN";
    mockSensorBadge.dataset.state = headCapacitive === 1 ? "active" : headCapacitive === 0 ? "idle" : "unknown";
  }
  if (mockHeadCapacitiveToggle && document.activeElement !== mockHeadCapacitiveToggle) {
    mockHeadCapacitiveToggle.checked = headCapacitive === 1;
  }
  if (mockTouchVisual) {
    mockTouchVisual.dataset.state = headCapacitive === 1 ? "active" : headCapacitive === 0 ? "idle" : "unknown";
  }
  if (mockTouchCaption) {
    mockTouchCaption.textContent =
      headCapacitive === 1 ? "灯头电容已触发，当前应视为触摸 / 贴近。" : headCapacitive === 0 ? "灯头电容空闲，可继续等待接触。" : "暂未拿到灯头电容状态。";
  }

  if (!ledState) {
    mockLedMode.textContent = "-";
    mockLedMeta.textContent = "等待 LED 状态";
    mockLedNote.textContent = "等待 LED 状态";
    if (mockPixelSignalSummary) mockPixelSignalSummary.textContent = "-";
    if (mockPixelSignalHint) mockPixelSignalHint.textContent = "等待 LED signal";
    mockColorSwatch.style.background = "linear-gradient(135deg, rgba(255,255,255,0.9), rgba(220,224,255,0.7))";
    mockServoGrid.innerHTML = "";
    renderPixelRing([], 0, 0, "-");
    mockPixelStrip.innerHTML = "";
    return;
  }

  mockLedMode.textContent = ledState.mode || "-";
  const pixelSignals = derivePixelSignals(ledState);
  const ledCount = pixelSignals.length || ledState.led_count || ledState.ledCount || 0;
  const activeCount = pixelSignals.filter((pixel) => pixel.brightness > 0).length;
  const averageBrightness =
    pixelSignals.length > 0
      ? Math.round(pixelSignals.reduce((sum, pixel) => sum + pixel.brightness, 0) / pixelSignals.length)
      : 0;
  mockLedMeta.textContent = `brightness ${ledState.brightness ?? averageBrightness} · ${ledCount} px · active ${activeCount}`;
  if (mockPixelSignalSummary) {
    mockPixelSignalSummary.textContent = `${activeCount}/${ledCount} active · avg ${averageBrightness}`;
  }
  if (mockPixelSignalHint) {
    mockPixelSignalHint.textContent =
      ledState.mode === "vector"
        ? "每格显示颜色与亮度；悬停可查看完整 signal。"
        : "当前不是 vector 模式，面板按统一色和亮度推断信号。";
  }
  renderPixelRing(pixelSignals, activeCount, averageBrightness, ledState.mode || "solid");

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

  if (ledState.mode === "vector") {
    mockLedNote.textContent = `当前为 vector 模式，预览 ${pixelSignals.length} 个 pixelSignals。`;
  } else {
    mockLedNote.textContent = `当前为 ${ledState.mode || "solid"} 模式，面板按统一色推断 40 灯 signal。`;
  }

  const swatchColor = pixelSignals[0] || normalizePixelSignal(ledState.color, ledState.brightness ?? 255);
  mockColorSwatch.style.background = rgbToCss(swatchColor);

  mockPixelStrip.innerHTML = "";
  pixelSignals.forEach((pixel, index) => {
    const card = document.createElement("div");
    card.className = "mock-pixel";
    card.title = `#${index + 1} [${pixel.r}, ${pixel.g}, ${pixel.b}, ${pixel.brightness}]`;

    const color = rgbToCss(pixel);
    card.style.setProperty("--pixel-color", color);
    card.style.setProperty("--pixel-brightness", `${Math.max(10, Math.round((pixel.brightness / 255) * 100))}%`);
    card.style.opacity = `${0.35 + (pixel.brightness / 255) * 0.65}`;

    card.innerHTML = `
      <span class="mock-pixel-index">${String(index + 1).padStart(2, "0")}</span>
      <span class="mock-pixel-glow"></span>
      <span class="mock-pixel-brightness">${pixel.brightness}</span>
    `;
    mockPixelStrip.appendChild(card);
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
    } else if (item.text.includes("[audio")) {
      row.classList.add("is-step");
    } else if (item.text.includes("[trigger]") || item.text.includes("[cue-")) {
      row.classList.add("is-scene");
    } else if (item.text.includes("[pose]") || item.text.includes("[action]")) {
      row.classList.add("is-step");
    }
    logOutput.appendChild(row);
  });

  logOutput.scrollTop = logOutput.scrollHeight;
}

function renderVisionState(payload) {
  visionState = payload;
  renderVisionSummary();
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
      <div class="servo-copy">
        <strong>${servoName}</strong>
        <small>${data.label || "-"}</small>
      </div>
      <div class="servo-values">
        <span>N ${data.neutral ?? "-"}</span>
        <span>R ${(data.rehearsal_range || []).join(" ~ ") || "-"}</span>
        <span>${data.verified ? "verified" : "draft"}</span>
      </div>
      <div class="servo-editor">
        <input data-field="label" value="${data.label || ""}" placeholder="label" />
        <input data-field="neutral" type="number" value="${data.neutral ?? ""}" placeholder="neutral" />
        <div class="servo-range-inline">
          <input data-field="rehearsal-min" type="number" value="${data.rehearsal_range?.[0] ?? ""}" placeholder="min" />
          <input data-field="rehearsal-max" type="number" value="${data.rehearsal_range?.[1] ?? ""}" placeholder="max" />
        </div>
        <label class="checkbox compact">
          <input data-field="verified" type="checkbox" ${data.verified ? "checked" : ""} />
          <span>verified</span>
        </label>
        <button type="button" class="servo-save">保存 ${servoName}</button>
      </div>
    `;
    row.querySelector(".servo-save").addEventListener("click", () => saveServoMeta(servoName, row));
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
  const scene = currentSceneForPresentation();
  document.body.dataset.scene = scene?.id || "default";
  renderSceneDecor(scene);
}

function renderSceneDecor(scene) {
  const decor = SCENE_DECOR[scene?.id] || {
    left: { icon: "✦", label: "Mira" },
    right: { icon: "✧", label: "Light" },
  };
  if (sceneDecorLeftIcon) sceneDecorLeftIcon.textContent = decor.left.icon;
  if (sceneDecorLeftLabel) sceneDecorLeftLabel.textContent = decor.left.label;
  if (sceneDecorRightIcon) sceneDecorRightIcon.textContent = decor.right.icon;
  if (sceneDecorRightLabel) sceneDecorRightLabel.textContent = decor.right.label;
  scheduleSceneDecorPlacement();
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function randomBetween(min, max) {
  return min + Math.random() * (max - min);
}

function scheduleSceneDecorPlacement() {
  if (sceneDecorFrame) {
    window.cancelAnimationFrame(sceneDecorFrame);
  }
  sceneDecorFrame = window.requestAnimationFrame(() => {
    sceneDecorFrame = 0;
    updateSceneDecorPlacement();
  });
}

function placeSticker(element, { left = null, right = null, top = 96, mode = "gutter", rotate = 0 }) {
  if (!element) return;
  element.classList.toggle("is-overlay", mode === "overlay");
  element.style.left = left == null ? "" : `${Math.round(left)}px`;
  element.style.right = right == null ? "" : `${Math.round(right)}px`;
  element.style.top = `${Math.round(top)}px`;
  element.style.setProperty("--sticker-rotate", `${rotate}deg`);
}

function updateSceneDecorPlacement() {
  if (!pageShell || !sceneDecorLeft || !sceneDecorRight) return;

  const rect = pageShell.getBoundingClientRect();
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const stickerWidth = viewportWidth < 760 ? 104 : viewportWidth < 1260 ? 118 : 136;
  const sidePadding = viewportWidth < 760 ? 10 : 18;
  const leftGap = Math.max(0, rect.left);
  const rightGap = Math.max(0, viewportWidth - rect.right);
  const leftHasGutter = leftGap >= stickerWidth + sidePadding;
  const rightHasGutter = rightGap >= stickerWidth + sidePadding;

  const upperTop = clamp(viewportHeight * 0.16, 78, Math.max(78, viewportHeight - 236));
  const lowerTop = clamp(viewportHeight * 0.68, upperTop + 114, Math.max(upperTop + 114, viewportHeight - 132));

  const leftGutterLeft = clamp((leftGap - stickerWidth) / 2, 12, Math.max(12, leftGap - stickerWidth - 8));
  const rightGutterRight = clamp((rightGap - stickerWidth) / 2, 12, Math.max(12, rightGap - stickerWidth - 8));

  const leftOverlayLeft = clamp(Math.max(12, rect.left - stickerWidth * 0.1), 12, Math.max(12, viewportWidth - stickerWidth - 12));
  const rightOverlayRight = clamp(Math.max(12, viewportWidth - rect.right - stickerWidth * 0.1), 12, Math.max(12, viewportWidth - stickerWidth - 12));

  placeSticker(sceneDecorLeft, {
    left: leftHasGutter ? leftGutterLeft : leftOverlayLeft,
    top: upperTop,
    mode: leftHasGutter ? "gutter" : "overlay",
    rotate: -8,
  });
  placeSticker(sceneDecorRight, {
    right: rightHasGutter ? rightGutterRight : rightOverlayRight,
    top: lowerTop,
    mode: rightHasGutter ? "gutter" : "overlay",
    rotate: 7,
  });
}

function getSparkAnchor(element, side) {
  const target = element?.querySelector(".scene-charm") || element;
  if (!target) return null;
  const rect = target.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  return {
    side,
    x: rect.left + rect.width / 2,
    y: rect.top + rect.height / 2,
  };
}

function addSparkFlare(anchor, accent) {
  if (!sceneSparkLayer) return;
  const flare = document.createElement("span");
  flare.className = "scene-spark-flare";
  flare.style.left = `${anchor.x}px`;
  flare.style.top = `${anchor.y}px`;
  flare.style.setProperty("--spark-color", accent);
  flare.style.setProperty("--flare-size", `${randomBetween(54, 82).toFixed(0)}px`);
  flare.addEventListener("animationend", () => flare.remove(), { once: true });
  sceneSparkLayer.appendChild(flare);
}

function getBurstOrigin(leftAnchor, rightAnchor) {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const fallbackY = clamp(viewportHeight * 0.38, 156, viewportHeight - 180);
  return {
    x: (leftAnchor?.x + rightAnchor?.x) / 2 || viewportWidth / 2,
    y: clamp(((leftAnchor?.y || fallbackY) + (rightAnchor?.y || fallbackY)) / 2, 140, viewportHeight - 160),
  };
}

function addBurstSticker(origin, target, icon, accent, index) {
  if (!sceneSparkLayer) return;
  const spark = document.createElement("span");
  spark.className = "scene-spark";
  spark.textContent = icon;
  spark.style.left = `${origin.x.toFixed(1)}px`;
  spark.style.top = `${origin.y.toFixed(1)}px`;
  spark.style.setProperty("--spark-color", accent);
  spark.style.setProperty("--spark-size", `${randomBetween(42, 54).toFixed(1)}px`);
  spark.style.setProperty("--spark-emoji-size", `${randomBetween(22, 28).toFixed(1)}px`);
  spark.style.setProperty("--spark-duration", `${randomBetween(920, 1320).toFixed(0)}ms`);
  spark.style.setProperty("--spark-delay", `${(index * 0.035 + randomBetween(0, 0.04)).toFixed(3)}s`);
  spark.style.setProperty("--spark-scale", randomBetween(0.92, 1.12).toFixed(2));
  spark.style.setProperty("--spark-rotate", `${randomBetween(-18, 18).toFixed(1)}deg`);
  spark.style.setProperty("--spark-dx", `${(target.x - origin.x).toFixed(1)}px`);
  spark.style.setProperty("--spark-dy", `${(target.y - origin.y).toFixed(1)}px`);
  spark.addEventListener("animationend", () => spark.remove(), { once: true });
  sceneSparkLayer.appendChild(spark);
}

function triggerSceneBurst(sceneId) {
  if (!sceneSparkLayer) return;
  scheduleSceneDecorPlacement();
  const accent = window.getComputedStyle(document.body).getPropertyValue("--scene-accent").trim() || "#ff6b9d";
  const burst = SCENE_BURSTS[sceneId] || {
    left: ["🌟", "🫧", "🌈", "💫"],
    right: ["🌙", "🕊️", "✨", "🎐"],
  };

  window.requestAnimationFrame(() => {
    const leftAnchor = getSparkAnchor(sceneDecorLeft, "left");
    const rightAnchor = getSparkAnchor(sceneDecorRight, "right");
    if (!leftAnchor || !rightAnchor) return;

    const origin = getBurstOrigin(leftAnchor, rightAnchor);
    addSparkFlare(origin, accent);

    const leftIcons = burst.left.slice(0, Math.max(3, burst.left.length));
    const rightIcons = burst.right.slice(0, Math.max(3, burst.right.length));

    leftIcons.forEach((icon, index) => {
      const spreadIndex = index - (leftIcons.length - 1) / 2;
      addBurstSticker(
        origin,
        {
          x: leftAnchor.x + randomBetween(-28, 20),
          y: clamp(leftAnchor.y + spreadIndex * 52 + randomBetween(-10, 10), 92, window.innerHeight - 92),
        },
        icon,
        accent,
        index,
      );
    });

    rightIcons.forEach((icon, index) => {
      const spreadIndex = index - (rightIcons.length - 1) / 2;
      addBurstSticker(
        origin,
        {
          x: rightAnchor.x + randomBetween(-20, 28),
          y: clamp(rightAnchor.y + spreadIndex * 52 + randomBetween(-10, 10), 92, window.innerHeight - 92),
        },
        icon,
        accent,
        leftIcons.length + index,
      );
    });
  });
}

async function refreshRuntime() {
  const data = await fetchJson("/api/runtime");
  renderRuntime(data.runtime);
}

async function refreshVisionOperator() {
  const data = await fetchJson("/api/vision-operator");
  visionOperatorState = data.state || {};
  renderVisionSummary();
}

async function refreshVisionState() {
  const data = await fetchJson("/api/vision");
  visionState = data;
  renderVisionSummary();
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
  sensorsState = data.data?.sensors || sensorsState;
  renderJson(statusOutput, data.data);
  renderMockOverview();
}

async function refreshLed() {
  const data = await fetchJson("/api/led");
  ledState = data.data;
  renderJson(ledOutput, data.data);
  renderMockOverview();
}

async function refreshSensors(options = {}) {
  const { silent = true } = options;
  try {
    const data = await fetchJson("/api/sensors");
    sensorsState = data.data?.sensors || data.data || null;
  } catch (error) {
    sensorsState = statusState?.sensors || sensorsState;
    if (!silent) {
      throw error;
    }
  }
  renderMockOverview();
}

async function refreshActions() {
  const data = await fetchJson("/api/actions");
  actionsState = data.data;
  renderJson(actionsOutput, data.data);
}

async function refreshVision() {
  const data = await fetchJson("/api/vision");
  renderVisionState(data);
}

async function refreshProfile() {
  const data = await fetchJson("/api/profile");
  renderProfile(data.profile);
}

async function capturePose() {
  const name = capturePoseNameInput.value.trim();
  if (!name) {
    setProfileFlash("先填一个 pose 名称。", "error");
    return;
  }

  try {
    const data = await fetchJson("/api/profile/capture-pose", {
      method: "POST",
      body: JSON.stringify({
        name,
        notes: capturePoseNotesInput.value.trim(),
        verified: capturePoseVerifiedInput.checked,
      }),
    });
    setProfileFlash(`已捕获 pose: ${data.data.saved}`, "success");
    await Promise.all([refreshProfile(), refreshStatus(), refreshLogs()]);
  } catch (error) {
    setProfileFlash(error.message, "error");
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function saveServoMeta(servoName, row) {
  const label = row.querySelector('[data-field="label"]').value.trim();
  const neutral = row.querySelector('[data-field="neutral"]').value.trim();
  const rehearsalMin = row.querySelector('[data-field="rehearsal-min"]').value.trim();
  const rehearsalMax = row.querySelector('[data-field="rehearsal-max"]').value.trim();
  const verified = row.querySelector('[data-field="verified"]').checked;

  if ((rehearsalMin === "") !== (rehearsalMax === "")) {
    setProfileFlash("rehearsal min/max 需要一起填写。", "error");
    return;
  }

  const payload = {
    servo: servoName,
    label: label || null,
    neutral: neutral === "" ? null : Number(neutral),
    rehearsalRange:
      rehearsalMin === "" && rehearsalMax === ""
        ? null
        : [Number(rehearsalMin || 0), Number(rehearsalMax || 0)],
    verified,
  };

  try {
    await fetchJson("/api/profile/set-servo-meta", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setProfileFlash(`已更新 ${servoName}。`, "success");
    await refreshProfile();
  } catch (error) {
    setProfileFlash(error.message, "error");
    appendLocalLog(`[ui-error] ${error.message}`);
  }
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

async function triggerEvent(eventName, payload = {}) {
  try {
    await fetchJson("/api/trigger", {
      method: "POST",
      body: JSON.stringify({
        event: eventName,
        payload,
      }),
    });
    await Promise.all([refreshRuntime(), refreshLogs(), refreshStatus(), refreshLed()]);
  } catch (error) {
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function setVisionOperatorLock(lockSelectedTrackId, note = "") {
  try {
    const data = await fetchJson("/api/vision-operator", {
      method: "POST",
      body: JSON.stringify({
        lockSelectedTrackId,
        note,
        updatedAt: new Date().toISOString(),
      }),
    });
    visionOperatorState = data.state || {};
    renderVisionSummary();
    appendLocalLog(`vision operator lock updated: ${visionOperatorState.lockSelectedTrackId ?? "none"}`);
  } catch (error) {
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function applyHeadCapacitive() {
  if (!mockHeadCapacitiveToggle) return;
  const nextValue = mockHeadCapacitiveToggle.checked ? 1 : 0;
  try {
    const data = await fetchJson("/api/sensors", {
      method: "POST",
      body: JSON.stringify({ headCapacitive: nextValue }),
    });
    sensorsState = data.data?.sensors || data.data || { headCapacitive: nextValue };
    renderMockOverview();
    appendLocalLog(`headCapacitive set to ${nextValue}`);
    await Promise.all([refreshStatus(), refreshLogs()]);
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

async function setVisionLock(trackId) {
  try {
    await fetchJson("/api/vision/lock", {
      method: "POST",
      body: JSON.stringify({ trackId }),
    });
    setVisionFlash(`已锁定 track #${trackId}`, "success");
    await refreshVision();
  } catch (error) {
    setVisionFlash(error.message, "error");
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

async function clearVisionLock() {
  try {
    await fetchJson("/api/vision/lock/clear", {
      method: "POST",
      body: JSON.stringify({}),
    });
    setVisionFlash("已清除目标锁定", "success");
    await refreshVision();
  } catch (error) {
    setVisionFlash(error.message, "error");
    appendLocalLog(`[ui-error] ${error.message}`);
  }
}

function bindClick(id, handler) {
  const element = document.getElementById(id);
  if (!element) return;
  element.addEventListener("click", handler);
}

bindClick("save-config", saveConfig);
bindClick("refresh-status", refreshStatus);
bindClick("refresh-led", refreshLed);
bindClick("mock-refresh-sensors", () => refreshSensors({ silent: false }));
bindClick("mock-apply-head-capacitive", applyHeadCapacitive);
bindClick("refresh-actions", refreshActions);
bindClick("refresh-vision", refreshVisionState);
bindClick("clear-vision-lock", clearVisionLock);
bindClick("apply-neutral", () => applyPose("neutral"));
bindClick("apply-sleep", () => applyPose("sleep"));
bindClick("stop-scene", stopScene);
bindClick("stop-neutral", () => operatorAction("/api/operator/stop-to-neutral"));
bindClick("stop-sleep", () => operatorAction("/api/operator/stop-to-sleep"));
bindClick("reset-lamp", resetLamp);
if (cueModeDirectorInput) {
  cueModeDirectorInput.addEventListener("change", () => {
    writeCueMode(cueModeDirectorInput.checked ? "director" : "scene");
  });
}
bindClick("trigger-touch", () => triggerEvent("touch_detected", { side: "center" }));
bindClick("trigger-sigh", () => triggerEvent("sigh_detected", { transcript: "唉" }));
bindClick("trigger-voice-tired", () => triggerEvent("voice_tired", { transcript: "我今天好累啊" }));
bindClick("trigger-multi-person", () =>
  triggerEvent("multi_person_detected", { primaryDirection: "left", secondaryDirection: "right" }),
);
bindClick("trigger-farewell", () =>
  triggerEvent("farewell_detected", { direction: farewellDirectionInput?.value || "right", cueMode: readCueMode() }),
);
bindClick("trigger-startle", () =>
  triggerEvent("startle_detected", { transcript: "突然一声响动", cueMode: readCueMode() }),
);
bindClick("trigger-praise", () =>
  triggerEvent("praise_detected", { transcript: "你好可爱", cueMode: readCueMode() }),
);
bindClick("trigger-criticism", () =>
  triggerEvent("criticism_detected", { transcript: "你今天有点不太行", cueMode: readCueMode() }),
);
bindClick("vision-lock-current", () => {
  const selectedTrackId = visionState?.latestEvent?.selected_target?.track_id;
  const trackId = selectedTrackId || runtimeState?.trackingTarget?.trackId;
  if (!trackId) {
    appendLocalLog("[ui-error] 当前没有可锁定的 tracking target");
    return;
  }
  setVisionOperatorLock(trackId, "lock current target from director console");
});
bindClick("vision-unlock", () => setVisionOperatorLock(null, "operator lock cleared"));
bindClick("capture-pose", capturePose);
bindClick("refresh-profile", refreshProfile);

async function bootstrap() {
  try {
    cueModeDirectorInput.checked = readCueMode() === "director";
    setProfileFlash("等待操作");
    renderReadinessPanel();
    await refreshRuntime();
    await refreshScenes();
    await refreshStatus();
    await refreshLed();
    await refreshSensors();
    await refreshActions();
    await refreshProfile();
    await refreshLogs();
    await refreshVisionState();
    await refreshVisionOperator();
  } catch (error) {
    appendLocalLog(`[bootstrap-error] ${error.message}`);
  }

  setInterval(async () => {
    try {
      await Promise.all([refreshRuntime(), refreshLogs(), refreshStatus(), refreshLed(), refreshActions()]);
      await refreshVisionState();
      await refreshVisionOperator();
      renderMockOverview();
    } catch (error) {
      appendLocalLog(`[poll-error] ${error.message}`);
    }
  }, 2500);
}

bootstrap();
scheduleSceneDecorPlacement();
window.addEventListener("resize", scheduleSceneDecorPlacement);
window.addEventListener("scroll", scheduleSceneDecorPlacement, { passive: true });
window.visualViewport?.addEventListener("resize", scheduleSceneDecorPlacement);

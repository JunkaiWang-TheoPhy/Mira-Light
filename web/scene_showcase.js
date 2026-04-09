const config = window.SCENE_SHOWCASE_CONFIG;

const triggerButton = document.getElementById("trigger-scene");
const refreshButton = document.getElementById("refresh-runtime");
const stopButton = document.getElementById("stop-scene");
const webPhase = document.getElementById("web-phase");
const lampPhase = document.getElementById("lamp-phase");
const runtimeScene = document.getElementById("runtime-scene");
const runtimeStep = document.getElementById("runtime-step");
const runtimeNote = document.getElementById("runtime-note");

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

function setWebPhase(value) {
  webPhase.textContent = value;
}

async function refreshRuntime() {
  try {
    const data = await fetchJson("/api/runtime");
    const runtime = data.runtime;
    runtimeScene.textContent = runtime.runningScene || runtime.lastFinishedScene || "-";
    runtimeStep.textContent = runtime.currentStepLabel || runtime.lastCommand || "-";

    if (runtime.runningScene === config.sceneId) {
      lampPhase.textContent = "running";
      runtimeNote.textContent = `真实 Mira 正在执行 ${config.sceneId}`;
    } else if (runtime.lastError) {
      lampPhase.textContent = "runtime error";
      runtimeNote.textContent = runtime.lastError;
    } else if (runtime.deviceOnline === false) {
      lampPhase.textContent = "offline";
      runtimeNote.textContent = "设备离线，当前页面仅作为动作展示页";
    } else if (runtime.deviceOnline === true) {
      lampPhase.textContent = "ready";
      runtimeNote.textContent = config.readyNote || "设备在线，可直接触发场景。";
    } else {
      lampPhase.textContent = "unknown";
      runtimeNote.textContent = config.readyNote || "等待 runtime 状态返回。";
    }
  } catch (error) {
    lampPhase.textContent = "api unavailable";
    runtimeNote.textContent = error.message;
  }
}

async function triggerScene() {
  setWebPhase("triggering");
  runtimeNote.textContent = `尝试触发 ${config.sceneId} 场景`;
  try {
    await fetchJson(`/api/run-motion-script/${encodeURIComponent(config.sceneId)}`, { method: "POST" });
    setWebPhase("running");
    await refreshRuntime();
  } catch (error) {
    setWebPhase("error");
    runtimeNote.textContent = error.message;
  }
}

async function stopScene() {
  setWebPhase("stopping");
  try {
    await fetchJson("/api/stop", { method: "POST" });
    setWebPhase("idle");
    await refreshRuntime();
  } catch (error) {
    setWebPhase("error");
    runtimeNote.textContent = error.message;
  }
}

triggerButton?.addEventListener("click", triggerScene);
refreshButton?.addEventListener("click", refreshRuntime);
stopButton?.addEventListener("click", stopScene);

refreshRuntime();
window.setInterval(refreshRuntime, 2500);

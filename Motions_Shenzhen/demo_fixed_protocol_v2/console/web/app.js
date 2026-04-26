const sceneGrid = document.getElementById("scene-grid");
const quickGrid = document.getElementById("quick-grid");
const queueList = document.getElementById("queue-list");
const queueSummary = document.getElementById("queue-summary");
const output = document.getElementById("output");
const outputTitle = document.getElementById("output-title");
const boardSummary = document.getElementById("board-summary");
const passwordSummary = document.getElementById("password-summary");
const running = document.getElementById("running");
const current = document.getElementById("current");
const lastCode = document.getElementById("last-code");
const servoPositionSummary = document.getElementById("servo-position-summary");
const refreshServosButton = document.getElementById("refresh-servos");
const servoIds = ["0", "1", "2", "3"];
const servoPositionEls = servoIds.map((id) => document.getElementById(`servo-pos-${id}`));
const servoTargetEls = servoIds.map((id) => document.getElementById(`servo-target-${id}`));
const servoStepInput = document.getElementById("servo-step");
const servoControlButtons = Array.from(document.querySelectorAll("[data-servo-delta]"));
const hostInput = document.getElementById("host");
const portInput = document.getElementById("port");
const userInput = document.getElementById("user");
const passwordInput = document.getElementById("password");

let registry = null;
let lastRenderedResultKey = null;
let latestState = null;
let servoRefreshInFlight = false;
let servoControlInFlight = false;
let servoControlPending = false;
let servoHoldTimer = null;
const servoTargets = Object.fromEntries(servoIds.map((id) => [id, null]));
const servoMin = 0;
const servoMax = 4095;

function connectionPayload() {
  return {
    host: hostInput.value.trim(),
    port: Number(portInput.value || 22),
    user: userInput.value.trim(),
    password: passwordInput.value,
  };
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

function riskLabel(risk) {
  const labels = {
    "light-only": "只动灯",
    "read-only": "只读",
    "motion-medium": "中风险机械",
    "motion-high": "高风险机械",
  };
  return labels[risk] || risk;
}

function showOutput(title, payload) {
  outputTitle.textContent = title;
  output.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
}

function cleanRemoteOutput(text) {
  return String(text || "")
    .replace(/\r/g, "")
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      return trimmed && !trimmed.startsWith("spawn ssh ") && !trimmed.includes("'s password:");
    })
    .join("\n")
    .trim();
}

function parseServoPositions(stdout) {
  const positions = {};
  let currentId = null;
  for (const line of String(stdout || "").replace(/\r/g, "").split("\n")) {
    const idMatch = line.match(/^Read ID\s*:\s*(\d+)/);
    if (idMatch) {
      currentId = idMatch[1];
      continue;
    }
    const positionMatch = line.match(/^Position\s*:\s*(\d+)/);
    if (positionMatch && currentId !== null) {
      positions[currentId] = Number(positionMatch[1]);
      currentId = null;
    }
  }
  return positions;
}

function servoPositionLines(positions) {
  return servoIds
    .filter((id) => positions[id] !== undefined)
    .map((id) => `舵机 ${id}: ${positions[id]}`);
}

function clampServoPosition(value) {
  return Math.max(servoMin, Math.min(servoMax, Math.round(Number(value))));
}

function servoStepSize() {
  const value = Number(servoStepInput.value || 20);
  return Math.max(1, Math.min(200, Math.round(value)));
}

function hasCompleteServoTargets() {
  return servoIds.every((id) => Number.isFinite(servoTargets[id]));
}

function syncServoTargets(values, { force = false } = {}) {
  for (const id of servoIds) {
    if (values[id] !== undefined && (force || !Number.isFinite(servoTargets[id]))) {
      servoTargets[id] = clampServoPosition(values[id]);
    }
  }
  renderServoControls();
}

function renderServoControls() {
  for (let index = 0; index < servoTargetEls.length; index += 1) {
    const value = servoTargets[servoIds[index]];
    servoTargetEls[index].textContent = Number.isFinite(value) ? String(value) : "-";
  }

  const queueBusy = latestState && (latestState.running || (latestState.queue || []).length > 0);
  const externalControlBusy = latestState?.servoControl?.running && !servoControlInFlight;
  const disabled = queueBusy || externalControlBusy || !hasCompleteServoTargets();
  for (const button of servoControlButtons) {
    button.disabled = disabled;
  }
}

function manualServoErrorText(error) {
  if (!error) {
    return "";
  }
  if (String(error).includes("refresh")) {
    return "正在读取当前位置，稍后重试";
  }
  if (String(error).includes("queue")) {
    return "队列执行中，暂停微调";
  }
  return String(error);
}

async function sendServoTargets() {
  if (!hasCompleteServoTargets()) {
    servoPositionSummary.textContent = "请先刷新当前位置。";
    return;
  }
  if (servoControlInFlight) {
    servoControlPending = true;
    return;
  }

  servoControlInFlight = true;
  servoPositionSummary.textContent = "微调发送中...";
  try {
    const response = await fetch("/api/servo-control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...connectionPayload(),
        positions: Object.fromEntries(servoIds.map((id) => [id, servoTargets[id]])),
      }),
    });
    const data = await response.json();
    if (response.status === 409) {
      const message = data.error || "";
      servoPositionSummary.textContent = manualServoErrorText(message);
      if (message.includes("refresh") || message.includes("already running")) {
        servoControlPending = true;
      }
      return;
    }
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || data.servoPositions?.error || `HTTP ${response.status}`);
    }
    renderServoPositions(data.servoPositions);
    syncServoTargets(data.servoPositions.values || {}, { force: true });
    await refreshState();
  } catch (error) {
    servoPositionSummary.textContent = `微调失败：${error.message || String(error)}`;
  } finally {
    servoControlInFlight = false;
    if (servoControlPending) {
      servoControlPending = false;
      setTimeout(() => {
        sendServoTargets().catch(() => {});
      }, 120);
    }
  }
}

function nudgeServo(servoId, direction) {
  if (!Number.isFinite(servoTargets[servoId])) {
    servoPositionSummary.textContent = "请先刷新当前位置。";
    return;
  }
  servoTargets[servoId] = clampServoPosition(servoTargets[servoId] + direction * servoStepSize());
  renderServoControls();
  sendServoTargets().catch(() => {});
}

function stopServoHold() {
  if (servoHoldTimer !== null) {
    clearInterval(servoHoldTimer);
    servoHoldTimer = null;
  }
}

function startServoHold(button) {
  const row = button.closest("[data-servo-id]");
  if (!row || button.disabled) {
    return;
  }
  const servoId = row.dataset.servoId;
  const direction = Number(button.dataset.servoDelta);
  stopServoHold();
  nudgeServo(servoId, direction);
  servoHoldTimer = setInterval(() => nudgeServo(servoId, direction), 360);
}

function formatExecutionResult(result, options = {}) {
  const status = result.returnCode === 0 ? "完成" : "失败";
  const duration = Number.isFinite(result.durationSeconds) ? ` · ${result.durationSeconds}s` : "";
  const target = result.host ? ` · ${result.user || "root"}@${result.host}:${result.port}` : "";
  const header = `${status} · 返回码 ${result.returnCode}${duration}${target}`;
  const stderr = cleanRemoteOutput(result.stderr);

  if (options.actionId === "read_positions") {
    const positions = servoPositionLines(parseServoPositions(result.stdout));
    if (positions.length > 0) {
      return [`舵机当前位置`, positions.join("\n"), header, stderr ? `错误输出\n${stderr}` : ""]
        .filter(Boolean)
        .join("\n\n");
    }
  }

  const stdout = cleanRemoteOutput(result.stdout);
  return [header, stdout ? `输出\n${stdout}` : "", stderr ? `错误输出\n${stderr}` : ""]
    .filter(Boolean)
    .join("\n\n");
}

function sceneExtraInputId(sceneId) {
  return `extra-${sceneId}`;
}

function scenePayload(sceneId) {
  const input = document.getElementById(sceneExtraInputId(sceneId));
  return {
    ...connectionPayload(),
    extraArgs: input ? input.value.trim() : "",
  };
}

async function previewScene(scene) {
  const data = await fetchJson(`/api/preview/${encodeURIComponent(scene.id)}`, {
    method: "POST",
    body: JSON.stringify(scenePayload(scene.id)),
  });
  showOutput(`${scene.number} ${scene.title} · 预览`, data.script);
}

async function runScene(scene) {
  const data = await fetchJson(`/api/run/${encodeURIComponent(scene.id)}`, {
    method: "POST",
    body: JSON.stringify(scenePayload(scene.id)),
  });
  showOutput(`${scene.number} ${scene.title} · 已加入队列`, queueItemSummary(data.queued));
  await refreshState();
}

async function previewQuick(action) {
  const data = await fetchJson(`/api/quick-action/${encodeURIComponent(action.id)}`, {
    method: "POST",
    body: JSON.stringify({ ...connectionPayload(), preview: true }),
  });
  showOutput(`${action.title} · 预览`, data.script);
}

async function runQuick(action) {
  const data = await fetchJson(`/api/quick-action/${encodeURIComponent(action.id)}`, {
    method: "POST",
    body: JSON.stringify(connectionPayload()),
  });
  showOutput(`${action.title} · 已加入队列`, queueItemSummary(data.queued));
  await refreshState();
}

function queueStatusLabel(status) {
  const labels = {
    pending: "等待中",
    running: "执行中",
    done: "完成",
    failed: "失败",
    removed: "已删除",
  };
  return labels[status] || status;
}

function queueItemSummary(item) {
  if (!item) {
    return "已加入队列";
  }
  return [
    `队列 ID: ${item.queueId}`,
    `项目: ${item.title}`,
    `状态: ${queueStatusLabel(item.status)}`,
    `目标: ${item.user}@${item.host}:${item.port}`,
  ].join("\n");
}

async function deleteQueueItem(queueId) {
  const data = await fetchJson(`/api/queue/${encodeURIComponent(queueId)}`, {
    method: "DELETE",
  });
  showOutput("执行队列 · 已删除", queueItemSummary(data.removed));
  await refreshState();
}

function renderQueue(state) {
  const items = state.queue || [];
  const pendingCount = items.filter((item) => item.status === "pending").length;
  if (state.running || pendingCount > 0) {
    queueSummary.textContent = state.running ? `执行中 · ${pendingCount} 个等待` : `${pendingCount} 个等待`;
  } else {
    queueSummary.textContent = "空闲";
  }

  queueList.innerHTML = "";
  if (items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "queue-empty";
    empty.textContent = "当前没有等待或执行中的动作。";
    queueList.appendChild(empty);
    return;
  }

  for (const item of items) {
    const row = document.createElement("article");
    row.className = `queue-item ${item.status}`;

    const text = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = item.title;
    const meta = document.createElement("span");
    meta.textContent = `${queueStatusLabel(item.status)} · ${item.kind} · ${item.user}@${item.host}:${item.port} · ${item.queuedAt}`;
    text.append(title, meta);
    row.appendChild(text);

    if (item.status === "pending") {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "queue-remove";
      remove.textContent = "×";
      remove.setAttribute("aria-label", `删除 ${item.title}`);
      remove.addEventListener("click", () => wrap(() => deleteQueueItem(item.queueId)));
      row.appendChild(remove);
    }

    queueList.appendChild(row);
  }
}

function renderServoPositions(servoState = {}, { forceTargetSync = false } = {}) {
  const values = servoState.values || {};
  for (let index = 0; index < servoPositionEls.length; index += 1) {
    const value = values[String(index)];
    servoPositionEls[index].textContent = value === undefined ? "-" : String(value);
  }
  if (!servoControlInFlight && !servoControlPending) {
    syncServoTargets(values, { force: forceTargetSync });
  } else {
    renderServoControls();
  }

  if (servoState.running) {
    servoPositionSummary.textContent = "读取中...";
    return;
  }
  if (servoState.error) {
    servoPositionSummary.textContent = `读取失败：${servoState.error}`;
    return;
  }
  if (servoState.warning && servoState.updatedAt) {
    servoPositionSummary.textContent = `更新于 ${servoState.updatedAt}（已忽略尾部超时）`;
    return;
  }
  if (servoState.updatedAt) {
    servoPositionSummary.textContent = `更新于 ${servoState.updatedAt}`;
    return;
  }
  servoPositionSummary.textContent = "空闲时自动刷新。";
}

async function refreshServoPositions({ manual = false } = {}) {
  if (servoRefreshInFlight || servoControlInFlight || servoControlPending) {
    return;
  }
  if (!manual && latestState && (latestState.running || (latestState.queue || []).length > 0)) {
    renderServoPositions({ ...(latestState.servoPositions || {}), running: false });
    return;
  }

  servoRefreshInFlight = true;
  try {
    const response = await fetch("/api/servo-positions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(connectionPayload()),
    });
    const data = await response.json();
    if (response.status === 409) {
      const current = latestState ? latestState.servoPositions : {};
      renderServoPositions({ ...(current || {}), running: false, error: "动作执行中，暂停刷新" });
      return;
    }
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || data.servoPositions?.error || `HTTP ${response.status}`);
    }
    renderServoPositions(data.servoPositions, { forceTargetSync: manual });
    if (manual) {
      showOutput("舵机当前位置 · 刷新完成", servoPositionLines(data.servoPositions.values || {}).join("\n"));
    }
    await refreshState();
  } catch (error) {
    renderServoPositions({ values: {}, running: false, error: error.message || String(error) });
    if (manual) {
      showOutput("舵机当前位置 · 读取失败", error.message || String(error));
    }
  } finally {
    servoRefreshInFlight = false;
  }
}

function maybeRenderLastResult(state) {
  const result = state.lastResult;
  if (!result) {
    return;
  }
  const key = result.queueId || `${result.at}:${result.kind}:${result.id}:${result.returnCode}`;
  if (key === lastRenderedResultKey) {
    return;
  }
  lastRenderedResultKey = key;
  showOutput(`${result.title} · 执行结果`, formatExecutionResult(result, { actionId: result.id }));
}

function renderScenes() {
  sceneGrid.innerHTML = "";
  for (const scene of registry.scenes) {
    const card = document.createElement("article");
    card.className = `scene-card ${scene.risk}`;
    card.innerHTML = `
      <div class="scene-top">
        <span class="scene-number">${scene.number}</span>
        <span class="risk">${riskLabel(scene.risk)}</span>
      </div>
      <h3>${scene.title}</h3>
      <p class="subtitle">${scene.subtitle}</p>
      <dl>
        <dt>Operator Cue</dt>
        <dd>${scene.operatorCue}</dd>
        <dt>Success</dt>
        <dd>${scene.successSignal}</dd>
        <dt>Fallback</dt>
        <dd>${scene.fallbackBehavior}</dd>
      </dl>
      <label class="extra-label">
        Extra Args
        <input id="${sceneExtraInputId(scene.id)}" type="text" placeholder="${scene.defaultArgs.join(" ")}" />
      </label>
      <div class="button-row">
        <button type="button" data-action="preview">预览命令</button>
        <button type="button" class="execute" data-action="run">加入队列</button>
      </div>
    `;
    card.querySelector('[data-action="preview"]').addEventListener("click", () => wrap(() => previewScene(scene)));
    card.querySelector('[data-action="run"]').addEventListener("click", () => wrap(() => runScene(scene)));
    sceneGrid.appendChild(card);
  }
}

function renderQuickActions() {
  quickGrid.innerHTML = "";
  for (const action of registry.quickActions) {
    const card = document.createElement("article");
    card.className = `quick-card ${action.risk}`;
    card.innerHTML = `
      <div>
        <strong>${action.title}</strong>
        <span>${riskLabel(action.risk)}</span>
      </div>
      <div class="button-row">
        <button type="button" data-action="preview">预览</button>
        <button type="button" class="execute" data-action="run">入队</button>
      </div>
    `;
    card.querySelector('[data-action="preview"]').addEventListener("click", () => wrap(() => previewQuick(action)));
    card.querySelector('[data-action="run"]').addEventListener("click", () => wrap(() => runQuick(action)));
    quickGrid.appendChild(card);
  }
}

async function refreshState() {
  const data = await fetchJson("/api/state");
  const state = data.state;
  latestState = state;
  running.textContent = state.running ? "running" : "idle";
  current.textContent = state.current ? `${state.current.kind}:${state.current.title}` : "-";
  lastCode.textContent = state.lastResult ? String(state.lastResult.returnCode) : "-";
  renderQueue(state);
  renderServoPositions(state.servoPositions);
  maybeRenderLastResult(state);
}

async function load() {
  const data = await fetchJson("/api/scenes");
  registry = data.registry;
  hostInput.value = data.defaults.host;
  portInput.value = data.defaults.port;
  userInput.value = data.defaults.user;
  boardSummary.textContent = `${data.defaults.user}@${data.defaults.host}:${data.defaults.port}`;
  passwordSummary.textContent = data.passwordConfigured ? "password: env configured" : "password: optional";
  renderScenes();
  renderQuickActions();
  await refreshState();
  refreshServoPositions().catch(() => {});
}

async function wrap(fn) {
  try {
    showOutput("执行中", "Working...");
    await fn();
  } catch (error) {
    showOutput("错误", error.message || String(error));
  }
}

document.getElementById("refresh").addEventListener("click", () => wrap(refreshState));
refreshServosButton.addEventListener("click", () => wrap(() => refreshServoPositions({ manual: true })));
document.getElementById("clear-output").addEventListener("click", () => showOutput("等待操作", ""));
for (const button of servoControlButtons) {
  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    startServoHold(button);
  });
  button.addEventListener("pointerup", stopServoHold);
  button.addEventListener("pointercancel", stopServoHold);
  button.addEventListener("pointerleave", stopServoHold);
}
window.addEventListener("pointerup", stopServoHold);
servoStepInput.addEventListener("change", () => {
  servoStepInput.value = String(servoStepSize());
});

wrap(load);
setInterval(() => {
  refreshState().catch(() => {});
}, 1500);
setInterval(() => {
  refreshServoPositions().catch(() => {});
}, 6000);

const sceneGrid = document.getElementById("scene-grid");
const quickGrid = document.getElementById("quick-grid");
const output = document.getElementById("output");
const outputTitle = document.getElementById("output-title");
const boardSummary = document.getElementById("board-summary");
const passwordSummary = document.getElementById("password-summary");
const running = document.getElementById("running");
const current = document.getElementById("current");
const lastCode = document.getElementById("last-code");
const hostInput = document.getElementById("host");
const portInput = document.getElementById("port");
const userInput = document.getElementById("user");
const passwordInput = document.getElementById("password");

let registry = null;

function connectionPayload() {
  return {
    host: hostInput.value.trim(),
    port: Number(portInput.value || 6000),
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
  showOutput(`${scene.number} ${scene.title} · 执行结果`, data.result);
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
  showOutput(`${action.title} · 执行结果`, data.result);
  await refreshState();
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
        <button type="button" class="execute" data-action="run">执行真机</button>
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
        <button type="button" class="execute" data-action="run">执行</button>
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
  running.textContent = state.running ? "running" : "idle";
  current.textContent = state.current ? `${state.current.kind}:${state.current.title}` : "-";
  lastCode.textContent = state.lastResult ? String(state.lastResult.returnCode) : "-";
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
document.getElementById("clear-output").addEventListener("click", () => showOutput("等待操作", ""));

wrap(load);

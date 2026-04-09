const body = document.body;
const ribbon = document.getElementById("ribbon");
const cardKicker = document.getElementById("card-kicker");
const awardTitle = document.getElementById("award-title");
const popupMessage = document.getElementById("popup-message");
const tokenCounter = document.getElementById("token-counter");
const acceptRewardButton = document.getElementById("accept-reward");
const fireworkLayer = document.getElementById("firework-layer");
const fireworkBurstLayer = document.getElementById("firework-burst-layer");
const fireworkRocketLayer = document.getElementById("firework-rocket-layer");
const skyLaunchLayer = document.getElementById("sky-launch-layer");
const confettiLayer = document.getElementById("confetti-layer");
const coinBurstLayer = document.getElementById("coin-burst-layer");
const buttonBurstLayer = document.getElementById("button-burst-layer");

let currentRunId = 0;
let audioContext = null;
let leftBus = null;
let rightBus = null;
const AudioContextClass = window.AudioContext || window.webkitAudioContext;
const TOKEN_TOTAL = 100000000;
const FIREWORK_DENSITY_RATIO = 2 / 3;
const FIREWORK_SIZE_SCALE = 1.5;
const FIREWORK_PALETTES = [
  ["rgba(255, 243, 169, 1)", "rgba(255, 143, 95, 0.88)", "rgba(108, 219, 255, 0.8)"],
  ["rgba(255, 248, 212, 1)", "rgba(255, 114, 168, 0.84)", "rgba(132, 141, 255, 0.8)"],
  ["rgba(255, 234, 138, 1)", "rgba(255, 176, 72, 0.9)", "rgba(180, 128, 255, 0.78)"],
  ["rgba(255, 241, 158, 1)", "rgba(255, 98, 98, 0.88)", "rgba(86, 230, 195, 0.78)"],
];

const phaseLabels = {
  idle: "待命中",
  opening: "开始点亮",
  celebrating: "庆祝中",
  cooldown: "收尾中",
};

const copyByPhase = {
  idle: {
    popupMessage: "恭喜你拿到 1 亿 Token！",
    ribbon: "恭喜达成",
    kicker: "特別獎勵已送達",
    awardTitle: "1 亿 Token 已到账",
  },
  opening: {
    popupMessage: "恭喜你拿到 1 亿 Token！",
    ribbon: "开始庆祝",
    kicker: "全場氣氛正在拉滿",
    awardTitle: "你的 1 亿 Token 来了",
  },
  celebrating: {
    popupMessage: "恭喜你拿到 1 亿 Token！",
    ribbon: "恭喜你",
    kicker: "今天就該為你歡呼",
    awardTitle: "1 亿 Token 到账成功",
  },
  cooldown: {
    popupMessage: "恭喜你拿到 1 亿 Token！",
    ribbon: "再来一遍",
    kicker: "好消息仍在發光",
    awardTitle: "1 亿 Token 已稳稳到账",
  },
};

function setPhase(phase) {
  body.dataset.phase = phase;
}

function applyCopy(phase) {
  const copy = copyByPhase[phase];
  if (!copy) return;
  popupMessage.textContent = copy.popupMessage;
  ribbon.textContent = copy.ribbon;
  cardKicker.textContent = copy.kicker;
  awardTitle.textContent = copy.awardTitle;
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function formatTokens(value) {
  return new Intl.NumberFormat("zh-CN").format(Math.round(value));
}

function easeOutCubic(value) {
  return 1 - (1 - value) ** 3;
}

function selectEffectEntries(entries, ratio = FIREWORK_DENSITY_RATIO) {
  const targetCount = Math.max(1, Math.round(entries.length * ratio));
  if (targetCount >= entries.length) {
    return entries.map((entry) => [...entry]);
  }

  if (targetCount === 1) {
    return [[...entries[Math.floor(entries.length / 2)]]];
  }

  const picked = [];
  const seen = new Set();
  for (let slot = 0; slot < targetCount; slot += 1) {
    const index = Math.round((slot * (entries.length - 1)) / (targetCount - 1));
    if (seen.has(index)) continue;
    picked.push([...entries[index]]);
    seen.add(index);
  }

  for (let index = 0; picked.length < targetCount && index < entries.length; index += 1) {
    if (seen.has(index)) continue;
    picked.push([...entries[index]]);
  }

  return picked.sort((left, right) => left[left.length - 1] - right[right.length - 1]);
}

function scaleBurstEntries(entries) {
  return selectEffectEntries(entries).map(([x, y, size, delay]) => [x, y, Math.round(size * FIREWORK_SIZE_SCALE), delay]);
}

function scaleRocketEntries(entries) {
  return selectEffectEntries(entries).map(([sx, sy, ex, ey, size, delay]) => [
    sx,
    sy,
    ex,
    ey,
    Math.round(size * FIREWORK_SIZE_SCALE),
    delay,
  ]);
}

function createConfettiBurst(xPercent = 50, yPercent = 18, count = 36) {
  const colors = ["#ff6f61", "#ffbe3d", "#6fd6ff", "#7a73ff", "#fff2a6"];
  for (let index = 0; index < count; index += 1) {
    const piece = document.createElement("span");
    piece.className = "confetti";

    const width = 8 + Math.random() * 10;
    const height = 12 + Math.random() * 16;
    piece.style.left = `${xPercent + (Math.random() - 0.5) * 8}%`;
    piece.style.top = `${yPercent + (Math.random() - 0.5) * 4}%`;
    piece.style.width = `${width}px`;
    piece.style.height = `${height}px`;
    piece.style.borderRadius = Math.random() > 0.6 ? "999px" : "4px";
    piece.style.background = colors[index % colors.length];
    piece.style.setProperty("--dx", `${(Math.random() - 0.5) * 520}px`);
    piece.style.setProperty("--dy", `${120 + Math.random() * 280}px`);
    piece.style.setProperty("--rot", `${Math.round((Math.random() - 0.5) * 720)}deg`);
    confettiLayer.appendChild(piece);
    window.setTimeout(() => piece.remove(), 2100);
  }
}

function launchConfettiSequence() {
  createConfettiBurst(50, 18, 40);
  window.setTimeout(() => createConfettiBurst(34, 24, 28), 180);
  window.setTimeout(() => createConfettiBurst(66, 24, 28), 320);
}

function createCoinBurst(originXPercent, originYPercent, count = 16, side = "center") {
  for (let index = 0; index < count; index += 1) {
    const coin = document.createElement("span");
    coin.className = "burst-coin";
    coin.style.left = `${originXPercent + (Math.random() - 0.5) * 4}%`;
    coin.style.top = `${originYPercent + (Math.random() - 0.5) * 4}%`;

    let xSpread = (Math.random() - 0.5) * 220;
    if (side === "left") xSpread -= 90;
    if (side === "right") xSpread += 90;

    const yTravel = -(120 + Math.random() * 220);
    coin.style.setProperty("--coin-x", `${xSpread}px`);
    coin.style.setProperty("--coin-y", `${yTravel}px`);
    coin.style.setProperty("--coin-rot", `${Math.round((Math.random() - 0.5) * 540)}deg`);
    coin.style.width = `${44 + Math.random() * 26}px`;
    coin.style.height = coin.style.width;
    coinBurstLayer.appendChild(coin);
    window.setTimeout(() => coin.remove(), 2200);
  }
}

function launchCoinBurstSequence() {
  createCoinBurst(50, 72, 18, "center");
  window.setTimeout(() => createCoinBurst(36, 76, 12, "left"), 120);
  window.setTimeout(() => createCoinBurst(64, 76, 12, "right"), 220);
}

function createFireworkBurst(xPercent, yPercent, sizePx = 320, delayMs = 0) {
  if (!fireworkBurstLayer) return;

  const palette = FIREWORK_PALETTES[Math.floor(Math.random() * FIREWORK_PALETTES.length)];
  window.setTimeout(() => {
    const burst = document.createElement("span");
    burst.className = "firework firework-burst";
    burst.style.left = `${xPercent}%`;
    burst.style.top = `${yPercent}%`;
    burst.style.width = `${sizePx}px`;
    burst.style.height = `${sizePx}px`;
    burst.style.setProperty("--fw-a", palette[0]);
    burst.style.setProperty("--fw-b", palette[1]);
    burst.style.setProperty("--fw-c", palette[2]);
    burst.style.setProperty("--fw-d", "rgba(255, 235, 164, 0.92)");
    fireworkBurstLayer.appendChild(burst);
    window.setTimeout(() => burst.remove(), 1900);
  }, delayMs);
}

function launchOpeningFireworks() {
  const bursts = scaleBurstEntries([
    [8, 16, 420, 0],
    [18, 26, 360, 70],
    [30, 18, 440, 120],
    [42, 30, 390, 170],
    [50, 14, 560, 220],
    [58, 24, 420, 260],
    [70, 18, 460, 320],
    [82, 28, 390, 380],
    [92, 16, 440, 450],
    [14, 56, 360, 520],
    [28, 64, 320, 600],
    [50, 56, 430, 680],
    [72, 62, 330, 760],
    [86, 54, 370, 840],
  ]);

  bursts.forEach(([x, y, size, delay]) => createFireworkBurst(x, y, size, delay));
}

function launchCelebrationFireworks() {
  const bursts = scaleBurstEntries([
    [12, 18, 390, 0],
    [24, 24, 340, 60],
    [38, 16, 450, 110],
    [50, 12, 600, 170],
    [62, 18, 450, 220],
    [76, 24, 360, 290],
    [88, 18, 420, 350],
    [26, 64, 320, 430],
    [50, 48, 420, 500],
    [74, 64, 320, 580],
  ]);

  bursts.forEach(([x, y, size, delay]) => createFireworkBurst(x, y, size, delay));
}

function createRocketLaunch(startXPercent, startYPercent, endXPercent, endYPercent, sizePx = 440, delayMs = 0) {
  if (!skyLaunchLayer || !fireworkRocketLayer) return;

  const palette = FIREWORK_PALETTES[Math.floor(Math.random() * FIREWORK_PALETTES.length)];
  window.setTimeout(() => {
    const rect = skyLaunchLayer.getBoundingClientRect();
    const startLeft = rect.left + (rect.width * startXPercent) / 100;
    const startTop = rect.top + (rect.height * startYPercent) / 100;
    const endLeft = rect.left + (rect.width * endXPercent) / 100;
    const endTop = rect.top + (rect.height * endYPercent) / 100;

    const rocket = document.createElement("span");
    rocket.className = "sky-rocket";
    rocket.style.left = `${startLeft}px`;
    rocket.style.top = `${startTop}px`;
    rocket.style.setProperty("--rocket-dx", `${endLeft - startLeft}px`);
    rocket.style.setProperty("--rocket-dy", `${endTop - startTop}px`);
    rocket.style.setProperty("--trail-core", palette[0]);
    rocket.style.setProperty("--trail-flare", palette[1]);
    fireworkRocketLayer.appendChild(rocket);

    window.setTimeout(() => {
      const burst = document.createElement("span");
      burst.className = "sky-firework-burst";
      burst.style.left = `${endLeft}px`;
      burst.style.top = `${endTop}px`;
      burst.style.width = `${sizePx}px`;
      burst.style.height = `${sizePx}px`;
      burst.style.setProperty("--fw-a", palette[0]);
      burst.style.setProperty("--fw-b", palette[1]);
      burst.style.setProperty("--fw-c", palette[2]);
      burst.style.setProperty("--fw-d", "rgba(255, 235, 164, 0.94)");
      fireworkRocketLayer.appendChild(burst);
      window.setTimeout(() => burst.remove(), 2100);
    }, 620);

    window.setTimeout(() => rocket.remove(), 820);
  }, delayMs);
}

function launchOpeningRocketShow() {
  const launches = scaleRocketEntries([
    [42, 96, 26, 34, 420, 0],
    [46, 97, 38, 22, 480, 90],
    [50, 98, 50, 16, 620, 150],
    [54, 97, 62, 24, 500, 230],
    [58, 96, 74, 34, 420, 310],
    [48, 98, 34, 48, 360, 390],
    [52, 98, 66, 48, 360, 470],
    [44, 97, 46, 30, 420, 560],
    [56, 97, 54, 30, 420, 640],
  ]);

  launches.forEach(([sx, sy, ex, ey, size, delay]) => createRocketLaunch(sx, sy, ex, ey, size, delay));
}

function launchCelebrationRocketShow() {
  const launches = scaleRocketEntries([
    [40, 96, 24, 38, 380, 0],
    [44, 98, 36, 26, 460, 70],
    [48, 99, 50, 18, 620, 140],
    [52, 98, 64, 26, 460, 220],
    [56, 96, 76, 38, 380, 300],
    [46, 99, 42, 46, 340, 380],
    [54, 99, 58, 46, 340, 450],
  ]);

  launches.forEach(([sx, sy, ex, ey, size, delay]) => createRocketLaunch(sx, sy, ex, ey, size, delay));
}

function triggerButtonBurst() {
  const rect = acceptRewardButton.getBoundingClientRect();
  const originX = rect.left + rect.width / 2;
  const originY = rect.top + rect.height / 2;

  acceptRewardButton.classList.remove("is-bursting");
  void acceptRewardButton.offsetWidth;
  acceptRewardButton.classList.add("is-bursting");
  window.setTimeout(() => acceptRewardButton.classList.remove("is-bursting"), 440);

  const colors = ["#ff715d", "#ffd15a", "#fff2a6", "#ff8e68"];
  for (let index = 0; index < 26; index += 1) {
    const spark = document.createElement("span");
    spark.className = `burst-spark${index % 3 === 0 ? " is-round" : ""}`;
    spark.style.left = `${originX}px`;
    spark.style.top = `${originY}px`;
    spark.style.background = colors[index % colors.length];
    spark.style.setProperty("--btn-x", `${(Math.random() - 0.5) * 180}px`);
    spark.style.setProperty("--btn-y", `${(Math.random() - 0.5) * 120}px`);
    spark.style.setProperty("--btn-rot", `${Math.round((Math.random() - 0.5) * 540)}deg`);
    spark.style.width = `${10 + Math.random() * 14}px`;
    spark.style.height = `${10 + Math.random() * 14}px`;
    buttonBurstLayer.appendChild(spark);
    window.setTimeout(() => spark.remove(), 1000);
  }
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
    throw new Error(`接口没有返回合法 JSON：${url}`);
  }

  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `请求失败：${response.status}`);
  }

  return data;
}

async function triggerCelebrateScene() {
  try {
    await fetchJson("/api/run-motion-script/celebrate", { method: "POST" });
  } catch (error) {
    console.warn("Lamp celebrate trigger failed:", error);
  }
}

function ensureAudioContext() {
  if (!AudioContextClass) {
    throw new Error("当前浏览器不支持 Web Audio");
  }
  if (!audioContext) {
    audioContext = new AudioContextClass();
    leftBus = audioContext.createGain();
    rightBus = audioContext.createGain();

    const leftPanner = audioContext.createStereoPanner();
    const rightPanner = audioContext.createStereoPanner();
    leftPanner.pan.value = -0.85;
    rightPanner.pan.value = 0.85;

    leftBus.connect(leftPanner).connect(audioContext.destination);
    rightBus.connect(rightPanner).connect(audioContext.destination);
  }
  if (audioContext.state === "suspended") {
    return audioContext.resume().then(() => audioContext);
  }
  return Promise.resolve(audioContext);
}

function routeToStereoBuses(node, pan, gainAmount) {
  if (pan <= 0) {
    const leftSend = node.context.createGain();
    leftSend.gain.value = gainAmount * (pan === 0 ? 0.88 : 1);
    node.connect(leftSend).connect(leftBus);
  }

  if (pan >= 0) {
    const rightSend = node.context.createGain();
    rightSend.gain.value = gainAmount * (pan === 0 ? 0.88 : 1);
    node.connect(rightSend).connect(rightBus);
  }

  if (pan < 0 && pan > -1) {
    const rightBleed = node.context.createGain();
    rightBleed.gain.value = gainAmount * (1 + pan) * 0.5;
    node.connect(rightBleed).connect(rightBus);
  }

  if (pan > 0 && pan < 1) {
    const leftBleed = node.context.createGain();
    leftBleed.gain.value = gainAmount * (1 - pan) * 0.5;
    node.connect(leftBleed).connect(leftBus);
  }
}

function scheduleOscTone(context, start, frequency, duration, type, pan, gainAmount) {
  const oscillator = context.createOscillator();
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, start);

  const gain = context.createGain();
  oscillator.connect(gain);
  routeToStereoBuses(gain, pan, 1);
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(gainAmount, start + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  oscillator.start(start);
  oscillator.stop(start + duration + 0.04);
}

function scheduleNoiseBurst(context, start, duration, pan, gainAmount, highpass) {
  const buffer = context.createBuffer(1, Math.floor(context.sampleRate * duration), context.sampleRate);
  const channel = buffer.getChannelData(0);
  for (let index = 0; index < channel.length; index += 1) {
    channel[index] = Math.random() * 2 - 1;
  }

  const source = context.createBufferSource();
  source.buffer = buffer;
  const filter = context.createBiquadFilter();
  filter.type = "highpass";
  filter.frequency.setValueAtTime(highpass, start);
  const gain = context.createGain();
  source.connect(filter).connect(gain);
  routeToStereoBuses(gain, pan, 1);
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(gainAmount, start + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  source.start(start);
  source.stop(start + duration + 0.03);
}

async function playCelebrationAudio(runId) {
  const context = await ensureAudioContext();
  const start = context.currentTime + 0.05;
  const totalDurationMs = 4200;

  const fanfare = [
    { t: 0.0, f: 523.25, d: 0.28, p: -0.7 },
    { t: 0.16, f: 659.25, d: 0.28, p: 0.72 },
    { t: 0.32, f: 783.99, d: 0.3, p: -0.45 },
    { t: 0.52, f: 1046.5, d: 0.42, p: 0.45 },
    { t: 0.98, f: 880.0, d: 0.24, p: -0.6 },
    { t: 1.14, f: 987.77, d: 0.24, p: 0.62 },
    { t: 1.3, f: 1318.51, d: 0.4, p: 0 },
  ];

  fanfare.forEach((note) => {
    scheduleOscTone(context, start + note.t, note.f, note.d, "sawtooth", note.p, 0.11);
    scheduleOscTone(context, start + note.t, note.f * 0.5, note.d + 0.04, "triangle", note.p * 0.7, 0.05);
  });

  const danceBass = [
    { t: 1.7, f: 130.81, p: -0.7 },
    { t: 1.96, f: 130.81, p: 0.7 },
    { t: 2.22, f: 164.81, p: -0.5 },
    { t: 2.48, f: 174.61, p: 0.5 },
    { t: 2.74, f: 196.0, p: -0.7 },
    { t: 3.0, f: 220.0, p: 0.72 },
    { t: 3.26, f: 246.94, p: -0.45 },
    { t: 3.52, f: 261.63, p: 0.45 },
  ];

  danceBass.forEach((note) => {
    scheduleOscTone(context, start + note.t, note.f, 0.2, "square", note.p, 0.1);
    scheduleOscTone(context, start + note.t, note.f * 2, 0.16, "triangle", -note.p * 0.75, 0.045);
  });

  for (let beat = 0; beat < 10; beat += 1) {
    const t = start + 1.68 + beat * 0.22;
    scheduleNoiseBurst(context, t, 0.12, beat % 2 === 0 ? -0.8 : 0.8, 0.08, 1200);
  }

  for (let clap = 0; clap < 6; clap += 1) {
    const t = start + 2.04 + clap * 0.36;
    scheduleNoiseBurst(context, t, 0.08, clap % 2 === 0 ? 0.35 : -0.35, 0.05, 2200);
  }

  await wait(totalDurationMs);
  if (runId !== currentRunId) return;
}

function animateCounter(runId, fromValue, toValue, durationMs) {
  tokenCounter.textContent = formatTokens(fromValue);

  return new Promise((resolve) => {
    const startedAt = performance.now();

    function frame(now) {
      if (runId !== currentRunId) {
        resolve();
        return;
      }

      const progress = Math.min((now - startedAt) / durationMs, 1);
      const eased = easeOutCubic(progress);
      const currentValue = fromValue + (toValue - fromValue) * eased;
      tokenCounter.textContent = formatTokens(currentValue);

      if (progress < 1) {
        window.requestAnimationFrame(frame);
      } else {
        resolve();
      }
    }

    window.requestAnimationFrame(frame);
  });
}

async function runWebCelebrateTimeline(runId) {
  body.classList.add("is-celebrating");
  setPhase("opening");
  applyCopy("opening");
  tokenCounter.textContent = formatTokens(0);
  launchCelebrationFireworks();
  launchCelebrationRocketShow();

  await wait(260);
  if (runId !== currentRunId) return;

  setPhase("celebrating");
  applyCopy("celebrating");
  launchCelebrationFireworks();
  launchCelebrationRocketShow();
  launchConfettiSequence();
  launchCoinBurstSequence();

  const counterPromise = animateCounter(runId, 0, TOKEN_TOTAL, 1800);
  await wait(900);
  if (runId !== currentRunId) return;

  launchConfettiSequence();
  launchCoinBurstSequence();
  await counterPromise;
  if (runId !== currentRunId) return;

  setPhase("cooldown");
  applyCopy("cooldown");
  await wait(960);
  if (runId !== currentRunId) return;

  body.classList.remove("is-celebrating");
  setPhase("idle");
  applyCopy("idle");
  tokenCounter.textContent = formatTokens(TOKEN_TOTAL);
}

async function playScene() {
  currentRunId += 1;
  const runId = currentRunId;
  acceptRewardButton.disabled = true;
  triggerButtonBurst();

  try {
    const audioPromise = playCelebrationAudio(runId).catch(() => {});
    const triggerPromise = triggerCelebrateScene();
    const timelinePromise = runWebCelebrateTimeline(runId);

    await Promise.all([audioPromise, triggerPromise, timelinePromise]);
  } finally {
    if (runId !== currentRunId) return;
    acceptRewardButton.disabled = false;
  }
}

setPhase("idle");
applyCopy("idle");
tokenCounter.textContent = formatTokens(TOKEN_TOTAL);
launchOpeningFireworks();
launchOpeningRocketShow();
acceptRewardButton.addEventListener("click", playScene);

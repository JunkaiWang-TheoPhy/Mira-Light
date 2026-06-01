(function () {
  const candidateTitle = document.getElementById("candidate-title");
  const receivedTime = document.getElementById("received-time");
  const celebrateButton = document.getElementById("celebrate-btn");
  const confettiLayer = document.getElementById("confetti-layer");

  const params = new URLSearchParams(window.location.search);
  const candidate = (params.get("candidate") || "Mira Light").trim();
  candidateTitle.textContent = candidate;

  const now = new Date();
  receivedTime.textContent = now.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

  function burstConfetti() {
    const colors = ["#ff8f3d", "#f2c14b", "#ff607d", "#41c67a", "#4e8dff"];
    for (let index = 0; index < 28; index += 1) {
      const piece = document.createElement("span");
      piece.className = "confetti";
      piece.style.left = `${Math.random() * 100}%`;
      piece.style.background = colors[index % colors.length];
      piece.style.setProperty("--travel-x", `${(Math.random() - 0.5) * 180}px`);
      piece.style.setProperty("--spin", `${(Math.random() - 0.5) * 720}deg`);
      piece.style.animationDelay = `${Math.random() * 180}ms`;
      confettiLayer.appendChild(piece);
      window.setTimeout(() => piece.remove(), 2600);
    }
  }

  async function triggerOfferCelebrate() {
    const response = await fetch("/api/run/04_offer_celebrate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "offer_demo",
        context: {
          trigger: "offer_demo_celebrate",
          candidate,
        },
      }),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
  }

  celebrateButton.addEventListener("click", async function () {
    burstConfetti();
    celebrateButton.disabled = true;
    celebrateButton.textContent = "正在触发 Mira 庆祝";
    try {
      await triggerOfferCelebrate();
      celebrateButton.textContent = "Mira 已开始庆祝";
    } catch (error) {
      console.warn("Offer celebrate trigger failed:", error);
      celebrateButton.textContent = "触发失败，请回主控台检查";
    }
    window.setTimeout(function () {
      celebrateButton.disabled = false;
      celebrateButton.textContent = "播放庆祝氛围";
    }, 2600);
  });
})();

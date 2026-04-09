const PLUGIN_ID = "mira-light-bridge";
const DEFAULT_BRIDGE_URL = "http://127.0.0.1:9783";
const DEFAULT_TIMEOUT_MS = 5000;

function asTextContent(data) {
  return {
    content: [
      {
        type: "text",
        text: typeof data === "string" ? data : JSON.stringify(data, null, 2),
      },
    ],
  };
}

function resolvePluginConfig(api) {
  const raw = api.config?.plugins?.entries?.[PLUGIN_ID]?.config ?? {};
  return {
    bridgeBaseUrl: raw.bridgeBaseUrl ?? process.env.MIRA_LIGHT_BRIDGE_URL ?? DEFAULT_BRIDGE_URL,
    bridgeToken: raw.bridgeToken ?? process.env.MIRA_LIGHT_BRIDGE_TOKEN ?? "",
    requestTimeoutMs: Number(raw.requestTimeoutMs ?? process.env.MIRA_LIGHT_BRIDGE_TIMEOUT_MS ?? DEFAULT_TIMEOUT_MS),
  };
}

async function callBridge(api, method, endpoint, payload) {
  const cfg = resolvePluginConfig(api);
  const controller = typeof AbortController === "function" ? new AbortController() : null;
  const timeoutHandle = setTimeout(() => controller?.abort(), cfg.requestTimeoutMs);

  try {
    const response = await fetch(`${cfg.bridgeBaseUrl}${endpoint}`, {
      method,
      headers: {
        ...(cfg.bridgeToken ? { Authorization: `Bearer ${cfg.bridgeToken}` } : {}),
        "Content-Type": "application/json",
      },
      body: payload == null ? undefined : JSON.stringify(payload),
      signal: controller?.signal,
    });

    const raw = await response.text();
    let parsed = raw;
    try {
      parsed = raw ? JSON.parse(raw) : {};
    } catch {
      // keep raw
    }

    if (!response.ok) {
      throw new Error(typeof parsed === "string" ? parsed : JSON.stringify(parsed));
    }

    return parsed;
  } finally {
    clearTimeout(timeoutHandle);
  }
}

function buildSceneListTool(api) {
  return {
    name: "mira_light_list_scenes",
    description: "List available Mira Light booth scenes from the local bridge.",
    parameters: { type: "object", properties: {}, required: [] },
    async execute() {
      const data = await callBridge(api, "GET", "/v1/mira-light/scenes");
      return asTextContent(data);
    },
  };
}

function buildRuntimeTool(api) {
  return {
    name: "mira_light_runtime_status",
    description: "Read the runtime state of the local Mira Light bridge.",
    parameters: { type: "object", properties: {}, required: [] },
    async execute() {
      const data = await callBridge(api, "GET", "/v1/mira-light/runtime");
      return asTextContent(data);
    },
  };
}

function buildStatusTool(api) {
  return {
    name: "mira_light_status",
    description: "Read the current servo status of the Mira Light lamp.",
    parameters: { type: "object", properties: {}, required: [] },
    async execute() {
      const data = await callBridge(api, "GET", "/v1/mira-light/status");
      return asTextContent(data);
    },
  };
}

function buildRunSceneTool(api) {
  return {
    name: "mira_light_run_scene",
    description: "Run a named Mira Light booth scene through the local bridge.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["scene"],
      properties: {
        scene: { type: "string" },
        async: { type: "boolean" },
      },
    },
    async execute(_id, params) {
      const data = await callBridge(api, "POST", "/v1/mira-light/run-scene", {
        scene: params.scene,
        async: params.async !== false,
      });
      return asTextContent(data);
    },
  };
}

function buildSpeakTool(api) {
  return {
    name: "mira_light_speak",
    description:
      "Speak a short public line through Mira Light's configured speaker path. Prefer scenes for expressive multi-step behavior.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["text"],
      properties: {
        text: { type: "string", minLength: 1, maxLength: 80 },
        voice: { type: "string", enum: ["tts", "openclaw", "say"] },
        wait: { type: "boolean" },
      },
    },
    async execute(_id, params) {
      const payload = {
        text: params.text,
        ...(params.voice ? { voice: params.voice } : {}),
        ...(typeof params.wait === "boolean" ? { wait: params.wait } : {}),
      };
      const data = await callBridge(api, "POST", "/v1/mira-light/speak", payload);
      return asTextContent(data);
    },
  };
}

function buildStopTool(api) {
  return {
    name: "mira_light_stop",
    description: "Stop the currently running Mira Light scene and send /action/stop.",
    parameters: { type: "object", properties: {}, required: [] },
    async execute() {
      const data = await callBridge(api, "POST", "/v1/mira-light/stop");
      return asTextContent(data);
    },
  };
}

function buildResetTool(api) {
  return {
    name: "mira_light_reset",
    description: "Reset the Mira Light lamp via the local bridge.",
    parameters: { type: "object", properties: {}, required: [] },
    async execute() {
      const data = await callBridge(api, "POST", "/v1/mira-light/reset");
      return asTextContent(data);
    },
  };
}

function buildLedTool(api) {
  const rgbSchema = {
    type: "object",
    additionalProperties: false,
    properties: {
      r: { type: "integer", minimum: 0, maximum: 255 },
      g: { type: "integer", minimum: 0, maximum: 255 },
      b: { type: "integer", minimum: 0, maximum: 255 },
    },
    required: ["r", "g", "b"],
  };

  return {
    name: "mira_light_set_led",
    description: "Set the Mira Light LED state through the local bridge.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        mode: {
          type: "string",
          enum: ["off", "solid", "breathing", "rainbow", "rainbow_cycle", "vector"],
        },
        brightness: { type: "integer", minimum: 0, maximum: 255 },
        color: rgbSchema,
        pixels: {
          type: "array",
          minItems: 40,
          maxItems: 40,
          items: rgbSchema,
        },
      },
      required: ["mode"],
    },
    async execute(_id, params) {
      const data = await callBridge(api, "POST", "/v1/mira-light/led", params);
      return asTextContent(data);
    },
  };
}

function buildControlTool(api) {
  return {
    name: "mira_light_control_joints",
    description: "Directly control Mira Light servo joints through the local bridge.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        mode: { type: "string", enum: ["relative", "absolute"] },
        servo1: { type: "number" },
        servo2: { type: "number" },
        servo3: { type: "number" },
        servo4: { type: "number" },
      },
      required: ["mode"],
    },
    async execute(_id, params) {
      const data = await callBridge(api, "POST", "/v1/mira-light/control", params);
      return asTextContent(data);
    },
  };
}

const plugin = {
  id: PLUGIN_ID,
  name: "Mira Light Bridge",
  description: "Bridge-backed scene and hardware control for the local Mira Light lamp.",
  register(api) {
    api.registerTool(buildSceneListTool(api), { optional: false });
    api.registerTool(buildRuntimeTool(api), { optional: false });
    api.registerTool(buildStatusTool(api), { optional: false });
    api.registerTool(buildRunSceneTool(api), { optional: false });
    api.registerTool(buildSpeakTool(api), { optional: false });
    api.registerTool(buildStopTool(api), { optional: false });
    api.registerTool(buildResetTool(api), { optional: false });
    api.registerTool(buildLedTool(api), { optional: false });
    api.registerTool(buildControlTool(api), { optional: false });
  },
};

export default plugin;

"""Scene definitions for the Mira Light booth demo.

This file now provides a more structured choreography layer:

- servo calibration notes
- named poses
- reusable motion primitives
- scene definitions built from those poses and primitives

What is still intentionally provisional:

- the exact physical meaning of servo1 ~ servo4
- exact collision-safe limits on the real lamp
- tracking / touch / voice / audio integrations

Those unresolved parts stay visible as comments and TODO notes instead of being
hidden behind fake precision.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any, Dict, List


Step = Dict[str, Any]


# IMPORTANT:
# The real hardware should validate these semantic guesses before the demo.
# For now, we freeze them here so all scenes speak the same "motion language".
#
# The practical goal is not to claim these labels are final, but to stop scenes
# from using unexplained raw deltas everywhere.
DEFAULT_SERVO_CALIBRATION: Dict[str, Dict[str, Any]] = {
    "servo1": {
        "label": "base_yaw",
        "verified": False,
        "neutral": 90,
        "hard_range": [0, 180],
        "rehearsal_range": [72, 110],
        "notes": "Primary left-right attention axis. Keep movements modest until real base clearance is confirmed.",
    },
    "servo2": {
        "label": "lower_arm_lift",
        "verified": False,
        "neutral": 96,
        "hard_range": [0, 180],
        "rehearsal_range": [78, 112],
        "notes": "Primary lift / crouch axis. Used to make the lamp feel like it wakes, bows, or tucks in.",
    },
    "servo3": {
        "label": "upper_arm_pitch",
        "verified": False,
        "neutral": 98,
        "hard_range": [0, 180],
        "rehearsal_range": [80, 120],
        "notes": "Secondary reach axis. Often paired with servo2 for extend / retract behavior.",
    },
    "servo4": {
        "label": "head_tilt",
        "verified": False,
        "neutral": 90,
        "hard_range": [0, 180],
        "rehearsal_range": [80, 104],
        "notes": "Best candidate for nod, tilt, and fragile emotional expression. Keep amplitudes small.",
    },
}


# Named poses are intentionally more deterministic than pure relative deltas.
# Using these as checkpoints helps prevent posture drift across long booth demos.
DEFAULT_POSES: Dict[str, Dict[str, Any]] = {
    "sleep": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 80, "servo3": 82, "servo4": 98},
        "notes": "Compact folded waiting pose.",
    },
    "wake_half": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 88, "servo3": 90, "servo4": 94},
        "notes": "Midway pose during wake-up, before the final stretch.",
    },
    "wake_high": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 96, "servo3": 104, "servo4": 88},
        "notes": "Higher, more alert pose right before returning to neutral.",
    },
    "neutral": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90},
        "notes": "Calm forward-facing presentation pose.",
    },
    "curious_half_left": {
        "verified": False,
        "angles": {"servo1": 98, "servo2": 96, "servo3": 98, "servo4": 92},
        "notes": "Half-turn, used to create hesitation before a full look.",
    },
    "curious_full_left": {
        "verified": False,
        "angles": {"servo1": 104, "servo2": 97, "servo3": 100, "servo4": 92},
        "notes": "Full left-facing attention pose.",
    },
    "tilt_left": {
        "verified": False,
        "angles": {"servo1": 104, "servo2": 97, "servo3": 100, "servo4": 98},
        "notes": "Left-leaning cute / curious tilt.",
    },
    "tilt_right": {
        "verified": False,
        "angles": {"servo1": 104, "servo2": 97, "servo3": 100, "servo4": 82},
        "notes": "Right-leaning cute / curious tilt.",
    },
    "extend_soft": {
        "verified": False,
        "angles": {"servo1": 92, "servo2": 102, "servo3": 108, "servo4": 90},
        "notes": "Gentle forward reach without looking aggressive.",
    },
    "extend_full": {
        "verified": False,
        "angles": {"servo1": 92, "servo2": 106, "servo3": 114, "servo4": 90},
        "notes": "More committed reach, used sparingly.",
    },
    "retract_soft": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 92, "servo3": 90, "servo4": 94},
        "notes": "Small retreat, good for timid behavior.",
    },
    "daydream_left": {
        "verified": False,
        "angles": {"servo1": 76, "servo2": 96, "servo3": 94, "servo4": 86},
        "notes": "Lookaway pose for absent-minded scenes.",
    },
    "daydream_drop": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 88, "servo3": 84, "servo4": 102},
        "notes": "Sleepy head-drop pose.",
    },
    "reminder_ready": {
        "verified": False,
        "angles": {"servo1": 94, "servo2": 100, "servo3": 104, "servo4": 92},
        "notes": "Small forward-ready pose before the stand-up bumps.",
    },
    "farewell_look": {
        "verified": False,
        "angles": {"servo1": 106, "servo2": 96, "servo3": 98, "servo4": 92},
        "notes": "Softer sideways look for watching someone leave.",
    },
    "farewell_bow": {
        "verified": False,
        "angles": {"servo1": 106, "servo2": 92, "servo3": 94, "servo4": 98},
        "notes": "Slightly lowered, softer end-of-goodbye pose.",
    },
    "celebrate_ready": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 104, "servo3": 112, "servo4": 86},
        "notes": "Lifted pre-dance pose so the celebration does not start from a slouch.",
    },
    "sleep_ready": {
        "verified": False,
        "angles": {"servo1": 90, "servo2": 88, "servo3": 86, "servo4": 96},
        "notes": "Intermediate pose before folding into sleep.",
    },
}


WARM_AMBER = {"r": 255, "g": 180, "b": 120}
SOFT_WARM = {"r": 255, "g": 220, "b": 180}
COMFORT_WARM = {"r": 255, "g": 170, "b": 110}


SCENE_META: Dict[str, Dict[str, Any]] = {
    "wake_up": {
        "emotionTags": ["苏醒", "欢迎"],
        "readiness": "tuning",
        "durationMs": 3280,
        "accent": "dawn",
        "priority": "P0",
        "requirements": ["基础姿态已校准"],
        "requirementIds": ["base_calibrated"],
        "fallbackHint": "直接运行 stretch 后回 neutral",
        "operatorCue": "适合作为开场第一幕，强调‘它不是机械启动’。",
    },
    "curious_observe": {
        "emotionTags": ["好奇", "试探"],
        "readiness": "tuning",
        "durationMs": 3600,
        "accent": "curious",
        "priority": "P0",
        "requirements": ["头部转向姿态已校准"],
        "requirementIds": ["base_calibrated"],
        "fallbackHint": "固定执行 half-turn -> tilt -> nod",
        "operatorCue": "主持人此时最好站在灯的左前方，方便观众理解它在看谁。",
    },
    "touch_affection": {
        "emotionTags": ["亲近", "撒娇"],
        "readiness": "tuning",
        "durationMs": 2320,
        "accent": "warm",
        "priority": "P0",
        "requirements": ["手部互动", "extend/retract 已校准"],
        "requirementIds": ["touch_ready", "base_calibrated"],
        "fallbackHint": "直接前探并执行小幅 rub_motion",
        "operatorCue": "邀请评委伸手时再触发，避免空蹭。",
    },
    "cute_probe": {
        "emotionTags": ["卖萌", "胆小"],
        "readiness": "ready",
        "durationMs": 2520,
        "accent": "curious",
        "priority": "P1",
        "requirements": ["无特殊附件"],
        "requirementIds": [],
        "fallbackHint": "只保留 tilt_left / tilt_right 版本",
        "operatorCue": "这个场景适合在讲故事时穿插，不需要单独大讲。",
    },
    "daydream": {
        "emotionTags": ["发呆", "走神"],
        "readiness": "ready",
        "durationMs": 5600,
        "accent": "dream",
        "priority": "P1",
        "requirements": ["无特殊附件"],
        "requirementIds": [],
        "fallbackHint": "固定看左上方 3 秒，再 snap back",
        "operatorCue": "适合展示它不是一直表演，而像真的有自己的节奏。",
    },
    "standup_reminder": {
        "emotionTags": ["提醒", "可爱"],
        "readiness": "tuning",
        "durationMs": 3120,
        "accent": "alert",
        "priority": "P1",
        "requirements": ["提醒语境", "前顶动作已校准"],
        "requirementIds": ["base_calibrated"],
        "fallbackHint": "直接执行 3 次 bump + 双点头",
        "operatorCue": "主持人最好先说‘假装你已经坐了一小时没动’。",
    },
    "track_target": {
        "emotionTags": ["专注", "感知"],
        "readiness": "tuning",
        "durationMs": 2900,
        "accent": "vision",
        "priority": "P0",
        "requirements": ["摄像头", "目标跟踪", "目标到关节映射"],
        "requirementIds": ["camera_ready", "tracking_ready"],
        "fallbackHint": "改用滑杆模拟 tracking 方向或只口头说明",
        "operatorCue": "只有在 tracking 真正可用时才作为主秀，否则放到备选。",
    },
    "celebrate": {
        "emotionTags": ["庆祝", "爆发"],
        "readiness": "tuning",
        "durationMs": 3980,
        "accent": "celebrate",
        "priority": "P0",
        "requirements": ["offer 页面", "音频素材", "dance 动作稳定"],
        "requirementIds": ["offer_ready", "audio_ready", "base_calibrated"],
        "fallbackHint": "保留灯效 + dance，音乐失败也能继续",
        "operatorCue": "这是全场情绪峰值，建议配合屏幕上的假邮件和音乐。",
    },
    "farewell": {
        "emotionTags": ["送别", "不舍"],
        "readiness": "ready",
        "durationMs": 2360,
        "accent": "farewell",
        "priority": "P0",
        "requirements": ["无特殊附件"],
        "requirementIds": [],
        "fallbackHint": "直接执行 wave + farewell_bow",
        "operatorCue": "结束时用它来收尾，再接 sleep。",
    },
    "sleep": {
        "emotionTags": ["收场", "安静"],
        "readiness": "tuning",
        "durationMs": 3440,
        "accent": "sleep",
        "priority": "P0",
        "requirements": ["sleep pose 已校准"],
        "requirementIds": ["sleep_calibrated"],
        "fallbackHint": "直接 apply sleep pose 并 fade lights",
        "operatorCue": "每轮演示结束都可以回到这个场景，形成闭环。",
    },
    "sigh_demo": {
        "emotionTags": ["安慰", "理解"],
        "readiness": "sensor-needed",
        "durationMs": 1900,
        "accent": "comfort",
        "priority": "P1",
        "requirements": ["麦克风", "叹气检测"],
        "requirementIds": ["mic_ready"],
        "fallbackHint": "手动触发固定安慰反应",
        "operatorCue": "适合讲 Mira 理解情绪的价值主张。",
    },
    "multi_person_demo": {
        "emotionTags": ["纠结", "活物感"],
        "readiness": "prototype",
        "durationMs": 1400,
        "accent": "vision",
        "priority": "P2",
        "requirements": ["多人目标识别"],
        "requirementIds": ["camera_ready", "tracking_ready"],
        "fallbackHint": "固定左右扫视代替",
        "operatorCue": "如果现场人多，这一幕很容易逗笑评委，但现在仍偏概念验证。",
    },
    "voice_demo_tired": {
        "emotionTags": ["听懂了", "接住你"],
        "readiness": "sensor-needed",
        "durationMs": 2200,
        "accent": "comfort",
        "priority": "P1",
        "requirements": ["语音识别", "情绪分类"],
        "requirementIds": ["mic_ready"],
        "fallbackHint": "手动触发低头 + 暖色呼吸",
        "operatorCue": "适合讲‘它不需要说话，也能表达理解’。",
    },
}


DEFAULT_PROFILE_PATH = Path(
    os.environ.get(
        "MIRA_LIGHT_PROFILE_PATH",
        str(Path(__file__).resolve().parent.parent / "config" / "mira_light_profile.local.json"),
    )
)


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_profile_overrides(profile_path: Path) -> Dict[str, Any] | None:
    if not profile_path.is_file():
        return None

    raw = profile_path.read_text(encoding="utf-8").strip()
    if not raw:
        return None

    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid profile file: {profile_path}")
    return parsed


SERVO_CALIBRATION = deepcopy(DEFAULT_SERVO_CALIBRATION)
POSES = deepcopy(DEFAULT_POSES)
PROFILE_INFO: Dict[str, Any] = {
    "path": str(DEFAULT_PROFILE_PATH),
    "exists": DEFAULT_PROFILE_PATH.is_file(),
    "loaded": False,
    "ledPixelCount": int(os.environ.get("MIRA_LIGHT_LED_PIXEL_COUNT", "40")),
    "supportedLedModes": ["off", "solid", "breathing", "rainbow", "rainbow_cycle", "vector"],
}

_profile_overrides = _load_profile_overrides(DEFAULT_PROFILE_PATH)
if _profile_overrides:
    if isinstance(_profile_overrides.get("servoCalibration"), dict):
        SERVO_CALIBRATION = _deep_merge_dict(SERVO_CALIBRATION, _profile_overrides["servoCalibration"])
    if isinstance(_profile_overrides.get("poses"), dict):
        POSES = _deep_merge_dict(POSES, _profile_overrides["poses"])
    PROFILE_INFO["loaded"] = True


def comment(text: str) -> Step:
    return {"type": "comment", "text": text}


def delay(ms: int) -> Step:
    return {"type": "delay", "ms": ms}


def led(mode: str, brightness: int | None = None, color: Dict[str, int] | None = None) -> Step:
    payload: Dict[str, Any] = {"mode": mode}
    if brightness is not None:
        payload["brightness"] = brightness
    if color is not None:
        payload["color"] = color
    return {"type": "led", "payload": payload}


def pose(name: str) -> Step:
    return {"type": "pose", "name": name}


def absolute(**servo_values: int) -> Step:
    return {"type": "control", "payload": {"mode": "absolute", **servo_values}}


def nudge(**servo_values: int) -> Step:
    return {"type": "control", "payload": {"mode": "relative", **servo_values}}


def action(name: str, loops: int = 1) -> Step:
    return {"type": "action", "payload": {"name": name, "loops": loops}}


def action_stop() -> Step:
    return {"type": "action_stop"}


def reset() -> Step:
    return {"type": "reset"}


def audio(
    name: str | None = None,
    *,
    text: str | None = None,
    voice: str = "tts",
    wait: bool | None = None,
    allow_missing: bool = True,
    fallback_asset: str | None = None,
) -> Step:
    step: Step = {"type": "audio", "voice": voice, "allowMissing": allow_missing}
    if name is not None:
        step["name"] = name
    if text is not None:
        step["text"] = text
    step["wait"] = bool(text) if wait is None else bool(wait)
    if fallback_asset:
        step["fallbackAsset"] = fallback_asset
    return step


def micro_shiver(axis: str = "servo4", amplitude: int = 4, repeats: int = 2, beat_ms: int = 140) -> List[Step]:
    steps: List[Step] = []
    for _ in range(repeats):
        steps.extend(
            [
                nudge(**{axis: amplitude}),
                delay(beat_ms),
                nudge(**{axis: -amplitude}),
                delay(beat_ms),
            ]
        )
    return steps


def rub_motion(axis: str = "servo1", amplitude: int = 4, loops: int = 2, beat_ms: int = 160) -> List[Step]:
    steps: List[Step] = []
    for _ in range(loops):
        steps.extend(
            [
                nudge(**{axis: amplitude}),
                delay(beat_ms),
                nudge(**{axis: -amplitude * 2}),
                delay(beat_ms),
                nudge(**{axis: amplitude}),
                delay(beat_ms),
            ]
        )
    return steps


def pawing_bump(loops: int = 3, reach_axis: str = "servo3", brace_axis: str = "servo2") -> List[Step]:
    steps: List[Step] = []
    for _ in range(loops):
        steps.extend(
            [
                nudge(**{brace_axis: -4, reach_axis: 6}),
                delay(180),
                nudge(**{brace_axis: 4, reach_axis: -6}),
                delay(180),
            ]
        )
    return steps


def celebration_sway(amplitude: int = 6, loops: int = 2) -> List[Step]:
    steps: List[Step] = []
    for _ in range(loops):
        steps.extend(
            [
                nudge(servo1=amplitude, servo4=-3),
                delay(200),
                nudge(servo1=-amplitude * 2, servo4=6),
                delay(200),
                nudge(servo1=amplitude, servo4=-3),
                delay(200),
            ]
        )
    return steps


def fade_to_sleep(color: Dict[str, int]) -> List[Step]:
    return [
        led("solid", brightness=60, color=color),
        delay(260),
        led("solid", brightness=30, color=color),
        delay(320),
        led("solid", brightness=12, color=color),
        delay(380),
        led("off", brightness=0),
    ]


SCENES: Dict[str, Dict[str, Any]] = {
    "wake_up": {
        "title": "起床",
        "host_line": "当 Mira 感觉到有人靠近，它不会立刻机械转头，而是像刚醒的小动物一样慢慢睁眼、抖一抖、伸个懒腰。",
        "notes": [
            "TODO: 把这个场景接到 person_detected_near 事件；在那之前默认通过 OpenClaw 或终端命令触发。",
            "当前版本按 PDF1 的分镜细化为：微光 -> 起身 -> 伸懒腰 -> 抖毛 -> 看向评委。",
        ],
        "tuning_notes": [
            "先调 sleep / wake_half / wake_high / neutral 四个姿态，确认起身和回落都不拉扯结构。",
            "如果抖毛看起来像故障，先减小 servo1 与 servo4 的抖动幅度，而不是删掉整个阶段。",
        ],
        "steps": [
            pose("sleep"),
            comment("微光亮起，像刚睁眼。"),
            led("solid", brightness=6, color={"r": 255, "g": 176, "b": 116}),
            delay(220),
            led("solid", brightness=12, color={"r": 255, "g": 188, "b": 130}),
            delay(180),
            led("solid", brightness=22, color={"r": 255, "g": 200, "b": 148}),
            delay(180),
            led("breathing", brightness=42, color={"r": 255, "g": 214, "b": 172}),
            delay(420),
            comment("身体抬到半醒。"),
            pose("wake_half"),
            delay(360),
            comment("继续升高并仰头，做伸懒腰。"),
            absolute(servo1=90, servo2=98, servo3=108, servo4=84),
            delay(320),
            absolute(servo1=90, servo2=100, servo3=112, servo4=82),
            delay(700),
            comment("回到正常高度并抖两下，像小动物醒来抖毛。"),
            absolute(servo1=90, servo2=96, servo3=98, servo4=90),
            nudge(servo1=4, servo4=-2),
            delay(120),
            nudge(servo1=-8, servo4=4),
            delay(120),
            nudge(servo1=4, servo4=-2),
            delay(120),
            nudge(servo1=-4, servo4=2),
            delay(120),
            nudge(servo1=8, servo4=-4),
            delay(120),
            nudge(servo1=-4, servo4=2),
            delay(120),
            comment("最后慢慢看向评委。"),
            absolute(servo1=96, servo2=96, servo3=98, servo4=90),
            led("solid", brightness=132, color=SOFT_WARM),
        ],
    },
    "curious_observe": {
        "title": "好奇你是谁",
        "host_line": "Mira 不会机械地直接盯着你，它会先试探着转过去一半，停一下，再歪头看你。",
        "notes": [
            "TODO: 接入目标方向识别后，把当前左前方版本改成按目标方位动态生成。",
            "当前版本按 PDF2 处理为：靠近 -> 害羞转开并低头 -> 再探出来 -> 点头的完整路径。",
        ],
        "tuning_notes": [
            "‘好奇’的关键是半转后的停顿，别把停顿删没了。",
            "害羞阶段不要做得太快，否则会像逃跑而不是怯生生。"
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
            delay(160),
            comment("先注意到评委。"),
            absolute(servo1=94, servo2=96, servo3=98, servo4=90),
            delay(220),
            comment("向评委方向靠近一点。"),
            absolute(servo1=100, servo2=98, servo3=102, servo4=90),
            delay(260),
            comment("缓慢摇头一次，像在确认你是谁。"),
            nudge(servo1=4, servo4=-2),
            delay(140),
            nudge(servo1=-8, servo4=4),
            delay(140),
            nudge(servo1=4, servo4=-2),
            delay(180),
            comment("再更靠近一点，看着用户。"),
            absolute(servo1=102, servo2=98, servo3=104, servo4=90),
            delay(220),
            comment("转开并低头，表示害羞。"),
            led("solid", brightness=100, color={"r": 246, "g": 214, "b": 186}),
            absolute(servo1=82, servo2=94, servo3=94, servo4=100),
            delay(320),
            nudge(servo4=4),
            delay(120),
            nudge(servo4=-8),
            delay(120),
            nudge(servo4=4),
            delay(180),
            comment("再转向你，慢慢探出来看。"),
            led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
            absolute(servo1=96, servo2=98, servo3=106, servo4=92),
            delay(220),
            nudge(servo1=3),
            delay(110),
            nudge(servo1=-6),
            delay(110),
            nudge(servo1=3),
            delay(160),
            comment("面对你点头一下。"),
            absolute(servo1=96, servo2=98, servo3=102, servo4=90),
            nudge(servo4=4),
            delay(120),
            nudge(servo4=-8),
            delay(140),
            nudge(servo4=4),
            delay(180),
            comment("如果对方继续靠近，则转向远离评委侧并低头，表示有点怕。"),
            absolute(servo1=84, servo2=94, servo3=98, servo4=102),
            delay(240),
            comment("害羞结束后，再慢慢往回和往前靠。"),
            absolute(servo1=94, servo2=98, servo3=102, servo4=92),
        ],
    },
    "touch_affection": {
        "title": "摸一摸",
        "host_line": "你可以摸摸它。它会主动靠过来，不只是响应动作，而是在表达亲近。",
        "notes": [
            "TODO: 触摸传感器或手部识别接入后，真正按手的位置选择前探方向。",
            "当前默认按左前方来手的版本处理，并细化成靠近、蹭、追手、回到自然照明方向四段。"
        ],
        "tuning_notes": [
            "这个场景不要幅度太大，‘亲近感’比‘动作量’更重要。",
            "如果看起来像撞手，先减小 servo1 的左右摆幅，再减小 servo3 前探量。"
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=168, color={"r": 255, "g": 190, "b": 120}),
            comment("先温和地靠近手。"),
            absolute(servo1=94, servo2=100, servo3=108, servo4=90),
            delay(260),
            comment("身体往下送一点，让灯头进入手掌下方。"),
            absolute(servo1=94, servo2=104, servo3=110, servo4=94),
            delay(240),
            comment("在手下做小幅上下和左右蹭动。"),
            led("solid", brightness=182, color={"r": 255, "g": 176, "b": 106}),
            absolute(servo1=98, servo2=104, servo3=110, servo4=94),
            delay(140),
            absolute(servo1=90, servo2=104, servo3=110, servo4=86),
            delay(140),
            absolute(servo1=98, servo2=103, servo3=109, servo4=94),
            delay(140),
            absolute(servo1=90, servo2=103, servo3=109, servo4=86),
            delay(140),
            comment("手拿开后轻轻追一下手的方向。"),
            absolute(servo1=100, servo2=98, servo3=104, servo4=90),
            delay(320),
            comment("慢慢回到自然照明的方向，等下一次互动。"),
            absolute(servo1=92, servo2=96, servo3=98, servo4=92),
            led("solid", brightness=138, color={"r": 255, "g": 210, "b": 170}),
            delay(220),
            pose("neutral"),
        ],
    },
    "cute_probe": {
        "title": "卖萌",
        "host_line": "它会像小狗一样歪头研究你，有时还会探头一下又缩回去。",
        "notes": [
            "当前版本按 PDF1 做成：轻点头 -> 左右找角度 -> 中间关节上下 -> 胆小探头。",
        ],
        "tuning_notes": [
            "节奏要慢，给评委留出‘看懂它在想什么’的时间。",
            "探头时宁可小一点，也不要做出攻击性前冲。",
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=124, color={"r": 255, "g": 222, "b": 178}),
            comment("先轻轻点头，再停住。"),
            absolute(servo1=90, servo2=96, servo3=98, servo4=96),
            delay(120),
            absolute(servo1=90, servo2=96, servo3=98, servo4=90),
            delay(140),
            comment("底座向一侧，再向另一侧，像在找角度研究你。"),
            absolute(servo1=82, servo2=96, servo3=98, servo4=90),
            delay(180),
            absolute(servo1=98, servo2=96, servo3=98, servo4=90),
            delay(180),
            comment("中间关节先抬一下，再往下放。"),
            absolute(servo1=90, servo2=96, servo3=108, servo4=88),
            delay(180),
            absolute(servo1=90, servo2=96, servo3=92, servo4=94),
            delay(180),
            comment("慢慢探头。"),
            led("solid", brightness=138, color={"r": 255, "g": 228, "b": 188}),
            absolute(servo1=92, servo2=102, servo3=114, servo4=90),
            delay(260),
            comment("突然缩回，像被吓到了。"),
            absolute(servo1=90, servo2=92, servo3=92, servo4=96),
            delay(180),
            comment("再慢慢探出去，胆小但还是好奇。"),
            led("solid", brightness=118, color={"r": 252, "g": 216, "b": 174}),
            absolute(servo1=92, servo2=100, servo3=110, servo4=90),
            delay(260),
            pose("neutral"),
        ],
    },
    "daydream": {
        "title": "发呆",
        "host_line": "它不会一直表演，它也会像人一样走神，盯着某个方向发一会儿呆。",
        "notes": [
            "TODO: 未来可接随机方向选择或环境显著目标选择。",
            "当前版本把 PDF1 的两个版本都编进来了：先走神看远处，再做一次打瞌睡惊醒。"
        ],
        "tuning_notes": [
            "这个场景的重点是留白，持有时间要足够。",
            "回神动作要明显快于前半段，才有‘突然回过神’的感觉。",
            "如果打盹版太危险，优先减小 servo2 和 servo3 的下沉量。"
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=118, color={"r": 245, "g": 235, "b": 210}),
            comment("先慢慢抬头，看向一个莫名其妙的方向。"),
            absolute(servo1=74, servo2=98, servo3=100, servo4=80),
            delay(520),
            led("solid", brightness=108, color={"r": 240, "g": 232, "b": 208}),
            delay(3200),
            comment("突然回过神来。"),
            pose("neutral"),
            delay(180),
            comment("再来一次打瞌睡版。"),
            led("solid", brightness=110, color={"r": 245, "g": 230, "b": 205}),
            absolute(servo1=90, servo2=92, servo3=92, servo4=96),
            delay(420),
            led("solid", brightness=96, color={"r": 240, "g": 225, "b": 200}),
            absolute(servo1=90, servo2=88, servo3=86, servo4=102),
            delay(420),
            led("solid", brightness=72, color={"r": 230, "g": 214, "b": 190}),
            absolute(servo1=90, servo2=84, servo3=82, servo4=108),
            delay(520),
            comment("快贴到桌面时突然弹回来。"),
            pose("neutral"),
            led("solid", brightness=120, color={"r": 245, "g": 235, "b": 210}),
        ],
    },
    "standup_reminder": {
        "title": "久坐检测：蹭蹭",
        "host_line": "如果你坐太久，它不会直接警报，而是会像宠物一样蹭蹭你，提醒你起来动一动。",
        "notes": [
            "TODO: 久坐检测信号可来自电脑端计时器、手环或座位传感器。",
            "当前版本按 PDF2 细化为：转向 -> 前埋后顶的三次蹭蹭 -> 双点头 -> 被拒绝后轻摇头。"
        ],
        "tuning_notes": [
            "三次蹭蹭必须带有‘埋头 -> 顶起 -> 后退’的节奏，不要做成机械抖动。",
            "被拒绝后的轻摇头应该很克制，像‘好吧’，不要像强烈反对。",
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=132, color={"r": 255, "g": 218, "b": 176}),
            comment("先转向评委并把灯臂往前送。"),
            absolute(servo1=98, servo2=100, servo3=102, servo4=92),
            delay(220),
            comment("第一次蹭蹭：先往下埋，再往上顶，然后后退一点。"),
            absolute(servo1=98, servo2=102, servo3=98, servo4=102),
            delay(140),
            absolute(servo1=98, servo2=96, servo3=110, servo4=88),
            delay(140),
            absolute(servo1=96, servo2=100, servo3=102, servo4=94),
            delay(120),
            comment("第二次蹭蹭。"),
            absolute(servo1=98, servo2=102, servo3=98, servo4=102),
            delay(140),
            absolute(servo1=98, servo2=96, servo3=110, servo4=88),
            delay(140),
            absolute(servo1=96, servo2=100, servo3=102, servo4=94),
            delay(120),
            comment("第三次蹭蹭。"),
            absolute(servo1=98, servo2=102, servo3=98, servo4=102),
            delay(140),
            absolute(servo1=98, servo2=96, servo3=110, servo4=88),
            delay(140),
            absolute(servo1=96, servo2=100, servo3=102, servo4=94),
            delay(160),
            comment("清晰地点两次头。"),
            nudge(servo4=5),
            delay(140),
            nudge(servo4=-10),
            delay(140),
            nudge(servo4=5),
            delay(180),
            nudge(servo4=5),
            delay(140),
            nudge(servo4=-10),
            delay(140),
            nudge(servo4=5),
            delay(180),
            comment("评委说不要后，轻轻摇一下头。"),
            nudge(servo1=4),
            delay(120),
            nudge(servo1=-8),
            delay(120),
            nudge(servo1=4),
            delay(180),
            comment("慢慢回到原位。"),
            pose("neutral"),
            led("solid", brightness=118, color=SOFT_WARM),
        ],
    },
    "track_target": {
        "title": "追踪",
        "host_line": "你试着在桌上移动这本书，它会一直跟着书看，这一段是用来证明它真的看得见。",
        "notes": [
            "TODO: 这里最终应接入真实视觉目标坐标。",
            "当前版本实现的是展位排练用 surrogate choreography：按左 -> 中 -> 右 -> 停 -> 再移动 的跟随节奏编排。"
        ],
        "tuning_notes": [
            "真正实现时要限制更新频率，避免灯头一步一跳。",
            "即使是 surrogate 版本，也要尽量做得平滑，不要像预设摆头。",
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=170, color={"r": 232, "g": 242, "b": 255}),
            comment("书在左侧时，灯头压低并看向左侧桌面。"),
            absolute(servo1=78, servo2=96, servo3=96, servo4=102),
            delay(420),
            comment("目标开始向中间移动。"),
            absolute(servo1=88, servo2=96, servo3=96, servo4=98),
            delay(360),
            comment("目标继续到右侧。"),
            absolute(servo1=102, servo2=96, servo3=96, servo4=102),
            delay(420),
            comment("评委停下来，Mira 也停住。"),
            delay(520),
            comment("评委再移动，Mira 再跟。"),
            absolute(servo1=94, servo2=96, servo3=96, servo4=98),
            delay(320),
            absolute(servo1=108, servo2=96, servo3=96, servo4=104),
            delay(420),
            comment("回到中性工作位。"),
            pose("neutral"),
            led("solid", brightness=156, color={"r": 244, "g": 244, "b": 236}),
        ],
    },
    "celebrate": {
        "title": "跳舞模式",
        "host_line": "当它收到一个超级开心的消息时，它会像真的高兴一样跳起来。",
        "notes": [
            "运行时现在会真正播放音频；若仓库里没有 dance.mp3，会先尝试系统自带提示音兜底。",
            "TODO: offer 邮件页面作为独立素材准备，不写死在脚本里。",
            "当前动作按 PDF2 为主、参考 PDF3 的手绘页，拆成上摇、下摇、灯光变色、减速和收尾摇头。"
        ],
        "tuning_notes": [
            "庆祝的起手式要高一点，这样 `dance` 不会从疲软姿态开始。",
            "如果彩虹灯太花导致动作看不清，可降低亮度到 180~200。",
            "减速收尾一定要明显，不要在最嗨的姿态上突然停掉。",
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=168, color={"r": 255, "g": 236, "b": 180}),
            delay(180),
            comment("收到 offer 后先整体往上摇。"),
            absolute(servo1=90, servo2=108, servo3=116, servo4=80),
            led("solid", brightness=198, color={"r": 255, "g": 64, "b": 64}),
            delay(180),
            absolute(servo1=78, servo2=108, servo3=112, servo4=82),
            led("solid", brightness=202, color={"r": 64, "g": 128, "b": 255}),
            delay(180),
            absolute(servo1=90, servo2=106, servo3=114, servo4=80),
            delay(140),
            absolute(servo1=102, servo2=108, servo3=112, servo4=82),
            led("solid", brightness=202, color={"r": 72, "g": 220, "b": 132}),
            delay(180),
            absolute(servo1=90, servo2=106, servo3=114, servo4=80),
            delay(160),
            comment("再整体往下摇。"),
            absolute(servo1=90, servo2=94, servo3=98, servo4=100),
            led("solid", brightness=196, color={"r": 255, "g": 168, "b": 72}),
            delay(180),
            absolute(servo1=82, servo2=94, servo3=96, servo4=100),
            led("solid", brightness=198, color={"r": 208, "g": 96, "b": 255}),
            delay(180),
            absolute(servo1=90, servo2=96, servo3=98, servo4=98),
            delay(140),
            absolute(servo1=100, servo2=94, servo3=96, servo4=100),
            led("solid", brightness=198, color={"r": 64, "g": 224, "b": 224}),
            delay(180),
            absolute(servo1=90, servo2=96, servo3=98, servo4=98),
            delay(180),
            comment("进入彩色庆祝灯效。"),
            audio(text="太好了，我们来庆祝一下！", wait=True, voice="tts"),
            led("rainbow_cycle", brightness=210),
            audio("dance.mp3", wait=False, fallback_asset="/System/Library/Sounds/Hero.aiff"),
            action("dance", loops=1),
            delay(380),
            comment("音乐停后慢慢减速，回到正常姿态。"),
            led("solid", brightness=176, color={"r": 255, "g": 208, "b": 156}),
            absolute(servo1=94, servo2=102, servo3=106, servo4=88),
            delay(180),
            absolute(servo1=90, servo2=98, servo3=102, servo4=90),
            delay(180),
            comment("左右摇头，再身体转一下，像刚跳完舞喘口气。"),
            nudge(servo4=4),
            delay(120),
            nudge(servo4=-8),
            delay(120),
            nudge(servo4=4),
            delay(120),
            nudge(servo1=6),
            delay(140),
            nudge(servo1=-6),
            delay(140),
            pose("neutral"),
            led("solid", brightness=140, color=SOFT_WARM),
        ],
    },
    "farewell": {
        "title": "挥手送别",
        "host_line": "当你离开时，它会目送你，还会轻轻摆摆头像在说再见。",
        "notes": [
            "TODO: 离场方向识别接入后，把 farewell_look 改成按离场方位实时生成。",
            "当前版本按 PDF2 为主、参考 PDF3 的手绘页，做成：目送 -> 两次慢慢点头式挥手 -> 舍不得地低头。"
        ],
        "tuning_notes": [
            "先看过去，再挥手，再低头，这三个阶段不要压成一团。",
            "挥手动作宁可慢一点，也不要做成机械抽搐。",
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=108, color={"r": 255, "g": 214, "b": 176}),
            comment("先目送评委离开的方向。"),
            absolute(servo1=106, servo2=96, servo3=100, servo4=92),
            delay(420),
            audio(text="谢谢你来看我，下次见。", wait=True, voice="tts"),
            comment("再做两次慢慢点头，像挥手说再见。"),
            nudge(servo4=5),
            delay(180),
            nudge(servo4=-10),
            delay(180),
            nudge(servo4=5),
            delay(220),
            nudge(servo4=5),
            delay(180),
            nudge(servo4=-10),
            delay(180),
            nudge(servo4=5),
            delay(220),
            comment("最后微微低头，像有点舍不得。"),
            absolute(servo1=102, servo2=92, servo3=96, servo4=100),
            delay(180),
            pose("neutral"),
            led("solid", brightness=90, color={"r": 255, "g": 210, "b": 170}),
        ],
    },
    "sleep": {
        "title": "睡觉",
        "host_line": "当人离开后，它会慢慢收回自己，回到休息状态，等下一个人来。",
        "notes": [
            "TODO: 若未来支持自动入睡，应由 no_person_timeout 或 session_end 触发。",
            "当前版本按 PDF2 / PDF3 的组合理解：先慢慢低头与降臂，再做一次舒展，最后蜷缩并慢慢熄灯。"
        ],
        "tuning_notes": [
            "最后一定要落到固定 sleep pose，避免长时间 drift。",
            "睡觉不应该像断电，而应该像慢慢把自己收回去。",
        ],
        "steps": [
            pose("neutral"),
            led("solid", brightness=118, color={"r": 250, "g": 226, "b": 184}),
            comment("先慢慢低头。"),
            absolute(servo1=90, servo2=94, servo3=96, servo4=98),
            delay(280),
            comment("灯臂缓缓降下去。"),
            absolute(servo1=90, servo2=90, servo3=90, servo4=102),
            delay(320),
            comment("做一个小伸懒腰：先舒展一下。"),
            absolute(servo1=90, servo2=96, servo3=104, servo4=88),
            delay(260),
            comment("再慢慢回到准备睡觉的姿态。"),
            pose("sleep_ready"),
            delay(300),
            pose("sleep"),
            delay(220),
            *fade_to_sleep(WARM_AMBER),
        ],
    },
    "sigh_demo": {
        "title": "叹气检测",
        "host_line": "你对着它叹一口气，它就会像听懂了一样看你一下，光也会变暖。",
        "notes": [
            "TODO: 这里需要麦克风与音频模式识别；在那之前默认通过 OpenClaw 或终端命令触发。",
        ],
        "tuning_notes": [
            "这个场景应该偏克制，像安静地看向你，而不是夸张动作。"
        ],
        "steps": [
            pose("tilt_left"),
            audio(text="我在呢，慢一点也没关系。", wait=True, voice="tts"),
            led("breathing", brightness=88, color=COMFORT_WARM),
            delay(1700),
            pose("neutral"),
        ],
    },
    "multi_person_demo": {
        "title": "多人反应",
        "host_line": "如果同时有两个人，它会短暂纠结，不知道该先看谁，最后才选定一个。",
        "notes": [
            "TODO: 真正实现时需要多目标检测。当前用固定左右扫视代替。"
        ],
        "tuning_notes": [
            "左右扫视不要过快，否则像监控摄像头而不是纠结。"
        ],
        "steps": [
            pose("curious_half_left"),
            delay(420),
            pose("neutral"),
            delay(220),
            pose("curious_full_left"),
            delay(420),
            pose("neutral"),
        ],
    },
    "voice_demo_tired": {
        "title": "语音理解：我今天好累",
        "host_line": "你只要说一句‘今天好累啊’，它就会用动作和灯光告诉你：它听懂了。",
        "notes": [
            "TODO: 真正实现时接语音识别和情绪分类；在那之前默认通过 OpenClaw 或终端命令触发。"
        ],
        "tuning_notes": [
            "重点是安静地接住情绪，不要做成积极打招呼。"
        ],
        "steps": [
            pose("farewell_bow"),
            audio(text="辛苦了，要不要先休息一下？", wait=True, voice="tts"),
            led("breathing", brightness=70, color=COMFORT_WARM),
            delay(2000),
            pose("neutral"),
            led("solid", brightness=110, color=SOFT_WARM),
        ],
    },
}

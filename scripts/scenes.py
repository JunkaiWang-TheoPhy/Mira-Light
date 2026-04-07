"""Scene definitions for the Mira Light booth demo.

This file is intentionally "half concrete, half commented":

- Concrete parts:
  - scene names
  - host lines
  - rough step order
  - HTTP-call-friendly primitives that already match the ESP32 API

- Placeholder parts:
  - exact servo semantics
  - sensor triggers
  - audio playback integration
  - vision / voice / touch detection

The goal is to let us wire the booth flow now, even before every hardware detail
is finalized.
"""

# IMPORTANT:
# The project currently exposes only `servo1` ~ `servo4`.
# Their true physical meanings should be confirmed later, for example:
#
# - servo1: base yaw
# - servo2: lower arm lift
# - servo3: upper arm pitch
# - servo4: head pitch / head tilt
#
# Until that mapping is verified on the real lamp, all angle values below are
# "rehearsal placeholders". They are useful for script structure, but must be
# tuned on hardware before the demo.

SCENES = {
    "wake_up": {
        "title": "起床",
        "host_line": "当 Mira 感觉到有人靠近，它不会立刻机械转头，而是像刚醒的小动物一样慢慢睁眼、抖一抖、伸个懒腰。",
        "notes": [
            "TODO: 把这个场景接到 person_detected_near 事件；在那之前默认通过 OpenClaw 或终端命令触发。",
            "TODO: 真实调试后把睡姿 -> 正常位的角度写成明确姿态表，而不是相对增量。",
        ],
        "steps": [
            {"type": "comment", "text": "先把灯从睡眠微光慢慢唤醒。"},
            {
                "type": "led",
                "payload": {
                    "mode": "breathing",
                    "color": {"r": 255, "g": 180, "b": 120},
                    "brightness": 40,
                },
            },
            {"type": "delay", "ms": 700},
            {"type": "comment", "text": "粗略抬起灯臂。具体关节语义后续再校准。"},
            {"type": "control", "payload": {"mode": "relative", "servo2": 12, "servo3": 8}},
            {"type": "delay", "ms": 500},
            {"type": "comment", "text": "模拟醒来抖两下。"},
            {"type": "control", "payload": {"mode": "relative", "servo4": 8}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo4": -8}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo4": 6}},
            {"type": "delay", "ms": 200},
            {"type": "action", "payload": {"name": "stretch", "loops": 1}},
            {
                "type": "led",
                "payload": {
                    "mode": "solid",
                    "color": {"r": 255, "g": 220, "b": 180},
                    "brightness": 130,
                },
            },
        ],
    },
    "curious_observe": {
        "title": "好奇你是谁",
        "host_line": "Mira 不会机械地直接盯着你，它会先试探着转过去一半，停一下，再歪头看你。",
        "notes": [
            "TODO: 接入目标方向识别后，把固定动作改成 turn_to_target(target)。",
            "TODO: 如果能识别左右方向，可以准备 left / center / right 三个版本。"
        ],
        "steps": [
            {"type": "comment", "text": "先半转头，制造试探感。"},
            {"type": "control", "payload": {"mode": "relative", "servo1": 10}},
            {"type": "delay", "ms": 450},
            {"type": "comment", "text": "继续转过去。"},
            {"type": "control", "payload": {"mode": "relative", "servo1": 10}},
            {"type": "delay", "ms": 400},
            {"type": "comment", "text": "歪头看你。"},
            {"type": "control", "payload": {"mode": "relative", "servo4": 12}},
            {"type": "delay", "ms": 1800},
            {"type": "action", "payload": {"name": "nod", "loops": 1}},
            {"type": "delay", "ms": 300},
            {"type": "control", "payload": {"mode": "relative", "servo4": -12}},
        ],
    },
    "touch_affection": {
        "title": "摸一摸",
        "host_line": "你可以摸摸它。它会主动靠过来，不只是响应动作，而是在表达亲近。",
        "notes": [
            "TODO: 触摸传感器或手部识别接入后，真正根据手的位置调整前探方向。",
            "TODO: 现在的 rub_motion 是简化版，用小幅左右摆模拟。"
        ],
        "steps": [
            {
                "type": "led",
                "payload": {
                    "mode": "solid",
                    "color": {"r": 255, "g": 190, "b": 120},
                    "brightness": 180,
                },
            },
            {"type": "comment", "text": "向手的方向前探。当前先用固定前探。"},
            {"type": "control", "payload": {"mode": "relative", "servo2": 6, "servo3": 8}},
            {"type": "delay", "ms": 350},
            {"type": "comment", "text": "小幅左右蹭手。"},
            {"type": "control", "payload": {"mode": "relative", "servo1": 6}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo1": -12}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo1": 6}},
            {"type": "delay", "ms": 180},
            {"type": "comment", "text": "手拿开后追一下。"},
            {"type": "control", "payload": {"mode": "relative", "servo1": 8}},
            {"type": "delay", "ms": 220},
            {"type": "control", "payload": {"mode": "relative", "servo1": -8, "servo2": -6, "servo3": -8}},
        ],
    },
    "cute_probe": {
        "title": "卖萌",
        "host_line": "它会像小狗一样歪头研究你，有时还会探头一下又缩回去。",
        "notes": [
            "这个场景建议保留两个版本：歪头版和探头版。",
            "TODO: 后续可做 scene variant 选择，目前先合成一个短版。"
        ],
        "steps": [
            {"type": "control", "payload": {"mode": "relative", "servo4": 10}},
            {"type": "delay", "ms": 1000},
            {"type": "control", "payload": {"mode": "relative", "servo4": -20}},
            {"type": "delay", "ms": 1000},
            {"type": "control", "payload": {"mode": "relative", "servo4": 10}},
            {"type": "delay", "ms": 250},
            {"type": "comment", "text": "做一个胆小的探头。"},
            {"type": "control", "payload": {"mode": "relative", "servo2": 6, "servo3": 10}},
            {"type": "delay", "ms": 600},
            {"type": "control", "payload": {"mode": "relative", "servo2": -6, "servo3": -10}},
        ],
    },
    "daydream": {
        "title": "发呆",
        "host_line": "它不会一直表演，它也会像人一样走神，盯着某个方向发一会儿呆。",
        "notes": [
            "TODO: 未来可接随机方向选择或环境显著目标选择。",
            "TODO: 可以再加一个 sleepy_nod 变体。"
        ],
        "steps": [
            {"type": "control", "payload": {"mode": "relative", "servo1": -15, "servo4": -6}},
            {"type": "delay", "ms": 3500},
            {"type": "comment", "text": "回过神来，快速回正。"},
            {"type": "control", "payload": {"mode": "relative", "servo1": 15, "servo4": 6}},
        ],
    },
    "standup_reminder": {
        "title": "久坐检测：蹭蹭",
        "host_line": "如果你坐太久，它不会直接警报，而是会像宠物一样蹭蹭你，提醒你起来动一动。",
        "notes": [
            "TODO: 久坐检测信号可以来自电脑端计时器、手环或座位传感器。",
            "TODO: 当前的 pawing_bump 只是近似版，需要真实关节语义后再调。"
        ],
        "steps": [
            {"type": "comment", "text": "蹭蹭 x3。"},
            {"type": "control", "payload": {"mode": "relative", "servo2": -5, "servo3": 8}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo2": 5, "servo3": -8}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo2": -5, "servo3": 8}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo2": 5, "servo3": -8}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo2": -5, "servo3": 8}},
            {"type": "delay", "ms": 180},
            {"type": "control", "payload": {"mode": "relative", "servo2": 5, "servo3": -8}},
            {"type": "delay", "ms": 250},
            {"type": "action", "payload": {"name": "nod", "loops": 2}},
            {"type": "delay", "ms": 300},
            {"type": "comment", "text": "如果用户明确拒绝提醒，可播放 shake。当前默认不自动执行。"},
        ],
    },
    "track_target": {
        "title": "追踪",
        "host_line": "你试着在桌上移动这本书，它会一直跟着书看，这一段是用来证明它真的看得见。",
        "notes": [
            "TODO: 这里必须接入视觉系统或至少鼠标/滑杆模拟目标输入。",
            "TODO: 当前只保留注释，不做假实现，以免误导为真正追踪。"
        ],
        "steps": [
            {"type": "comment", "text": "TODO: 进入 tracking loop，根据目标 x/y 持续调整 servo1/servo4。"},
            {"type": "comment", "text": "TODO: 若没有视觉，先在控制台做 fake tracking：用滑杆给目标方向。"},
        ],
    },
    "celebrate": {
        "title": "跳舞模式",
        "host_line": "当它收到一个超级开心的消息时，它会像真的高兴一样跳起来。",
        "notes": [
            "TODO: 本地电脑配一首固定的 dance.mp3；当前控制器里只打印 audio TODO。",
            "TODO: offer 邮件页面作为独立素材准备，不写死在脚本里。"
        ],
        "steps": [
            {
                "type": "led",
                "payload": {
                    "mode": "rainbow_cycle",
                    "brightness": 220,
                },
            },
            {"type": "audio", "name": "dance.mp3"},
            {"type": "action", "payload": {"name": "dance", "loops": 2}},
            {"type": "delay", "ms": 500},
            {"type": "comment", "text": "跳舞结束后慢慢收回来。"},
            {
                "type": "led",
                "payload": {
                    "mode": "solid",
                    "color": {"r": 255, "g": 220, "b": 180},
                    "brightness": 140,
                },
            },
        ],
    },
    "farewell": {
        "title": "挥手送别",
        "host_line": "当你离开时，它会目送你，还会轻轻摆摆头像在说再见。",
        "notes": [
            "TODO: 离场方向识别接入后，把 wave 前面的跟随方向变成真实跟随。",
            "当前先用固定动作，保证现场稳定性。"
        ],
        "steps": [
            {"type": "control", "payload": {"mode": "relative", "servo1": 12}},
            {"type": "delay", "ms": 500},
            {"type": "action", "payload": {"name": "wave", "loops": 1}},
            {"type": "delay", "ms": 250},
            {"type": "control", "payload": {"mode": "relative", "servo4": 8}},
            {"type": "delay", "ms": 300},
            {"type": "control", "payload": {"mode": "relative", "servo4": -8, "servo1": -12}},
        ],
    },
    "sleep": {
        "title": "睡觉",
        "host_line": "当人离开后，它会慢慢收回自己，回到休息状态，等下一个人来。",
        "notes": [
            "TODO: 真实睡姿建议改成 absolute 姿态表，便于重复回到同一姿势。",
        ],
        "steps": [
            {"type": "action", "payload": {"name": "stretch", "loops": 1}},
            {"type": "delay", "ms": 300},
            {"type": "comment", "text": "粗略进入睡姿。"},
            {"type": "control", "payload": {"mode": "relative", "servo2": -12, "servo3": -12, "servo4": 6}},
            {
                "type": "led",
                "payload": {
                    "mode": "solid",
                    "color": {"r": 255, "g": 180, "b": 120},
                    "brightness": 20,
                },
            },
            {"type": "delay", "ms": 600},
            {
                "type": "led",
                "payload": {
                    "mode": "off",
                    "brightness": 0,
                },
            },
        ],
    },
    "sigh_demo": {
        "title": "叹气检测",
        "host_line": "你对着它叹一口气，它就会像听懂了一样看你一下，光也会变暖。",
        "notes": [
            "TODO: 这里需要麦克风与音频模式识别；在那之前默认通过 OpenClaw 或终端命令触发。",
        ],
        "steps": [
            {"type": "control", "payload": {"mode": "relative", "servo4": 8}},
            {
                "type": "led",
                "payload": {
                    "mode": "breathing",
                    "color": {"r": 255, "g": 170, "b": 110},
                    "brightness": 90,
                },
            },
            {"type": "delay", "ms": 1800},
            {"type": "control", "payload": {"mode": "relative", "servo4": -8}},
        ],
    },
    "multi_person_demo": {
        "title": "多人反应",
        "host_line": "如果同时有两个人，它会短暂纠结，不知道该先看谁，最后才选定一个。",
        "notes": [
            "TODO: 真正实现时需要多目标检测。当前用固定左右扫视代替。"
        ],
        "steps": [
            {"type": "control", "payload": {"mode": "relative", "servo1": 12}},
            {"type": "delay", "ms": 500},
            {"type": "control", "payload": {"mode": "relative", "servo1": -24}},
            {"type": "delay", "ms": 500},
            {"type": "control", "payload": {"mode": "relative", "servo1": 12}},
        ],
    },
    "voice_demo_tired": {
        "title": "语音理解：我今天好累",
        "host_line": "你只要说一句‘今天好累啊’，它就会用动作和灯光告诉你：它听懂了。",
        "notes": [
            "TODO: 真正实现时接语音识别和情绪分类；在那之前默认通过 OpenClaw 或终端命令触发。"
        ],
        "steps": [
            {"type": "control", "payload": {"mode": "relative", "servo4": 6}},
            {
                "type": "led",
                "payload": {
                    "mode": "breathing",
                    "color": {"r": 255, "g": 180, "b": 120},
                    "brightness": 70,
                },
            },
            {"type": "delay", "ms": 2000},
            {"type": "control", "payload": {"mode": "relative", "servo4": -6}},
        ],
    },
}

from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
BRIDGE_DIR = ROOT / "tools" / "mira_light_bridge"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

from bridge_server import BridgeHTTPServer, BridgeHandler
import mira_light_runtime as runtime_module
from mira_light_runtime import BoothController, MiraLightRuntime
from scenes import LED_PIXEL_COUNT, POSES, SCENES


def request_json(url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        finally:
            exc.close()


class MinimalSmokeTest(unittest.TestCase):
    PRIMARY_SCENES = {
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
    }

    def _wait_until_not_running(self, bridge_base_url: str, *, attempts: int = 20) -> None:
        for _ in range(attempts):
            status, runtime_state = request_json(f"{bridge_base_url}/v1/mira-light/runtime")
            self.assertEqual(status, 200)
            if not runtime_state["runtime"]["running"]:
                return
            time.sleep(0.02)
        self.fail("runtime did not settle before the next trigger")

    def test_runtime_lists_ready_scenes_only_by_default(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        scenes = runtime.list_scenes()
        self.assertTrue(scenes)
        self.assertEqual({item["id"] for item in scenes}, self.PRIMARY_SCENES)
        self.assertTrue(self.PRIMARY_SCENES.issuperset({item["id"] for item in scenes}))

    def test_celebrate_scene_uses_vector_color_ring(self) -> None:
        led_steps = [step for step in SCENES["celebrate"]["steps"] if step.get("type") == "led"]
        vector_steps = [step for step in led_steps if step["payload"].get("mode") == "vector"]

        self.assertEqual(len(vector_steps), 1)
        self.assertEqual(vector_steps[0]["payload"]["brightness"], 210)
        self.assertEqual(len(vector_steps[0]["payload"]["pixels"]), LED_PIXEL_COUNT)
        self.assertGreater(len({tuple(sorted(pixel.items())) for pixel in vector_steps[0]["payload"]["pixels"]}), 1)

    def test_bridge_supports_minimal_mode(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, health = request_json(f"{base_url}/health")
                self.assertEqual(status, 200)
                self.assertTrue(health["ok"])

                status, scenes = request_json(f"{base_url}/v1/mira-light/scenes")
                self.assertEqual(status, 200)
                self.assertEqual({item["id"] for item in scenes["items"]}, self.PRIMARY_SCENES)

                status, blocked = request_json(
                    f"{base_url}/v1/mira-light/run-scene",
                    method="POST",
                    payload={"scene": "voice_demo_tired", "async": False},
                )
                self.assertEqual(status, 400)
                self.assertIn("minimal mode", blocked["error"])

                status, ran = request_json(
                    f"{base_url}/v1/mira-light/run-scene",
                    method="POST",
                    payload={"scene": "farewell", "async": False, "cueMode": "director"},
                )
                self.assertEqual(status, 200)
                self.assertTrue(ran["ok"])

                status, logs = request_json(f"{base_url}/v1/mira-light/logs")
                self.assertEqual(status, 200)
                self.assertTrue(logs["items"])
                log_text = "\n".join(item["text"] for item in logs["items"])
                self.assertIn("[cue-host]", log_text)
                self.assertIn("[audio-dry-run]", log_text)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_bridge_exposes_signal_delivery_contract_and_schema(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, contract = request_json(f"{base_url}/v1/mira-light/signal-delivery")
                self.assertEqual(status, 200)
                self.assertEqual(contract["data"]["docPath"], "docs/Guide/09-Mira Light统一信号交付格式说明.md")
                self.assertEqual(contract["data"]["schemaPath"], "config/mira_light_signal_delivery.schema.json")
                self.assertEqual(contract["data"]["signalDomains"], ["jointControl", "led", "headCapacitive"])
                self.assertEqual(contract["data"]["contracts"][1]["payload"]["readPixelsField"], "pixelSignals")

                status, schema = request_json(f"{base_url}/v1/mira-light/signal-delivery/schema")
                self.assertEqual(status, 200)
                self.assertEqual(schema["data"]["$id"], "https://mira-light.local/schemas/mira_light_signal_delivery.schema.json")
                self.assertIn("led_count", schema["data"]["$defs"]["led_state"]["required"])
                self.assertIn("headCapacitive", schema["data"]["$defs"]["sensor_write_request"]["required"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_bridge_silent_mode_skips_audio_steps(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, ran = request_json(
                    f"{base_url}/v1/mira-light/run-scene",
                    method="POST",
                    payload={"scene": "farewell", "async": False, "cueMode": "director", "silentMode": True},
                )
                self.assertEqual(status, 200)
                self.assertTrue(ran["ok"])

                status, logs = request_json(f"{base_url}/v1/mira-light/logs")
                self.assertEqual(status, 200)
                log_text = "\n".join(item["text"] for item in logs["items"])
                self.assertIn("[cue-host-muted]", log_text)
                self.assertIn("[audio-skip-silent]", log_text)
                self.assertNotIn("[audio-dry-run]", log_text)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_bridge_trigger_endpoint_starts_unavailable_scene(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, triggered = request_json(
                    f"{base_url}/v1/mira-light/trigger",
                    method="POST",
                    payload={"event": "voice_tired", "payload": {"transcript": "我今天好累啊"}},
                )
                self.assertEqual(status, 200)
                self.assertTrue(triggered["ok"])
                self.assertIn(
                    "voice_demo_tired",
                    {triggered["runtime"]["runningScene"], triggered["runtime"]["lastFinishedScene"]},
                )
                self._wait_until_not_running(base_url)

                status, praise = request_json(
                    f"{base_url}/v1/mira-light/trigger",
                    method="POST",
                    payload={"event": "praise_detected", "payload": {"transcript": "你好可爱"}},
                )
                self.assertEqual(status, 200)
                self.assertTrue(praise["ok"])
                self.assertIn(
                    "praise_demo",
                    {praise["runtime"]["runningScene"], praise["runtime"]["lastFinishedScene"]},
                )
                self._wait_until_not_running(base_url)

                status, startle = request_json(
                    f"{base_url}/v1/mira-light/trigger",
                    method="POST",
                    payload={"event": "startle_detected", "payload": {"transcript": "突然一声响动"}},
                )
                self.assertEqual(status, 200)
                self.assertTrue(startle["ok"])
                self.assertIn(
                    "startle_sound",
                    {startle["runtime"]["runningScene"], startle["runtime"]["lastFinishedScene"]},
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_bridge_speak_endpoint_supports_short_public_lines(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, spoken = request_json(
                    f"{base_url}/v1/mira-light/speak",
                    method="POST",
                    payload={"text": "你好，我是 Mira。", "voice": "openclaw", "wait": False},
                )
                self.assertEqual(status, 200)
                self.assertTrue(spoken["ok"])
                self.assertEqual(spoken["data"]["payload"]["voice"], "openclaw")
                self.assertFalse(spoken["data"]["payload"]["wait"])

                status, blocked = request_json(
                    f"{base_url}/v1/mira-light/speak",
                    method="POST",
                    payload={"text": "x" * 81},
                )
                self.assertEqual(status, 400)
                self.assertIn("no longer than", blocked["error"])

                status, logs = request_json(f"{base_url}/v1/mira-light/logs")
                self.assertEqual(status, 200)
                log_text = "\n".join(item["text"] for item in logs["items"])
                self.assertIn("[runtime] speak voice=openclaw", log_text)
                self.assertIn("[audio-dry-run]", log_text)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_runtime_validates_direct_joint_control_payload(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)

        accepted = runtime.control_joints({"mode": "absolute", "servo1": 90, "servo4": 92})
        self.assertEqual(
            accepted["payload"],
            {"mode": "absolute", "servo1": 90, "servo4": 92},
        )

        with self.assertRaisesRegex(RuntimeError, "At least one servo field is required"):
            runtime.control_joints({"mode": "absolute"})

        with self.assertRaisesRegex(RuntimeError, "rehearsal_range"):
            runtime.control_joints({"mode": "absolute", "servo1": 160})

        with self.assertRaisesRegex(RuntimeError, "relative delta must be between"):
            runtime.control_joints({"mode": "relative", "servo2": 90})

    def test_runtime_prealigns_scene_start_when_status_is_misaligned(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        fake_status = {
            "servos": [
                {"name": "servo1", "angle": 104},
                {"name": "servo2", "angle": 96},
                {"name": "servo3", "angle": 98},
                {"name": "servo4", "angle": 90},
            ]
        }
        control_calls: list[tuple[dict, int | None]] = []

        def fake_control(payload: dict, *, move_ms: int | None = None) -> dict:
            control_calls.append((payload, move_ms))
            return {"ok": True}

        with mock.patch.object(runtime_module, "SCENE_START_ALIGN_ENABLED", True):
            with mock.patch.object(runtime, "get_status", return_value=fake_status):
                with mock.patch.object(runtime.get_client(), "control", side_effect=fake_control):
                    with mock.patch.object(BoothController, "run_scene", autospec=True, return_value=None):
                        runtime.run_scene_blocking("wake_up")

        self.assertEqual(len(control_calls), 1)
        self.assertEqual(control_calls[0][0], {"mode": "absolute", **POSES["sleep"]["angles"]})
        self.assertEqual(control_calls[0][1], 700)
        log_text = "\n".join(item["text"] for item in runtime.get_logs())
        self.assertIn("[pre-align] wake_up", log_text)

    def test_runtime_skips_scene_prealign_when_status_already_matches_start_pose(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        sleep_angles = POSES["sleep"]["angles"]
        fake_status = {
            "servos": [
                {"name": "servo1", "angle": sleep_angles["servo1"]},
                {"name": "servo2", "angle": sleep_angles["servo2"]},
                {"name": "servo3", "angle": sleep_angles["servo3"]},
                {"name": "servo4", "angle": sleep_angles["servo4"]},
            ]
        }

        with mock.patch.object(runtime_module, "SCENE_START_ALIGN_ENABLED", True):
            with mock.patch.object(runtime, "get_status", return_value=fake_status):
                with mock.patch.object(runtime.get_client(), "control") as mocked_control:
                    with mock.patch.object(BoothController, "run_scene", autospec=True, return_value=None):
                        runtime.run_scene_blocking("wake_up")

        mocked_control.assert_not_called()
        log_text = "\n".join(item["text"] for item in runtime.get_logs())
        self.assertNotIn("[pre-align] wake_up", log_text)

    def test_runtime_blocks_manual_joint_and_led_changes_while_scene_running(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with runtime._state_lock:
            runtime._running_scene = "farewell"

        with self.assertRaisesRegex(RuntimeError, "while a scene is running"):
            runtime.control_joints({"mode": "absolute", "servo1": 90})

        with self.assertRaisesRegex(RuntimeError, "while a scene is running"):
            runtime.set_led_state({"mode": "solid", "color": {"r": 255, "g": 200, "b": 100}})

    def test_runtime_validates_manual_speak_payload(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)

        accepted = runtime.speak_text({"text": " 你好，\n我是 Mira。 ", "voice": "openclaw", "wait": False})
        self.assertEqual(
            accepted["payload"],
            {"text": "你好， 我是 Mira。", "voice": "openclaw", "wait": False},
        )

        with self.assertRaisesRegex(RuntimeError, "text is required"):
            runtime.speak_text({})

        with self.assertRaisesRegex(RuntimeError, "no longer than"):
            runtime.speak_text({"text": "x" * 81})

        with self.assertRaisesRegex(RuntimeError, "voice must be one of"):
            runtime.speak_text({"text": "你好", "voice": "robot"})

    def test_runtime_validates_led_vector_payload(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        pixels = [{"r": index, "g": 255 - index, "b": 32} for index in range(40)]
        rgba_pixels = [[index, 255 - index, 32, 180] for index in range(40)]

        accepted = runtime.set_led_state({"mode": "vector", "brightness": 180, "pixels": pixels})
        self.assertEqual(accepted["payload"]["mode"], "vector")
        self.assertEqual(len(accepted["payload"]["pixels"]), 40)
        self.assertEqual(accepted["payload"]["pixels"][0], {"r": 0, "g": 255, "b": 32, "brightness": 180})

        accepted = runtime.set_led_state({"mode": "vector", "pixels": rgba_pixels})
        self.assertEqual(accepted["payload"]["pixels"][0], {"r": 0, "g": 255, "b": 32, "brightness": 180})

        with self.assertRaisesRegex(RuntimeError, "exactly 40"):
            runtime.set_led_state({"mode": "vector", "pixels": pixels[:10]})

        with self.assertRaisesRegex(RuntimeError, "between 0 and 255"):
            runtime.set_led_state(
                {"mode": "vector", "brightness": 180, "pixels": [[0, 0, 0]] * 39 + [[256, 0, 0]]}
            )

        with self.assertRaisesRegex(RuntimeError, "use pixels"):
            runtime.set_led_state({"mode": "vector", "pixelSignals": rgba_pixels})

    def test_runtime_tcp_cache_exposes_unified_signal_status(self) -> None:
        runtime = MiraLightRuntime(base_url="tcp://127.0.0.1:9527", dry_run=True)
        pixels = [[12, 34, 56, 120] for _ in range(40)]

        led_state = runtime.set_led_state({"mode": "vector", "pixels": pixels})
        self.assertEqual(led_state["led_count"], 40)
        self.assertEqual(led_state["pixelSignals"][0], [12, 34, 56, 120])
        self.assertFalse(led_state["supported"])

        sensors_state = runtime.set_sensors_state({"headCapacitive": 1})
        self.assertEqual(sensors_state["headCapacitive"], 1)
        self.assertTrue(sensors_state["simulated"])

        status = runtime.get_status()
        self.assertEqual(status["sensors"]["headCapacitive"], 1)
        self.assertEqual(status["led"]["led_count"], 40)
        self.assertEqual(status["led"]["pixelSignals"][0], [12, 34, 56, 120])
        self.assertIn("pixels", status["led"])

        direct_sensors = runtime.get_sensors()
        self.assertEqual(direct_sensors["headCapacitive"], 1)
        self.assertEqual(direct_sensors["transport"], "tcp")

    def test_bridge_rejects_invalid_control_and_accepts_led_vector(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, blocked = request_json(
                    f"{base_url}/v1/mira-light/control",
                    method="POST",
                    payload={"mode": "absolute", "servo2": 160},
                )
                self.assertEqual(status, 400)
                self.assertIn("rehearsal_range", blocked["error"])

                pixels = [[12, 34, 56, 120] for _ in range(40)]
                status, accepted = request_json(
                    f"{base_url}/v1/mira-light/led",
                    method="POST",
                    payload={"mode": "vector", "pixels": pixels},
                )
                self.assertEqual(status, 200)
                self.assertEqual(len(accepted["data"]["payload"]["pixels"]), 40)
                self.assertEqual(accepted["data"]["payload"]["pixels"][0]["brightness"], 120)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_dynamic_farewell_preview_uses_requested_direction(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        scene = runtime.preview_scene("farewell", {"departureDirection": "left"})
        first_absolute = next(
            step for step in scene["steps"] if step.get("type") == "control" and step.get("payload", {}).get("mode") == "absolute"
        )
        self.assertEqual(first_absolute["payload"]["servo1"], 78)

    def test_dynamic_curious_preview_uses_owner_direction_when_face_found(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        scene = runtime.preview_scene(
            "curious_observe",
            {
                "ownerFaceFound": True,
                "ownerDirection": "right",
                "judgeDirection": "left",
                "ownerDetector": "haar_face",
            },
        )
        self.assertIn("主人的脸", scene["notes"][0])
        self.assertIn("右侧", scene["notes"][0])
        target_step = next(
            step for step in scene["steps"]
            if step.get("type") == "comment" and "找到主人的脸后" in step.get("text", "")
        )
        target_index = scene["steps"].index(target_step)
        focus_step = scene["steps"][target_index + 1]
        self.assertEqual(focus_step["payload"]["servo1"], 100)

    def test_dynamic_curious_preview_falls_back_opposite_judge_direction(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        scene = runtime.preview_scene(
            "curious_observe",
            {
                "ownerFaceFound": False,
                "judgeDirection": "right",
            },
        )
        self.assertIn("反方向左侧回退", scene["notes"][0])
        fallback_step = next(
            step for step in scene["steps"]
            if step.get("type") == "comment" and "反方向左侧" in step.get("text", "")
        )
        fallback_index = scene["steps"].index(fallback_step)
        fallback_pose = scene["steps"][fallback_index + 2]
        self.assertEqual(fallback_pose["payload"]["servo1"], 78)

    def test_capture_pose_and_servo_meta_refresh_runtime_profile(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        fake_status = {
            "servos": [
                {"name": "servo1", "angle": 91},
                {"name": "servo2", "angle": 95},
                {"name": "servo3", "angle": 101},
                {"name": "servo4", "angle": 89},
            ]
        }
        with TemporaryDirectory() as tmpdir:
            temp_profile = Path(tmpdir) / "mira_light_profile.local.json"
            with mock.patch.object(runtime, "_profile_path", return_value=temp_profile):
                with mock.patch.object(runtime, "get_status", return_value=fake_status):
                    saved = runtime.capture_pose_to_profile("test_pose_runtime", notes="unit-test", verified=True)
                self.assertEqual(saved["angles"]["servo3"], 101)
                self.assertIn("test_pose_runtime", runtime.get_profile()["poses"])
                updated = runtime.update_servo_meta_in_profile(
                    "servo1",
                    {"neutral": 93, "rehearsal_range": [74, 108], "verified": True},
                )
                self.assertEqual(updated["value"]["neutral"], 93)
                self.assertEqual(runtime.get_profile()["servoCalibration"]["servo1"]["neutral"], 93)

    def test_apply_tracking_event_sets_tracking_state(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        event = {
            "event_type": "target_updated",
            "tracking": {
                "target_present": True,
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "distance_band": "mid",
                "approach_state": "stable",
                "target_class": "person",
                "confidence": 0.84,
            },
            "control_hint": {
                "yaw_error_norm": 0.35,
                "pitch_error_norm": -0.15,
                "lift_intent": 0.62,
                "reach_intent": 0.58,
            },
        }
        state = runtime.apply_tracking_event(event)
        self.assertTrue(state["trackingActive"])
        self.assertEqual(state["trackingTarget"]["horizontalZone"], "right")
        self.assertEqual(state["trackingTarget"]["servoCommand"]["mode"], "absolute")


if __name__ == "__main__":
    unittest.main()

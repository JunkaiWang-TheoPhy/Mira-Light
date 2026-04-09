import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from scripts.mira_lingzhu_client import normalize_string_list, send_via_lingzhu_messages


class _Handler(BaseHTTPRequestHandler):
    last_request = None

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        payload = json.loads(body)
        _Handler.last_request = {
            "path": self.path,
            "headers": dict(self.headers),
            "payload": payload,
        }
        response = {
            "ok": True,
            "text": "你好呀",
            "upstream": {"model": "openai-codex/gpt-5.3-codex-spark"},
            "promptPack": {"additionalUserIds": payload.get("additional_user_ids", [])},
        }
        encoded = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):  # noqa: A003
        return


class MiraLingzhuClientTest(unittest.TestCase):
    def test_normalize_string_list(self):
        self.assertEqual(normalize_string_list("mira-light-bridge, booth-a, booth-a"), ["mira-light-bridge", "booth-a"])
        self.assertEqual(normalize_string_list(["a", " ", "b", "a"]), ["a", "b"])

    def test_send_via_lingzhu_messages_builds_expected_payload(self):
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            text, meta = send_via_lingzhu_messages(
                [{"role": "system", "content": "你是 Mira。"}, {"role": "user", "content": "你好"}],
                base_url=f"http://127.0.0.1:{server.server_port}",
                auth_ak="secret-ak",
                agent_id="main",
                user_id="booth-user-1",
                session_id="session-1",
                additional_user_ids="mira-light-bridge, booth-runtime",
                timeout_seconds=5,
            )
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

        self.assertEqual(text, "你好呀")
        self.assertEqual(meta["provider"], "lingzhu-live-adapter")
        self.assertEqual(meta["model"], "openai-codex/gpt-5.3-codex-spark")
        self.assertEqual(meta["additionalUserIds"], ["mira-light-bridge", "booth-runtime"])
        self.assertEqual(_Handler.last_request["path"], "/v1/chat")
        self.assertEqual(_Handler.last_request["headers"]["Authorization"], "Bearer secret-ak")
        self.assertEqual(_Handler.last_request["payload"]["user_id"], "booth-user-1")
        self.assertEqual(_Handler.last_request["payload"]["session_id"], "session-1")
        self.assertEqual(_Handler.last_request["payload"]["additional_user_ids"], ["mira-light-bridge", "booth-runtime"])
        self.assertEqual(_Handler.last_request["payload"]["message"][0]["role"], "system")
        self.assertEqual(_Handler.last_request["payload"]["message"][1]["text"], "你好")

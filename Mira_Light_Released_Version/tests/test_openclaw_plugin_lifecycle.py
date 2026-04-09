import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import sys


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = ROOT / "scripts" / "install_local_openclaw_mira_light.py"
REMOVE_SCRIPT = ROOT / "scripts" / "remove_local_openclaw_mira_light.py"


class OpenClawPluginLifecycleTest(unittest.TestCase):
    def test_install_and_remove_plugin_round_trip(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            config_path = tmp_root / "openclaw.json"
            extensions_dir = tmp_root / "extensions"
            config_path.write_text(
                json.dumps(
                    {
                        "plugins": {
                            "allow": ["other-plugin"],
                            "entries": {"other-plugin": {"enabled": True, "config": {"hello": "world"}}},
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            install = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--config-path",
                    str(config_path),
                    "--extensions-dir",
                    str(extensions_dir),
                    "--bridge-base-url",
                    "http://127.0.0.1:19783",
                    "--bridge-token",
                    "token-xyz",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertEqual(install.returncode, 0, install.stdout)

            installed = json.loads(config_path.read_text(encoding="utf-8"))
            plugin_entry = installed["plugins"]["entries"]["mira-light-bridge"]
            self.assertIn("mira-light-bridge", installed["plugins"]["allow"])
            self.assertEqual(plugin_entry["config"]["bridgeBaseUrl"], "http://127.0.0.1:19783")
            self.assertEqual(plugin_entry["config"]["bridgeToken"], "token-xyz")
            plugin_dir = extensions_dir / "mira-light-bridge"
            self.assertTrue(plugin_dir.is_symlink())

            remove = subprocess.run(
                [
                    sys.executable,
                    str(REMOVE_SCRIPT),
                    "--config-path",
                    str(config_path),
                    "--extensions-dir",
                    str(extensions_dir),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertEqual(remove.returncode, 0, remove.stdout)

            removed = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertNotIn("mira-light-bridge", removed["plugins"]["allow"])
            self.assertNotIn("mira-light-bridge", removed["plugins"]["entries"])
            self.assertIn("other-plugin", removed["plugins"]["allow"])
            self.assertIn("other-plugin", removed["plugins"]["entries"])
            self.assertFalse(plugin_dir.exists() or plugin_dir.is_symlink())

            backups = sorted(tmp_root.glob("openclaw.json.bak.mira-light-*"))
            self.assertGreaterEqual(len(backups), 2)


if __name__ == "__main__":
    unittest.main()

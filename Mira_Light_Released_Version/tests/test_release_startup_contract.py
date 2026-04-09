import subprocess
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import console_server


class ReleaseStartupContractTest(unittest.TestCase):
    def test_console_parser_accepts_bridge_base_url_and_legacy_alias(self) -> None:
        parser = console_server.build_parser()

        args = parser.parse_args(["--bridge-base-url", "http://127.0.0.1:9783"])
        self.assertEqual(args.bridge_base_url, "http://127.0.0.1:9783")

        args = parser.parse_args(["--base-url", "http://127.0.0.1:19783"])
        self.assertEqual(args.bridge_base_url, "http://127.0.0.1:19783")

    def test_release_shell_scripts_have_valid_bash_syntax(self) -> None:
        scripts = [
            ROOT / "scripts" / "start_director_console.sh",
            ROOT / "scripts" / "start_local_stack.sh",
            ROOT / "scripts" / "smoke_local_stack.sh",
            ROOT / "scripts" / "run_preflight_release.sh",
            ROOT / "scripts" / "diagnose_mira_light_network.sh",
            ROOT / "scripts" / "fix_mira_light_hotspot_route.sh",
            ROOT / "scripts" / "remove_openclaw_plugin.sh",
            ROOT / "scripts" / "start_simple_lamp_receiver.sh",
            ROOT / "tools" / "mira_light_bridge" / "start_bridge.sh",
        ]

        for script in scripts:
            result = subprocess.run(
                ["bash", "-n", str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"{script} failed syntax check: {result.stderr}")


if __name__ == "__main__":
    unittest.main()

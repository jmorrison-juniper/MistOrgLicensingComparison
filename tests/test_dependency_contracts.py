"""Contract tests for the dependency guards of issue #24.

The tests read the workflow and Dependabot files as text, because the offline
test job installs the runtime lock only, and that lock has no YAML parser.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DependencyContractTests(unittest.TestCase):
    """Keep the guards that stop a mando version that radon cannot use."""

    def test_offline_tests_resolve_the_development_lock(self) -> None:
        """The offline test job must resolve requirements-dev.lock.txt."""
        workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text()
        self.assertIn(
            "python -m pip install --dry-run -r requirements-dev.lock.txt", workflow
        )

    def test_dependabot_ignores_mando_0_8_for_pip(self) -> None:
        """The pip entry must ignore mando 0.8 and later while radon pins it."""
        config = (ROOT / ".github" / "dependabot.yml").read_text()
        pip_entry = config.split('- package-ecosystem: "pip"')[1].split(
            "- package-ecosystem:"
        )[0]
        self.assertRegex(
            pip_entry,
            re.compile(r'dependency-name: "mando"\s+versions: \[">=0\.8"\]'),
        )

    def test_development_lock_keeps_a_mando_that_radon_accepts(self) -> None:
        """radon 6.0.1 requires mando<0.8, so the lock must pin mando 0.7."""
        lock = (ROOT / "requirements-dev.lock.txt").read_text()
        self.assertIn("radon==6.0.1", lock)
        mando = re.search(r"^mando==(\d+)\.(\d+)", lock, re.MULTILINE)
        self.assertIsNotNone(mando)
        self.assertLess((int(mando.group(1)), int(mando.group(2))), (0, 8))


if __name__ == "__main__":
    unittest.main()

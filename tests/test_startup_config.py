import importlib.util
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_message_text():
    spec = importlib.util.spec_from_file_location("message_text", ROOT / "message_text.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StartupConfigTests(unittest.TestCase):
    def test_default_message_is_plain_text(self):
        module = load_message_text()
        self.assertIsInstance(module.message, str)
        self.assertTrue(module.message.strip())
        self.assertFalse(module.message.startswith("message="))

    def test_env_example_uses_linux_paths(self):
        text = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertNotIn("C:\\", text)
        self.assertIn("chrome_user_data", text)

    def test_launchers_are_executable_and_install_requirements(self):
        for name in ("launch_skoutz.sh", "run_skout_bot.sh"):
            with self.subTest(name=name):
                path = ROOT / name
                text = path.read_text(encoding="utf-8")
                self.assertTrue(os.access(path, os.X_OK), f"{name} must be executable")
                self.assertIn("requirements.txt", text)
                self.assertIn("python3 -m venv", text)

    def test_gui_launcher_clear_is_best_effort(self):
        text = (ROOT / "launch_skoutz.sh").read_text(encoding="utf-8")
        self.assertIn("clear 2>/dev/null || true", text)

    def test_desktop_entry_launches_project_script(self):
        text = (ROOT / "Link to Application.desktop").read_text(encoding="utf-8")
        self.assertIn("Name=SkoutZ", text)
        self.assertIn("Exec=/home/panda/Documents/PythonScripts/SKOUT/launch_skoutz.sh", text)
        self.assertIn("Path=/home/panda/Documents/PythonScripts/SKOUT", text)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from chrome_profile import quarantine_cache_dirs
from profile_progress import unseen_profile_labels, visible_profiles_are_exhausted


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
        self.assertIn("SKOUT_PROFILE_DIRECTORY=Profile1", text)

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
        self.assertIn("Exec=/home/panda/Documents/PythonScripts/SKOUT/run_skout_bot.sh", text)
        self.assertIn("Path=/home/panda/Documents/PythonScripts/SKOUT", text)
        self.assertIn("Terminal=true", text)

    def test_quarantine_cache_dirs_preserves_profile_data(self):
        with TemporaryDirectory() as temp_dir:
            profile = Path(temp_dir) / "chrome_user_data"
            cache = profile / "Default" / "Cache"
            cookies = profile / "Default" / "Cookies"
            cache.mkdir(parents=True)
            cookies.write_text("keep", encoding="utf-8")
            cache.joinpath("broken-entry").write_text("move", encoding="utf-8")

            backup = quarantine_cache_dirs(profile)

            self.assertIsNotNone(backup)
            self.assertFalse(cache.exists())
            self.assertTrue(cookies.exists())
            self.assertTrue((backup / "Default" / "Cache" / "broken-entry").exists())

    def test_bot_requires_manual_login_confirmation(self):
        text = (ROOT / "SKOUT_MESSAGE_BOT.py").read_text(encoding="utf-8")
        self.assertIn("Complete Google sign-in in Chrome", text)
        self.assertIn("Sign-in was not completed", text)
        self.assertNotIn('log("⚠️  Already logged in.")', text)

    def test_message_entry_does_not_overwrite_message_with_trigger_character(self):
        bot_text = (ROOT / "SKOUT_MESSAGE_BOT.py").read_text(encoding="utf-8")
        gui_text = (ROOT / "skoutz_gui.py").read_text(encoding="utf-8")
        helper_text = (ROOT / "message_draft.py").read_text(encoding="utf-8")

        self.assertNotIn('message_box.send_keys("H")', bot_text)
        self.assertNotIn('message_box.send_keys("H")', gui_text)
        self.assertIn("prepare_message_draft", bot_text)
        self.assertIn("prepare_message_draft", gui_text)
        self.assertIn("Input.insertText", helper_text)
        self.assertIn('return arguments[0].value;', helper_text)
        self.assertIn("Message text verification failed", helper_text)

    def test_profile_is_only_recorded_after_verified_manual_draft(self):
        bot_text = (ROOT / "SKOUT_MESSAGE_BOT.py").read_text(encoding="utf-8")
        gui_text = (ROOT / "skoutz_gui.py").read_text(encoding="utf-8")

        self.assertNotIn("send_button.click()", bot_text)
        self.assertNotIn("send_button.click()", gui_text)
        self.assertIn("Draft prepared for manual review", bot_text)
        self.assertIn("Draft prepared for manual review", gui_text)
        self.assertLess(
            bot_text.index("Draft prepared for manual review"),
            bot_text.index("messaged_profiles.add(profile_label)"),
        )
        self.assertLess(
            gui_text.index("Draft prepared for manual review"),
            gui_text.index("self.messaged_profiles.add(profile_label)"),
        )

    def test_visible_profiles_are_exhausted_when_all_labels_are_recorded(self):
        labels = ["Alice", "", None, "Bob", "Alice"]
        messaged = {"Alice", "Bob"}

        self.assertEqual([], unseen_profile_labels(labels, messaged))
        self.assertTrue(visible_profiles_are_exhausted(labels, messaged))
        self.assertFalse(visible_profiles_are_exhausted(["Alice", "Cara"], messaged))

    def test_bot_scrolls_when_visible_profiles_are_exhausted(self):
        bot_text = (ROOT / "SKOUT_MESSAGE_BOT.py").read_text(encoding="utf-8")
        gui_text = (ROOT / "skoutz_gui.py").read_text(encoding="utf-8")

        self.assertIn("visible_profiles_are_exhausted(profile_labels, messaged_profiles)", bot_text)
        self.assertIn("visible_profiles_are_exhausted(profile_labels, self.messaged_profiles)", gui_text)
        self.assertIn("All visible profiles are already recorded", bot_text)
        self.assertIn("All visible profiles are already recorded", gui_text)
        self.assertIn("scroll_discover_page", bot_text)
        self.assertIn("scroll_discover_page", gui_text)
        self.assertNotIn("window.scrollTo(0, document.body.scrollHeight);", bot_text)
        self.assertNotIn("window.scrollTo(0, document.body.scrollHeight);", gui_text)


if __name__ == "__main__":
    unittest.main()

import unittest

from selenium.common.exceptions import WebDriverException

from message_draft import MessageDraftError, prepare_message_draft


class FakeTextarea:
    def __init__(self):
        self.value = ""
        self.clicks = 0
        self.clears = 0
        self.sent_keys = []

    def click(self):
        self.clicks += 1

    def clear(self):
        self.clears += 1
        self.value = ""

    def send_keys(self, text):
        self.sent_keys.append(text)
        self.value += text


class FakeDriver:
    def __init__(self, fail_cdp=False, wipe_script_writes=False):
        self.fail_cdp = fail_cdp
        self.wipe_script_writes = wipe_script_writes
        self.cdp_calls = []
        self.scripts = []
        self.focused_element = None

    def execute_script(self, script, *args):
        self.scripts.append(script)
        if "return arguments[0].value" in script:
            return args[0].value
        if "scrollIntoView" in script or ".focus()" in script:
            self.focused_element = args[0]
            return None
        if "HTMLTextAreaElement.prototype" in script:
            element, value = args
            element.value = "" if self.wipe_script_writes else value
            return element.value
        return None

    def execute_cdp_cmd(self, command, params):
        self.cdp_calls.append((command, params))
        if self.fail_cdp:
            raise WebDriverException("CDP insert failed")
        self.focused_element.value = params["text"]


class MessageDraftTests(unittest.TestCase):
    def test_prepares_stable_draft_with_browser_insert_text(self):
        driver = FakeDriver()
        textarea = FakeTextarea()

        prepare_message_draft(driver, textarea, "Hello there", wait_after_write=lambda: None)

        self.assertEqual("Hello there", textarea.value)
        self.assertEqual([("Input.insertText", {"text": "Hello there"})], driver.cdp_calls)
        self.assertEqual([], textarea.sent_keys)

    def test_falls_back_to_real_keys_when_insert_and_script_are_wiped(self):
        driver = FakeDriver(fail_cdp=True, wipe_script_writes=True)
        textarea = FakeTextarea()

        prepare_message_draft(driver, textarea, "Hello again", wait_after_write=lambda: None)

        self.assertEqual("Hello again", textarea.value)
        self.assertEqual(["Hello again"], textarea.sent_keys)

    def test_raises_when_every_entry_method_is_cleared(self):
        driver = FakeDriver(fail_cdp=True, wipe_script_writes=True)
        textarea = FakeTextarea()

        def wipe_after_write():
            textarea.value = ""

        with self.assertRaisesRegex(MessageDraftError, "0/12 characters"):
            prepare_message_draft(
                driver,
                textarea,
                "Hello again!",
                wait_after_write=wipe_after_write,
                attempts=1,
            )


if __name__ == "__main__":
    unittest.main()

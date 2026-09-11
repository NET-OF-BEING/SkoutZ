import unittest

from page_scroll import SCROLL_DISCOVER_PAGE_SCRIPT, scroll_discover_page


class FakeDriver:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute_script(self, script, pixels):
        self.calls.append((script, pixels))
        return self.result


class PageScrollTests(unittest.TestCase):
    def test_scroll_discover_page_uses_scrollable_containers(self):
        driver = FakeDriver(
            {
                "scrolled": True,
                "target": "DIV.discover",
                "before": 0,
                "after": 700,
            }
        )
        waits = []

        result = scroll_discover_page(driver, wait_after_scroll=lambda: waits.append("wait"), pixels=700)

        self.assertEqual(driver.result, result)
        self.assertEqual(["wait"], waits)
        script, pixels = driver.calls[0]
        self.assertEqual(700, pixels)
        self.assertIn("querySelectorAll", script)
        self.assertIn("scrollableCandidates", script)
        self.assertIn("scrollTop", script)

    def test_scroll_script_does_not_depend_on_body_only_scroll(self):
        self.assertIn("document.scrollingElement", SCROLL_DISCOVER_PAGE_SCRIPT)
        self.assertIn("window.dispatchEvent", SCROLL_DISCOVER_PAGE_SCRIPT)
        self.assertNotIn(
            "window.scrollTo(0, document.body.scrollHeight)",
            SCROLL_DISCOVER_PAGE_SCRIPT,
        )


if __name__ == "__main__":
    unittest.main()

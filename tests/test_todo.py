"""Browser tests for the actual app. Run from any working directory."""

import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import unittest

from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class TodoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(root))
        )
        cls.server_thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.playwright = sync_playwright().start()
        options = {"headless": True}
        if os.environ.get("TODO_CHROMIUM_PATH"):
            options["executable_path"] = os.environ["TODO_CHROMIUM_PATH"]
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server_thread.join()
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(has_touch=True)
        self.page = self.context.new_page()
        self.page.goto(f"http://127.0.0.1:{self.server.server_port}")

    def tearDown(self):
        self.context.close()

    def add_task(self, title):
        self.page.locator("#task-input").fill(title)
        self.page.locator("#task-input").press("Enter")

    def test_add_by_button_and_enter(self):
        self.assertTrue(self.page.locator("#empty-message").is_visible())
        self.page.locator("#task-input").fill("  買い物  ")
        self.page.get_by_role("button", name="追加", exact=True).click()
        self.add_task("読書")
        self.assertEqual(self.page.locator(".task span").all_text_contents(), ["買い物", "読書"])
        self.assertEqual(self.page.locator("#task-summary").inner_text(), "未完了 2 件 / 全 2 件")
        self.assertFalse(self.page.locator("#empty-message").is_visible())
        self.assertEqual(self.page.locator("#task-input").input_value(), "")

    def test_completion_can_be_toggled(self):
        self.add_task("読書")
        checkbox = self.page.get_by_role("checkbox", name="読書")
        checkbox.check()
        self.assertEqual(self.page.locator(".task.completed").count(), 1)
        self.assertEqual(self.page.locator("#task-summary").inner_text(), "未完了 0 件 / 全 1 件")
        checkbox.uncheck()
        self.assertEqual(self.page.locator(".task.completed").count(), 0)
        self.assertEqual(self.page.locator("#task-summary").inner_text(), "未完了 1 件 / 全 1 件")

    def test_deletion_restores_empty_state_and_focus(self):
        self.add_task("買い物")
        self.add_task("読書")
        self.page.get_by_role("button", name="買い物を削除", exact=True).click()
        self.assertEqual(self.page.locator(".task span").all_text_contents(), ["読書"])
        self.page.get_by_role("button", name="読書を削除", exact=True).click()
        self.assertEqual(self.page.locator(".task").count(), 0)
        self.assertTrue(self.page.locator("#empty-message").is_visible())
        self.assertEqual(self.page.locator("#task-summary").inner_text(), "未完了 0 件 / 全 0 件")
        self.assertTrue(self.page.locator("#task-input").evaluate("el => el === document.activeElement"))

    def test_whitespace_is_rejected_and_html_is_plain_text(self):
        self.add_task("   ")
        self.assertEqual(self.page.locator(".task").count(), 0)
        self.assertTrue(self.page.locator("#input-error").is_visible())
        title = '<img src=x onerror="alert(1)">'
        self.add_task(title)
        self.assertEqual(self.page.locator(".task span").inner_text(), title)
        self.assertEqual(self.page.locator(".task img").count(), 0)
        self.assertFalse(self.page.locator("#input-error").is_visible())

    def test_long_titles_keep_mobile_delete_button_usable(self):
        for width in (320, 390, 480, 768):
            for title in ("長いタスク名" * 33, "a" * 200):
                with self.subTest(width=width, title=title[:12]):
                    self.page.set_viewport_size({"width": width, "height": 844})
                    self.add_task(title)
                    self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                    button = self.page.locator(".task button").bounding_box()
                    label = self.page.locator(".task label").bounding_box()
                    self.assertGreaterEqual(button["width"], 88 if width <= 480 else 80)
                    self.assertGreaterEqual(button["height"], 48)
                    self.assertAlmostEqual(button["y"], label["y"], delta=1)
                    self.assertGreaterEqual(button["x"], label["x"] + label["width"])
                    self.assertLessEqual(button["x"] + button["width"], width)
                    self.page.locator(".task button").tap()
                    self.assertEqual(self.page.locator(".task").count(), 0)


if __name__ == "__main__":
    unittest.main()

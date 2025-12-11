"""Base page class with common methods for all page objects."""

from playwright.sync_api import Page


class BasePage:
    """Base class for page objects with common functionality.

    Provides shared methods for navigation and waiting that all
    page objects can inherit.
    """

    BASE_URL = "http://127.0.0.1:8000"

    def __init__(self, page: Page):
        """Initialize the page object with a Playwright page instance.

        Args:
            page: Playwright Page object for browser interaction.
        """
        self.page = page

    def goto(self, path: str = ""):
        """Navigate to a page path relative to the base URL.

        Args:
            path: URL path to navigate to (e.g., "/prettyquote.html").
        """
        url = f"{self.BASE_URL}{path}"
        self.page.goto(url)

    def wait_for_load(self):
        """Wait for the page to finish loading.

        Waits for the network to be idle, indicating all resources
        have been fetched.
        """
        self.page.wait_for_load_state("networkidle")

    def wait_for_selector(self, selector: str, timeout: int = 5000):
        """Wait for an element to appear on the page.

        Args:
            selector: CSS selector for the element.
            timeout: Maximum time to wait in milliseconds.
        """
        self.page.locator(selector).wait_for(timeout=timeout)

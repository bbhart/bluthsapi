"""Page object for the index.html landing page."""

from playwright.sync_api import Page

from tests.pages.base_page import BasePage


class IndexPage(BasePage):
    """Page object for interacting with the index/landing page.

    Provides selectors and methods for testing the landing page
    display and analytics integration.
    """

    # Selectors
    PAGE_TITLE = "h1"
    ENDPOINT_BLOCKS = ".endpoint"
    ANALYTICS_SCRIPT = 'script[src*="gtag"]'

    def __init__(self, page: Page):
        """Initialize the IndexPage.

        Args:
            page: Playwright Page object for browser interaction.
        """
        super().__init__(page)

    def goto(self):
        """Navigate to the index page."""
        super().goto("/")
        self.wait_for_load()

    def get_title(self) -> str:
        """Get the page title (h1) text.

        Returns:
            The text content of the h1 element.
        """
        return self.page.locator(self.PAGE_TITLE).text_content() or ""

    def has_analytics(self) -> bool:
        """Check if Google Analytics script is present.

        Returns:
            True if the gtag script is found in the page, False otherwise.
        """
        # Check for the Google Analytics script tag
        analytics_script = self.page.locator(self.ANALYTICS_SCRIPT)
        return analytics_script.count() > 0

    def get_endpoint_count(self) -> int:
        """Get the number of endpoint documentation blocks.

        Returns:
            The count of .endpoint elements on the page.
        """
        return self.page.locator(self.ENDPOINT_BLOCKS).count()

    def get_endpoint_titles(self) -> list[str]:
        """Get the titles of all endpoint documentation blocks.

        Returns:
            List of endpoint titles (h3 text within .endpoint blocks).
        """
        endpoints = self.page.locator(f"{self.ENDPOINT_BLOCKS} h3")
        return endpoints.all_text_contents()

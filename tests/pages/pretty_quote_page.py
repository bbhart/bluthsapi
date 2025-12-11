"""Page object for the prettyquote.html page."""

from playwright.sync_api import Page, expect

from tests.pages.base_page import BasePage


class PrettyQuotePage(BasePage):
    """Page object for interacting with the prettyquote page.

    Provides selectors and methods for testing quote display,
    copy functionality, and reload behavior.
    """

    # Selectors
    QUOTE_TEXT = "#quote"
    COPY_BUTTON = "#copy-btn"
    RELOAD_BUTTON = "#reload-btn"
    QUOTE_IMAGE = "#quote-image"
    IMAGE_CONTAINER = "#image-container"
    TOAST = "#toast"

    def __init__(self, page: Page):
        """Initialize the PrettyQuotePage.

        Args:
            page: Playwright Page object for browser interaction.
        """
        super().__init__(page)

    def goto(self):
        """Navigate to the prettyquote page."""
        super().goto("/prettyquote.html")
        self.wait_for_load()

    def get_quote_text(self) -> str:
        """Get the current quote text.

        Returns:
            The text content of the quote element.
        """
        return self.page.locator(self.QUOTE_TEXT).text_content() or ""

    def is_image_visible(self) -> bool:
        """Check if the quote image is visible.

        Returns:
            True if the image is displayed, False otherwise.
        """
        # Check if image container is not hidden
        container = self.page.locator(self.IMAGE_CONTAINER)
        if container.get_attribute("class") and "hidden" in container.get_attribute("class"):
            return False
        return self.page.locator(self.QUOTE_IMAGE).is_visible()

    def click_copy_quote(self):
        """Click the Copy Quote button."""
        self.page.locator(self.COPY_BUTTON).click()

    def get_copy_button_text(self) -> str:
        """Get the current text of the copy button.

        Returns:
            The text content of the copy button.
        """
        return self.page.locator(self.COPY_BUTTON).text_content() or ""

    def click_image(self):
        """Click on the quote image to copy it."""
        self.page.locator(self.QUOTE_IMAGE).click()

    def get_toast_text(self) -> str:
        """Get the toast notification text.

        Returns:
            The text content of the toast element.
        """
        return self.page.locator(self.TOAST).text_content() or ""

    def is_toast_visible(self) -> bool:
        """Check if the toast notification is visible.

        Returns:
            True if the toast is displayed, False otherwise.
        """
        toast = self.page.locator(self.TOAST)
        toast_class = toast.get_attribute("class") or ""
        return "show" in toast_class

    def click_reload(self):
        """Click the Reload button and wait for new quote."""
        self.page.locator(self.RELOAD_BUTTON).click()
        # Wait for network request to complete
        self.page.wait_for_load_state("networkidle")

    def is_reload_button_loading(self) -> bool:
        """Check if the reload button is in loading state.

        Returns:
            True if the button has the loading class, False otherwise.
        """
        button = self.page.locator(self.RELOAD_BUTTON)
        button_class = button.get_attribute("class") or ""
        return "loading" in button_class

    def get_quote_font_size(self) -> str:
        """Get the computed font size of the quote text.

        Returns:
            The font-size CSS value (e.g., "24px").
        """
        return self.page.locator(self.QUOTE_TEXT).evaluate(
            "el => window.getComputedStyle(el).fontSize"
        )

    def is_quote_overflowing(self) -> bool:
        """Check if the quote text is overflowing its container.

        Returns:
            True if the content is overflowing, False otherwise.
        """
        return self.page.locator(self.QUOTE_TEXT).evaluate(
            "el => el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth"
        )

    def wait_for_quote_loaded(self, timeout: int = 5000):
        """Wait for a quote to be loaded (not in loading state).

        Args:
            timeout: Maximum time to wait in milliseconds.
        """
        # Wait for the quote element to not have the loading class
        self.page.locator(f"{self.QUOTE_TEXT}:not(.loading)").wait_for(timeout=timeout)

    def right_click_image(self):
        """Right-click on the quote image to open context menu."""
        self.page.locator(self.QUOTE_IMAGE).click(button="right")

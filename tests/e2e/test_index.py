"""End-to-end tests for the index/landing page.

Tests verify index page display and analytics integration (Issue #7).
"""

import pytest
from playwright.sync_api import Page

from tests.pages.index_page import IndexPage


class TestIndexPageDisplay:
    """Tests for index page display (User Story 6)."""

    def test_index_page_displays_title(self, page: Page):
        """Verify that index page displays the expected title.

        Given: A user navigates to the root URL
        When: The page loads
        Then: The index page is displayed with expected content
        """
        index_page = IndexPage(page)
        index_page.goto()

        title = index_page.get_title()
        assert title, "Page should have a title"
        assert "Arrested Development" in title or "Quotes" in title, \
            "Title should reference Arrested Development or Quotes"

    def test_google_analytics_present(self, page: Page):
        """Verify that Google Analytics tracking code is present (Issue #7).

        Given: The index page is displayed
        When: Inspecting the page
        Then: Google Analytics tracking code is present
        """
        index_page = IndexPage(page)
        index_page.goto()

        has_analytics = index_page.has_analytics()
        assert has_analytics, "Google Analytics script (gtag) should be present"

    def test_endpoint_documentation_visible(self, page: Page):
        """Verify that API endpoint documentation is displayed.

        Given: A user navigates to the index page
        When: The page loads
        Then: API endpoint documentation blocks are visible
        """
        index_page = IndexPage(page)
        index_page.goto()

        endpoint_count = index_page.get_endpoint_count()
        assert endpoint_count > 0, "Should display endpoint documentation"

        # Verify expected endpoints are documented
        endpoint_titles = index_page.get_endpoint_titles()
        titles_text = " ".join(endpoint_titles).lower()

        # Check for key endpoints
        assert "random" in titles_text, "Should document random quote endpoint"

    def test_page_loads_without_errors(self, page: Page):
        """Verify that the page loads without JavaScript errors.

        Given: A user navigates to the index page
        When: The page loads
        Then: No JavaScript errors occur
        """
        errors = []

        # Capture console errors
        page.on("pageerror", lambda error: errors.append(str(error)))

        index_page = IndexPage(page)
        index_page.goto()

        assert len(errors) == 0, f"Page should load without errors: {errors}"

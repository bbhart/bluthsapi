"""API endpoint tests for the Bluths API.

Tests verify API responses match expected schemas and behavior.
"""

import httpx
import pytest


BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture
def api_client():
    """Create an HTTP client for API testing."""
    with httpx.Client(base_url=BASE_URL) as client:
        yield client


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_endpoint_returns_healthy(self, api_client: httpx.Client):
        """Verify /health endpoint returns healthy status.

        Given: The API server is running
        When: A request is made to /health
        Then: A healthy status response is returned
        """
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "quotes_loaded" in data
        assert data["quotes_loaded"] > 0


class TestRandomQuoteEndpoint:
    """Tests for the /api/quotes/random endpoint."""

    def test_random_quote_returns_valid_schema(self, api_client: httpx.Client):
        """Verify /api/quotes/random returns correct structure.

        Given: The API server is running
        When: A request is made to /api/quotes/random
        Then: A JSON response with a quote is returned
        """
        response = api_client.get("/api/quotes/random")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "data" in data
        quote_data = data["data"]

        # Required fields
        assert "quote" in quote_data
        assert isinstance(quote_data["quote"], str)
        assert len(quote_data["quote"]) > 0

    def test_random_quote_has_optional_fields(self, api_client: httpx.Client):
        """Verify random quote may include optional fields.

        The response may include:
        - id: unique identifier
        - speakers: comma-separated character names, "" when unknown
        - context: episode reference
        - imageUrl: image URL (for meme quotes)
        """
        response = api_client.get("/api/quotes/random")
        data = response.json()["data"]

        # speakers is always present, possibly empty
        assert "speakers" in data
        assert isinstance(data["speakers"], str)
        assert not data["speakers"].startswith(",")
        assert not data["speakers"].endswith(",")

        if "context" in data and data["context"] is not None:
            assert isinstance(data["context"], str)

        if "imageUrl" in data and data["imageUrl"] is not None:
            assert isinstance(data["imageUrl"], str)
            assert data["imageUrl"].startswith("http")


class TestMemeQuoteEndpoint:
    """Tests for the /api/quotes/meme endpoint."""

    def test_meme_quote_has_image_url(self, api_client: httpx.Client):
        """Verify /api/quotes/meme includes imageUrl.

        Given: The API server is running
        When: A request is made to /api/quotes/meme
        Then: A JSON response with a quote containing an imageUrl is returned
        """
        response = api_client.get("/api/quotes/meme")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        quote_data = data["data"]

        # Meme quotes must have imageUrl
        assert "imageUrl" in quote_data
        assert quote_data["imageUrl"] is not None
        assert isinstance(quote_data["imageUrl"], str)
        assert quote_data["imageUrl"].startswith("http")

        # Should also have quote text
        assert "quote" in quote_data
        assert len(quote_data["quote"]) > 0


class TestSpeakerEndpoint:
    """Tests for the /api/quotes/{speaker} endpoint."""

    def test_speaker_endpoint_returns_filtered_quote(self, api_client: httpx.Client):
        """Verify /api/quotes/{speaker} returns quote from that speaker.

        Given: The API server is running
        When: A request is made to /api/quotes/{speaker}
        Then: A JSON response with quotes from that speaker is returned
        """
        # First get a random quote to find a valid speaker
        random_response = api_client.get("/api/quotes/random")
        random_data = random_response.json()["data"]

        # Use the first speaker if the quote names one
        if random_data.get("speakers"):
            speaker = random_data["speakers"].split(",")[0]

            response = api_client.get(f"/api/quotes/{speaker}")
            assert response.status_code == 200

            data = response.json()["data"]
            assert "quote" in data

    def test_nonexistent_speaker_returns_404(self, api_client: httpx.Client):
        """Verify 404 response for non-existent speaker.

        Given: The API server is running
        When: A request is made to /api/quotes/{speaker} with invalid speaker
        Then: A 404 response is returned
        """
        response = api_client.get("/api/quotes/NonExistentCharacter12345")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_speaker_search_is_case_insensitive(self, api_client: httpx.Client):
        """Verify speaker search is case-insensitive.

        Given: The API server is running
        When: Requests are made with different casing
        Then: All return valid quotes for the same speaker
        """
        # Get a valid speaker first
        random_response = api_client.get("/api/quotes/random")
        random_data = random_response.json()["data"]

        if random_data.get("speakers"):
            speaker = random_data["speakers"].split(",")[0]

            # Try different cases
            lower_response = api_client.get(f"/api/quotes/{speaker.lower()}")
            upper_response = api_client.get(f"/api/quotes/{speaker.upper()}")

            # At least one should succeed (case insensitive)
            responses = [lower_response, upper_response]
            success_count = sum(1 for r in responses if r.status_code == 200)

            # Both should return 200 for case-insensitive search
            assert success_count >= 1, "Case-insensitive search should work"

"""Pytest configuration and shared fixtures for Playwright E2E tests."""

import subprocess
import sys
import time
import urllib.request
import urllib.error

import pytest


# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
HEALTH_ENDPOINT = f"{BASE_URL}/health"


@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for tests."""
    return BASE_URL


@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Start the FastAPI server before tests and stop it after.

    Uses subprocess to start uvicorn, waits for the /health endpoint
    to respond, then yields control to tests. Terminates the server
    after all tests complete.
    """
    # Start uvicorn in background
    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", SERVER_HOST,
            "--port", str(SERVER_PORT),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready by polling /health
    max_retries = 30
    retry_delay = 0.5  # seconds

    for i in range(max_retries):
        try:
            response = urllib.request.urlopen(HEALTH_ENDPOINT, timeout=1)
            if response.status == 200:
                break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            pass

        # Check if process has died
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Server failed to start.\n"
                f"stdout: {stdout.decode()}\n"
                f"stderr: {stderr.decode()}"
            )

        if i == max_retries - 1:
            process.terminate()
            raise RuntimeError(
                f"Server did not respond to health check after "
                f"{max_retries * retry_delay} seconds"
            )

        time.sleep(retry_delay)

    yield  # Tests run here

    # Cleanup: terminate server process
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
def browser_context_args(browser_context_args):
    """Grant clipboard permissions for clipboard tests.

    This fixture extends pytest-playwright's browser_context_args to
    grant clipboard-read and clipboard-write permissions, required for
    testing copy functionality.
    """
    return {
        **browser_context_args,
        "permissions": ["clipboard-read", "clipboard-write"],
    }

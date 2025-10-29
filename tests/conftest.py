"""Pytest configuration and fixtures for E2E tests."""

import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def storage_dir():
    """Create a temporary directory for test storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def app_server(storage_dir):
    """Start the NiceGUI app server for E2E testing as a subprocess."""
    port = 8765  # Use a different port to avoid conflicts
    project_root = Path(__file__).parent.parent

    # Environment variables for test
    test_env = os.environ.copy()
    test_env["APP_ENV"] = "test"  # Use test environment (loads .env.test)
    test_env["APP_PORT"] = str(port)  # Use APP_PORT not PORT
    test_env["RELOAD"] = "false"  # Disable auto-reload in tests

    # Remove Playwright-related env vars to prevent NiceGUI from entering screen test mode
    test_env.pop("PYTEST_CURRENT_TEST", None)
    for key in list(test_env.keys()):
        if "PLAYWRIGHT" in key or "NICEGUI" in key:
            test_env.pop(key, None)

    # Start the app as a subprocess
    process = subprocess.Popen(
        ["python", "main.py"],
        cwd=str(project_root),
        env=test_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    max_retries = 30
    server_started = False
    for _i in range(max_retries):
        try:
            import urllib.request

            urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=1)
            server_started = True
            break
        except Exception as exc:
            if process.poll() is not None:
                # Process has terminated unexpectedly
                stdout, stderr = process.communicate()
                raise RuntimeError(
                    f"App process terminated unexpectedly.\nStdout: {stdout.decode()}\nStderr: {stderr.decode()}"
                ) from exc
            time.sleep(0.5)

    if not server_started:
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        raise RuntimeError(
            f"Failed to start app server after {max_retries * 0.5}s.\nStdout: {stdout.decode()}\nStderr: {stderr.decode()}"
        )

    yield f"http://127.0.0.1:{port}"

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
def page(app_server, page: Page):
    """Configure page for E2E tests with app server URL."""
    import urllib.request

    # Store base URL in page object for easy access
    page.base_url = app_server

    # Clear storage before each test
    page.context.clear_cookies()
    page.context.clear_permissions()

    # Clear NiceGUI storage via API endpoint
    try:
        req = urllib.request.Request(
            f"{app_server}/api/test/clear-storage",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=b"{}",
        )
        urllib.request.urlopen(req, timeout=5)
        # Storage cleared successfully
    except Exception:
        # If clearing fails on first test, that's ok (no storage yet)
        pass

    # Override goto to handle relative URLs
    original_goto = page.goto

    def goto_with_base(url, **kwargs):
        if url.startswith("/"):
            url = app_server + url
        return original_goto(url, **kwargs)

    page.goto = goto_with_base
    return page


@pytest.fixture
def sample_credentials():
    """Sample Google Sheets credentials for testing."""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\\ntest-key\\n-----END PRIVATE KEY-----\\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    }


@pytest.fixture
def sample_sheet_url():
    """Sample Google Sheets URL for testing."""
    return "https://docs.google.com/spreadsheets/d/test-sheet-id/edit"

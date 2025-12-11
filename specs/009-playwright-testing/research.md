# Research: Playwright E2E Testing Framework

## Decision Summary

### 1. Test Framework Setup

**Decision:** Python pytest-playwright with synchronous API
**Rationale:** Matches existing Python codebase (FastAPI), simpler than TypeScript for this project size
**Alternatives considered:**
- TypeScript Playwright: More ecosystem tooling but adds complexity
- Selenium: Slower, more verbose, Playwright has better async/clipboard support

### 2. Directory Structure

**Decision:** Tests in `tests/` folder with `pages/`, `e2e/`, and `api/` subdirectories
**Rationale:** Clear separation of concerns, pytest auto-discovery, matches Python conventions
**Alternatives considered:**
- Single flat tests folder: Less organized as tests grow
- TypeScript `tests/` with separate config: Adds build step complexity

### 3. Server Lifecycle Management

**Decision:** Pytest fixture in `conftest.py` starts uvicorn subprocess, waits for `/health`, terminates after tests
**Rationale:** Works with Python pytest-playwright (webServer config is JS-only), provides automatic startup/shutdown
**Alternatives considered:**
- Manual server startup: Requires two terminals, error-prone
- Threading approach: More complex, harder to debug

### 4. Page Object Model Pattern

**Decision:** Simple Python classes with selectors as class constants and action methods
**Rationale:** Reduces duplication, makes tests readable, easy to maintain for small project
**Alternatives considered:**
- No page objects: Selectors scattered across tests, harder to update
- Complex inheritance hierarchies: Over-engineered for project size

### 5. Test Data Strategy

**Decision:** Hybrid - E2E tests use actual API data verifying structure; API tests use live endpoints
**Rationale:** Aligns with clarification session; real data ensures integration works; structure assertions prevent brittleness
**Alternatives considered:**
- Full mocking: Misses integration bugs
- Exact content matching: Breaks when quote data changes

### 6. Clipboard Testing

**Decision:** Grant clipboard-read/write permissions via browser context args, verify via `page.evaluate()`
**Rationale:** Most reliable approach for Chromium; allows full content verification
**Alternatives considered:**
- UI feedback only: Doesn't verify actual clipboard operation
- Event interception: More complex, less realistic

### 7. Browser Target

**Decision:** Chromium primary, clipboard tests skip Firefox/WebKit
**Rationale:** Clipboard API support varies; Chromium has best support. Matches spec assumption.
**Alternatives considered:**
- All browsers: Flaky clipboard tests on non-Chromium
- Headed mode only: Limits CI usage

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=7.0 | Test framework |
| pytest-playwright | >=0.4 | Playwright pytest integration |
| playwright | >=1.40 | Browser automation |
| httpx | >=0.25 | API test client |

## Technical Constraints

1. **Python focus**: No TypeScript/JavaScript test files (constitution requires Python)
2. **Local only**: CI/CD integration deferred per clarification
3. **Chromium-first**: Clipboard tests may skip other browsers
4. **5-minute timeout**: Full suite must complete within spec requirement

## Key Patterns

### Server Startup Fixture
```python
@pytest.fixture(scope="session", autouse=True)
def start_server():
    process = subprocess.Popen(["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])
    # Wait for health check
    yield
    process.terminate()
```

### Clipboard Permission Grant
```python
@pytest.fixture
def browser_context_args():
    return {"permissions": ["clipboard-read", "clipboard-write"]}
```

### Page Object Structure
```python
class PrettyQuotePage:
    QUOTE_TEXT = "#quote"
    COPY_BUTTON = "#copy-btn"

    def __init__(self, page):
        self.page = page
```

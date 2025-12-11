# Quickstart: Running Playwright Tests

## Prerequisites

- Python 3.11+
- Project cloned and dependencies installed

## Installation

```bash
# Install test dependencies
pip install pytest pytest-playwright httpx

# Install Playwright browsers (Chromium by default)
playwright install chromium
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### Specific Test File
```bash
pytest tests/e2e/test_prettyquote.py
```

### Tests Matching Pattern
```bash
pytest -k "clipboard"
pytest -k "api"
```

### Headed Mode (See Browser)
```bash
pytest tests/ --headed
```

### Verbose Output
```bash
pytest tests/ -v
```

## Test Structure

```
tests/
├── conftest.py           # Server startup + fixtures
├── pages/
│   ├── base_page.py      # Common page methods
│   ├── pretty_quote_page.py
│   └── index_page.py
├── e2e/
│   ├── test_prettyquote.py   # Quote display, copy, reload
│   └── test_index.py         # Landing page, analytics
└── api/
    └── test_endpoints.py     # API response validation
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `pytest tests/` | Run all tests |
| `pytest tests/ -v` | Verbose output |
| `pytest tests/ --headed` | Show browser |
| `pytest tests/ -k "copy"` | Run matching tests |
| `pytest tests/ --tb=short` | Short tracebacks |

## Troubleshooting

### Server Won't Start
- Check port 8000 is available
- Verify `uvicorn` is installed
- Check `app/main.py` exists

### Clipboard Tests Fail
- Only supported on Chromium
- Must run in secure context (localhost)
- Check browser permissions granted

### Timeout Issues
- Increase timeout in individual tests
- Check network/server responsiveness

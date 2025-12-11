# Implementation Plan: Playwright E2E Testing Framework

**Feature Branch:** `009-playwright-testing`
**Created:** 2025-12-10
**Status:** Ready for Implementation

## Technical Context

| Aspect | Value |
|--------|-------|
| Language | Python 3.11+ |
| Test Framework | pytest + pytest-playwright |
| Browser | Chromium (primary) |
| Server | FastAPI with uvicorn |
| Base URL | http://localhost:8000 |

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Read-Only Access | N/A | Testing framework, not API changes |
| Public Access | N/A | Testing framework, not API changes |
| Code Quality | PASS | Tests will use pytest conventions |
| Cross-Platform | PASS | Python/Playwright works on MacOS/Windows |
| No Symlinks | PASS | No symlinks planned |
| Speckit Workflow | PASS | No auto-commits, manual review required |

## Implementation Phases

### Phase 1: Project Setup
**Goal:** Install dependencies and configure pytest-playwright

**Tasks:**
1. Create `requirements-dev.txt` with test dependencies
2. Install Playwright browsers
3. Create `tests/` directory structure
4. Create `pytest.ini` or `pyproject.toml` test config

**Files to create:**
- `requirements-dev.txt`
- `tests/__init__.py`
- `tests/conftest.py`
- `pytest.ini`

### Phase 2: Server Fixture
**Goal:** Automatic server startup/shutdown for tests

**Tasks:**
1. Create session-scoped fixture to start uvicorn
2. Wait for `/health` endpoint before yielding
3. Terminate server after all tests complete
4. Add `base_url` fixture

**Files to modify:**
- `tests/conftest.py`

### Phase 3: Page Objects
**Goal:** Create reusable page abstractions

**Tasks:**
1. Create `BasePage` class with common methods
2. Create `PrettyQuotePage` with selectors and actions
3. Create `IndexPage` with selectors and actions
4. Export page objects from `pages/__init__.py`

**Files to create:**
- `tests/pages/__init__.py`
- `tests/pages/base_page.py`
- `tests/pages/pretty_quote_page.py`
- `tests/pages/index_page.py`

### Phase 4: API Tests
**Goal:** Verify API endpoints return correct responses

**Tasks:**
1. Create API test file
2. Test `/health` endpoint
3. Test `/api/quotes/random` response schema
4. Test `/api/quotes/meme` response has imageUrl
5. Test `/api/quotes/{speaker}` returns filtered quotes
6. Test 404 for non-existent speaker

**Files to create:**
- `tests/api/__init__.py`
- `tests/api/test_endpoints.py`

**Coverage:** FR-008, User Story 4

### Phase 5: Quote Display Tests
**Goal:** Verify prettyquote page displays quotes correctly

**Tasks:**
1. Create e2e test file for prettyquote
2. Test quote container displays text
3. Test long quote font size adjustment (Issue #15)
4. Test image displays when present
5. Test image hidden when no imageUrl

**Files to create:**
- `tests/e2e/__init__.py`
- `tests/e2e/test_prettyquote.py`

**Coverage:** FR-003, FR-004, User Story 2

### Phase 6: Copy Functionality Tests
**Goal:** Verify clipboard operations work correctly

**Tasks:**
1. Add clipboard permission fixture
2. Test Copy Quote button copies text
3. Test button shows "Copied!" feedback
4. Test image click copies to clipboard (Issue #16)
5. Test success toast appears
6. Test right-click context menu available (Issue #16)

**Files to modify:**
- `tests/conftest.py` (clipboard permissions)
- `tests/e2e/test_prettyquote.py`

**Coverage:** FR-005, FR-006, FR-007, User Story 3

### Phase 7: Reload Functionality Tests
**Goal:** Verify reload button fetches new quotes

**Tasks:**
1. Test reload button changes quote
2. Test loading state during request

**Files to modify:**
- `tests/e2e/test_prettyquote.py`

**Coverage:** FR-009, User Story 5

### Phase 8: Index Page Tests
**Goal:** Verify landing page displays correctly

**Tasks:**
1. Create e2e test file for index
2. Test page loads with title
3. Test Google Analytics present (Issue #7)
4. Test endpoint documentation visible

**Files to create:**
- `tests/e2e/test_index.py`

**Coverage:** User Story 6

### Phase 9: Error Handling Tests
**Goal:** Verify graceful error handling

**Tasks:**
1. Test error message when API fails (mock/intercept)
2. Test clipboard error fallback

**Files to modify:**
- `tests/e2e/test_prettyquote.py`

**Coverage:** FR-010, Edge Cases

### Phase 10: Final Verification
**Goal:** Ensure all tests pass and suite completes quickly

**Tasks:**
1. Run full test suite
2. Verify execution under 5 minutes (SC-001)
3. Verify all success criteria met
4. Generate test report

## File Structure (Final)

```
tests/
├── __init__.py
├── conftest.py                 # Server fixture, clipboard permissions
├── pytest.ini                  # Test configuration
├── pages/
│   ├── __init__.py
│   ├── base_page.py           # BasePage class
│   ├── pretty_quote_page.py   # PrettyQuotePage class
│   └── index_page.py          # IndexPage class
├── e2e/
│   ├── __init__.py
│   ├── test_prettyquote.py    # Quote display, copy, reload tests
│   └── test_index.py          # Index page tests
└── api/
    ├── __init__.py
    └── test_endpoints.py      # API response tests
```

## Dependencies

Add to `requirements-dev.txt`:
```
pytest>=7.0
pytest-playwright>=0.4.0
httpx>=0.25.0
```

## Success Criteria Mapping

| Criteria | Implementation |
|----------|----------------|
| SC-001 (5 min) | Phase 10 verification |
| SC-002 (Issue coverage) | Phases 5-6 for #15, #16; Phase 8 for #7 |
| SC-003 (100% pass) | Phase 10 verification |
| SC-004 (Single command) | `pytest tests/` |
| SC-005 (Clear errors) | pytest default output |
| SC-006 (Headed/headless) | `--headed` flag support |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Clipboard flaky on CI | Skip clipboard tests on non-Chromium |
| Server startup race | Health check polling in fixture |
| Test isolation | Each test gets fresh page context |
| Port conflicts | Use consistent port 8000, check availability |

## Next Steps

1. Run `/speckit.tasks` to generate detailed task list
2. Implement phases sequentially
3. Run tests after each phase to verify
4. Manual review and commit after completion

# Tasks: Playwright E2E Testing Framework

**Feature Branch:** `009-playwright-testing`
**Generated:** 2025-12-10
**Total Tasks:** 34

## User Story Summary

| Story | Priority | Tasks | Description |
|-------|----------|-------|-------------|
| US1 | P1 | 4 | Developer Runs Automated Tests |
| US2 | P1 | 4 | Verify Quote Display Functionality |
| US3 | P1 | 5 | Verify Copy Functionality |
| US4 | P2 | 4 | Verify API Endpoints |
| US5 | P2 | 2 | Verify Reload Functionality |
| US6 | P3 | 3 | Verify Index Page |

---

## Phase 1: Setup

**Goal:** Initialize project with test dependencies and directory structure

- [x] T001 Create `requirements-dev.txt` with pytest, pytest-playwright, httpx dependencies
- [x] T002 Create `pytest.ini` with test configuration (testpaths, python_files patterns)
- [x] T003 Create `tests/__init__.py` to make tests a package
- [x] T004 Create `tests/pages/__init__.py` for page objects package
- [x] T005 Create `tests/e2e/__init__.py` for e2e tests package
- [x] T006 Create `tests/api/__init__.py` for api tests package

**Verification:** `pip install -r requirements-dev.txt && playwright install chromium` completes without error

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal:** Create shared fixtures and page object base class required by all tests

- [x] T007 Create server startup fixture in `tests/conftest.py` using subprocess to start uvicorn
- [x] T008 Add health check polling in `tests/conftest.py` to wait for server ready
- [x] T009 Add `base_url` fixture returning "http://localhost:8000" in `tests/conftest.py`
- [x] T010 Create `BasePage` class with `__init__(page)`, `goto(path)`, `wait_for_load()` methods in `tests/pages/base_page.py`

**Verification:** `pytest --collect-only` shows fixtures registered, no import errors

---

## Phase 3: User Story 1 - Developer Runs Automated Tests (P1)

**Goal:** Enable running tests with single command that produces pass/fail report

**Independent Test:** Run `pytest tests/` and verify summary report appears

- [x] T011 [US1] Create `PrettyQuotePage` class with selectors (#quote, #copy-btn, #reload-btn, #quote-image, #image-container, #toast) in `tests/pages/pretty_quote_page.py`
- [x] T012 [US1] Add `goto()`, `get_quote_text()`, `is_image_visible()` methods to `PrettyQuotePage` in `tests/pages/pretty_quote_page.py`
- [x] T013 [US1] Create `IndexPage` class with selectors (h1, .endpoint, script[src*="gtag"]) in `tests/pages/index_page.py`
- [x] T014 [US1] Add `goto()`, `get_title()`, `has_analytics()` methods to `IndexPage` in `tests/pages/index_page.py`

**Verification:** Import page objects in Python REPL without errors; `pytest tests/ --collect-only` shows 0 errors

---

## Phase 4: User Story 2 - Verify Quote Display Functionality (P1)

**Goal:** Tests verify prettyquote page displays quotes correctly (Issue #15 coverage)

**Independent Test:** Run `pytest tests/e2e/test_prettyquote.py -k "display"` and verify all pass

- [x] T015 [US2] Create `tests/e2e/test_prettyquote.py` with test class setup using PrettyQuotePage
- [x] T016 [US2] Add `test_quote_container_displays_text()` verifying #quote has non-empty text in `tests/e2e/test_prettyquote.py`
- [x] T017 [US2] Add `test_long_quote_font_size_adjusts()` verifying no overflow on long quotes (Issue #15) in `tests/e2e/test_prettyquote.py`
- [x] T018 [US2] Add `test_image_displays_when_present()` verifying #quote-image visible when imageUrl exists in `tests/e2e/test_prettyquote.py`

**Verification:** `pytest tests/e2e/test_prettyquote.py -k "display or image"` passes

---

## Phase 5: User Story 3 - Verify Copy Functionality (P1)

**Goal:** Tests verify clipboard operations work correctly (Issue #16 coverage)

**Independent Test:** Run `pytest tests/e2e/test_prettyquote.py -k "copy"` and verify all pass

- [x] T019 [US3] Add clipboard permissions fixture (`browser_context_args`) in `tests/conftest.py`
- [x] T020 [US3] Add `click_copy_quote()`, `click_image()`, `get_toast_text()` methods to `PrettyQuotePage` in `tests/pages/pretty_quote_page.py`
- [x] T021 [US3] Add `test_copy_quote_button_copies_text()` verifying clipboard content matches quote in `tests/e2e/test_prettyquote.py`
- [x] T022 [US3] Add `test_copy_quote_shows_feedback()` verifying button text changes to "Copied!" in `tests/e2e/test_prettyquote.py`
- [x] T023 [US3] Add `test_image_click_copies_to_clipboard()` verifying toast appears (Issue #16) in `tests/e2e/test_prettyquote.py`

**Verification:** `pytest tests/e2e/test_prettyquote.py -k "copy"` passes on Chromium

---

## Phase 6: User Story 4 - Verify API Endpoints (P2)

**Goal:** Tests verify API returns correct response schemas

**Independent Test:** Run `pytest tests/api/test_endpoints.py` and verify all pass

- [x] T024 [P] [US4] Create `tests/api/test_endpoints.py` with httpx client setup
- [x] T025 [P] [US4] Add `test_health_endpoint_returns_healthy()` verifying /health response in `tests/api/test_endpoints.py`
- [x] T026 [P] [US4] Add `test_random_quote_returns_valid_schema()` verifying /api/quotes/random has required fields in `tests/api/test_endpoints.py`
- [x] T027 [P] [US4] Add `test_meme_quote_has_image_url()` verifying /api/quotes/meme includes imageUrl in `tests/api/test_endpoints.py`

**Verification:** `pytest tests/api/` passes

---

## Phase 7: User Story 5 - Verify Reload Functionality (P2)

**Goal:** Tests verify reload button fetches new quotes

**Independent Test:** Run `pytest tests/e2e/test_prettyquote.py -k "reload"` and verify all pass

- [x] T028 [US5] Add `click_reload()` method to `PrettyQuotePage` in `tests/pages/pretty_quote_page.py`
- [x] T029 [US5] Add `test_reload_button_changes_quote()` verifying quote text differs after reload in `tests/e2e/test_prettyquote.py`

**Verification:** `pytest tests/e2e/test_prettyquote.py -k "reload"` passes

---

## Phase 8: User Story 6 - Verify Index Page (P3)

**Goal:** Tests verify index page displays correctly (Issue #7 coverage)

**Independent Test:** Run `pytest tests/e2e/test_index.py` and verify all pass

- [x] T030 [P] [US6] Create `tests/e2e/test_index.py` with test class setup using IndexPage
- [x] T031 [P] [US6] Add `test_index_page_displays_title()` verifying h1 contains expected text in `tests/e2e/test_index.py`
- [x] T032 [P] [US6] Add `test_google_analytics_present()` verifying gtag script exists (Issue #7) in `tests/e2e/test_index.py`

**Verification:** `pytest tests/e2e/test_index.py` passes

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal:** Handle edge cases and ensure full test coverage

- [x] T033 Add `test_error_state_displays_message()` verifying error handling when API fails in `tests/e2e/test_prettyquote.py`
- [x] T034 Run full test suite with `pytest tests/ -v` and verify all tests pass within 5 minutes (SC-001)

**Verification:** `pytest tests/ -v` shows 100% pass rate

---

## Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
    ├── Phase 3 (US1: Test Framework) ──┐
    │                                    │
    ├── Phase 4 (US2: Quote Display) ───┼── Can run in parallel after Phase 3
    │                                    │
    ├── Phase 5 (US3: Copy) ────────────┤
    │                                    │
    ├── Phase 6 (US4: API) ─────────────┤
    │                                    │
    ├── Phase 7 (US5: Reload) ──────────┤
    │                                    │
    └── Phase 8 (US6: Index) ───────────┘
                   ↓
            Phase 9 (Polish)
```

## Parallel Execution Opportunities

**Within Phase 6 (API Tests):** T024-T027 can all be implemented in parallel (different test functions, no shared state)

**Within Phase 8 (Index Tests):** T030-T032 can all be implemented in parallel (different test functions)

**Across Phases 4-8:** After Phase 3 completes, user stories US2-US6 can be implemented in any order or parallel

## Implementation Strategy

### MVP Scope (Recommended First Iteration)
Complete Phases 1-4 only (US1 + US2):
- Test framework running ✓
- Quote display verified ✓
- Foundation for remaining stories ✓

### Incremental Delivery
1. **Iteration 1:** Phases 1-4 (Setup + US1 + US2) - Core framework
2. **Iteration 2:** Phase 5 (US3) - Copy functionality (Issue #16)
3. **Iteration 3:** Phases 6-7 (US4 + US5) - API + Reload
4. **Iteration 4:** Phases 8-9 (US6 + Polish) - Index page + edge cases

## File Structure (Final)

```
tests/
├── __init__.py                 # T003
├── conftest.py                 # T007, T008, T009, T019
├── pages/
│   ├── __init__.py             # T004
│   ├── base_page.py            # T010
│   ├── pretty_quote_page.py    # T011, T012, T020, T028
│   └── index_page.py           # T013, T014
├── e2e/
│   ├── __init__.py             # T005
│   ├── test_prettyquote.py     # T015-T018, T021-T023, T029, T033
│   └── test_index.py           # T030-T032
└── api/
    ├── __init__.py             # T006
    └── test_endpoints.py       # T024-T027

requirements-dev.txt            # T001
pytest.ini                      # T002
```

## Success Criteria Checklist

| Criteria | Task(s) | Status |
|----------|---------|--------|
| SC-001: < 5 min execution | T034 | ✅ Complete (13.39s) |
| SC-002: Issue coverage | T017 (#15), T023 (#16), T032 (#7) | ✅ Complete |
| SC-003: 100% pass | T034 | ✅ Complete (22/22) |
| SC-004: Single command | T002 (pytest.ini) | ✅ Complete |
| SC-005: Clear errors | pytest default | ✅ Complete |
| SC-006: Headed/headless | pytest-playwright default | ✅ Complete |

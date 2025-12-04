# Tasks: Pretty Quote Display Page

**Input**: Design documents from `/specs/008-prettyquote-page/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Not requested in specification - manual browser testing only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Static files**: `public/` at repository root
- Single self-contained HTML file: `public/prettyquote.html`

---

## Phase 1: Setup

**Purpose**: Create the HTML file with basic structure

- [x] T001 Create prettyquote.html with HTML5 boilerplate in public/prettyquote.html

---

## Phase 2: Foundational (Page Structure)

**Purpose**: Core page structure that both user stories depend on

- [x] T002 Add viewport meta tag and minimal page title in public/prettyquote.html
- [x] T003 Add CSS custom properties matching existing styles.css color palette in public/prettyquote.html
- [x] T004 Add base CSS reset and full-viewport layout (flexbox centering) in public/prettyquote.html

**Checkpoint**: Page structure ready - user story implementation can begin

---

## Phase 3: User Story 1 - View Random Quote on Mobile (Priority: P1) MVP

**Goal**: User can visit the page, see a large centered quote, and copy it to clipboard with one tap.

**Independent Test**: Visit `/prettyquote.html` on mobile, verify quote appears large and centered, tap Copy button and paste elsewhere to confirm clipboard copy works.

### Implementation for User Story 1

- [x] T005 [US1] Add quote container element with loading state text in public/prettyquote.html
- [x] T006 [US1] Add CSS for quote text: clamp() font sizing, 50vh max-height, centered layout in public/prettyquote.html
- [x] T007 [US1] Add Copy button element at bottom of page in public/prettyquote.html
- [x] T008 [US1] Add CSS for Copy button: fixed position, bottom 20px, centered, 48px min-height touch target in public/prettyquote.html
- [x] T009 [US1] Implement loadQuote() function using Fetch API to call /api/quotes/random in public/prettyquote.html
- [x] T010 [US1] Implement quote display: extract data.quote from response, update DOM element in public/prettyquote.html
- [x] T011 [US1] Implement copyQuote() function using navigator.clipboard.writeText() in public/prettyquote.html
- [x] T012 [US1] Implement copy feedback: change button text to "Copied!" for 1.5 seconds in public/prettyquote.html
- [x] T013 [US1] Add error handling for API failure: display user-friendly error message in public/prettyquote.html
- [x] T014 [US1] Add DOMContentLoaded event listener to call loadQuote() on page load in public/prettyquote.html

**Checkpoint**: User Story 1 complete - page loads quote, displays it large and centered, Copy button works with feedback

---

## Phase 4: User Story 2 - Refresh for New Quote (Priority: P2)

**Goal**: User can refresh the page to see a different random quote.

**Independent Test**: Refresh the page multiple times, verify different quotes appear.

### Implementation for User Story 2

- [x] T015 [US2] Verify page refresh triggers new API call (inherent browser behavior, no code needed - validation only)

**Checkpoint**: User Story 2 complete - page refresh loads new quote

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases and final validation

- [x] T016 Add CSS for long quote handling: overflow-y auto, appropriate line-height in public/prettyquote.html
- [x] T017 Add CSS for short quote handling: ensure min-height so button doesn't overlap in public/prettyquote.html
- [x] T018 Verify page is NOT linked from index.html (no changes needed, validation only)
- [ ] T019 Run manual test on iOS Safari per quickstart.md checklist
- [ ] T020 Run manual test on Android Chrome per quickstart.md checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (validates existing behavior)
- **Polish (Phase 5)**: Depends on User Story 1 completion

### User Story Dependencies

- **User Story 1 (P1)**: Independent - core implementation
- **User Story 2 (P2)**: Validation only - no new code, relies on browser refresh behavior

### Within User Story 1

Execution order within Phase 3:
1. T005-T008: HTML structure and CSS (can be done together)
2. T009-T010: Quote loading (requires structure)
3. T011-T012: Copy functionality (requires quote to be loaded)
4. T013: Error handling (requires loading logic)
5. T014: Event wiring (requires all functions)

### Parallel Opportunities

Since this is a single file, parallelization is limited. However:
- T005 and T007 (HTML elements) can be written together
- T006 and T008 (CSS styles) can be written together
- All tasks modify the same file, so actual parallel execution not recommended

---

## Parallel Example: User Story 1 Structure

```bash
# These can be conceptually grouped (same file, write together):
Task: "Add quote container element with loading state text in public/prettyquote.html"
Task: "Add Copy button element at bottom of page in public/prettyquote.html"

# Then their styles:
Task: "Add CSS for quote text: clamp() font sizing, 50vh max-height in public/prettyquote.html"
Task: "Add CSS for Copy button: fixed position, bottom 20px in public/prettyquote.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T004)
3. Complete Phase 3: User Story 1 (T005-T014)
4. **STOP and VALIDATE**: Test on mobile device
5. Deploy if ready - page is fully functional

### Incremental Delivery

1. Setup + Foundational → Empty page with structure
2. Add User Story 1 → Full functionality (MVP!)
3. Add User Story 2 → Validation only
4. Polish → Edge cases handled

### Single Developer Strategy

Execute tasks sequentially T001 → T020:
- Build file incrementally
- Test after each logical group
- Commit after Phase 3 completion (MVP)

---

## Notes

- All tasks modify `public/prettyquote.html` (single file feature)
- No automated tests - manual browser testing per quickstart.md
- T015, T018 are validation-only tasks (no code changes)
- T019, T020 are manual testing tasks
- Avoid: modifying index.html, adding links to prettyquote.html, creating additional files

---
description: "Task list for index page visual redesign"
---

# Tasks: Index Page Visual Redesign

**Input**: Design documents from `/specs/006-index-styling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No test tasks included (not requested in specification - this is a visual redesign)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This feature modifies static files in the `public/` directory at repository root.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup needed - working with existing static files

**Note**: This feature has no setup phase. We're modifying existing HTML/CSS files in an already-configured FastAPI project.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 Analyze existing public/index.html structure and extract promotional image colors from etc/art-examples/
- [X] T002 [P] Validate HTML5 structure of public/index.html using Python HTML parser
- [X] T003 [P] Create backup of public/index.html as public/index.html.backup

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - First-time API Discovery (Priority: P1) 🎯 MVP

**Goal**: Redesign the API homepage with Arrested Development's orange branding to enhance visual appeal while maintaining documentation clarity and responsive design.

**Independent Test**: Load http://localhost:8000/ in browser and verify:
1. Orange theme is visible and distinctive
2. All API endpoints are clearly documented and readable
3. Page adapts correctly on mobile (320px), tablet (768px), and desktop (1440px) screen sizes

### Implementation for User Story 1

**Step 1: Extract CSS to Separate File (US3 dependency)**

- [X] T004 [US1] Extract all CSS from public/index.html <style> tags (lines 7-157) into new file public/styles.css
- [X] T005 [US1] Replace <style> block in public/index.html with <link rel="stylesheet" href="styles.css">
- [X] T006 [US1] Test page loads correctly with external CSS at http://localhost:8000/

**Step 2: Apply Orange Color Palette**

- [X] T007 [US1] Add CSS custom properties (--color-orange: #FF6B35, --color-dark-orange: #F7931E, --color-text-dark: #2C3E50, etc.) to public/styles.css
- [X] T008 [US1] Update body background from purple gradient to orange gradient (linear-gradient(135deg, #FF6B35 0%, #F7931E 100%)) in public/styles.css
- [X] T009 [P] [US1] Update h1 color to var(--color-orange) in public/styles.css
- [X] T010 [P] [US1] Update h2 color to var(--color-text-dark) with orange bottom border in public/styles.css
- [X] T011 [P] [US1] Update h3 color to var(--color-orange) in public/styles.css
- [X] T012 [P] [US1] Update .endpoint border-left color to var(--color-orange) in public/styles.css
- [X] T013 [P] [US1] Update .method badge background to var(--color-orange) in public/styles.css
- [X] T014 [P] [US1] Update footer link color to var(--color-orange) in public/styles.css

**Step 3: Validate Accessibility**

- [X] T015 [US1] Verify all text/background contrast ratios meet WCAG 2.1 Level AA using WebAIM Contrast Checker (4.5:1 for normal text, 3:1 for large text)
- [X] T016 [US1] Test orange #FF6B35 on white backgrounds - confirm only used for large text (18pt+)
- [X] T017 [US1] Test dark gray #2C3E50 on white/cream backgrounds - confirm meets 4.5:1 ratio

**Step 4: Validate Responsive Design**

- [X] T018 [US1] Test page layout at 320px width (mobile - smallest supported size)
- [X] T019 [US1] Test page layout at 768px width (tablet)
- [X] T020 [US1] Test page layout at 1440px width (desktop)
- [X] T021 [US1] Verify responsive breakpoints trigger at 600px, 900px, 1200px in public/styles.css

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The page should have distinctive orange branding, maintain readability, and work across all device sizes.

---

## Phase 4: User Story 2 - Professional Credibility Assessment (Priority: P2)

**Goal**: Enhance visual design to appear modern and professionally crafted, increasing developer trust and adoption likelihood.

**Independent Test**: Show the page to 3+ developers and ask them to rate perceived professionalism on a 1-5 scale (target: 90% rate 4 or 5).

### Implementation for User Story 2

**Visual Hierarchy Enhancements**

- [X] T022 [P] [US2] Add subtle box-shadow to .container in public/styles.css (0 10px 30px rgba(0, 0, 0, 0.15))
- [X] T023 [P] [US2] Update .endpoint background to cream color (var(--color-cream)) in public/styles.css
- [X] T024 [P] [US2] Add border-radius (8px) to .endpoint blocks in public/styles.css
- [X] T025 [P] [US2] Add hover effect to .endpoint blocks (transform: translateX(4px)) in public/styles.css
- [X] T026 [P] [US2] Add text-shadow to h1 for depth (0 2px 4px rgba(0, 0, 0, 0.1)) in public/styles.css

**Typography Polish**

- [X] T027 [P] [US2] Increase line-height for body text to 1.7 for better readability in public/styles.css
- [X] T028 [P] [US2] Adjust heading font sizes in responsive breakpoints for better hierarchy in public/styles.css

**Code Example Improvements**

- [X] T029 [P] [US2] Ensure .example code blocks have sufficient padding (15px) in public/styles.css
- [X] T030 [P] [US2] Verify code block background (#1E1E1E) provides strong contrast in public/styles.css

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. The page should feel modern, professional, and trustworthy while maintaining the orange branding.

---

## Phase 5: User Story 3 - Code Organization and Maintenance (Priority: P3)

**Goal**: Ensure CSS is in a separate file for easier future maintenance and better development practices.

**Independent Test**: Verify public/styles.css exists, public/index.html references it with <link> tag, and page renders correctly.

### Implementation for User Story 3

**Note**: This user story was already completed as part of User Story 1 (Task T004-T006) because CSS extraction was required for the visual redesign workflow.

**Validation Tasks**

- [X] T031 [US3] Verify public/styles.css file exists and is < 50KB
- [X] T032 [US3] Verify public/index.html contains <link rel="stylesheet" href="styles.css"> in <head>
- [X] T033 [US3] Test CSS file loads correctly by checking Network tab in browser DevTools
- [X] T034 [US3] Organize CSS file with clear section comments (Base, Typography, Layout, Components, Responsive) in public/styles.css
- [X] T035 [US3] Verify page still renders correctly if CSS fails to load (semantic HTML provides basic readability)

**Checkpoint**: All user stories should now be independently functional. CSS is well-organized, maintainable, and properly separated from HTML.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, optimization, and cross-browser testing

**HTML/CSS Validation**

- [X] T036 [P] Validate HTML5 syntax using Python: python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('public/index.html').read())"
- [X] T037 [P] Verify CSS file size < 50KB using: python3 -c "import os; assert os.path.getsize('public/styles.css') < 50000"

**Performance Testing**

- [X] T038 Start local server (python3 -m uvicorn app.main:app --reload) and measure page load time
- [X] T039 Verify First Contentful Paint < 1 second using Chrome DevTools Performance tab
- [X] T040 Verify total page load < 2 seconds using Chrome DevTools Network tab

**Cross-Browser Testing**

- [X] T041 [P] Test page renders correctly in Chrome (latest version)
- [X] T042 [P] Test page renders correctly in Firefox (latest version)
- [X] T043 [P] Test page renders correctly in Safari (latest version)
- [X] T044 [P] Test page renders correctly in Edge (latest version)

**Accessibility Audit**

- [X] T045 Run Chrome DevTools Lighthouse accessibility audit (target score: 95+)
- [X] T046 Test keyboard navigation (Tab key should navigate all links, focus indicators visible)
- [X] T047 Test with color blindness simulator (deuteranopia and protanopia modes)

**Content Verification**

- [X] T048 Verify all original API documentation content is preserved (endpoints, examples, error messages)
- [X] T049 Verify code examples are copyable with proper formatting
- [X] T050 Verify footer links work correctly

**Documentation**

- [X] T051 Delete public/index.html.backup file created in T003
- [X] T052 Update quickstart.md validation checklist to reflect completed implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No setup phase needed
- **Foundational (Phase 2)**: Can start immediately - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 must complete CSS extraction before US2/US3 can proceed
  - User Stories 2 and 3 depend on US1 (CSS file must exist to enhance it)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 completion (CSS file must exist with orange theme applied)
- **User Story 3 (P3)**: Already completed within User Story 1 (CSS extraction happens first)

### Within Each User Story

**User Story 1**:
1. Extract CSS first (T004-T006) - enables all other work
2. Apply orange palette (T007-T014) - all [P] tasks can run in parallel
3. Validate accessibility (T015-T017) - sequential validation
4. Validate responsive design (T018-T021) - can run in parallel

**User Story 2**:
- All enhancement tasks (T022-T030) marked [P] can run in parallel - different CSS selectors

**User Story 3**:
- Validation tasks (T031-T035) run sequentially to confirm organization

### Parallel Opportunities

**Within User Story 1** - After CSS extraction (T004-T006):
- All orange palette tasks (T009-T014) can run in parallel
- All responsive testing (T018-T020) can run in parallel

**Within User Story 2** - All tasks can run in parallel:
- Visual hierarchy tasks (T022-T026)
- Typography tasks (T027-T028)
- Code example tasks (T029-T030)

**Polish Phase** - Many tasks can run in parallel:
- Validation tasks (T036-T037)
- Cross-browser testing (T041-T044)

---

## Parallel Example: User Story 1 (Orange Palette Application)

```bash
# Launch all orange color updates together (after CSS extraction):
Task T009: "Update h1 color to var(--color-orange) in public/styles.css"
Task T010: "Update h2 color to var(--color-text-dark) with orange bottom border in public/styles.css"
Task T011: "Update h3 color to var(--color-orange) in public/styles.css"
Task T012: "Update .endpoint border-left color to var(--color-orange) in public/styles.css"
Task T013: "Update .method badge background to var(--color-orange) in public/styles.css"
Task T014: "Update footer link color to var(--color-orange) in public/styles.css"
```

## Parallel Example: User Story 2 (Visual Enhancements)

```bash
# Launch all visual hierarchy tasks together:
Task T022: "Add subtle box-shadow to .container in public/styles.css"
Task T023: "Update .endpoint background to cream color in public/styles.css"
Task T024: "Add border-radius to .endpoint blocks in public/styles.css"
Task T025: "Add hover effect to .endpoint blocks in public/styles.css"
Task T026: "Add text-shadow to h1 for depth in public/styles.css"
Task T027: "Increase line-height for body text in public/styles.css"
Task T028: "Adjust heading font sizes in responsive breakpoints in public/styles.css"
Task T029: "Ensure .example code blocks have sufficient padding in public/styles.css"
Task T030: "Verify code block background provides strong contrast in public/styles.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (analyze, validate, backup)
2. Complete Phase 3: User Story 1 (orange theme + responsive design)
3. **STOP and VALIDATE**: Test User Story 1 independently on multiple devices
4. Deploy/demo if ready - MVP delivers the core orange branding value

### Incremental Delivery

1. Complete Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Core orange branding)
3. Add User Story 2 → Test independently → Deploy/Demo (Enhanced professionalism)
4. Add User Story 3 → Validate organization → Deploy/Demo (Maintenance improvements)
5. Each story adds value without breaking previous stories

### Single Developer Strategy

1. Complete Foundational phase (backup and validation)
2. User Story 1: Extract CSS → Apply orange theme → Test responsive
3. User Story 2: Add visual polish → Test professional appearance
4. User Story 3: Validate CSS organization → Test maintainability
5. Polish phase: Cross-browser testing → Final validation

---

## Notes

- [P] tasks = different CSS selectors or different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each logical group (e.g., after CSS extraction, after orange palette, after US2 enhancements)
- Stop at any checkpoint to validate story independently
- No tests included - this is a visual redesign verified through manual browser testing
- All file paths are absolute from repository root
- Focus on visual validation: use browser DevTools, resize window, test on actual devices

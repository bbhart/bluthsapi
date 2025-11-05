---
description: "Task list for Google Analytics 4 integration"
---

# Tasks: Google Analytics 4 Integration

**Input**: Design documents from `/specs/007-google-analytics/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: This feature uses manual verification testing as specified in the feature requirements. No automated test tasks are included.

**Organization**: Tasks are grouped by user story, though all three stories are satisfied by a single HTML modification plus verification steps.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses a single-project structure:
- Static HTML files: `public/`
- Python backend: `app/`
- No test directory modifications needed (manual verification)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify prerequisites and prepare development environment

- [X] T001 Verify Google Analytics property exists and measurement ID G-PEMHDLKW9H is active
- [X] T002 Verify local development server runs successfully (python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000)
- [X] T003 Verify public/index.html exists and is served correctly at http://localhost:8000

**Checkpoint**: Development environment ready for implementation

---

## Phase 2: Foundational (No Blocking Prerequisites)

**Purpose**: This feature has no foundational blocking tasks - it's a pure frontend addition

**⚠️ Note**: No foundational phase needed. User stories can begin immediately after setup.

---

## Phase 3: User Story 1 - Track Page Views (Priority: P1) 🎯 MVP

**Goal**: Automatically collect page view data when visitors browse the site to understand traffic volume and popular content

**Independent Test**: Visit the site pages and verify page view events appear in Google Analytics dashboard within 24-48 hours OR verify in browser DevTools Network tab that GA4 requests are sent successfully

### Implementation for User Story 1

- [X] T004 [US1] Add Google Analytics 4 gtag.js snippet to public/index.html in <head> section after <meta> tags
- [X] T005 [US1] Verify measurement ID G-PEMHDLKW9H is correctly configured in gtag config call
- [X] T006 [US1] Test locally: Start dev server and verify page loads without errors
- [ ] T007 [US1] Test locally: Open Browser DevTools Network tab and verify gtag.js loads from googletagmanager.com [MANUAL TEST REQUIRED]
- [ ] T008 [US1] Test locally: Verify google-analytics.com/g/collect requests are sent on page load [MANUAL TEST REQUIRED]
- [ ] T009 [US1] Test graceful degradation: Enable ad blocker (uBlock Origin) and verify site still functions normally [MANUAL TEST REQUIRED]
- [ ] T010 [US1] Test graceful degradation: Verify no console errors when analytics is blocked [MANUAL TEST REQUIRED]

**Checkpoint**: Page view tracking is functional. When you visit the site, GA4 captures the page URL, title, and basic session data. User Story 1 (P1) is complete and testable.

---

## Phase 4: User Story 2 - Track User Demographics (Priority: P2)

**Goal**: Collect information about who visitors are (geographic location, device type, browser) to better understand the audience

**Independent Test**: Access the site from different devices/browsers/locations and verify Google Analytics reports show correct device types, browsers, and geographic data

### Implementation for User Story 2

**⚠️ Note**: User Story 2 is automatically satisfied by the GA4 snippet added in User Story 1. GA4 collects demographic data (location, device, browser) by default with no additional code required.

- [X] T011 [US2] Verify in quickstart.md that GA4 automatically collects device type, browser, screen resolution, and geographic location
- [ ] T012 [US2] Test from different devices: Load site on desktop, mobile, and tablet (or use browser DevTools device emulation) [MANUAL TEST REQUIRED]
- [ ] T013 [US2] Verify in Google Analytics dashboard: Navigate to Reports → Realtime and confirm device type is captured [MANUAL TEST REQUIRED]
- [ ] T014 [US2] Verify in Google Analytics dashboard: Navigate to Reports → User attributes → Demographics and confirm location/device data appears (may take 24-48 hours for full reports) [MANUAL TEST REQUIRED]

**Checkpoint**: Demographic tracking is functional. GA4 automatically captures visitor device types, browsers, screen resolutions, and geographic locations. User Story 2 (P2) is complete and testable.

---

## Phase 5: User Story 3 - Track Referral Sources (Priority: P3)

**Goal**: Know how visitors found the site (direct visit, search engine, social media, external link) to understand which marketing channels are most effective

**Independent Test**: Access the site through different referral methods (direct URL, search results, social media links) and verify the referral source appears correctly in Google Analytics acquisition reports

### Implementation for User Story 3

**⚠️ Note**: User Story 3 is automatically satisfied by the GA4 snippet added in User Story 1. GA4 captures referral information (traffic source, medium, referring domain) by default with no additional code required.

- [X] T015 [US3] Verify in quickstart.md that GA4 automatically collects referral information (traffic source, medium, referring domain)
- [ ] T016 [US3] Test direct traffic: Visit site by typing URL directly in browser address bar [MANUAL TEST REQUIRED]
- [ ] T017 [US3] Test referral traffic: Create a test link from another site (e.g., personal blog, social media post) and click through [MANUAL TEST REQUIRED]
- [ ] T018 [US3] Test search traffic: If site is indexed, search for it and click the search result link [MANUAL TEST REQUIRED]
- [ ] T019 [US3] Verify in Google Analytics dashboard: Navigate to Reports → Acquisition → Traffic acquisition and confirm referral sources are captured (may take 24-48 hours for full reports) [MANUAL TEST REQUIRED]

**Checkpoint**: Referral tracking is functional. GA4 automatically captures how visitors arrive at the site (direct, search, social media, external links). User Story 3 (P3) is complete and testable. All user stories are now independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, deployment, and documentation

- [ ] T020 Measure performance impact: Compare page load times before/after GA4 integration (should be < 100ms increase per success criteria SC-003)
- [ ] T021 Run quickstart.md validation: Follow all verification steps in quickstart.md to confirm implementation is correct
- [ ] T022 Create git commit with changes to public/index.html following project commit message format
- [ ] T023 Deploy to production: Push branch and deploy via GitHub Actions OR deploy manually via SAM CLI
- [ ] T024 Verify production deployment: Visit production site and check DevTools Network tab for GA4 requests
- [ ] T025 Monitor Google Analytics dashboard: Wait 24-48 hours and verify all three metrics (page views, demographics, referral sources) appear correctly in GA dashboard
- [ ] T026 Document any privacy policy updates needed (site owner responsibility, not implementation task)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Not applicable - no blocking prerequisites
- **User Story 1 (Phase 3)**: Depends on Setup completion - Core implementation
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion - Verification only (code already in place)
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion - Verification only (code already in place)
- **Polish (Phase 6)**: Depends on all user stories being complete and verified

### User Story Dependencies

**Special Note for This Feature**: All three user stories are satisfied by the single GA4 snippet added in Phase 3 (User Story 1). User Stories 2 and 3 are verification-only phases.

- **User Story 1 (P1)**: Core implementation - Adds GA4 tracking code
  - No dependencies on other stories
  - BLOCKS User Stories 2 and 3 (they verify this implementation)
- **User Story 2 (P2)**: Verification phase - Tests demographic tracking
  - Depends on User Story 1 (needs GA4 code in place)
  - Can run in parallel with User Story 3 verification
- **User Story 3 (P3)**: Verification phase - Tests referral tracking
  - Depends on User Story 1 (needs GA4 code in place)
  - Can run in parallel with User Story 2 verification

### Within Each User Story

- **User Story 1**: Sequential implementation (add code → test locally → test gracefully)
- **User Stories 2 & 3**: Verification tasks can be done in any order once US1 is complete

### Parallel Opportunities

Due to the simple nature of this feature (single HTML file modification), parallel opportunities are limited:

- **Within Setup (Phase 1)**: Tasks T001-T003 can run in parallel if desired (all verification tasks)
- **After User Story 1 Complete**: User Stories 2 and 3 (verification phases) can run in parallel
- **Within Polish (Phase 6)**: Tasks T020 (performance), T021 (validation), and T026 (documentation) can run in parallel before deployment

---

## Parallel Example: Verification After User Story 1

```bash
# Once User Story 1 is complete, launch verification for both US2 and US3 together:

# User Story 2 verification:
Task: "Verify in quickstart.md that GA4 automatically collects device type, browser, screen resolution, and geographic location"
Task: "Test from different devices: Load site on desktop, mobile, and tablet"

# User Story 3 verification (in parallel):
Task: "Verify in quickstart.md that GA4 automatically collects referral information"
Task: "Test direct traffic: Visit site by typing URL directly in browser"
Task: "Test referral traffic: Create test link and click through"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 3: User Story 1 (T004-T010)
3. **STOP and VALIDATE**: Test page view tracking independently
4. Deploy if ready - you now have basic analytics!

**At this point**: You can track page views, the core requirement. This is a fully functional MVP.

### Incremental Delivery

1. Complete Setup → Environment ready
2. Add User Story 1 → Test page view tracking → Deploy (MVP! 🎯)
3. Add User Story 2 verification → Confirm demographic data is being collected → Deploy
4. Add User Story 3 verification → Confirm referral tracking works → Deploy
5. Complete Polish → Final validation and production monitoring

### Sequential Strategy (Recommended for Solo Developer)

Since all user stories share the same implementation (single GA4 snippet):

1. Complete Setup (Phase 1)
2. Complete User Story 1 implementation (Phase 3: T004-T010)
3. Immediately verify User Stories 2 & 3 work (Phases 4-5: T011-T019)
4. Complete Polish and deploy (Phase 6: T020-T026)

**Total Implementation Time**: ~30 minutes for all phases

---

## Notes

- This is a simple, low-risk feature: one HTML file, ~10 lines of code
- All three user stories are satisfied by a single code change (adding GA4 snippet)
- User Stories 2 and 3 are verification-only phases (no additional code needed)
- The GA4 snippet automatically handles page views, demographics, and referrals
- Testing is manual (browser DevTools + Google Analytics dashboard)
- No backend changes, no new dependencies, no deployment config changes
- Performance impact is minimal (< 100ms per success criteria)
- Site continues to work normally if analytics is blocked (graceful degradation)

---

## Success Criteria Validation

After completing all tasks, verify these criteria from spec.md are met:

- [ ] **SC-001**: Analytics data appears in Google Analytics dashboard within 48 hours of implementation
- [ ] **SC-002**: 95% or more of page views are successfully tracked (accounting for ad blockers and privacy tools)
- [ ] **SC-003**: Site performance remains unchanged with page load times not increasing by more than 100ms
- [ ] **SC-004**: All three core metrics (traffic volume, user demographics, referral sources) are visible in the analytics dashboard with accurate data
- [ ] **SC-005**: Site continues to function normally for visitors who block analytics scripts

# Tasks: Smart Tweet Staging Filter

**Input**: Design documents from `/specs/003-tweet-filtering/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification, so they are not included in this task list. Test tasks can be added if needed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `etc/scripts/` for utility scripts, `tests/` at repository root
- Paths follow the structure from plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create etc/scripts directory if it doesn't exist
- [X] T002 Create empty filter_tweets.py script in etc/scripts/filter_tweets.py
- [X] T003 [P] Add shebang and module docstring to etc/scripts/filter_tweets.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement CLI argument parsing (argparse) in etc/scripts/filter_tweets.py
- [X] T005 [P] Implement JSON file loading and validation in etc/scripts/filter_tweets.py
- [X] T006 [P] Implement text normalization function (lowercase, remove punctuation, collapse whitespace) in etc/scripts/filter_tweets.py
- [X] T007 [P] Implement FilterResult data structure in etc/scripts/filter_tweets.py
- [X] T008 Implement error handling and exit codes (0-5) with stderr output in etc/scripts/filter_tweets.py
- [X] T009 [P] Implement main() entry point and script structure in etc/scripts/filter_tweets.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Filter Low-Quality Tweets (Priority: P1) 🎯 MVP

**Goal**: Automatically filter out low-quality tweets based on engagement metrics, retweets, hashtags, and substantive content

**Independent Test**: Run filter on staging file with known low-quality tweets and verify they are removed based on defined criteria

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement is_retweet filter function in etc/scripts/filter_tweets.py
- [X] T011 [P] [US1] Implement hashtag detection filter function (check for "#" in text) in etc/scripts/filter_tweets.py
- [X] T012 [P] [US1] Implement engagement threshold filter function (favorite_count and retweet_count) in etc/scripts/filter_tweets.py
- [X] T013 [P] [US1] Implement substantive content filter function (only hashtags/@mentions/URLs detection) in etc/scripts/filter_tweets.py
- [X] T014 [US1] Integrate all US1 filters into main filtering pipeline in etc/scripts/filter_tweets.py
- [X] T015 [US1] Handle missing metadata fields (default to 0 for numeric, empty string for text) in etc/scripts/filter_tweets.py
- [X] T016 [US1] Update FilterResult to track removal counts by category for US1 filters in etc/scripts/filter_tweets.py

**Checkpoint**: At this point, User Story 1 should be fully functional - basic filtering works and removes retweets, hashtags, low-engagement, and empty content tweets

---

## Phase 4: User Story 2 - Preserve High-Value Content (Priority: P2)

**Goal**: Ensure tweets meeting quality thresholds are retained even if they have borderline characteristics

**Independent Test**: Run filter on staging data with high-engagement tweets that have borderline characteristics and verify they are retained

### Implementation for User Story 2

- [X] T017 [US2] Implement media attachment bonus logic (check for non-empty media_urls array) in etc/scripts/filter_tweets.py
- [X] T018 [US2] Implement composite scoring function (consider both favorite_count and retweet_count) in etc/scripts/filter_tweets.py
- [X] T019 [US2] Integrate composite scoring into engagement filter to allow strong metric compensation in etc/scripts/filter_tweets.py
- [X] T020 [US2] Update media attachment handling to give preferential treatment in borderline cases in etc/scripts/filter_tweets.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - filtering is more intelligent and preserves high-value content

---

## Phase 5: User Story 3 - Remove Near-Duplicate Tweets (Priority: P3)

**Goal**: Detect and remove tweets that are materially similar to previously retained tweets using text similarity algorithm

**Independent Test**: Run filter on staging file with known near-duplicate tweets and verify similar tweets are removed while keeping first occurrence

### Implementation for User Story 3

- [X] T021 [P] [US3] Implement text similarity function using difflib.SequenceMatcher in etc/scripts/filter_tweets.py
- [X] T022 [P] [US3] Implement SimilarityComparison data structure for example output in etc/scripts/filter_tweets.py
- [X] T023 [US3] Implement deduplication filter (compare each tweet to previously retained tweets) in etc/scripts/filter_tweets.py
- [X] T024 [US3] Add similarity threshold configuration parameter (default 0.85) in etc/scripts/filter_tweets.py
- [X] T025 [US3] Collect up to 5 similarity comparison examples during deduplication in etc/scripts/filter_tweets.py
- [X] T026 [US3] Integrate deduplication filter into main pipeline (run after all other filters) in etc/scripts/filter_tweets.py
- [X] T027 [US3] Update FilterResult to track near-duplicate removal count in etc/scripts/filter_tweets.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work - filtering includes deduplication with similarity detection

---

## Phase 6: User Story 4 - Generate Filter Report (Priority: P4)

**Goal**: Generate summary report showing what was removed and why, with similarity examples for validation

**Independent Test**: Run filter and verify report shows counts of removed tweets by reason category and includes five similarity examples

### Implementation for User Story 4

- [X] T028 [P] [US4] Implement report generation function (summary section with counts and percentages) in etc/scripts/filter_tweets.py
- [X] T029 [P] [US4] Implement similarity examples formatting function (display 5 examples with scores) in etc/scripts/filter_tweets.py
- [X] T030 [P] [US4] Implement configuration summary section for report in etc/scripts/filter_tweets.py
- [X] T031 [US4] Integrate report generation into main script (output to stdout or file) in etc/scripts/filter_tweets.py
- [X] T032 [US4] Add --report command-line option to save report to file in etc/scripts/filter_tweets.py
- [X] T033 [US4] Output five similarity examples to stdout regardless of report destination in etc/scripts/filter_tweets.py

**Checkpoint**: All user stories should now be independently functional - complete filtering with detailed reporting

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Add output file generation with updated metadata (filtered_at, filter_version, tweets_retained) in etc/scripts/filter_tweets.py
- [X] T035 [P] Implement --output command-line option (overwrite input if not specified) in etc/scripts/filter_tweets.py
- [X] T036 [P] Add --help and --version command-line options in etc/scripts/filter_tweets.py
- [X] T037 [P] Add processing time tracking and reporting in etc/scripts/filter_tweets.py
- [ ] T038 [P] Add logging for major filtering stages in etc/scripts/filter_tweets.py
- [X] T039 Add comprehensive error messages for all exit codes (1-5) in etc/scripts/filter_tweets.py
- [X] T040 [P] Validate output JSON structure matches input schema in etc/scripts/filter_tweets.py
- [X] T041 [P] Add input validation for configuration parameters (threshold 0.0-1.0, counts >= 0) in etc/scripts/filter_tweets.py
- [X] T042 Make script executable (chmod +x etc/scripts/filter_tweets.py)
- [ ] T043 Test script with sample data from etc/staging/tweets_staging.json
- [ ] T044 [P] Create test_filter_tweets.py with basic unit tests in tests/test_filter_tweets.py (if desired)
- [ ] T045 Run quickstart.md validation - verify all examples work as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 engagement filter but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Adds deduplication independently
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Reporting can be built independently of filtering logic

**Note**: While US2 extends US1's filtering, and US3 depends on filtering being complete, each story can be implemented and tested independently. The filter pipeline applies filters in order, so each story adds its functionality to the pipeline.

### Within Each User Story

- Tasks marked [P] can run in parallel within the same story
- Core filter functions before integration into pipeline
- Data structure updates after core functionality
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, parallelizable tasks within each user story can run together
- All Polish tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all filter functions for User Story 1 together:
Task: "Implement is_retweet filter function in etc/scripts/filter_tweets.py"
Task: "Implement hashtag detection filter function in etc/scripts/filter_tweets.py"
Task: "Implement engagement threshold filter function in etc/scripts/filter_tweets.py"
Task: "Implement substantive content filter function in etc/scripts/filter_tweets.py"

# Then sequentially:
Task: "Integrate all US1 filters into main filtering pipeline"
Task: "Handle missing metadata fields"
Task: "Update FilterResult to track removal counts"
```

---

## Parallel Example: User Story 3

```bash
# Launch similarity components for User Story 3 together:
Task: "Implement text similarity function using difflib.SequenceMatcher"
Task: "Implement SimilarityComparison data structure"

# Then sequentially:
Task: "Implement deduplication filter"
Task: "Add similarity threshold configuration parameter"
Task: "Collect up to 5 similarity comparison examples"
Task: "Integrate deduplication filter into main pipeline"
Task: "Update FilterResult to track near-duplicate removal count"
```

---

## Parallel Example: User Story 4

```bash
# Launch all report components for User Story 4 together:
Task: "Implement report generation function (summary section)"
Task: "Implement similarity examples formatting function"
Task: "Implement configuration summary section for report"

# Then sequentially:
Task: "Integrate report generation into main script"
Task: "Add --report command-line option"
Task: "Output five similarity examples to stdout"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003) - ~10 minutes
2. Complete Phase 2: Foundational (T004-T009) - ~1-2 hours
3. Complete Phase 3: User Story 1 (T010-T016) - ~2-3 hours
4. **STOP and VALIDATE**: Test User Story 1 independently with real staging data
5. At this point you have: Basic tweet filtering that removes retweets, hashtags, low-engagement, and empty content tweets

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~2 hours)
2. Add User Story 1 → Test independently (~2-3 hours) → **Working filter!** (MVP)
3. Add User Story 2 → Test independently (~1 hour) → Enhanced filtering with composite scoring
4. Add User Story 3 → Test independently (~2-3 hours) → Deduplication added
5. Add User Story 4 → Test independently (~1-2 hours) → Full reporting
6. Polish phase → Production-ready (~2-3 hours)

**Total estimated time**: ~10-15 hours for complete implementation

### Parallel Team Strategy

With multiple developers (not typical for a single-script utility, but possible):

1. Team completes Setup + Foundational together (~2 hours)
2. Once Foundational is done:
   - Developer A: User Story 1 (core filtering)
   - Developer B: User Story 3 (deduplication - can work independently)
   - Developer C: User Story 4 (reporting - can work independently)
3. Developer A then adds User Story 2 (extends their US1 work)
4. Stories integrate via the filter pipeline structure

**More realistic for this feature**: Single developer working sequentially through user stories in priority order.

---

## Notes

- [P] tasks = different functions/sections in the same file, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group (e.g., after completing each user story)
- Stop at any checkpoint to validate story independently
- All functionality is in a single script file (etc/scripts/filter_tweets.py) - simplifies implementation
- Uses Python stdlib only (difflib, string, json, pathlib, argparse, datetime) - no external dependencies
- Script should be executable and runnable from command line
- Configuration via CLI arguments (no config file in MVP, can add later)
- Processing pipeline order: retweets → hashtags → engagement → substantive content → deduplication

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 6 tasks
- **Phase 3 (User Story 1)**: 7 tasks
- **Phase 4 (User Story 2)**: 4 tasks
- **Phase 5 (User Story 3)**: 7 tasks
- **Phase 6 (User Story 4)**: 6 tasks
- **Phase 7 (Polish)**: 12 tasks

**Total**: 45 tasks

**Parallelizable tasks**: 24 tasks marked [P]
**Sequential tasks**: 21 tasks

**MVP scope** (User Story 1 only): 16 tasks (Setup + Foundational + US1)

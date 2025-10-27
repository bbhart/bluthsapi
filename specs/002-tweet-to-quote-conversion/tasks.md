# Tasks: Tweet to Quote Conversion System

**Input**: Design documents from `/specs/002-tweet-to-quote-conversion/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so this task list focuses on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `scripts/`, `etc/`, `app/data/`, `media/` at repository root
- Paths follow structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create scripts/ directory for conversion utilities
- [X] T002 Create etc/staging/ directory for intermediate staging files (add to .gitignore)
- [X] T003 Create media/tweet_images/ directory for downloaded images (add to .gitignore)
- [X] T004 Verify app/data/ directory exists for quotes.json output

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared utilities needed by multiple user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create shared utility module scripts/tweet_parser.py with functions for parsing tweets.js JavaScript wrapper and extracting JSON
- [X] T006 [P] Create shared utility module scripts/speaker_detector.py with regex pattern matching for "Name:" prefix detection (alphabetical characters and spaces only)
- [X] T007 [P] Create shared utility module scripts/quote_id_generator.py with logic to scan existing quotes.json, find highest ID, and generate next sequential ID with collision handling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Quotes from Tweet Archive (Priority: P1) 🎯 MVP

**Goal**: Extract tweets from Twitter archive to human-reviewable staging file

**Independent Test**: Run `python3 scripts/extract_tweets.py` on sample tweets.js file and verify staging file is created with all required fields, retweets are flagged, and speaker names are detected

### Implementation for User Story 1

- [X] T008 [US1] Implement main extraction logic in scripts/extract_tweets.py with CLI argument parsing (--source, --output, --verbose, --help flags)
- [X] T009 [US1] Add tweet parsing logic to read etc/tweets.js, strip JavaScript wrapper using tweet_parser utility, parse JSON array
- [X] T010 [US1] Add tweet filtering logic to exclude tweets with empty full_text, tweets with only URLs, and preserve tweets with meaningful content
- [X] T011 [US1] Add retweet detection logic to identify tweets starting with "RT @" and set is_retweet flag to true
- [X] T012 [US1] Add speaker detection logic using speaker_detector utility to identify "Name:" prefix pattern and store detected speaker in staging metadata
- [X] T013 [US1] Add media URL extraction logic to collect all media_url_https from entities.media and extended_entities.media arrays, filtering for type="photo" only
- [X] T014 [US1] Add staging file generation logic to create JSON output with metadata section (extracted_at, source_file, total_extracted, version) and tweets array, preserving created_at timestamps as-is from source
- [X] T015 [US1] Add UTF-8 encoding handling for emoji and special character preservation in tweet text
- [X] T016 [US1] Add progress feedback to print extraction progress every 100 tweets and final summary
- [X] T017 [US1] Add error handling for missing source file, invalid JSON, and write permission errors with clear stderr messages and non-zero exit codes
- [X] T018 [US1] Write staging file to etc/staging/tweets_staging.json with pretty-printing (indent=2) for human readability

**Checkpoint**: At this point, User Story 1 should be fully functional - can extract tweets.js to staging file independently

---

## Phase 4: User Story 2 - Review and Edit Extracted Quotes (Priority: P2)

**Goal**: Enable human review and manual editing of staging file before conversion

**Independent Test**: Manually edit etc/staging/tweets_staging.json (delete entries, modify text, add exclude flags), then verify conversion script respects all changes

### Implementation for User Story 2

- [X] T020 [US2] Add JSON schema validation function in scripts/staging_validator.py to verify staging file structure matches expected schema from contracts/schemas.md
- [X] T021 [US2] Create command-line helper script scripts/validate_staging.py that validates staging file JSON syntax and schema, reporting specific errors with line numbers
- [X] T022 [US2] Update extract_tweets.py to include helpful comments in staging file JSON explaining editable fields (text, exclude, notes)
- [X] T023 [US2] Document manual review process in staging file header comment: how to delete entries, edit text, mark exclusions

**Checkpoint**: At this point, User Story 2 should be complete - staging files are human-reviewable and editable with validation support

---

## Phase 5: User Story 3 - Convert Reviewed Quotes to Final Format (Priority: P3)

**Goal**: Convert reviewed staging file to application-ready quotes.json with proper schema

**Independent Test**: Run `python3 scripts/convert_to_quotes.py` on edited staging file and verify quotes.json is created/appended with correct schema, speaker extraction works, and retweets are excluded

### Implementation for User Story 3

- [X] T024 [US3] Implement main conversion logic in scripts/convert_to_quotes.py with CLI argument parsing (--staging, --quotes, --dry-run, --verbose, --help flags)
- [X] T025 [US3] Add staging file loader to read and parse etc/staging/tweets_staging.json with error handling for missing/corrupted file
- [X] T026 [US3] Add existing quotes loader to read app/data/quotes.json (create empty structure if file doesn't exist)
- [X] T027 [US3] Add quote ID generation logic using quote_id_generator utility to determine starting ID from existing quotes
- [X] T028 [US3] Add speaker extraction logic using speaker_detector utility to parse "Name:" prefix from tweet text (e.g., "Lucille: I don't understand..." → primarySpeaker="Lucille", quote="I don't understand...")
- [X] T029 [US3] Add quote text processing to strip speaker prefix from text if detected, otherwise use full text as quote
- [X] T030 [US3] Add filtering logic to skip entries with is_retweet=true and entries with exclude=true
- [X] T031 [US3] Add image URL extraction logic to use first media URL from staging entry media_urls array (filter for images only, skip videos/GIFs)
- [X] T032 [US3] Add quote record generation to create objects with schema {id, quote, primarySpeaker, imageUrl} per contracts/schemas.md
- [X] T033 [US3] Add quote appending logic to merge new quotes with existing quotes.json array, preserving existing entries
- [X] T034 [US3] Add ID collision detection and auto-increment logic per quote_id_generator utility
- [X] T035 [US3] Add UTF-8 encoding handling when writing quotes.json with ensure_ascii=False for proper Unicode preservation
- [X] T036 [US3] Add progress feedback to show skipped retweets count, excluded entries count, and conversion progress
- [X] T037 [US3] Add dry-run mode (--dry-run flag) to preview conversion without writing to quotes.json
- [X] T038 [US3] Add error handling for invalid staging schema, write permission errors, and JSON serialization errors with clear stderr messages
- [X] T039 [US3] Write final quotes.json with pretty-printing (indent=2) to app/data/quotes.json

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work together as a complete pipeline - extract → review → convert

---

## Phase 6: User Story 4 - Download Tweet Image Assets (Priority: P4)

**Goal**: Download tweet images to local folder for S3 upload preparation

**Independent Test**: Run `python3 scripts/download_media.py` and verify images are downloaded to media/tweet_images/ with proper naming, videos/GIFs are skipped, and existing files are not re-downloaded

### Implementation for User Story 4

- [X] T040 [US4] Implement main download logic in scripts/download_media.py with CLI argument parsing (--staging, --output-dir, --skip-existing, --timeout, --verbose, --help flags)
- [X] T041 [US4] Add staging file loader to read etc/staging/tweets_staging.json and extract media_urls from each entry
- [X] T042 [US4] Add media type filtering logic to check media type field from staging data and skip videos (type="video") and animated GIFs (type="animated_gif"), process only photos (type="photo")
- [X] T043 [US4] Add filename generation logic to create filenames as <tweet_id>_<index>.<ext> where ext is derived from URL or Content-Type header
- [X] T044 [US4] Add file existence checking logic to compare local file size with remote Content-Length header (using HTTP HEAD request), skip if sizes match
- [X] T045 [US4] Add HTTP download logic using urllib.request with 30-second timeout and User-Agent header set to avoid bot blocking
- [X] T046 [US4] Add error handling for HTTP errors (404, 403, timeouts) to log failure but continue processing remaining media
- [X] T047 [US4] Add progress feedback to show download status for each file ([N/total] filename... ✓/✗/skipped) and final summary
- [X] T048 [US4] Add download log generation to create media/download_log.json with detailed results per contracts/schemas.md (summary counts, individual download records with status)
- [X] T049 [US4] Create media/tweet_images/ directory if it doesn't exist before starting downloads
- [X] T050 [US4] Write downloaded images to media/tweet_images/ with proper binary file handling

**Checkpoint**: All user stories are now complete - full pipeline from extraction to media download works independently and together

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and usability improvements

- [X] T051 Add comprehensive docstrings to all Python modules following Google-style format
- [X] T052 Add --help text for all CLI scripts with usage examples and argument descriptions
- [X] T053 Create scripts/README.md with quickstart guide referencing specs/002-tweet-to-quote-conversion/quickstart.md
- [X] T054 Add example tweets.js sample file in etc/sample_tweets.js for testing (3-5 representative tweets)
- [X] T055 Validate all scripts work with quickstart.md workflow by running complete end-to-end test
- [X] T056 Validate speaker extraction accuracy by creating test staging file with entries containing "Michael: Test quote", "Lucille: Another quote", "George Michael: Third quote", and "No speaker here", then verify conversion extracts speakers correctly (Michael, Lucille, George Michael, and empty string respectively) in quotes.json and strips speaker prefix from quote text
- [X] T057 Add type hints to all Python functions (Python 3.11+ syntax) for better IDE support
- [X] T058 Update .gitignore to exclude etc/staging/, media/tweet_images/, and media/download_log.json

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (US1): Can start immediately after Foundational
  - User Story 2 (US2): Depends on US1 (needs staging file format)
  - User Story 3 (US3): Depends on US1 and US2 (needs reviewed staging file)
  - User Story 4 (US4): Can start after US1 (only needs staging file, independent of US3)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs staging file schema)
- **User Story 3 (P3)**: Depends on US1 and US2 completion (needs reviewed staging file)
- **User Story 4 (P4)**: Depends on US1 completion (reads staging file) - Independent of US2 and US3

### Within Each User Story

- User Story 1: Sequential implementation (T008 → T009 → ... → T019)
- User Story 2: Can run in parallel with other stories once US1 complete
- User Story 3: Sequential implementation (T024 → T025 → ... → T039)
- User Story 4: Sequential implementation (T040 → T041 → ... → T050)

### Parallel Opportunities

- **Phase 1 (Setup)**: All tasks T001-T004 can run in parallel (different directories)
- **Phase 2 (Foundational)**: All tasks T005-T007 can run in parallel (different files)
- **Once US1 complete**: US2 and US4 can start in parallel (US2 adds validation, US4 downloads media)
- **Polish phase**: Tasks T051-T057 can run in parallel (different concerns)

---

## Parallel Example: Foundational Phase

```bash
# Launch all foundational utilities together:
Task: "Create shared utility module scripts/tweet_parser.py"
Task: "Create shared utility module scripts/speaker_detector.py"
Task: "Create shared utility module scripts/quote_id_generator.py"
```

---

## Parallel Example: After User Story 1

```bash
# Once US1 is complete, these can run in parallel:
Task: "Add JSON schema validation function in scripts/staging_validator.py" (US2)
Task: "Implement main download logic in scripts/download_media.py" (US4)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T007) - CRITICAL
3. Complete Phase 3: User Story 1 (T008-T019)
4. **STOP and VALIDATE**: Test extraction with real tweets.js file
5. Review staging file manually - MVP delivers value here!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Extract tweets to staging → **Deploy/Demo (MVP!)** - Users can now extract and manually review
3. Add User Story 2 → Add validation tools → **Deploy/Demo** - Better review experience
4. Add User Story 3 → Complete conversion pipeline → **Deploy/Demo** - Full quotes.json generation
5. Add User Story 4 → Add media downloads → **Deploy/Demo** - Complete with images
6. Polish → Documentation and usability → **Final Release**

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T007)
2. Developer A completes User Story 1 (T008-T019) - CRITICAL PATH
3. Once US1 done:
   - Developer A: User Story 3 (T024-T039) - Main conversion logic
   - Developer B: User Story 2 (T020-T023) - Validation tools
   - Developer C: User Story 4 (T040-T050) - Media downloads
4. Team collaborates on Polish phase (T051-T057)

---

## Implementation Notes

### Speaker Extraction Pattern

The speaker_detector.py utility should implement this regex pattern:

```python
import re

def detect_speaker(text: str) -> tuple[str | None, str]:
    """
    Detect speaker from "Name:" prefix pattern.

    Returns: (speaker_name, remaining_text) or (None, original_text)

    Pattern: ^([A-Za-z\s]+):\s*(.+)$
    - Matches alphabetical characters and spaces only
    - Followed by colon
    - Preserves exact capitalization

    Examples:
        "Michael: I've made a huge mistake" → ("Michael", "I've made a huge mistake")
        "George Michael: Her?" → ("George Michael", "Her?")
        "GOB: I've made a huge tiny mistake" → ("GOB", "I've made a huge tiny mistake")
        "R2D2: Beep boop" → (None, "R2D2: Beep boop")  # No match (contains numbers)
    """
    match = re.match(r'^([A-Za-z\s]+):\s*(.+)$', text, re.DOTALL)
    if match:
        speaker = match.group(1).strip()
        remaining = match.group(2).strip()
        return (speaker, remaining)
    return (None, text)
```

**Usage in Conversion Script (convert_to_quotes.py, T028-T029)**:

```python
from speaker_detector import detect_speaker

# For each staging entry during conversion:
speaker, quote_text = detect_speaker(staging_entry['text'])

quote_record = {
    'id': f'quote-{next_id}',
    'quote': quote_text,
    'primarySpeaker': speaker or '',  # Use extracted speaker or empty string
    'imageUrl': staging_entry['media_urls'][0] if staging_entry['media_urls'] else None
}
```

### Quote ID Generation Logic

The quote_id_generator.py utility should implement:

```python
import re

def get_next_quote_id(existing_quotes: list[dict]) -> str:
    """
    Find highest existing quote ID and return next available.

    Handles collisions by auto-incrementing.

    Returns formatted ID string without zero-padding (e.g., "quote-1", "quote-42")
    """
    used_ids = set()
    max_id = 0

    for quote in existing_quotes:
        match = re.match(r'^quote-(\d+)$', quote.get('id', ''))
        if match:
            num = int(match.group(1))
            used_ids.add(num)
            max_id = max(max_id, num)

    next_id = max_id + 1
    while next_id in used_ids:
        next_id += 1

    return f'quote-{next_id}'  # Return formatted string, no zero-padding
```

### Media Type Filtering

When processing media URLs, check the type field:

```python
# In extract_tweets.py
for media in tweet.get('entities', {}).get('media', []):
    if media.get('type') == 'photo':  # Only photos
        media_urls.append(media['media_url_https'])
```

### Error Handling Standards

All scripts should follow this pattern:

```python
import sys

try:
    # Operation
    pass
except FileNotFoundError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON - {e}", file=sys.stderr)
    sys.exit(2)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

---

## Task Completion Summary

**Total Tasks**: 57

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 3 tasks
- Phase 3 (US1 - Extract): 11 tasks
- Phase 4 (US2 - Review): 4 tasks
- Phase 5 (US3 - Convert): 16 tasks
- Phase 6 (US4 - Download): 11 tasks
- Phase 7 (Polish): 8 tasks

**By User Story**:
- US1 (Extract): 11 tasks
- US2 (Review): 4 tasks
- US3 (Convert): 16 tasks
- US4 (Download): 11 tasks
- Infrastructure: 7 tasks (Setup + Foundational)
- Polish: 8 tasks

**Parallel Opportunities**: 12 tasks marked [P]

**Independent Test Criteria**:
- US1: Run extraction, verify staging file created with correct schema
- US2: Edit staging file, verify validation works
- US3: Run conversion, verify quotes.json appended correctly with speaker extraction
- US4: Run download, verify images downloaded and videos skipped

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US1 only) = Basic tweet extraction to staging file

---

## Notes

- No tests included (not requested in specification)
- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All paths use Python standard library (json, pathlib, urllib.request) - no external dependencies

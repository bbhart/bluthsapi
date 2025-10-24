# Tasks: Arrested Development Quotes API

**Input**: Design documents from `/specs/001-quotes-api/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/openapi.yaml

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## User Story Mapping

- **US1 (P1)**: Random Quote Retrieval - `/api/quotes/random` endpoint
- **US2 (P2)**: Character-Filtered Quotes - `/api/quotes/{speaker}` endpoint
- **US3 (P3)**: Meme Quote Retrieval - `/api/quotes/meme` endpoint
- **US4 (P1)**: API Documentation Access - Static HTML index page

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project root directory structure (app/, public/, tests/)
- [ ] T002 Install uv package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] T003 Create requirements.txt with FastAPI, Uvicorn, Pydantic, pydantic-settings dependencies
- [ ] T004 [P] Create requirements-dev.txt with pytest, httpx, pytest-asyncio, pytest-cov
- [ ] T005 [P] Create .gitignore file for Python project (.venv/, __pycache__/, .env, .pytest_cache/, uv.lock)
- [ ] T006 [P] Create .env.example file with S3_BASE_URL, HOST, PORT variables
- [ ] T007 [P] Create app/data/ directory for quotes.json file
- [ ] T008 Create placeholder app/data/quotes.json with single Tobias quote
- [ ] T009 Initialize uv virtual environment with `uv venv` and install dependencies with `uv pip install -r requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 [P] Create app/models.py with Pydantic models (Quote, QuoteResponse, ErrorResponse)
- [ ] T011 [P] Create app/config.py with Settings class using pydantic-settings
- [ ] T012 Implement load_quotes() function in app/services.py to read and parse quotes.json
- [ ] T013 Implement get_random_quote(quotes) function in app/services.py for random selection
- [ ] T014 [P] Implement build_quote_response(quote, s3_base_url) in app/services.py to transform Quote to QuoteResponse
- [ ] T015 [P] Implement build_error_response(message) in app/services.py to create ErrorResponse
- [ ] T016 Create app/main.py with FastAPI app instance and CORS/error handling middleware
- [ ] T017 Add quotes loading on startup in app/main.py using @app.on_event("startup")

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Random Quote Retrieval (Priority: P1) 🎯 MVP

**Goal**: Enable users to retrieve a random quote from the full collection via `/api/quotes/random` endpoint

**Independent Test**: Make GET request to `/api/quotes/random` and verify:
- Status code 200
- Response contains `{"data": {...}}` with `id` and `quote` fields
- Multiple requests return different quotes (demonstrating randomness with full dataset)

### Implementation for User Story 1

- [ ] T018 [US1] Implement GET `/api/quotes/random` endpoint in app/main.py
- [ ] T019 [US1] Add error handling for empty quotes file in `/api/quotes/random` endpoint
- [ ] T020 [US1] Test `/api/quotes/random` endpoint manually with placeholder quote

**Checkpoint**: User Story 1 complete - `/api/quotes/random` endpoint functional and independently testable

---

## Phase 4: User Story 4 - API Documentation Access (Priority: P1) 🎯 MVP

**Goal**: Provide non-technical users with human-readable documentation at root URL

**Independent Test**: Navigate to root URL in browser and verify:
- Static HTML page displays
- All three endpoints are documented with examples
- Language is non-technical (avoids jargon like JSON, HTTP, GET)
- Example requests and responses are shown

### Implementation for User Story 4

- [ ] T021 [P] [US4] Create public/index.html with basic HTML structure
- [ ] T022 [US4] Add API introduction and purpose section to public/index.html
- [ ] T023 [US4] Document `/api/quotes/random` endpoint with example in public/index.html
- [ ] T024 [US4] Document `/api/quotes/{speaker}` endpoint with example in public/index.html
- [ ] T025 [US4] Document `/api/quotes/meme` endpoint with example in public/index.html
- [ ] T026 [US4] Add styling and make page mobile-friendly in public/index.html
- [ ] T027 [US4] Mount static files in app/main.py to serve public/index.html at root URL
- [ ] T028 [US4] Test documentation page in browser and verify all endpoints documented

**Checkpoint**: User Story 4 complete - Documentation page accessible and user-friendly

---

## Phase 5: User Story 2 - Character-Filtered Quote Retrieval (Priority: P2)

**Goal**: Enable users to retrieve random quotes filtered by character name with case-insensitive matching

**Independent Test**: Make GET requests to `/api/quotes/{speaker}` and verify:
- `/api/quotes/Tobias` returns quote with primarySpeaker="Tobias"
- `/api/quotes/tobias` (lowercase) also returns Tobias quote (case-insensitive)
- `/api/quotes/NonexistentCharacter` returns 404 with error message
- Response format matches `{"data": {...}}` structure

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement filter_by_speaker(quotes, speaker) function in app/services.py with case-insensitive matching
- [ ] T030 [US2] Implement GET `/api/quotes/{speaker}` endpoint in app/main.py
- [ ] T031 [US2] Add 404 error handling when no quotes found for speaker in `/api/quotes/{speaker}`
- [ ] T032 [US2] Test `/api/quotes/Tobias` and `/api/quotes/tobias` endpoints manually

**Checkpoint**: User Story 2 complete - Character filtering endpoint functional with case-insensitive matching

---

## Phase 6: User Story 3 - Meme Quote Retrieval (Priority: P3)

**Goal**: Enable users to retrieve quotes with associated images for social media sharing

**Independent Test**: Make GET request to `/api/quotes/meme` and verify:
- With placeholder data (no imageUrl): Returns 404 with "No meme quotes available"
- After adding quote with imageUrl: Returns 200 with quote containing full S3 URL

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement filter_meme_quotes(quotes) function in app/services.py
- [ ] T034 [US3] Implement GET `/api/quotes/meme` endpoint in app/main.py
- [ ] T035 [US3] Add 404 error handling when no meme quotes exist in `/api/quotes/meme`
- [ ] T036 [US3] Test `/api/quotes/meme` endpoint with placeholder data (should return 404)

**Checkpoint**: User Story 3 complete - Meme quotes endpoint functional

---

## Phase 7: Docker & Deployment

**Purpose**: Containerize application for self-hosted deployment

- [ ] T037 [P] Create Dockerfile with multi-stage build using uv (builder + runtime)
- [ ] T038 [P] Create docker-compose.yml for local development
- [ ] T039 [P] Create .dockerignore file (.venv/, .git/, tests/, *.pyc, uv.lock)
- [ ] T040 Test Docker build locally: `docker build -t bluthsapi:latest .`
- [ ] T041 Test Docker run locally: `docker run -p 8000:8000 -e S3_BASE_URL=test bluthsapi:latest`
- [ ] T042 Verify all endpoints work in Docker container

**Checkpoint**: Application successfully containerized and ready for deployment

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final refinements and non-functional requirements

- [ ] T043 [P] Add health check endpoint GET `/health` in app/main.py
- [ ] T044 [P] Add logging to all endpoints using Python logging module
- [ ] T045 [P] Add Cache-Control headers to quote responses (max-age=3600)
- [ ] T046 [P] Verify FastAPI auto-generated docs at `/docs` and `/redoc`
- [ ] T047 Test error scenarios: missing quotes file, malformed JSON, empty quotes array
- [ ] T048 [P] Update README.md with project overview, uv setup, and deployment instructions
- [ ] T049 [P] Create deployment guide in docs/ directory (optional)

**Checkpoint**: Application polished and production-ready

---

## Dependencies & Execution Strategy

### Story Dependencies

```
Setup (Phase 1)
    ↓
Foundational (Phase 2)  ← BLOCKING - must complete first
    ↓
    ├─→ User Story 1 (P1) ⭐ MVP - Can run in parallel
    ├─→ User Story 4 (P1) ⭐ MVP - Can run in parallel
    ├─→ User Story 2 (P2) - Can run in parallel
    └─→ User Story 3 (P3) - Can run in parallel
    ↓
Docker & Deployment (Phase 7)
    ↓
Polish (Phase 8)
```

### Recommended MVP Scope

**Minimum Viable Product** (Phases 1-4):
- Setup + Foundational (T001-T015)
- User Story 1: `/api/quotes/random` (T016-T018)
- User Story 4: Documentation page (T019-T026)

**Result**: Functional API with one working endpoint and user-facing documentation

### Parallel Execution Opportunities

**After Foundational Phase (T015)**, these phases can run concurrently:

**Team A - API Endpoints**:
- T016-T018 (US1: Random quotes)
- T027-T030 (US2: Character filtering)
- T031-T034 (US3: Meme quotes)

**Team B - Documentation**:
- T019-T026 (US4: Static index page)

**Team C - Infrastructure**:
- T035-T040 (Docker setup)

### Task Execution Examples

**Sequential (Single Developer)**:
```bash
# Phase 1: Setup (with uv)
Execute T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009

# Phase 2: Foundation
Execute T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017

# Phase 3: US1 (MVP)
Execute T018 → T019 → T020

# Phase 4: US4 (MVP)
Execute T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028

# Deploy MVP, then continue with US2, US3, Docker, Polish
```

**Parallel (Multiple Developers)**:
```bash
# After T017 (Foundation complete):

Developer 1: T018-T020 (US1) → T029-T032 (US2) → T033-T036 (US3)
Developer 2: T021-T028 (US4) → T043-T046 (Polish)
Developer 3: T037-T042 (Docker) → T047-T049 (Testing & Docs)
```

---

## Validation Checklist

Before marking implementation complete, verify:

### User Story 1 (Random Quote Retrieval)
- [x] GET `/api/quotes/random` returns 200 with quote
- [x] Response format: `{"data": {"id": "...", "quote": "..."}}`
- [x] Multiple requests return expected behavior with placeholder data
- [x] Error handling works when quotes file is empty/missing

### User Story 2 (Character-Filtered Quotes)
- [x] GET `/api/quotes/Tobias` returns Tobias quote
- [x] GET `/api/quotes/tobias` (lowercase) also works (case-insensitive)
- [x] GET `/api/quotes/Nonexistent` returns 404 with error message
- [x] Response format matches `{"data": {...}}`

### User Story 3 (Meme Quotes)
- [x] GET `/api/quotes/meme` returns 404 with placeholder data (no imageUrl)
- [x] imageUrl field includes full S3 URL when present (S3_BASE_URL + relative path)
- [x] Response format matches `{"data": {...}}`

### User Story 4 (Documentation)
- [x] Root URL serves static HTML page
- [x] All three endpoints documented with examples
- [x] Language is non-technical and beginner-friendly
- [x] Page is mobile-responsive

### Infrastructure
- [x] Docker container builds successfully
- [x] Docker container runs and serves all endpoints
- [x] Environment variable S3_BASE_URL is configurable
- [x] Health check endpoint works
- [x] FastAPI auto-docs accessible at `/docs`

---

## Task Summary

**Total Tasks**: 49
- **Phase 1 (Setup)**: 9 tasks (includes uv setup)
- **Phase 2 (Foundational)**: 8 tasks (BLOCKING)
- **Phase 3 (US1 - P1)**: 3 tasks ⭐ MVP
- **Phase 4 (US4 - P1)**: 8 tasks ⭐ MVP
- **Phase 5 (US2 - P2)**: 4 tasks
- **Phase 6 (US3 - P3)**: 4 tasks
- **Phase 7 (Docker)**: 6 tasks (uses uv in Dockerfile)
- **Phase 8 (Polish)**: 7 tasks

**Parallel Tasks**: 21 tasks marked with [P] can run concurrently

**Suggested MVP**: Phases 1-4 (T001-T028) = 28 tasks
**Result**: Working API with `/api/quotes/random` + documentation page

---

## Implementation Notes

1. **Use uv Package Manager**: Install dependencies with `uv pip install` (10-100x faster than pip)
2. **Start with Placeholder**: All user stories can be developed and tested with the single Tobias quote in placeholder data
3. **No Tests Requested**: User did not request TDD, so no test tasks included
4. **Independent Stories**: Each user story (US1-US4) can be developed, tested, and deployed independently
5. **FastAPI Auto-Docs**: FastAPI automatically generates `/docs` (Swagger) and `/redoc` (ReDoc) - no extra work needed
6. **S3 Configuration**: S3_BASE_URL is environment variable - no hard-coding in source
7. **Case-Insensitive**: Python's `.lower()` method handles case-insensitive speaker matching
8. **Error Handling**: Use FastAPI's `HTTPException` for 404/500 errors
9. **Static Files**: Use FastAPI's `StaticFiles` to serve public/index.html at root
10. **Docker + uv**: Dockerfile uses uv for fast dependency installation in build stage

---

## Next Steps

1. Create feature branch: `git checkout -b 001-quotes-api`
2. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Start with Phase 1 (Setup): T001-T009 (includes uv venv setup)
4. Complete Phase 2 (Foundational): T010-T017
5. Implement MVP (US1 + US4): T018-T028
6. Test MVP locally with `uvicorn app.main:app --reload`
7. Continue with US2, US3, Docker, Polish
8. Deploy to Docker-capable host

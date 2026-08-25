# bluthsapi Development Guidelines

Auto-generated from feature plans, with hand-written guidance at the end.
Last updated: 2026-08-25

## Active Technologies

- Python 3.11+ (see `requirements.txt`) + FastAPI, Mangum (ASGI-to-Lambda), AWS SAM CLI
- File-based storage: `app/data/quotes.json` bundled into the Lambda package; images on S3
- Static front end in `public/`, served by FastAPI `StaticFiles`. No build step, no framework
- YAML (SAM/CloudFormation) for infrastructure, including budget controls and the
  cost-shutdown path (`app/budget_shutdown.py`, `app/month_rollover_check.py`)

## Project Structure

```text
app/          FastAPI application; app/data/ holds quotes.json and the character list
public/       Static site: index.html, prettyquote.html, styles.css, llms.txt, robots.txt
scripts/      Quote-data tooling (see scripts/README.md)
tests/        unit/ (fast, no server), api/ (httpx), e2e/ (Playwright)
docs/         ARCHITECTURE.md, budget-reset.md, plans/
specs/        Historical spec-kit artifacts. Features 002 and 003 describe the tweet
              import pipeline, which has been removed — do not follow them.
work/         Gitignored scratch: fetched transcripts, worksheets
build/        Gitignored generated reports and patches
```

There is no `src/` directory and no container image.

## Commands

```bash
uvicorn app.main:app --reload          # run locally (the dev path; no Docker image exists)
pytest tests/unit tests/api            # fast suite, no browser needed
pytest tests/e2e                       # needs: playwright install chromium
python3 scripts/normalize_speakers.py --check   # data gate; CI runs this
```

## Code Style

Follow the conventions already in the file you are editing. Module and function
docstrings explain *why*, not *what*. Standard library is preferred in `scripts/`;
none of them take third-party dependencies.

## Recent Changes

- Landing page redesigned; `og-image.png`, `llms.txt`, JSON-LD and OpenAPI metadata added
- Container files removed (`Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.samignore`)
- `primarySpeaker` replaced by a canonical `speakers` field; attributions verified
  against episode transcripts
- Tweet import pipeline (002, 003) removed; `quotes.json` is now maintained by hand

<!-- MANUAL ADDITIONS START -->

## The speakers contract

This is the thing most easily broken, so read it before touching `app/data/quotes.json`.

`speakers` is a **comma-separated string, no space after the comma**, listing everyone
who speaks in the quote **in the order they speak**: `"Lucille,Michael"`. It is `""`
when nobody has identified the speaker — an empty value is the honest answer and is
preferred over a guess. A wrong name is worse than no name, because it makes
`/api/quotes/{character}` return lines that character never said.

Every name must appear verbatim in `app/data/list-of-characters.txt` (46 names in use).
That file is **generated** — never edit it by hand. One canonical spelling per
character: `GOB`, never `Gob` or `G.O.B.`. `Lucille` is Lucille Bluth; Lucille Austero
is written out. Aliases and personas fold into the real speaker, so
`Mrs. Featherbottom` resolves to `Tobias`.

To add a character, add them to `CHARACTERS` in `scripts/speaker_names.py`, then run
`python3 scripts/normalize_speakers.py` to regenerate the list.

`normalize_speakers.py` **fails closed**: an unrecognized name stops the run, writes
nothing, and exits non-zero. Do not try to route around it. It behaves that way
because silently dropping a name deletes a curator's work and leaves a record that
looks correct afterwards.

Quote text is never modified. Exchanges keep their `"Lucille: ... Michael: ..."`
prefixes; parsing reads speakers *out of* the text without rewriting it.

## Quote tooling

All in `scripts/`, standard library only, documented in `scripts/README.md`:

- `speaker_names.py` — canonical registry, alias resolution, speaker parsing
- `normalize_speakers.py` — normalizes `speakers`, regenerates the character list; `--check` is the CI gate
- `speakers_worksheet.py` — export unattributed quotes to a flat file, edit by hand, merge back
- `find_duplicate_quotes.py` — near-duplicate report plus a reviewable patch; changes nothing itself
- `fetch_transcripts.py` / `verify_attributions.py` — settle speakers against episode transcripts
- `quote_id_generator.py` — next sequential `quote-N` id

A pattern worth keeping: these tools report and propose rather than silently rewrite,
and anything they cannot resolve confidently is listed for a human instead of guessed.

## Things that must not be committed

- `work/transcripts/` holds full transcripts of copyrighted episodes, fetched as local
  reference. Keep them local. `work/` is gitignored and has its own `.gitignore` as a
  second line of defence.
- This repository is public. No AWS account ids, ARNs, or personal email addresses.
  `CertificateArn` and `AlertEmail` are template parameters fed from CI secrets
  (`ACM_CERTIFICATE_ARN`, `ALERT_EMAIL`); `samconfig.toml` deliberately carries neither.

## Deployment

Push to `main` deploys via GitHub Actions. `sam build --use-container` needs a running
Docker daemon — that is SAM's own build image, not a Dockerfile in this repo.

The stack has a hard $30/month budget that throttles API Gateway to zero when tripped;
see `docs/budget-reset.md` for recovery. Because every request is a billed invocation,
`robots.txt` disallows crawling `/api/` while allowing the docs and the OpenAPI spec.

<!-- MANUAL ADDITIONS END -->

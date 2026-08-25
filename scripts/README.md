# Quote Data Scripts

Utilities for maintaining `app/data/quotes.json` and the canonical character list.

## Overview

`quotes.json` was originally seeded from an export of the @bluthquotes Twitter
archive. That import was a one-time event and its tooling (tweet extraction,
staging, filtering, media download) has been removed. The quote database is now
maintained by hand and by pull request — see
[CONTRIBUTING.md](../CONTRIBUTING.md#contributing-quotes).

These scripts use the standard library only.

## normalize_speakers.py

Normalizes the `speakers` field in `app/data/quotes.json` and regenerates
`app/data/list-of-characters.txt`. Idempotent — safe to re-run.

**Usage:**
```bash
# Rewrite quotes.json and regenerate the character list
python3 scripts/normalize_speakers.py

# Verify only; exits non-zero if a name is not canonical or the list is stale
python3 scripts/normalize_speakers.py --check
```

It parses speakers out of the quote text, folds every name to its canonical form
via the alias table in `speaker_names.py`, and rewrites the character list from
the names actually in use. `--check` is what CI runs on pull requests. See
[CONTRIBUTING.md](../CONTRIBUTING.md#character-names).

A name that doesn't resolve to a canonical character stops the run in **both**
modes: nothing is written and the exit code is 1 until the quote is fixed or the
character is added to `CHARACTERS`. The script never normalizes around an unknown
name — that would silently delete data.

An unrecognized `Name:` prefix *inside the quote text* is only a warning. The
quote text is never modified, so nothing is lost; it just means a speaker went
unrecorded, and that detection is a heuristic that can misfire on ordinary
punctuation.

## find_duplicate_quotes.py

Finds near-duplicate quotes and writes a report plus a patch. It never modifies
`quotes.json` — you review, then apply.

**Usage:**
```bash
python3 scripts/find_duplicate_quotes.py
less build/duplicates-report.txt          # read this first
git apply build/duplicates.patch
python3 scripts/normalize_speakers.py --check
```

**Options:**
- `--threshold FLOAT` - similarity ratio to call a pair duplicate (default: 0.85)
- `--containment-min-tokens N` - a contained quote needs at least N words (default: 6)
- `--quotes PATH` / `--patch PATH` / `--report PATH` - override paths
- `--stdout` - print the report instead of writing files

Matching runs on a normalized form of the text: lowercased, speaker prefixes
removed, censorship markers (`[bleep]`, `__`, `****`) collapsed, punctuation
flattened. A pair matches on similarity ratio, or on containment — one quote
wholly inside another, which is the common case here, since the same line was
tweeted both truncated and in full. Groups are transitive.

The surviving record is the one with the longest text, so a punchline is never
traded away for a shorter variant that happened to carry an image; the image is
inherited instead. Anything the merge cannot reconcile — a duplicate naming a
different speaker, or a second image that would be discarded — is listed under
CONFLICTS at the top of the report rather than silently resolved.

## Utility Modules

### speaker_names.py

The canonical character registry, alias resolution, and multi-speaker text
parsing. Names like `GOB` / `Gob` / `G.O.B.` all fold to one canonical `GOB`.

**Key Functions:**
```python
resolve(name: str) -> str | None
# "G.O.B." -> "GOB";  "George Sr" -> "George Sr.";  "Nobody" -> None

parse_speakers(text: str) -> list[str]
# "Lucille: You tricked me. Michael: I deceived you." -> ["Lucille", "Michael"]

unknown_prefixes(text: str) -> list[str]
# "Name:" prefixes that no alias resolves, so they can be reported not dropped
```

Unlike a bare `^\w+:` regex, `parse_speakers` only accepts a prefix that resolves
to a known character, so `"Next stop: LAX"` yields no speaker. Parsing never
modifies the quote text — a `"Lucille:"` prefix stays in the quote body, because
that is how the exchange reads.

To add a character, add an entry to the `CHARACTERS` dict here and re-run
`normalize_speakers.py`.

### quote_id_generator.py

Generates the next sequential quote ID.

**Key Function:**
```python
get_next_quote_id(existing_quotes: list[dict]) -> str
# Returns formatted ID like "quote-1", "quote-42"
```

## Tests

```bash
pytest tests/unit
```

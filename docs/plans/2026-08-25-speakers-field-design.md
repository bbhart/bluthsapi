# Design: `speakers` field and canonical character names

Date: 2026-08-25
Status: accepted

## Problem

`quotes.json` records carry a single `primarySpeaker` string. Many quotes are
multi-character exchanges, so one name cannot describe them. Separately, the
names already in the data are inconsistent — `GOB` / `Gob` / `G.O.B.` all refer
to the same character, as do `George` / `George Sr` / `George Sr.` — which makes
`/api/quotes/{speaker}` unreliable.

## Schema

`primarySpeaker` and the declared-but-unused `speakers: list[str]` are both
removed from the `Quote` model. They are replaced by one field:

```json
{
  "id": "quote-288",
  "quote": "Lucille: You tricked me. Michael: I deceived you, Mom. ...",
  "speakers": "Lucille,Michael"
}
```

- Type `str`, comma-separated, no space after the comma.
- Ordered by first appearance in the quote text.
- `""` when the speaker is unknown. The key is always present so consumers see a
  stable shape.
- Every comma-separated token must appear verbatim in
  `app/data/list-of-characters.txt`.

## Canonical names

`app/data/list-of-characters.txt` holds one canonical name per line, sorted, and
contains exactly the names in use in `quotes.json`. It is generated, not
hand-maintained.

Short forms are used where they are unambiguous and already conventional
(`Michael`, `Lucille`, `Tobias`, `Buster`, `Lindsay`, `Maeby`, `George Michael`,
`Oscar`, `Annyong`). Full names are used only where the short form collides with
another character or is not how the character is known.

`Lucille` means Lucille Bluth. Lucille Austero is written out in full as
`Lucille Austero`.

Collisions resolved from the existing data:

| Found in data | Canonical |
| --- | --- |
| `GOB`, `Gob`, `G.O.B.` | `GOB` |
| `George`, `George Sr`, `George Sr.` | `George Sr.` |
| `Barry` | `Barry Zuckerkorn` |
| `Wayne` | `Wayne Jarvis` |
| `Larry`, `Larry the surrogate` | `Larry Middleman` |
| `Veal`, `Rev. Veal` | `Reverend Veal` |

## Parsing

A naive `^Name:` regex over-matches. Run against the real data it produced
entries like `Next stop`, `Not tonight. Michael` and `She old school. Michael`.

The parser is therefore alias-table driven: a `Name:` prefix is only treated as
a speaker if `Name` resolves to a known canonical character. Longest aliases are
matched first so `George Michael:` is not read as `George`. Prefixes that do not
resolve are reported rather than silently accepted.

## Tooling

`scripts/speaker_names.py` holds the canonical registry, alias resolution, and
the text parser. `scripts/normalize_speakers.py` is the CLI. Both are
idempotent and safe to re-run.

1. Parse in-text speaker prefixes for any quote whose `speakers` is empty.
2. Merge in the legacy `primarySpeaker` value if present.
3. Resolve every name through the alias table to its canonical form.
4. Write `speakers`, drop `primarySpeaker`.
5. Regenerate `list-of-characters.txt` from the names in use.

`--check` makes no writes and exits non-zero if any name in `quotes.json` is not
a canonical name, or if `list-of-characters.txt` is stale. This lets CI enforce
the naming rule instead of CONTRIBUTING merely asking for it.

## Attribution

Deterministic parsing plus the legacy `primarySpeaker` values cover roughly 120
of 666 quotes. The remaining quotes carry no in-text signal and are attributed
from knowledge of the show, written directly into `quotes.json` in a dedicated
commit so the diff is the audit trail. Quotes that cannot be attributed with
confidence keep `""` rather than a guess.

## Blast radius

- `app/models.py` — field replacement.
- `app/services.py` — `filter_by_speaker` splits on commas and matches any
  token, case-insensitively. `/api/quotes/Michael` matches `Lucille,Michael`.
- The tweet import pipeline (`extract_tweets.py`, `convert_to_quotes.py` and the
  staging/media tooling) was removed in the same change: that import was a
  one-time event, and `quotes.json` is now maintained by hand.
- `tests/api/test_endpoints.py` — field references.
- `README.md`, `public/index.html` — sample payloads and field docs.
- `CONTRIBUTING.md` — new Character Names section.

`public/prettyquote.html` does not render speakers and is untouched.

## Testing

- Unit tests for alias resolution and the text parser, including the
  over-matching cases the naive regex failed on.
- Unit test for multi-speaker `filter_by_speaker`.
- Data integrity test asserting every name in `quotes.json` appears in
  `list-of-characters.txt`.

## Quote text is never modified

Parsing speakers out of a quote does not change the quote. A record keeps its
`"Lucille: ... Michael: ..."` prefixes in the text — they are part of how the
exchange reads — and the names are recorded alongside it in `speakers`.

## Out of scope

Splitting a quote into per-speaker lines. A `primarySpeaker` back-compatibility
alias in API responses.

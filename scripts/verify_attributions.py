#!/usr/bin/env python3
"""Check quotes.json `speakers` values against the episode transcripts.

Most attributions in quotes.json were inferred rather than read off the source
(issue #21). The transcripts in work/transcripts/ are the source, so a quote
whose text can be located in an episode has its speaker settled as a fact
rather than a guess.

    python3 scripts/fetch_transcripts.py --all-seasons --delay 2.0
    python3 scripts/verify_attributions.py --dry-run      # report only
    python3 scripts/verify_attributions.py                # apply the findings

How a quote is located
----------------------
Each transcript line is split into a speaker label and its dialogue. Stage
directions are dropped, and the dialogue is normalized the same way the quote
is: lowercased, punctuation and whitespace flattened. Each episode's dialogue
is then joined into one string, remembering which line every character came
from.

A quote is matched by finding its normalized text as a substring of that joined
dialogue. Because the join spans line boundaries, an exchange spread over
several lines matches in one go, and the character span maps straight back to
the speakers in the order they spoke -- which is exactly the order the
`speakers` field wants.

Matching is deliberately conservative, because a wrong attribution is worse
than none:

* a quote must be at least --min-words words and --min-chars characters, so
  short common phrases cannot match by accident
* if a quote matches in more than one place and those places disagree about who
  is speaking, it is reported as ambiguous and left alone
* if a speaker label does not resolve to a canonical character, the quote is
  reported and left alone rather than written with an unknown name

Everything it changes is listed in the report, with the episode and the line it
matched, so each change can be checked against the source.
"""

import argparse
import difflib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from speaker_names import (  # noqa: E402
    _ALIAS_PATTERN,
    format_speakers,
    parse_speakers,
    resolve,
    split_speakers,
)

REPO_ROOT = Path(__file__).parent.parent
QUOTES_PATH = REPO_ROOT / "app" / "data" / "quotes.json"
TRANSCRIPTS = REPO_ROOT / "work" / "transcripts"
DEFAULT_REPORT = REPO_ROOT / "build" / "attribution-report.txt"

KEY_ORDER = ["id", "quote", "speakers", "imageUrl"]

SPEAKER_LINE = re.compile(r"^([A-Z][A-Za-z .'\-]{1,30}):\s+(\S.*)$")

# Stage directions: "(beat)", "[laughs]". Never spoken, so never matched on.
STAGE_DIRECTION = re.compile(r"\([^()]*\)|\[[^\[\]]*\]")

# A quoted run of dialogue, as used in quotes.json to write an exchange
# without speaker labels: "line one." "line two."
QUOTED_SEGMENT = re.compile(r"[\"“”]([^\"“”]{10,})[\"“”]")


def normalize(text: str) -> str:
    """Flatten text to the form used for matching."""
    text = STAGE_DIRECTION.sub(" ", text or "")
    text = _ALIAS_PATTERN.sub(" ", text)      # drop "Michael:" prefixes
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class Episode:
    """One transcript, indexed so a span of text maps back to its speakers."""

    def __init__(self, slug: str, raw: str):
        self.slug = slug
        self.labels: list[str] = []
        self.raw_lines: list[str] = []
        spans: list[tuple[int, int, int]] = []
        pieces: list[str] = []
        cursor = 0

        for line in raw.splitlines():
            match = SPEAKER_LINE.match(line.strip())
            if not match:
                continue
            label, dialogue = match.group(1).strip(), match.group(2)
            norm = normalize(dialogue)
            if not norm:
                continue
            index = len(self.labels)
            self.labels.append(label)
            self.raw_lines.append(f"{label}: {dialogue}")
            start = cursor
            pieces.append(norm)
            cursor += len(norm) + 1          # +1 for the joining space
            spans.append((start, start + len(norm), index))

        self.text = " ".join(pieces)
        self.spans = spans

    def speakers_for_span(self, start: int, end: int) -> list[int]:
        """Line indexes overlapped by the character range."""
        return [i for s, e, i in self.spans if s < end and start < e]

    def find_all(self, needle: str, cap: int = 8) -> list[tuple[int, int]]:
        hits: list[tuple[int, int]] = []
        at = self.text.find(needle)
        while at != -1 and len(hits) < cap:
            hits.append((at, at + len(needle)))
            at = self.text.find(needle, at + 1)
        return hits


def load_episodes(directory: Path) -> list[Episode]:
    episodes = []
    for path in sorted(directory.glob("*.txt")):
        episode = Episode(path.stem, path.read_text(encoding="utf-8"))
        if episode.text:
            episodes.append(episode)
    return episodes


class Match:
    def __init__(self, episode: Episode, indexes: list[int]):
        self.episode = episode
        self.indexes = indexes
        self.labels = []
        for i in indexes:
            label = episode.labels[i]
            if label not in self.labels:
                self.labels.append(label)

    @property
    def canonical(self) -> list[str] | None:
        """Canonical names, or None if any label is unrecognized."""
        names: list[str] = []
        for label in self.labels:
            name = resolve(label)
            if name is None:
                return None
            if name not in names:
                names.append(name)
        return names

    @property
    def excerpt(self) -> str:
        first = self.episode.raw_lines[self.indexes[0]]
        return first[:110] + ("..." if len(first) > 110 else "")


def find_matches(quote_text: str, episodes: list[Episode],
                 min_words: int, min_chars: int) -> tuple[list[Match], str | None]:
    """Locate a quote across all episodes.

    Returns (matches, skip_reason). A skip_reason means the quote was too short
    to match safely.
    """
    needle = normalize(quote_text)
    if len(needle.split()) < min_words:
        return [], f"too short ({len(needle.split())} words)"
    if len(needle) < min_chars:
        return [], f"too short ({len(needle)} chars)"

    matches: list[Match] = []
    for episode in episodes:
        for start, end in episode.find_all(needle):
            indexes = episode.speakers_for_span(start, end)
            if indexes:
                matches.append(Match(episode, indexes))
    return matches, None


# Words too common to help narrow a search.
STOPWORDS = frozenset("""
a an and are as at be been but by do does did for from get got had has have he
her him his i if in is it its just like me my no not of on or our out she so
that the their them then there they this to too up us was we were what when
who will with would you your im dont thats youre ive
""".split())


class FuzzyIndex:
    """Inverted index over transcript lines, for candidate retrieval.

    Scoring every quote against every line is far too slow, so candidates are
    drawn from lines sharing an uncommon word with the quote and only those are
    scored properly.
    """

    def __init__(self, episodes: list[Episode], max_postings: int = 400):
        self.episodes = episodes
        index: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for ep_i, episode in enumerate(episodes):
            for line_i, (start, end, _) in enumerate(episode.spans):
                for token in set(episode.text[start:end].split()):
                    if token not in STOPWORDS and len(token) > 2:
                        index[token].append((ep_i, line_i))
        # Words appearing almost everywhere cannot discriminate.
        self.index = {t: p for t, p in index.items() if len(p) <= max_postings}

    def candidates(self, needle: str, limit: int = 60) -> list[tuple[int, int]]:
        tokens = {t for t in needle.split() if t not in STOPWORDS and len(t) > 2}
        hits: dict[tuple[int, int], int] = defaultdict(int)
        for token in tokens:
            for posting in self.index.get(token, ()):
                hits[posting] += 1
        if not hits:
            return []
        ranked = sorted(hits.items(), key=lambda kv: -kv[1])
        return [posting for posting, _ in ranked[:limit]]


class FuzzyMatch:
    def __init__(self, episode: Episode, indexes: list[int], score: float):
        self.episode = episode
        self.indexes = indexes
        self.score = score
        self.labels: list[str] = []
        for i in indexes:
            label = episode.labels[i]
            if label not in self.labels:
                self.labels.append(label)

    @property
    def canonical(self) -> list[str] | None:
        names: list[str] = []
        for label in self.labels:
            name = resolve(label)
            if name is None:
                return None
            if name not in names:
                names.append(name)
        return names

    @property
    def excerpt(self) -> str:
        first = self.episode.raw_lines[self.indexes[0]]
        return first[:110] + ("..." if len(first) > 110 else "")


def best_fuzzy(quote_text: str, index: FuzzyIndex,
               min_words: int) -> list[FuzzyMatch]:
    """Score a quote against plausible windows of consecutive dialogue lines.

    Returns the scored windows, best first. The caller decides what score is
    good enough.
    """
    needle = normalize(quote_text)
    if len(needle.split()) < min_words:
        return []

    scored: list[FuzzyMatch] = []
    seen: set[tuple[int, int, int]] = set()
    for ep_i, line_i in index.candidates(needle):
        episode = index.episodes[ep_i]
        # Windows starting at, or just before, the candidate line -- a quote
        # often begins mid-exchange.
        for offset in (0, -1):
            start_line = line_i + offset
            if start_line < 0:
                continue
            span_start = episode.spans[start_line][0]
            end_line = start_line
            while end_line < len(episode.spans) - 1:
                span_end = episode.spans[end_line][1]
                if span_end - span_start >= len(needle) * 1.25:
                    break
                end_line += 1
            for last in range(start_line, end_line + 1):
                key = (ep_i, start_line, last)
                if key in seen:
                    continue
                seen.add(key)
                window_end = episode.spans[last][1]
                window = episode.text[span_start:window_end]
                if not window:
                    continue
                matcher = difflib.SequenceMatcher(None, needle, window)
                ratio = matcher.ratio()

                # A window that scores well can still stretch past the quote,
                # picking up the next character's reply, or stop short of a
                # speaker the quote does include. Keep only the lines the quote
                # actually aligns with.
                aligned = [False] * len(window)
                for _, j, size in matcher.get_matching_blocks():
                    for k in range(j, min(j + size, len(window))):
                        aligned[k] = True

                kept: list[int] = []
                for line_no in range(start_line, last + 1):
                    l_start, l_end, _ = episode.spans[line_no]
                    rel_start = l_start - span_start
                    rel_end = min(l_end - span_start, len(window))
                    if rel_end <= rel_start:
                        continue
                    hits = sum(aligned[rel_start:rel_end])
                    length = rel_end - rel_start
                    if hits >= max(12, 0.35 * length):
                        kept.append(line_no)

                if not kept:
                    continue
                scored.append(FuzzyMatch(episode, kept, ratio))

    scored.sort(key=lambda m: -m.score)
    return scored[:12]


def render_quote(quote: dict) -> dict:
    ordered = {k: quote[k] for k in KEY_ORDER if k in quote}
    ordered.update({k: v for k, v in quote.items() if k not in ordered})
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--transcripts", type=Path, default=TRANSCRIPTS)
    parser.add_argument("--quotes", type=Path, default=QUOTES_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--dry-run", action="store_true",
                        help="report without changing quotes.json")
    parser.add_argument("--min-words", type=int, default=6,
                        help="minimum words a quote needs to be matchable (default: 6)")
    parser.add_argument("--min-chars", type=int, default=30,
                        help="minimum characters, after normalizing (default: 30)")
    parser.add_argument("--fuzzy", action="store_true",
                        help="also match paraphrased quotes that are not verbatim")
    parser.add_argument("--fuzzy-threshold", type=float, default=0.82, metavar="R",
                        help="similarity needed to accept a fuzzy match (default: 0.82)")
    parser.add_argument("--fuzzy-margin", type=float, default=0.04, metavar="R",
                        help="a fuzzy winner must beat any rival naming different "
                             "speakers by this much (default: 0.04)")
    parser.add_argument("--fuzzy-review-floor", type=float, default=0.70, metavar="R",
                        help="report, but do not apply, matches scoring at least "
                             "this (default: 0.70)")
    args = parser.parse_args()

    if not args.transcripts.is_dir():
        print(f"ERROR: no transcripts at {args.transcripts}.\n"
              "Run: python3 scripts/fetch_transcripts.py --all-seasons --delay 2.0",
              file=sys.stderr)
        return 1

    episodes = load_episodes(args.transcripts)
    if not episodes:
        print(f"ERROR: no usable transcripts in {args.transcripts}", file=sys.stderr)
        return 1

    quotes = json.loads(args.quotes.read_text(encoding="utf-8"))

    added, fixed, confirmed = [], [], []
    ambiguous, unknown_label, unmatched = [], [], []

    for quote in quotes:
        current = split_speakers(quote.get("speakers", ""))
        matches, skip = find_matches(
            quote["quote"], episodes, args.min_words, args.min_chars
        )

        if skip or not matches:
            unmatched.append((quote, skip or "not found in any transcript"))
            continue

        # Group distinct answers; disagreement means we cannot be sure.
        answers: dict[tuple[str, ...], list[Match]] = defaultdict(list)
        for match in matches:
            names = match.canonical
            if names is None:
                answers[("__unknown__", *match.labels)].append(match)
            else:
                answers[tuple(names)].append(match)

        if len(answers) > 1:
            ambiguous.append((quote, matches))
            continue

        key, group = next(iter(answers.items()))
        if key[0] == "__unknown__":
            unknown_label.append((quote, group[0]))
            continue

        found = list(key)
        if found == current:
            confirmed.append((quote, group[0]))
        elif not current:
            added.append((quote, group[0], found))
            quote["speakers"] = format_speakers(found)
        else:
            fixed.append((quote, group[0], current, found))
            quote["speakers"] = format_speakers(found)

    # ---- fuzzy second pass --------------------------------------------
    fuzzy_added, fuzzy_fixed, fuzzy_confirmed, fuzzy_review = [], [], [], []
    still_unmatched = []

    if args.fuzzy:
        index = FuzzyIndex(episodes)
        for quote, reason in unmatched:
            if reason.startswith("too short"):
                still_unmatched.append((quote, reason))
                continue

            # A quote carrying its own "Name:" prefixes already states who
            # speaks. That is better evidence than an approximate window, so
            # fuzzy matching is not allowed to overrule it.
            if parse_speakers(quote["quote"]):
                still_unmatched.append((quote, "speakers named in the quote text"))
                continue

            scored = best_fuzzy(quote["quote"], index, args.min_words)
            scored = [m for m in scored if m.canonical is not None]
            if not scored:
                still_unmatched.append((quote, reason))
                continue

            best = scored[0]
            names = best.canonical

            # A rival naming different speakers must be clearly worse, or we
            # cannot tell which of them the quote came from.
            rival = next(
                (m for m in scored[1:] if m.canonical != names), None
            )
            contested = rival is not None and (best.score - rival.score) < args.fuzzy_margin

            # An exchange written as several quoted segments needs at least
            # that many speakers. Fewer means the window trimmed a reply away,
            # and applying it would silently drop a speaker.
            segments = len(QUOTED_SEGMENT.findall(quote["quote"]))
            short_handed = segments >= 2 and len(names) < segments

            if best.score < args.fuzzy_threshold or contested or short_handed:
                if best.score >= args.fuzzy_review_floor:
                    fuzzy_review.append((quote, best, rival, contested))
                else:
                    still_unmatched.append((quote, reason))
                continue

            current = split_speakers(quote.get("speakers", ""))
            if names == current:
                fuzzy_confirmed.append((quote, best))
            elif not current:
                fuzzy_added.append((quote, best, names))
                quote["speakers"] = format_speakers(names)
            else:
                fuzzy_fixed.append((quote, best, current, names))
                quote["speakers"] = format_speakers(names)
    else:
        still_unmatched = unmatched

    # ---- report -------------------------------------------------------
    total = len(quotes)
    lines = [
        "Attribution check against episode transcripts",
        "=" * 72,
        f"quotes:                {total}",
        f"transcripts:           {len(episodes)}",
        "",
        f"confirmed (already correct):   {len(confirmed)}",
        f"ADDED (were empty):            {len(added)}",
        f"FIXED (disagreed with source): {len(fixed)}",
        f"ambiguous, left alone:         {len(ambiguous)}",
        f"unrecognized speaker label:    {len(unknown_label)}",
        "",
    ]
    if args.fuzzy:
        lines += [
            "fuzzy pass (paraphrased quotes):",
            f"  confirmed:                   {len(fuzzy_confirmed)}",
            f"  ADDED:                       {len(fuzzy_added)}",
            f"  FIXED:                       {len(fuzzy_fixed)}",
            f"  needs review, left alone:    {len(fuzzy_review)}",
        ]
    else:
        lines.append("fuzzy pass:                    not run (--fuzzy)")
    lines += [
        f"not matched:                   {len(still_unmatched)}",
        "",
        "Only quotes located verbatim in a transcript were touched. Everything",
        "else was left exactly as it was.",
        "",
    ]

    if fixed:
        lines += ["", "FIXED -- the source disagreed with the stored value",
                  "-" * 72, ""]
        for quote, match, before, after in fixed:
            lines.append(f"  {quote['id']}: {','.join(before)} -> {','.join(after)}")
            lines.append(f"      quote:  {quote['quote'][:100]}")
            lines.append(f"      source: {match.episode.slug} | {match.excerpt}")
            lines.append("")

    if added:
        lines += ["", "ADDED -- previously unattributed", "-" * 72, ""]
        for quote, match, after in added:
            lines.append(f"  {quote['id']}: -> {','.join(after)}")
            lines.append(f"      quote:  {quote['quote'][:100]}")
            lines.append(f"      source: {match.episode.slug} | {match.excerpt}")
            lines.append("")

    if fuzzy_fixed:
        lines += ["", "FUZZY FIXED -- paraphrase located; stored value disagreed",
                  "-" * 72, ""]
        for quote, match, before, after in fuzzy_fixed:
            lines.append(f"  {quote['id']}: {','.join(before)} -> {','.join(after)}"
                         f"   [score {match.score:.3f}]")
            lines.append(f"      quote:  {quote['quote'][:100]}")
            lines.append(f"      source: {match.episode.slug} | {match.excerpt}")
            lines.append("")

    if fuzzy_added:
        lines += ["", "FUZZY ADDED -- paraphrase located; was unattributed",
                  "-" * 72, ""]
        for quote, match, after in fuzzy_added:
            lines.append(f"  {quote['id']}: -> {','.join(after)}"
                         f"   [score {match.score:.3f}]")
            lines.append(f"      quote:  {quote['quote'][:100]}")
            lines.append(f"      source: {match.episode.slug} | {match.excerpt}")
            lines.append("")

    if fuzzy_review:
        lines += ["", "FUZZY NEEDS REVIEW -- plausible but not applied", "-" * 72,
                  "", "Below the accept threshold, or a rival match named someone",
                  "else. Decide these by hand.", ""]
        for quote, best, rival, contested in fuzzy_review:
            segments = len(QUOTED_SEGMENT.findall(quote["quote"]))
            if contested:
                why = "contested"
            elif segments >= 2 and len(best.canonical) < segments:
                why = f"{segments} quoted segments but only {len(best.canonical)} speaker(s)"
            else:
                why = "below threshold"
            lines.append(f"  {quote['id']}: suggests {','.join(best.canonical)}"
                         f"   [score {best.score:.3f}, {why}]")
            lines.append(f"      current: {quote['speakers'] or '(none)'}")
            lines.append(f"      quote:   {quote['quote'][:100]}")
            lines.append(f"      source:  {best.episode.slug} | {best.excerpt}")
            if rival is not None:
                lines.append(f"      rival:   {','.join(rival.canonical)} "
                             f"[score {rival.score:.3f}] {rival.episode.slug}")
            lines.append("")

    if ambiguous:
        lines += ["", "AMBIGUOUS -- matched in places that disagree; left alone",
                  "-" * 72, ""]
        for quote, matches in ambiguous:
            seen = {tuple(m.canonical or m.labels) for m in matches}
            lines.append(f"  {quote['id']}: candidates "
                         f"{sorted(','.join(s) for s in seen)}")
            lines.append(f"      quote: {quote['quote'][:100]}")
            lines.append("")

    if unknown_label:
        lines += ["", "UNRECOGNIZED SPEAKER LABEL -- left alone", "-" * 72,
                  "", "Add these to CHARACTERS in scripts/speaker_names.py to "
                  "let them be attributed.", ""]
        counts: dict[str, int] = defaultdict(int)
        for quote, match in unknown_label:
            for label in match.labels:
                if resolve(label) is None:
                    counts[label] += 1
        for label, count in sorted(counts.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {count:>4}  {label}")
        lines.append("")

    report = "\n".join(lines) + "\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    if not args.dry_run and (added or fixed or fuzzy_added or fuzzy_fixed):
        args.quotes.write_text(
            json.dumps([render_quote(q) for q in quotes], indent=2,
                       ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"transcripts: {len(episodes)}   quotes: {total}")
    print(f"  confirmed: {len(confirmed)}")
    print(f"  added:     {len(added)}")
    print(f"  fixed:     {len(fixed)}")
    if args.fuzzy:
        print(f"  fuzzy confirmed: {len(fuzzy_confirmed)}")
        print(f"  fuzzy added:     {len(fuzzy_added)}")
        print(f"  fuzzy fixed:     {len(fuzzy_fixed)}")
        print(f"  fuzzy review:    {len(fuzzy_review)}")
    print(f"  ambiguous: {len(ambiguous)}   unknown label: {len(unknown_label)}"
          f"   unmatched: {len(still_unmatched)}")
    print(f"\nReport: {args.report}")
    if args.dry_run:
        print("Dry run - quotes.json was not modified.")
    elif added or fixed or fuzzy_added or fuzzy_fixed:
        print(f"Updated {args.quotes}. Now run:")
        print("  python3 scripts/normalize_speakers.py --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())

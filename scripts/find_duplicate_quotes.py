#!/usr/bin/env python3
"""Find near-duplicate quotes in quotes.json and emit a reviewable patch.

The quote database was seeded from years of tweets, so the same line often
appears several times: truncated versions, paraphrases, differing censorship
("[bleep]" vs "__"), and the same exchange with or without its speaker prefixes.

This script finds those groups and writes two files:

* a **report** explaining every group -- why it matched and what would change
* a **patch** (unified diff) that removes the duplicates from quotes.json

Nothing is modified. Read the report, check the patch, then apply it yourself:

    python3 scripts/find_duplicate_quotes.py
    less build/duplicates-report.txt
    git apply build/duplicates.patch
    python3 scripts/normalize_speakers.py --check

Matching works on a normalized form of the quote text: lowercased, speaker
prefixes removed, censorship markers collapsed, punctuation and whitespace
flattened. Two quotes are considered duplicates when either

1. their similarity ratio (difflib.SequenceMatcher) meets --threshold, or
2. one is wholly contained in the other and the shorter has at least
   --containment-min-tokens words -- this catches the truncated variants that a
   plain ratio misses, since a short quote and its long expansion score poorly.

Groups are transitive: if A matches B and B matches C, all three are one group.

The surviving quote in a group is chosen by, in order: longest text, has
speakers, has an image, lowest id. It inherits imageUrl, speakers or context
that it lacks and a duplicate has, so merging does not quietly drop data.

Merging never overwrites a value the keeper already has, and never unions
disagreeing speaker lists -- a shorter excerpt that names a different character
usually means one of the two attributions is wrong, and silently combining them
would launder the error into the surviving record. Those cases, and any image
that a merge would discard, are listed under CONFLICTS at the top of the report
so you can settle them by hand.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from speaker_names import (  # noqa: E402
    _ALIAS_PATTERN,
    format_speakers,
    split_speakers,
)

REPO_ROOT = Path(__file__).parent.parent
QUOTES_PATH = REPO_ROOT / "app" / "data" / "quotes.json"

DEFAULT_PATCH = REPO_ROOT / "build" / "duplicates.patch"
DEFAULT_REPORT = REPO_ROOT / "build" / "duplicates-report.txt"

# Key order used when rewriting records, matching normalize_speakers.py.
KEY_ORDER = ["id", "quote", "speakers", "imageUrl"]

# Any run of censorship characters, so "[bleep]", "__", "****" and "f**k" all
# reduce to the same token and stop masking real duplicates.
_CENSOR_PATTERN = re.compile(r"\[bleep\]|_{2,}|\*{2,}|\*+(?=[a-z])|(?<=[a-z])\*+", re.I)


def normalize(text: str) -> str:
    """Reduce a quote to the form used for comparison."""
    text = _ALIAS_PATTERN.sub(" ", text or "")     # drop "Michael:" prefixes
    text = _CENSOR_PATTERN.sub(" CENSORED ", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(normalized: str) -> set[str]:
    return set(normalized.split())


class Group:
    """A set of quote ids believed to be the same quote."""

    def __init__(self, members: list[dict], reasons: dict[tuple[str, str], str]):
        self.members = members
        self.reasons = reasons

    @property
    def keeper(self) -> dict:
        """The record to survive: longest text, then speakers, then image, then id.

        Text completeness comes first on purpose. An earlier ordering preferred
        whichever record had an image, which kept "How do we filter out the
        teases?" and threw away the version carrying the answer. An image is
        inheritable and a lost punchline is not, so the fullest text wins and
        the image follows it.
        """
        def rank(q: dict):
            return (
                -len(q["quote"]),
                0 if q.get("speakers") else 1,
                0 if q.get("imageUrl") else 1,
                id_sort_key(q["id"]),
            )

        return sorted(self.members, key=rank)[0]

    @property
    def removed(self) -> list[dict]:
        keeper_id = self.keeper["id"]
        return [q for q in self.members if q["id"] != keeper_id]


def id_sort_key(quote_id: str) -> tuple[int, str]:
    match = re.match(r"^quote-(\d+)$", quote_id)
    return (int(match.group(1)), "") if match else (10**9, quote_id)


def find_groups(quotes: list[dict], threshold: float, min_tokens: int) -> list[Group]:
    """Cluster quotes into transitive groups of near-duplicates."""
    normalized = {q["id"]: normalize(q["quote"]) for q in quotes}
    token_sets = {q["id"]: tokens(normalized[q["id"]]) for q in quotes}

    parent: dict[str, str] = {q["id"]: q["id"] for q in quotes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    reasons: dict[tuple[str, str], str] = {}
    candidates = [q for q in quotes if normalized[q["id"]]]

    for i, left in enumerate(candidates):
        lid = left["id"]
        ltext, ltokens = normalized[lid], token_sets[lid]

        for right in candidates[i + 1:]:
            rid = right["id"]
            rtext, rtokens = normalized[rid], token_sets[rid]

            # Cheap prefilter: without meaningful word overlap there is no way
            # to reach the threshold, and this skips almost every pair.
            overlap = len(ltokens & rtokens)
            if overlap < 2:
                continue
            if overlap / max(len(ltokens), len(rtokens)) < 0.4:
                continue

            reason = None
            shorter, longer = sorted((ltext, rtext), key=len)
            if len(shorter.split()) >= min_tokens and shorter in longer:
                reason = f"contained ({len(shorter.split())} words inside {len(longer.split())})"
            else:
                ratio = difflib.SequenceMatcher(None, ltext, rtext).ratio()
                if ratio >= threshold:
                    reason = f"similarity {ratio:.3f}"

            if reason:
                union(lid, rid)
                reasons[(lid, rid)] = reason

    clustered: dict[str, list[dict]] = {}
    for quote in candidates:
        clustered.setdefault(find(quote["id"]), []).append(quote)

    groups = []
    for members in clustered.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda q: id_sort_key(q["id"]))
        ids = {q["id"] for q in members}
        group_reasons = {
            pair: why for pair, why in reasons.items()
            if pair[0] in ids and pair[1] in ids
        }
        groups.append(Group(members, group_reasons))

    groups.sort(key=lambda g: id_sort_key(g.keeper["id"]))
    return groups


def merge_into_keeper(group: Group) -> tuple[dict, list[str], list[str]]:
    """Return the keeper with inherited fields, what it gained, and conflicts."""
    keeper = dict(group.keeper)
    notes: list[str] = []
    conflicts: list[str] = []

    for field in ("imageUrl", "context"):
        if keeper.get(field):
            # The keeper already has one; anything different is dropped on the
            # floor by the merge, which is worth saying out loud.
            for other in group.removed:
                if other.get(field) and other[field] != keeper[field]:
                    conflicts.append(
                        f"{other['id']} has a different {field} "
                        f"({other[field]}) that this merge DISCARDS"
                    )
            continue
        for other in group.removed:
            if other.get(field):
                keeper[field] = other[field]
                notes.append(f"inherited {field} from {other['id']}")
                break

    keeper_names = split_speakers(keeper.get("speakers", ""))
    if keeper_names:
        # Do not union. A duplicate naming someone else means one of the two
        # attributions is wrong; combining them would hide that.
        for other in group.removed:
            other_names = split_speakers(other.get("speakers", ""))
            extra = [n for n in other_names if n not in keeper_names]
            if extra:
                conflicts.append(
                    f"{other['id']} names {', '.join(extra)} but "
                    f"{keeper['id']} does not -- check which is right"
                )
    else:
        for other in group.removed:
            for name in split_speakers(other.get("speakers", "")):
                if name not in keeper_names:
                    keeper_names.append(name)
                    notes.append(f"inherited speaker {name!r} from {other['id']}")
    keeper["speakers"] = format_speakers(keeper_names)

    ordered = {k: keeper[k] for k in KEY_ORDER if k in keeper}
    ordered.update({k: v for k, v in keeper.items() if k not in ordered})
    return ordered, notes, conflicts


def render_json(quotes: list[dict]) -> str:
    """Serialize exactly the way normalize_speakers.py does, so the patch is minimal."""
    return json.dumps(quotes, indent=2, ensure_ascii=False) + "\n"


def build_report(groups: list[Group], merges: dict[str, list[str]],
                 conflicts: dict[str, list[str]],
                 threshold: float, min_tokens: int, total: int) -> str:
    removed_total = sum(len(g.removed) for g in groups)
    group_number = {g.keeper["id"]: n for n, g in enumerate(groups, 1)}
    lines = [
        "Duplicate quote report",
        "=" * 70,
        f"quotes scanned:        {total}",
        f"duplicate groups:      {len(groups)}",
        f"quotes to remove:      {removed_total}",
        f"quotes remaining:      {total - removed_total}",
        f"groups with conflicts: {len(conflicts)}",
        f"ratio threshold:       {threshold}",
        f"containment min words: {min_tokens}",
        "",
        "Every group below collapses to one KEEP record. Check that the members",
        "really are the same line before applying the patch -- a callback that is",
        "deliberately repeated in different episodes is not a duplicate.",
        "",
    ]

    if conflicts:
        lines += [
            "CONFLICTS -- read these first",
            "-" * 70,
            "The merge could not reconcile these on its own. Settling them is a",
            "manual edit; the patch leaves the keeper's existing value alone.",
            "",
        ]
        for keeper_id, items in sorted(conflicts.items(),
                                       key=lambda kv: id_sort_key(kv[0])):
            lines.append(f"  Group {group_number[keeper_id]} ({keeper_id}):")
            for item in items:
                lines.append(f"    - {item}")
            lines.append("")
        lines.append("")

    for n, group in enumerate(groups, 1):
        keeper_id = group.keeper["id"]
        lines.append("-" * 70)
        lines.append(f"Group {n}  ({len(group.members)} quotes -> 1)")
        lines.append("")
        for quote in group.members:
            mark = "KEEP  " if quote["id"] == keeper_id else "REMOVE"
            lines.append(f"  {mark} {quote['id']}")
            lines.append(f"         text:     {quote['quote']}")
            if quote.get("speakers"):
                lines.append(f"         speakers: {quote['speakers']}")
            if quote.get("imageUrl"):
                lines.append(f"         image:    {quote['imageUrl']}")
            lines.append("")
        if group.reasons:
            lines.append("         matched because:")
            for (a, b), why in sorted(group.reasons.items()):
                lines.append(f"           {a} ~ {b}: {why}")
            lines.append("")
        if merges.get(keeper_id):
            lines.append(f"         {keeper_id} gains:")
            for note in merges[keeper_id]:
                lines.append(f"           {note}")
            lines.append("")
        if conflicts.get(keeper_id):
            lines.append("         CONFLICT:")
            for item in conflicts[keeper_id]:
                lines.append(f"           {item}")
            lines.append("")

    if not groups:
        lines.append("No duplicates found at these settings.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--quotes", type=Path, default=QUOTES_PATH,
                        help="quotes file to scan (default: app/data/quotes.json)")
    parser.add_argument("--patch", type=Path, default=DEFAULT_PATCH,
                        help="where to write the unified diff")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT,
                        help="where to write the human-readable report")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="similarity ratio to call a pair duplicate (default: 0.85)")
    parser.add_argument("--containment-min-tokens", type=int, default=6, metavar="N",
                        help="a contained quote must have at least N words (default: 6)")
    parser.add_argument("--stdout", action="store_true",
                        help="print the report instead of writing files")
    args = parser.parse_args()

    quotes = json.loads(args.quotes.read_text(encoding="utf-8"))
    groups = find_groups(quotes, args.threshold, args.containment_min_tokens)

    merges: dict[str, list[str]] = {}
    conflicts: dict[str, list[str]] = {}
    replacements: dict[str, dict] = {}
    drop: set[str] = set()
    for group in groups:
        keeper, notes, group_conflicts = merge_into_keeper(group)
        replacements[keeper["id"]] = keeper
        if notes:
            merges[keeper["id"]] = notes
        if group_conflicts:
            conflicts[keeper["id"]] = group_conflicts
        drop.update(q["id"] for q in group.removed)

    deduped = [
        replacements.get(q["id"], q)
        for q in quotes
        if q["id"] not in drop
    ]

    report = build_report(groups, merges, conflicts, args.threshold,
                          args.containment_min_tokens, len(quotes))

    if args.stdout:
        print(report, end="")
        return 0

    rel = args.quotes.relative_to(REPO_ROOT).as_posix()
    diff = difflib.unified_diff(
        render_json(quotes).splitlines(keepends=True),
        render_json(deduped).splitlines(keepends=True),
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
        n=3,
    )
    patch = "".join(diff)

    for path in (args.patch, args.report):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    args.patch.write_text(patch, encoding="utf-8")

    removed = sum(len(g.removed) for g in groups)
    print(f"{len(groups)} duplicate groups covering {removed} removable quotes "
          f"({len(quotes)} -> {len(deduped)}).")
    if conflicts:
        print(f"{len(conflicts)} group(s) need a manual decision - see CONFLICTS "
              f"at the top of the report.")
    print(f"  report: {args.report.relative_to(REPO_ROOT)}")
    print(f"  patch:  {args.patch.relative_to(REPO_ROOT)}")
    if patch:
        print("\nReview the report, then apply with:")
        print(f"  git apply {args.patch.relative_to(REPO_ROOT)}")
        print("  python3 scripts/normalize_speakers.py --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())

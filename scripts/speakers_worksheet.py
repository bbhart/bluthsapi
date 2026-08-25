#!/usr/bin/env python3
"""Export unattributed quotes to a plain text worksheet, and merge it back.

Filling in speakers is a reading job, not a coding job, so it should not mean
editing JSON. This exports the quotes that still have no `speakers` value into
a flat file with a blank line to type on, then reads that file back.

    python3 scripts/speakers_worksheet.py export      # writes the worksheet
    # ... edit work/unattributed.txt in any editor ...
    python3 scripts/speakers_worksheet.py apply --dry-run
    python3 scripts/speakers_worksheet.py apply

The worksheet looks like this, one block per quote:

    --- quote-31
    I think I might have someone who's going to "circumvrent" the law.
    speakers:

Type the name after `speakers:` and save. Several speakers are separated by
commas, in the order they speak:

    speakers: Lucille,Michael

Leave a block blank to skip it; blanks are simply ignored, so the worksheet can
be filled in over several sittings. Writing `DELETE` on the speakers line drops
that quote from quotes.json instead.

Names must be canonical. The worksheet lists every valid name at the top for
reference, and `apply` refuses to write anything if it finds a name it does not
recognize -- one wrong spelling stops the merge rather than being silently
dropped or quietly creating a second spelling of an existing character.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from speaker_names import CHARACTERS, resolve, split_speakers  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
QUOTES_PATH = REPO_ROOT / "app" / "data" / "quotes.json"
DEFAULT_WORKSHEET = REPO_ROOT / "work" / "unattributed.txt"

KEY_ORDER = ["id", "quote", "speakers", "imageUrl"]

BLOCK_START = re.compile(r"^--- (quote-\S+)\s*$")
SPEAKERS_LINE = re.compile(r"^speakers:\s*(.*)$")

DELETE_MARKER = "DELETE"


def wrap(text: str, width: int = 96, indent: str = "") -> list[str]:
    """Soft-wrap for readability. Never parsed back, only the id and speakers are."""
    words = text.split()
    lines, current = [], indent
    for word in words:
        candidate = f"{current} {word}".rstrip() if current.strip() else indent + word
        if len(candidate) > width and current.strip():
            lines.append(current)
            current = indent + word
        else:
            current = candidate
    if current.strip():
        lines.append(current)
    return lines or [indent]


def render_worksheet(quotes: list[dict]) -> str:
    names = sorted(CHARACTERS, key=str.lower)
    header = [
        "# Speaker worksheet",
        "#",
        f"# {len(quotes)} quotes with no speaker recorded.",
        "#",
        "# Type the name after `speakers:` on the line below each quote.",
        "# Several speakers: comma separated, in the order they speak, no space",
        "# after the comma.   e.g.   speakers: Lucille,Michael",
        "#",
        "# Leave a block blank to skip it - blanks are ignored, so you can fill",
        "# this in over several sittings and apply it as often as you like.",
        f"# Write `{DELETE_MARKER}` on the speakers line to drop that quote instead.",
        "#",
        "# Lines starting with # are ignored. The quote text is for reading only;",
        "# editing it here changes nothing.",
        "#",
        "# Names must be spelled exactly as below. Anything else stops the merge.",
        "# To add a character who is not listed, add them to CHARACTERS in",
        "# scripts/speaker_names.py first.",
        "#",
    ]
    for line in wrap("  ".join(names), width=92, indent="#   "):
        header.append(line)
    header += ["#", ""]

    blocks = []
    for quote in quotes:
        block = [f"--- {quote['id']}"]
        block += wrap(quote["quote"])
        if quote.get("imageUrl"):
            block.append(f"# (has image: {quote['imageUrl']})")
        block += ["speakers:", ""]
        blocks.append("\n".join(block))

    return "\n".join(header) + "\n".join(blocks) + "\n"


def parse_worksheet(text: str) -> tuple[dict[str, str], list[str]]:
    """Return {quote_id: speakers_value} for filled blocks, plus any problems."""
    filled: dict[str, str] = {}
    problems: list[str] = []
    current: str | None = None
    seen_speakers_line = False

    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if line.startswith("#"):
            continue

        start = BLOCK_START.match(line)
        if start:
            if current is not None and not seen_speakers_line:
                problems.append(f"{current}: block has no `speakers:` line")
            current = start.group(1)
            seen_speakers_line = False
            continue

        match = SPEAKERS_LINE.match(line)
        if match:
            if current is None:
                problems.append(f"line {number}: `speakers:` outside any block")
                continue
            if seen_speakers_line:
                problems.append(f"{current}: more than one `speakers:` line")
                continue
            seen_speakers_line = True
            value = match.group(1).strip()
            if value:
                filled[current] = value

    if current is not None and not seen_speakers_line:
        problems.append(f"{current}: block has no `speakers:` line")

    return filled, problems


def canonicalize(value: str) -> tuple[str | None, list[str]]:
    """Return the canonical form of a speakers value, plus unrecognized names."""
    if value.strip().upper() == DELETE_MARKER:
        return DELETE_MARKER, []
    names, bad = [], []
    for raw in split_speakers(value):
        name = resolve(raw)
        if name is None:
            bad.append(raw)
        elif name not in names:
            names.append(name)
    return (",".join(names) if names else None), bad


def render_quote(quote: dict) -> dict:
    ordered = {k: quote[k] for k in KEY_ORDER if k in quote}
    ordered.update({k: v for k, v in quote.items() if k not in ordered})
    return ordered


def cmd_export(args) -> int:
    quotes = json.loads(args.quotes.read_text(encoding="utf-8"))
    unattributed = [q for q in quotes if not q.get("speakers")]
    if not unattributed:
        print("Nothing unattributed - no worksheet written.")
        return 0

    args.worksheet.parent.mkdir(parents=True, exist_ok=True)
    if args.worksheet.exists() and not args.force:
        print(f"ERROR: {args.worksheet} already exists.\n"
              "Apply it first, or pass --force to overwrite your edits.",
              file=sys.stderr)
        return 1

    args.worksheet.write_text(render_worksheet(unattributed), encoding="utf-8")
    print(f"Wrote {args.worksheet} with {len(unattributed)} quotes to fill in.")
    print("\nEdit it, then:")
    print("  python3 scripts/speakers_worksheet.py apply --dry-run")
    return 0


def cmd_apply(args) -> int:
    if not args.worksheet.exists():
        print(f"ERROR: no worksheet at {args.worksheet}. Run `export` first.",
              file=sys.stderr)
        return 1

    filled, problems = parse_worksheet(args.worksheet.read_text(encoding="utf-8"))
    quotes = json.loads(args.quotes.read_text(encoding="utf-8"))
    by_id = {q["id"]: q for q in quotes}

    updates: dict[str, str] = {}
    deletions: list[str] = []
    for quote_id, value in filled.items():
        if quote_id not in by_id:
            problems.append(f"{quote_id}: not in quotes.json")
            continue
        canonical, bad = canonicalize(value)
        for name in bad:
            problems.append(
                f"{quote_id}: {name!r} is not a canonical character name"
            )
        if bad:
            continue
        if canonical == DELETE_MARKER:
            deletions.append(quote_id)
        elif canonical:
            updates[quote_id] = canonical

    # Nothing is written while a single name is unrecognized. Applying the good
    # rows and skipping the rest would leave the worksheet and the data
    # disagreeing, with no sign of which rows were dropped.
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        print(f"\n{len(problems)} problem(s); nothing was written.\n"
              "Fix the worksheet, or add the character to CHARACTERS in "
              "scripts/speaker_names.py.", file=sys.stderr)
        return 1

    if not updates and not deletions:
        print("Worksheet has no filled-in blocks yet - nothing to do.")
        return 0

    for quote_id, value in sorted(updates.items()):
        was = by_id[quote_id].get("speakers") or "(none)"
        print(f"  {quote_id:<14} {was:<22} -> {value}")
    for quote_id in sorted(deletions):
        print(f"  {quote_id:<14} DELETE")

    print(f"\n{len(updates)} attributed, {len(deletions)} deleted.")

    if args.dry_run:
        print("Dry run - quotes.json was not modified.")
        return 0

    for quote_id, value in updates.items():
        by_id[quote_id]["speakers"] = value
    remaining = [render_quote(q) for q in quotes if q["id"] not in set(deletions)]

    args.quotes.write_text(
        json.dumps(remaining, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Updated {args.quotes} ({len(remaining)} quotes).")
    print("\nNow run:")
    print("  python3 scripts/normalize_speakers.py")
    print("  python3 scripts/normalize_speakers.py --check")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--quotes", type=Path, default=QUOTES_PATH)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET)
    sub = parser.add_subparsers(dest="command")

    export = sub.add_parser("export", help="write the worksheet")
    export.add_argument("--force", action="store_true",
                        help="overwrite an existing worksheet")
    export.set_defaults(func=cmd_export)

    apply_cmd = sub.add_parser("apply", help="merge the worksheet back")
    apply_cmd.add_argument("--dry-run", action="store_true",
                           help="show what would change, write nothing")
    apply_cmd.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

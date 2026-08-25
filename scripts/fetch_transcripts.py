#!/usr/bin/env python3
"""Fetch episode transcripts from the Arrested Development Fandom wiki.

The transcripts are a reference for checking who actually says a line, which is
what issue #21 needs: most `speakers` values in quotes.json were inferred rather
than read off the source, and some are wrong.

    python3 scripts/fetch_transcripts.py                  # season one
    python3 scripts/fetch_transcripts.py --all-seasons
    python3 scripts/fetch_transcripts.py --category "Category:Season Two Transcripts"

Output goes to work/transcripts/ (gitignored -- see the note below), one .txt
per episode plus a manifest.json recording the source URL, revision id and
fetch time for every page.

This uses the MediaWiki API rather than scraping rendered HTML: it is the
interface the wiki offers for exactly this, it returns clean wikitext, and it
does not pull down page furniture. Requests are sequential with a delay between
them; there is no reason to hammer a fan wiki for a few dozen pages.

A NOTE ON THE CONTENT
---------------------
These are full transcripts of copyrighted television episodes. The wiki text is
CC-BY-SA, but the underlying dialogue is not the wiki's to relicense. Keeping a
local copy to check facts against is one thing; committing it to a public
repository would be republishing someone else's work at scale. The output
directory is gitignored on purpose -- please leave it that way.
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_OUT = REPO_ROOT / "work" / "transcripts"

API = "https://arresteddevelopment.fandom.com/api.php"
PAGE_BASE = "https://arresteddevelopment.fandom.com/wiki/"

USER_AGENT = (
    "bluthsapi-transcript-fetch/1.0 "
    "(https://github.com/bbhart/bluthsapi; one-off reference fetch)"
)

ROOT_CATEGORY = "Category:Transcripts"
DEFAULT_CATEGORY = "Category:Season One Transcripts"


def api_get(params: dict, delay: float) -> dict:
    """One API call, with the courtesy delay applied before returning."""
    query = urllib.parse.urlencode({**params, "format": "json"})
    request = urllib.request.Request(
        f"{API}?{query}", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if "error" in payload:
        raise RuntimeError(f"API error: {payload['error']}")

    time.sleep(delay)
    return payload


def category_members(category: str, delay: float, subcats: bool = False) -> list[dict]:
    """Every member of a category, following continuation.

    Pages by default; ``subcats=True`` returns the subcategories instead.
    """
    members: list[dict] = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": "200",
        "cmtype": "subcat" if subcats else "page",
    }
    if not subcats:
        params["cmnamespace"] = "0"
    while True:
        payload = api_get(params, delay)
        members.extend(payload["query"]["categorymembers"])
        if "continue" not in payload:
            return members
        params.update(payload["continue"])


def discover_categories(root: str, delay: float) -> list[str]:
    """Subcategories of ``root``, so seasons are not hardcoded."""
    found = [m["title"] for m in category_members(root, delay, subcats=True)]
    return sorted(found)


def fetch_page(title: str, delay: float) -> tuple[str, int]:
    """Return a page's wikitext and revision id."""
    payload = api_get(
        {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content|ids",
            "rvslots": "main",
            "titles": title,
        },
        delay,
    )
    page = next(iter(payload["query"]["pages"].values()))
    if "revisions" not in page:
        raise RuntimeError(f"no content for {title!r}")
    revision = page["revisions"][0]
    return revision["slots"]["main"]["*"], revision["revid"]


def strip_templates(text: str) -> str:
    """Remove {{...}} blocks, honouring nesting."""
    out: list[str] = []
    depth = 0
    i = 0
    while i < len(text):
        if text.startswith("{{", i):
            depth += 1
            i += 2
        elif text.startswith("}}", i) and depth:
            depth -= 1
            i += 2
        else:
            if not depth:
                out.append(text[i])
            i += 1
    return "".join(out)


def wikitext_to_text(text: str) -> str:
    """Flatten wikitext to the readable transcript underneath it."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = strip_templates(text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)

    # [[Target|Shown]] -> Shown, [[Target]] -> Target
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)

    text = re.sub(r"'{2,}", "", text)                 # bold / italic markers
    text = re.sub(r"^=+\s*(.*?)\s*=+$", r"\1", text, flags=re.M)   # headings
    text = re.sub(r"^[*#:;]+\s*", "", text, flags=re.M)            # list markers
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)

    lines = [line.rstrip() for line in text.splitlines()]
    cleaned: list[str] = []
    for line in lines:
        if not line.strip() and cleaned and not cleaned[-1].strip():
            continue          # collapse runs of blank lines
        cleaned.append(line.strip())
    return "\n".join(cleaned).strip() + "\n"


def slugify(title: str) -> str:
    name = title.removeprefix("Transcript of ").strip()
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return slug or "untitled"


def speaker_line_count(text: str) -> int:
    """Rough count of "NAME: dialogue" lines, as a sanity signal."""
    return sum(
        1 for line in text.splitlines()
        if re.match(r"^[A-Z][A-Za-z .'-]{1,30}:\s+\S", line)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--category", action="append", metavar="NAME",
                        help="wiki category to fetch (repeatable); "
                             "default: Category:Season One Transcripts")
    parser.add_argument("--all-seasons", action="store_true",
                        help=f"discover and fetch every subcategory of {ROOT_CATEGORY}")
    parser.add_argument("--root-category", default=ROOT_CATEGORY, metavar="NAME",
                        help=f"category to discover subcategories under "
                             f"(default: {ROOT_CATEGORY})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"output directory (default: {DEFAULT_OUT})")
    parser.add_argument("--delay", type=float, default=1.0, metavar="SECONDS",
                        help="pause between API calls (default: 1.0)")
    parser.add_argument("--keep-wikitext", action="store_true",
                        help="also save the raw wikitext alongside the .txt")
    parser.add_argument("--limit", type=int, metavar="N",
                        help="stop after N pages (for a quick trial run)")
    args = parser.parse_args()

    if args.all_seasons:
        categories = discover_categories(args.root_category, args.delay)
        if not categories:
            print(f"ERROR: no subcategories under {args.root_category}", file=sys.stderr)
            return 1
        print(f"{args.root_category}: {len(categories)} subcategories")
    elif args.category:
        categories = args.category
    else:
        categories = [DEFAULT_CATEGORY]

    args.out.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out / "manifest.json"
    manifest = {
        "source": "Arrested Development Wiki (Fandom)",
        "api": API,
        "license": "Wiki text is CC-BY-SA; the underlying episode dialogue is "
                   "not the wiki's to relicense. Local reference copy only -- "
                   "do not commit or redistribute.",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "categories": categories,
        "pages": [],
    }

    fetched = 0
    for category in categories:
        try:
            members = category_members(category, args.delay)
        except Exception as exc:                      # noqa: BLE001
            print(f"WARNING: {category}: {exc}", file=sys.stderr)
            continue

        if not members:
            print(f"WARNING: {category}: no pages found", file=sys.stderr)
            continue

        print(f"{category}: {len(members)} pages")
        for member in sorted(members, key=lambda m: m["title"]):
            if args.limit is not None and fetched >= args.limit:
                break

            title = member["title"]
            try:
                wikitext, revid = fetch_page(title, args.delay)
            except Exception as exc:                  # noqa: BLE001
                print(f"  FAILED {title}: {exc}", file=sys.stderr)
                continue

            text = wikitext_to_text(wikitext)
            slug = slugify(title)
            path = args.out / f"{slug}.txt"
            path.write_text(text, encoding="utf-8")
            if args.keep_wikitext:
                (args.out / f"{slug}.wiki").write_text(wikitext, encoding="utf-8")

            lines = speaker_line_count(text)
            manifest["pages"].append({
                "title": title,
                "slug": slug,
                "file": path.name,
                "pageid": member["pageid"],
                "revid": revid,
                "url": PAGE_BASE + urllib.parse.quote(title.replace(" ", "_")),
                "chars": len(text),
                "speaker_lines": lines,
            })
            fetched += 1
            flag = "" if lines else "   <- no speaker lines, check this one"
            print(f"  {slug:<28} {lines:>4} speaker lines{flag}")

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    total_lines = sum(p["speaker_lines"] for p in manifest["pages"])
    print(f"\nSaved {fetched} transcripts to {args.out} "
          f"({total_lines:,} speaker lines total).")
    print(f"Manifest: {manifest_path}")
    if not fetched:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

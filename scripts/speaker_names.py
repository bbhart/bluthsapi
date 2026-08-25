"""Canonical character names for Arrested Development quotes.

Quotes record speakers as a single comma-separated string (see
``docs/plans/2026-08-25-speakers-field-design.md``). Every name in that string
must be one of the canonical names registered here.

Short forms are canonical where they are unambiguous and already conventional.
Full names are used only where the short form collides with another character
or is not how the character is known. ``Lucille`` means Lucille Bluth; Lucille
Austero is always written out.
"""

import re
import unicodedata

# Canonical name -> additional aliases that should resolve to it.
# The canonical name itself is always an alias and need not be repeated.
CHARACTERS: dict[str, list[str]] = {
    # Bluth family
    "Michael": ["Michael Bluth", "Young Michael"],
    "Lucille": ["Lucille Bluth", "Mom", "Young Lucille"],
    "George Sr.": ["George", "George Sr", "George, Sr.", "George, Sr",
                   "George Bluth", "George Bluth Sr.", "George Bluth Sr",
                   "Father B"],
    "GOB": ["Gob", "G.O.B.", "G.O.B", "George Oscar Bluth", "Gob Bluth",
            "Young G.O.B.", "Young Gob"],
    "Buster": ["Buster Bluth", "Byron Bluth", "Young Buster"],
    "Lindsay": ["Lindsay Bluth", "Lindsay Funke", "Lindsay Bluth Funke"],
    "Tobias": ["Tobias Funke", "Dr. Funke", "Mrs. Featherbottom"],
    "George Michael": ["George Michael Bluth", "Mr. Manager"],
    "Maeby": ["Maeby Funke", "Mae Funke", "Surely Funke",
              "Maeby as Shaman Sheman"],
    "Oscar": ["Oscar Bluth", "Uncle Oscar"],
    "Annyong": ["Hel-loh", "Annyong Bluth"],

    # Recurring
    "Ann": ["Ann Veal", "Egg", "Bland"],
    "Barry Zuckerkorn": ["Barry", "Young Barry"],
    "Bob Loblaw": ["Loblaw"],
    "Carl Weathers": [],
    "Cindy Lightballoon": ["Cindi Lightballoon"],
    "Gene Parmesan": [],
    "Ice": [],
    "Jessie": ["Jessie Bowers"],
    "John Beard": [],
    "Kitty": ["Kitty Sanchez"],
    "Larry Middleman": ["Larry", "Larry the surrogate"],
    "Lucille Austero": ["Lucille 2", "Lucille Two"],
    "Lupe": [],
    "Marta": ["Marta Estrella"],
    "Mort Meyers": ["Mort"],
    "Narrator": ["Ron Howard"],
    "Reverend Veal": ["Veal", "Rev. Veal", "Rev Veal", "Pastor Veal"],
    "Rita": ["Rita Leeds", "Mr. F"],
    "Roger Danish": [],
    "Sally Sitwell": [],
    "Stan Sitwell": [],
    "Starla": [],
    "T-Bone": ["T Bone", "TBone"],
    "Steve Holt": [],
    "Mrs. Veal": [],
    "Terry Veal": [],
    "Tony Wonder": [],
    "Wayne Jarvis": ["Wayne"],
    "White Power Bill": [],

    # Further recurring characters, taken from the episode transcripts.
    "Adelaide": [],
    "Andy Richter": [],
    "Argyle Austero": ["Argyle"],
    "Beth Baerly": [],
    "Cal Cullen": [],
    "Carlos": [],
    "Colonel Smalls": [],
    "DeBrie Bardeaux": ["DeBrie"],
    "Detective Munch": [],
    "Donnie": [],
    "Doug Fleer": [],
    "Dr. Farmer": [],
    "Dr. Gunty": [],
    "Dr. Norman": ["Doctor Norman"],
    "Emmett": [],
    "Father Marsala": [],
    "Frank Wrench": [],
    "Herb Zuckerkorn": [],
    "Herbert Love": [],
    "Ira Gilligan": [],
    "J. Walter Weatherman": ["Walter Weatherman"],
    "James Carr": [],
    "Jan Eagleman": [],
    "Johnny Bark": [],
    "Judge Lionel Ping": ["Judge Ping"],
    "Judge Reinhold": [],
    "Loretta": [],
    "Maggie Lizer": ["Maggie"],
    "Mark Cherry": [],
    "Marky Bark": [],
    "Nellie": [],
    "Officer Carter": [],
    "Officer Taylor": [],
    "Ophelia Love": [],
    "P-Hound": [],
    "Perfecto Telles": [],
    "Phillip Litt": [],
    "Rebel Alley": [],
    "Richard Shaw": [],
    "Sheila": [],
    "Trevor": [],
    "Trisha Thoon": [],
    "Uncle Jack": ["Jack Dorso"],
    "Warden Gentiles": ["Warren Gentles"],

    # Generic / unnamed
    "Waitress": [],
    "Doctor": ["Dr. Fishman", "Fishman"],
}


def _fold(name: str) -> str:
    """Normalize a name for lookup: strip accents, punctuation, and case."""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", stripped.lower())


def _build_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for canonical, aliases in CHARACTERS.items():
        for alias in [canonical, *aliases]:
            key = _fold(alias)
            existing = index.get(key)
            if existing is not None and existing != canonical:
                raise ValueError(
                    f"Alias {alias!r} maps to both {existing!r} and {canonical!r}"
                )
            index[key] = canonical
    return index


ALIAS_INDEX: dict[str, str] = _build_alias_index()

# Longest aliases first so "George Michael:" is not read as "George".
_ALIAS_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])("
    + "|".join(
        re.escape(alias)
        for alias in sorted(
            {a for c, al in CHARACTERS.items() for a in [c, *al]},
            key=len,
            reverse=True,
        )
    )
    + r")\s*:",
    re.IGNORECASE,
)

# Any "Word:" or "Some Words:" prefix, used only to report unrecognized names.
_ANY_PREFIX_PATTERN = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Za-z.'À-ſ]*(?: [A-Z][A-Za-z.'À-ſ]*){0,2})\s*:")


def resolve(name: str) -> str | None:
    """Return the canonical name for ``name``, or None if it is unknown.

    >>> resolve("G.O.B.")
    'GOB'
    >>> resolve("Tobias Fünke")
    'Tobias'
    >>> resolve("Nobody")
    """
    return ALIAS_INDEX.get(_fold(name))


def is_canonical(name: str) -> bool:
    """True if ``name`` is exactly a canonical name."""
    return name in CHARACTERS


def parse_speakers(text: str) -> list[str]:
    """Extract canonical speakers from ``Name:`` prefixes in ``text``.

    Only prefixes that resolve to a known character are accepted, which avoids
    the false positives a bare ``^\\w+:`` regex produces on this data (``Next
    stop:``, ``She old school. Michael:``). Returns names in order of first
    appearance, without duplicates.

    >>> parse_speakers("Lucille: You tricked me. Michael: I deceived you, Mom.")
    ['Lucille', 'Michael']
    >>> parse_speakers("Next stop: the hospital.")
    []
    """
    seen: list[str] = []
    for match in _ALIAS_PATTERN.finditer(text or ""):
        canonical = resolve(match.group(1))
        if canonical is not None and canonical not in seen:
            seen.append(canonical)
    return seen


def unknown_prefixes(text: str) -> list[str]:
    """Return ``Name:`` prefixes in ``text`` that no alias resolves.

    Used by the normalizer to report names a curator may need to add to
    ``CHARACTERS`` rather than dropping them silently.
    """
    text = text or ""
    # Spans already accounted for by a recognized alias, so that "George Sr.:"
    # is not also reported as the unknown prefix "Sr.".
    known = [m.span() for m in _ALIAS_PATTERN.finditer(text)]
    unknown: list[str] = []
    for match in _ANY_PREFIX_PATTERN.finditer(text):
        start, end = match.span()
        if any(start < k_end and k_start < end for k_start, k_end in known):
            continue
        name = match.group(1)
        if resolve(name) is None and name not in unknown:
            unknown.append(name)
    return unknown


def format_speakers(names: list[str]) -> str:
    """Join canonical names into the stored comma-separated form."""
    return ",".join(names)


def split_speakers(value: str) -> list[str]:
    """Split a stored ``speakers`` value into individual names."""
    return [part.strip() for part in (value or "").split(",") if part.strip()]

"""Unit tests for canonical speaker names and text parsing."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from speaker_names import (  # noqa: E402
    CHARACTERS,
    format_speakers,
    is_canonical,
    parse_speakers,
    resolve,
    split_speakers,
    unknown_prefixes,
)


class TestResolve:
    """Alias resolution to canonical names."""

    @pytest.mark.parametrize("alias,expected", [
        ("GOB", "GOB"),
        ("Gob", "GOB"),
        ("G.O.B.", "GOB"),
        ("George Oscar Bluth", "GOB"),
        ("George", "George Sr."),
        ("George Sr", "George Sr."),
        ("George, Sr.", "George Sr."),
        ("Barry", "Barry Zuckerkorn"),
        ("Wayne", "Wayne Jarvis"),
        ("Rev. Veal", "Reverend Veal"),
        ("Larry the surrogate", "Larry Middleman"),
    ])
    def test_variants_collapse_to_one_name(self, alias, expected):
        assert resolve(alias) == expected

    def test_accents_and_case_are_ignored(self):
        assert resolve("Tobias Fünke") == "Tobias"
        assert resolve("tobias funke") == "Tobias"

    def test_lucille_is_lucille_bluth(self):
        """Bare "Lucille" is Lucille Bluth; Austero is always written out."""
        assert resolve("Lucille") == "Lucille"
        assert resolve("Lucille Bluth") == "Lucille"
        assert resolve("Lucille 2") == "Lucille Austero"
        assert resolve("Lucille Austero") == "Lucille Austero"

    def test_unknown_name_returns_none(self):
        assert resolve("Nobody At All") is None

    def test_every_canonical_name_resolves_to_itself(self):
        for name in CHARACTERS:
            assert resolve(name) == name
            assert is_canonical(name)


class TestParseSpeakers:
    """Extracting speakers from the quote text."""

    def test_multi_speaker_exchange(self):
        text = (
            "Lucille: You tricked me. Michael: I deceived you, Mom. "
            "Trick makes it sound like we have a playful relationship. "
            "Lucille: Touche."
        )
        assert parse_speakers(text) == ["Lucille", "Michael"]

    def test_names_are_canonicalized(self):
        assert parse_speakers("Gob: I've made a huge mistake.") == ["GOB"]

    def test_longest_alias_wins(self):
        """"George Michael:" must not be read as "George"."""
        assert parse_speakers("George Michael: Her?") == ["George Michael"]

    @pytest.mark.parametrize("text", [
        "Next stop: LAX. Oh, come on.",
        "It's, like, \"Hey, you want to go down to the whirlpool?\"",
        "The soup of the day is Bread",
    ])
    def test_non_speaker_colons_are_not_matched(self, text):
        """A bare ^\\w+: regex over-matched these; the alias table must not."""
        assert parse_speakers(text) == []

    def test_mid_sentence_name_without_colon_is_ignored(self):
        assert parse_speakers("I deceived you, Mom. Michael is fine.") == []

    def test_empty_text(self):
        assert parse_speakers("") == []
        assert parse_speakers(None) == []


class TestUnknownPrefixes:
    def test_recognized_prefix_is_not_reported(self):
        assert unknown_prefixes("George, Sr.: Well, he's, uh, dead.") == []

    def test_unrecognized_prefix_is_reported(self):
        assert unknown_prefixes("Franklin Delano: Hello.") == ["Franklin Delano"]


class TestFormatting:
    def test_round_trip(self):
        names = ["Lucille", "Michael"]
        assert format_speakers(names) == "Lucille,Michael"
        assert split_speakers("Lucille,Michael") == names

    def test_split_tolerates_spacing_and_empties(self):
        assert split_speakers(" Lucille , Michael ,, ") == ["Lucille", "Michael"]

    def test_split_of_empty_value(self):
        assert split_speakers("") == []

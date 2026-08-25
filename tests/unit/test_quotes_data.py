"""Data integrity tests for quotes.json and the canonical character list."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from speaker_names import split_speakers  # noqa: E402

from app.models import Quote  # noqa: E402
from app.services import filter_by_speaker  # noqa: E402

QUOTES_PATH = REPO_ROOT / "app" / "data" / "quotes.json"
CHARACTERS_PATH = REPO_ROOT / "app" / "data" / "list-of-characters.txt"


@pytest.fixture(scope="module")
def quotes():
    return json.loads(QUOTES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def canonical_names():
    lines = CHARACTERS_PATH.read_text(encoding="utf-8").splitlines()
    return [line for line in lines if line and not line.startswith("#")]


class TestQuotesData:
    def test_every_quote_has_a_speakers_field(self, quotes):
        missing = [q["id"] for q in quotes if "speakers" not in q]
        assert not missing, f"quotes missing 'speakers': {missing[:10]}"

    def test_primary_speaker_field_is_gone(self, quotes):
        stale = [q["id"] for q in quotes if "primarySpeaker" in q]
        assert not stale, f"quotes still carrying 'primarySpeaker': {stale[:10]}"

    def test_every_speaker_is_a_canonical_name(self, quotes, canonical_names):
        """The rule CONTRIBUTING.md documents, enforced.

        Prevents "GOB", "G.O.B." and "George Oscar Bluth" drifting apart again.
        """
        allowed = set(canonical_names)
        offenders = {
            name
            for q in quotes
            for name in split_speakers(q.get("speakers", ""))
            if name not in allowed
        }
        assert not offenders, (
            f"names not in list-of-characters.txt: {sorted(offenders)}. "
            "Run scripts/normalize_speakers.py."
        )

    def test_character_list_has_no_unused_names(self, quotes, canonical_names):
        in_use = {
            name
            for q in quotes
            for name in split_speakers(q.get("speakers", ""))
        }
        assert not set(canonical_names) - in_use

    def test_character_list_is_sorted_and_unique(self, canonical_names):
        assert canonical_names == sorted(canonical_names, key=str.lower)
        assert len(canonical_names) == len(set(canonical_names))

    def test_speakers_values_are_well_formed(self, quotes):
        for q in quotes:
            value = q["speakers"]
            assert isinstance(value, str), q["id"]
            assert value == value.strip(), q["id"]
            assert ", " not in value, f"{q['id']}: no space after comma"
            assert not value.startswith(","), q["id"]
            assert not value.endswith(","), q["id"]

    def test_no_duplicate_speaker_within_a_quote(self, quotes):
        for q in quotes:
            names = split_speakers(q["speakers"])
            assert len(names) == len(set(names)), q["id"]

    def test_every_quote_validates_against_the_model(self, quotes):
        for raw in quotes:
            Quote(**raw)


class TestFilterBySpeaker:
    @pytest.fixture
    def sample(self):
        return [
            Quote(id="a", quote="Lucille: You tricked me. Michael: I deceived you.",
                  speakers="Lucille,Michael"),
            Quote(id="b", quote="I've made a huge mistake.", speakers="GOB"),
            Quote(id="c", quote="Annyong", speakers=""),
        ]

    def test_matches_a_sole_speaker(self, sample):
        assert [q.id for q in filter_by_speaker(sample, "GOB")] == ["b"]

    def test_matches_any_speaker_in_a_multi_speaker_quote(self, sample):
        """Michael is second in "Lucille,Michael" and must still match."""
        assert [q.id for q in filter_by_speaker(sample, "Michael")] == ["a"]
        assert [q.id for q in filter_by_speaker(sample, "Lucille")] == ["a"]

    def test_is_case_insensitive(self, sample):
        assert [q.id for q in filter_by_speaker(sample, "gob")] == ["b"]
        assert [q.id for q in filter_by_speaker(sample, "MICHAEL")] == ["a"]

    def test_does_not_match_on_substrings(self, sample):
        """"Michael" must not pull in a quote spoken by "George Michael"."""
        quotes = [Quote(id="d", quote="Her?", speakers="George Michael")]
        assert filter_by_speaker(quotes, "Michael") == []

    def test_unattributed_quotes_never_match(self, sample):
        assert filter_by_speaker(sample, "") == []
        assert filter_by_speaker(sample, "Annyong") == []

    def test_unknown_speaker_returns_empty(self, sample):
        assert filter_by_speaker(sample, "Nobody") == []


NO_SUCH_NAME = "Zzzz Notarealcharacter"


class TestUnknownNamesAreNeverDropped:
    """An unresolvable name must stop the run, not get normalized away.

    Silently dropping it would delete a curator's work and leave a record that
    looks correct, so the failure has to be loud and the data left alone.

    NO_SUCH_NAME must stay something that will never become a real character.
    These tests originally used "Franklin", which later turned out to be one.
    """

    @pytest.fixture
    def normalizer(self, tmp_path, monkeypatch):
        import normalize_speakers as ns

        quotes_path = tmp_path / "quotes.json"
        chars_path = tmp_path / "list-of-characters.txt"
        monkeypatch.setattr(ns, "QUOTES_PATH", quotes_path)
        monkeypatch.setattr(ns, "CHARACTERS_PATH", chars_path)
        monkeypatch.setattr(sys, "argv", ["normalize_speakers.py"])

        def run(records, argv=("normalize_speakers.py",)):
            quotes_path.write_text(
                json.dumps(records, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            monkeypatch.setattr(sys, "argv", list(argv))
            code = ns.main()
            return code, quotes_path, chars_path

        return run

    def test_unknown_name_exits_non_zero(self, normalizer):
        code, _, _ = normalizer(
            [{"id": "quote-1", "quote": "Hello", "speakers": NO_SUCH_NAME}]
        )
        assert code == 1

    def test_unknown_name_leaves_the_file_untouched(self, normalizer):
        records = [{"id": "quote-1", "quote": "Hello", "speakers": NO_SUCH_NAME}]
        code, quotes_path, chars_path = normalizer(records)

        assert code == 1
        written = json.loads(quotes_path.read_text(encoding="utf-8"))
        assert written[0]["speakers"] == NO_SUCH_NAME, "the name must survive"
        assert not chars_path.exists(), "no character list on a failed run"

    def test_one_bad_name_blocks_the_whole_file(self, normalizer):
        """A good record must not be rewritten while a bad one is unresolved."""
        records = [
            {"id": "quote-1", "quote": "Hello", "speakers": "gob"},
            {"id": "quote-2", "quote": "Hello", "speakers": NO_SUCH_NAME},
        ]
        code, quotes_path, _ = normalizer(records)

        assert code == 1
        written = json.loads(quotes_path.read_text(encoding="utf-8"))
        assert written[0]["speakers"] == "gob", "not normalized to GOB"

    def test_check_mode_also_fails(self, normalizer):
        code, _, _ = normalizer(
            [{"id": "quote-1", "quote": "Hello", "speakers": NO_SUCH_NAME}],
            argv=("normalize_speakers.py", "--check"),
        )
        assert code == 1

    def test_known_names_still_normalize_and_write(self, normalizer):
        code, quotes_path, chars_path = normalizer(
            [{"id": "quote-1", "quote": "Hello", "speakers": "gob"}]
        )

        assert code == 0
        written = json.loads(quotes_path.read_text(encoding="utf-8"))
        assert written[0]["speakers"] == "GOB"
        assert "GOB" in chars_path.read_text(encoding="utf-8")

    def test_unrecognized_prefix_in_text_is_only_a_warning(self, normalizer):
        """The quote text is never modified, so nothing is lost."""
        code, quotes_path, _ = normalizer(
            [{"id": "quote-1", "quote": "Franklin Delano: Hello", "speakers": ""}]
        )

        assert code == 0
        written = json.loads(quotes_path.read_text(encoding="utf-8"))
        assert written[0]["quote"] == "Franklin Delano: Hello"

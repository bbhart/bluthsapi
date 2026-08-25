"""Unit tests for near-duplicate quote detection."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from find_duplicate_quotes import (  # noqa: E402
    find_groups,
    merge_into_keeper,
    normalize,
)


def quote(qid: str, text: str, **extra) -> dict:
    record = {"id": qid, "quote": text, "speakers": ""}
    record.update(extra)
    return record


def group_ids(groups):
    return [sorted(q["id"] for q in g.members) for g in groups]


class TestNormalize:
    def test_speaker_prefixes_are_dropped(self):
        assert normalize("Michael: I've made a huge mistake.") == \
            normalize("I've made a huge mistake.")

    def test_censorship_styles_collapse(self):
        """"[bleep]", "__" and "****" must not hide a duplicate."""
        a = normalize("interoffice [bleep]ing")
        b = normalize("interoffice __ing")
        c = normalize("interoffice ****ing")
        assert a == b == c

    def test_punctuation_and_case_are_flattened(self):
        assert normalize("Her?!") == normalize("her")

    def test_empty_text(self):
        assert normalize("") == ""


class TestFindGroups:
    def test_identical_quotes_group(self):
        groups = find_groups(
            [quote("quote-1", "Those are balls."),
             quote("quote-2", "Those are balls.")],
            threshold=0.85, min_tokens=6,
        )
        assert group_ids(groups) == [["quote-1", "quote-2"]]

    def test_truncated_variant_is_caught_by_containment(self):
        """A short quote scores a poor ratio against its long form."""
        groups = find_groups(
            [quote("quote-1", "How do we filter out the teases? We don't let them in."),
             quote("quote-2", "How do we filter out the teases?")],
            threshold=0.85, min_tokens=6,
        )
        assert group_ids(groups) == [["quote-1", "quote-2"]]

    def test_short_containment_is_ignored(self):
        """"Balls" inside a long quote is not evidence of duplication."""
        groups = find_groups(
            [quote("quote-1", "Balls"),
             quote("quote-2", "Balls are a thing that George Michael mentioned once here.")],
            threshold=0.85, min_tokens=6,
        )
        assert groups == []

    def test_unrelated_quotes_do_not_group(self):
        groups = find_groups(
            [quote("quote-1", "There's always money in the banana stand."),
             quote("quote-2", "I've made a huge mistake.")],
            threshold=0.85, min_tokens=6,
        )
        assert groups == []

    def test_grouping_is_transitive(self):
        groups = find_groups(
            [quote("quote-1", "I'm a scholar. I enjoy scholarly pursuits. Suddenly that counts."),
             quote("quote-2", "I'm a scholar. I enjoy scholarly pursuits."),
             quote("quote-3", "I enjoy scholarly pursuits. Suddenly that counts.")],
            threshold=0.85, min_tokens=6,
        )
        assert group_ids(groups) == [["quote-1", "quote-2", "quote-3"]]


class TestKeeperSelection:
    @pytest.fixture
    def image_on_the_short_one(self):
        return find_groups(
            [quote("quote-1", "How do we filter out the teases? We don't let them in."),
             quote("quote-2", "How do we filter out the teases?", imageUrl="a.jpg")],
            threshold=0.85, min_tokens=6,
        )[0]

    def test_longest_text_wins_over_an_image(self, image_on_the_short_one):
        """The punchline must not be traded away to preserve an image."""
        assert image_on_the_short_one.keeper["id"] == "quote-1"

    def test_the_image_is_inherited_rather_than_lost(self, image_on_the_short_one):
        keeper, notes, conflicts = merge_into_keeper(image_on_the_short_one)

        assert keeper["imageUrl"] == "a.jpg"
        assert any("inherited imageUrl" in n for n in notes)
        assert conflicts == []


class TestMergeConflicts:
    def test_speakers_are_inherited_when_the_keeper_has_none(self):
        group = find_groups(
            [quote("quote-1", "How do we filter out the teases? We don't let them in."),
             quote("quote-2", "How do we filter out the teases?", speakers="GOB")],
            threshold=0.85, min_tokens=6,
        )[0]
        keeper, notes, conflicts = merge_into_keeper(group)

        assert keeper["speakers"] == "GOB"
        assert conflicts == []

    def test_disagreeing_speakers_are_flagged_not_unioned(self):
        """Silently combining them would launder a wrong attribution."""
        group = find_groups(
            [quote("quote-1", "How do we filter out the teases? We don't let them in.",
                   speakers="GOB"),
             quote("quote-2", "How do we filter out the teases?", speakers="Michael")],
            threshold=0.85, min_tokens=6,
        )[0]
        keeper, _, conflicts = merge_into_keeper(group)

        assert keeper["speakers"] == "GOB"
        assert len(conflicts) == 1
        assert "Michael" in conflicts[0]

    def test_a_second_image_is_reported_as_discarded(self):
        group = find_groups(
            [quote("quote-1", "How do we filter out the teases? We don't let them in.",
                   imageUrl="keep.jpg"),
             quote("quote-2", "How do we filter out the teases?", imageUrl="lost.jpg")],
            threshold=0.85, min_tokens=6,
        )[0]
        keeper, _, conflicts = merge_into_keeper(group)

        assert keeper["imageUrl"] == "keep.jpg"
        assert len(conflicts) == 1
        assert "lost.jpg" in conflicts[0]
        assert "DISCARDS" in conflicts[0]

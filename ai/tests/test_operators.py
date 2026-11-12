from datetime import date, datetime
from decimal import Decimal

import pytest

from ai.matching.operators import apply_operator, between, contains, contains_any, eq, gte, in_, lte, neq, not_contains, not_in


# ---------- equality ----------
def test_eq_and_neq_on_text_and_booleans():
    assert eq("TN", "TN") and not eq("TN", "FR")
    assert eq(False, False) and not eq(False, True)
    assert neq("master", "phd") and not neq("none", "none")


def test_eq_does_not_merge_scale_values_with_same_rank():
    # master and engineering_cycle both have rank 2, but they are different values
    assert not eq("master", "engineering_cycle")


# ---------- in / not_in ----------
def test_in_and_not_in():
    assert in_("humanities", ["humanities", "other"])
    assert not in_("arts_music_performing", ["humanities"])
    assert not_in("architecture_design", ["arts_music_performing", "architecture_design"]) is False
    assert not_in("engineering_technology", ["arts_music_performing"])


def test_in_rejects_a_string_instead_of_a_list():
    with pytest.raises(ValueError):
        in_("TN", "TNX")


# ---------- gte / lte on numbers ----------
@pytest.mark.parametrize("actual, expected, result", [
    (80, 80, True), (79.9, 80, False), (Decimal("80.00"), 80, True), (Decimal("79.99"), 80, False),
])
def test_gte_numbers(actual, expected, result):
    assert gte(actual, expected) is result


@pytest.mark.parametrize("actual, expected, result", [
    (6, 6, True), (6.5, 6, False), (0, 0, True), (Decimal("2.5"), 3, True),
])
def test_lte_numbers(actual, expected, result):
    assert lte(actual, expected) is result


# ---------- ranked scales ----------
@pytest.mark.parametrize("actual, expected, result", [
    ("master", "bachelor", True), ("bachelor", "master", False),
    ("engineering_cycle", "master", True),   # same rank
    ("none", "bachelor", False), ("phd", "master", True),
    ("B2", "C1", False), ("C1", "C1", True), ("native", "C2", True),
])
def test_gte_on_ranked_scales(actual, expected, result):
    assert gte(actual, expected) is result


def test_lte_on_ranked_scale():
    assert lte("B2", "C1") and not lte("C2", "C1")


def test_ordering_two_different_scales_is_an_error():
    with pytest.raises(ValueError):
        gte("B2", "master")


def test_ordering_text_that_is_not_on_a_scale_is_an_error():
    with pytest.raises(ValueError):
        gte("abc", "abd")
    with pytest.raises(ValueError):
        gte("abc", 3)


# ---------- dates ----------
def test_date_against_iso_string():
    assert gte(date(1998, 5, 1), "1997-04-01")          # E-M02: born after 1 Apr 1997
    assert not gte(date(1996, 5, 1), "1997-04-01")
    assert lte(date(2000, 1, 1), "2008-08-31")          # S-M03


def test_two_iso_strings_and_datetimes():
    assert lte("2027-01-06", "2027-01-06")
    assert gte(datetime(2027, 2, 1, 10, 30), "2027-01-06")


# ---------- between (inclusive) ----------
@pytest.mark.parametrize("actual, result", [(1, False), (2, True), (3, True), (4, True), (5, False)])
def test_between_numbers_is_inclusive(actual, result):
    assert between(actual, [2, 4]) is result


@pytest.mark.parametrize("actual, result", [
    (date(2027, 8, 31), False), (date(2027, 9, 1), True), (date(2027, 12, 31), True), (date(2028, 1, 1), False),
])
def test_between_dates_is_inclusive(actual, result):   # G-07 graduation window
    assert between(actual, ["2027-09-01", "2027-12-31"]) is result


@pytest.mark.parametrize("bad", [[1], [1, 2, 3], 5, "ab"])
def test_between_needs_two_bounds(bad):
    with pytest.raises(ValueError):
        between(3, bad)


# ---------- list operators ----------
def test_contains_and_not_contains():
    assert contains(["TN", "FR"], "FR") and not contains(["TN"], "FR")
    assert not_contains(["TN"], "FR") and not not_contains(["TN", "FR"], "FR")
    assert not_contains([], "eiffel_master")           # empty list is a valid answer


def test_contains_any():
    assert contains_any(["TN", "FR"], ["TN"])
    assert contains_any(["FR"], ["TN", "FR"])
    assert not contains_any(["FR"], ["TN"])
    assert not contains_any([], ["TN"])


def test_list_operators_reject_a_string_profile_value():
    with pytest.raises(ValueError):
        contains("TNX", "TN")


# ---------- dispatch by name ----------
def test_apply_operator_by_name():
    assert apply_operator("gte", "master", "bachelor")
    assert apply_operator("in", "TN", ["TN"])
    assert apply_operator("contains_any", ["TN"], ["TN"])


def test_unknown_operator_is_an_error():
    with pytest.raises(ValueError):
        apply_operator("almost_equal", 1, 1)

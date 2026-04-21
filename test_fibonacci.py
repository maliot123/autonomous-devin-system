"""Tests for :mod:`fibonacci`."""

from __future__ import annotations

import pytest

from fibonacci import fibonacci


def test_zero_returns_empty_list() -> None:
    assert fibonacci(0) == []


def test_one_returns_single_zero() -> None:
    assert fibonacci(1) == [0]


def test_two_returns_zero_one() -> None:
    assert fibonacci(2) == [0, 1]


def test_first_ten_values() -> None:
    assert fibonacci(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def test_length_matches_n() -> None:
    assert len(fibonacci(25)) == 25


def test_negative_raises_value_error() -> None:
    with pytest.raises(ValueError):
        fibonacci(-1)


@pytest.mark.parametrize("bad", [1.5, "5", None, [5], 3.0])
def test_non_int_raises_type_error(bad: object) -> None:
    with pytest.raises(TypeError):
        fibonacci(bad)  # type: ignore[arg-type]


def test_bool_rejected() -> None:
    with pytest.raises(TypeError):
        fibonacci(True)  # type: ignore[arg-type]

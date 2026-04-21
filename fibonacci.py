"""Fibonacci sequence utilities."""

from __future__ import annotations


def fibonacci(n: int) -> list[int]:
    """Return the first ``n`` numbers of the Fibonacci sequence.

    The sequence starts ``0, 1, 1, 2, 3, 5, ...``.

    Args:
        n: The number of Fibonacci numbers to generate. Must be a non-negative
            integer. ``bool`` values are rejected even though they are a
            subclass of ``int``.

    Returns:
        A list containing the first ``n`` Fibonacci numbers. An empty list is
        returned when ``n`` is ``0``.

    Raises:
        TypeError: If ``n`` is not an ``int`` (or is a ``bool``).
        ValueError: If ``n`` is negative.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")

    sequence: list[int] = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence


if __name__ == "__main__":
    import sys

    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(fibonacci(count))

# Autonomous Engineering System

## Utilities

### `fibonacci(n)`

`fibonacci.py` exposes a `fibonacci(n)` function that returns the first `n`
numbers of the Fibonacci sequence as a list. It raises `TypeError` for
non-integer inputs (including `bool`) and `ValueError` for negative values.

```python
from fibonacci import fibonacci

fibonacci(10)  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

Run the tests with:

```bash
pytest
```


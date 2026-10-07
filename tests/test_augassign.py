"""AugAssign: `x += v` compiles to `x := __oneline_operator__.iadd(x, v)`.
The operator-module iXXX functions implement the full INPLACE_ADD protocol
(try `__iadd__`, fall back to `__add__`/`__radd__`), so mutable types keep
their object identity — aliases see the mutation, exactly like real Python.
visit_Module prepends `__oneline_operator__ := __import__("operator")` once
when any aug-assign was compiled; per-use cost is one attribute lookup.

Not pinned here (pre-existing limitations shared with plain Assign):
- rebinding a for-loop's own variable in its body (`for i in r: i += 1`)
  compiles to a walrus on the comprehension target, which raises SyntaxError
  in the output.
- non-Name targets (`d[k] += v`, `obj.a += v`) stay NotSupported, consistent
  with Assign.
"""


def test_aug_add(run_both):
    assert run_both("x = 1\nx += 2\nprint(x)\n") == "3\n"


def test_aug_int_ops(run_both):
    src = (
        "x = 10\n"
        "x -= 3\n"  # 7
        "x //= 2\n"  # 3
        "x %= 4\n"  # 3
        "x **= 3\n"  # 27
        "x <<= 1\n"  # 54
        "x |= 9\n"  # 63
        "x &= 14\n"  # 14
        "x ^= 5\n"  # 11
        "x >>= 1\n"  # 5
        "print(x)\n"
    )
    assert run_both(src) == "5\n"


def test_aug_truediv(run_both):
    assert run_both("x = 9\nx /= 2\nprint(x)\n") == "4.5\n"


def test_aug_string(run_both):
    assert run_both('s = "a"\ns += "bc"\nprint(s)\n') == "abc\n"


def test_aug_in_while_body(run_both):
    assert run_both("i = 0\nwhile i < 3:\n    i += 1\nprint(i)\n") == "3\n"


def test_aug_in_for_body(run_both):
    src = "total = 0\nfor i in [1, 2, 3]:\n    total += i\nprint(total)\n"
    assert run_both(src) == "6\n"


def test_aug_value_evaluated_once(run_both):
    src = (
        "calls = []\n"
        "def v():\n"
        "    calls.append(1)\n"
        "    return 10\n"
        "x = 0\n"
        "x += v()\n"
        "print(x, len(calls))\n"
    )
    assert run_both(src) == "10 1\n"


def test_aug_in_function_body(run_both):
    src = (
        "def tick(n):\n"
        "    i = 0\n"
        "    while i < n:\n"
        "        i += 1\n"
        "    return i\n"
        "print(tick(5))\n"
    )
    assert run_both(src) == "5\n"


def test_aug_in_place_protocol(run_both):
    src = "a = [1]\nb = a\na += [2]\nprint(b)\n"
    assert run_both(src) == "[1, 2]\n"

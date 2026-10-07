"""Assignment in all forms.

Plain `x = v` becomes `x := v`. With several targets — or any non-Name
target — the value is hoisted into `__oneline_value__` first: CPython
evaluates the value before the targets, and chained targets must share one
evaluation (which also fixed `x = y = f()` calling f once per target).

Subscript/attribute targets store through the same mechanisms as the
bytecode: `d[k] = v` -> `d.__setitem__(k, t)`, `obj.a = v` -> `setattr(obj,
"a", t)`. Slice keys are rebuilt as runtime slice(lower, upper[, step])
objects — a Slice node is not an expression and cannot become a call
argument. Augmented assignment keeps the full in-place protocol via the
operator prelude: `x += v` -> `x := __oneline_operator__.iadd(x, v)`, so
mutable types keep identity and aliases see the mutation; the subscript/
attribute forms evaluate receiver and key exactly once into temps.

Known limit shared with plain Assign: rebinding a for-loop's own variable in
its body compiles to a walrus on the comprehension target -> SyntaxError.
"""


# --- plain names ---


def test_assign_single(run_both):
    assert run_both("x = 3\nprint(x)\n") == "3\n"


def test_assign_then_use(run_both):
    assert run_both("x = 3\ny = x * 2\nprint(x, y)\n") == "3 6\n"


def test_assign_chained(run_both):
    assert run_both("a = b = 2\nprint(a, b)\n") == "2 2\n"


# --- subscript / attribute / slice targets ---


def test_setitem_dict(run_both):
    assert run_both('d = {}\nd["k"] = 1\nprint(d)\n') == "{'k': 1}\n"


def test_setitem_list(run_both):
    assert run_both("lst = [0, 0]\nlst[1] = 7\nprint(lst)\n") == "[0, 7]\n"


def test_setattr_instance(run_both):
    src = "class B:\n    pass\nb = B()\nb.x = 5\nprint(b.x)\n"
    assert run_both(src) == "5\n"


def test_chained_mixed_targets(run_both):
    src = 'd = {}\nd["a"] = d["b"] = 2\nprint(d)\n'
    assert run_both(src) == "{'a': 2, 'b': 2}\n"


def test_slice_assign_basic(run_both):
    src = "lst = [0, 0, 0]\nlst[1:3] = [7, 8]\nprint(lst)\n"
    assert run_both(src) == "[0, 7, 8]\n"


def test_slice_assign_shrink(run_both):
    src = "lst = [0, 1, 2, 3]\nlst[:2] = [9]\nprint(lst)\n"
    assert run_both(src) == "[9, 2, 3]\n"


def test_slice_assign_step(run_both):
    src = "lst = [0, 1, 2, 3]\nlst[::2] = [7, 7]\nprint(lst)\n"
    assert run_both(src) == "[7, 1, 7, 3]\n"


def test_slice_assign_open_end(run_both):
    src = "lst = [0, 1, 2]\nlst[1:] = [8, 9]\nprint(lst)\n"
    assert run_both(src) == "[0, 8, 9]\n"


# --- augmented, Name targets ---


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


# --- augmented, subscript / attribute / slice targets ---


def test_aug_subscript(run_both):
    src = 'c = {}\nc["a"] = 0\nc["a"] += 1\nc["a"] += 2\nprint(c)\n'
    assert run_both(src) == "{'a': 3}\n"


def test_aug_list_element(run_both):
    assert run_both("n = [0]\nn[0] += 5\nprint(n)\n") == "[5]\n"


def test_aug_attribute(run_both):
    src = "class P:\n    pass\np = P()\np.total = 0\np.total += 4\nprint(p.total)\n"
    assert run_both(src) == "4\n"


def test_aug_subscript_keeps_in_place_identity(run_both):
    src = "a = [1]\nb = a\na[0] += 1\nprint(b)\n"
    assert run_both(src) == "[2]\n"


def test_aug_slice_tail(run_both):
    src = "n = [0, 1, 2]\nn[1:] += [9]\nprint(n)\n"
    assert run_both(src) == "[0, 1, 2, 9]\n"


# --- evaluation-order / eval-once fidelity pins ---


def test_name_chained_evaluates_value_once(run_both):
    src = (
        "calls = []\n"
        "def f():\n"
        "    calls.append(1)\n"
        "    return 3\n"
        "x = y = f()\n"
        "print(x, y, len(calls))\n"
    )
    assert run_both(src) == "3 3 1\n"


def test_subscript_eval_order_value_first(run_both):
    src = (
        "seq = []\n"
        "def kf():\n"
        '    seq.append("k")\n'
        '    return "key"\n'
        "def vf():\n"
        '    seq.append("v")\n'
        "    return 1\n"
        "d = {}\n"
        "d[kf()] = vf()\n"
        "print(seq, d)\n"
    )
    assert run_both(src) == "['v', 'k'] {'key': 1}\n"


def test_attr_eval_order_value_first(run_both):
    src = (
        "seq = []\n"
        "class B:\n"
        "    pass\n"
        "b = B()\n"
        "def vf():\n"
        '    seq.append("v")\n'
        "    return 1\n"
        "b.a = vf()\n"
        "print(seq)\n"
    )
    assert run_both(src) == "['v']\n"

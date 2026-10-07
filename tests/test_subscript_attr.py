"""Subscript/attribute assignment: `d[k] = v` compiles to a hoisted value
temp followed by `d.__setitem__(k, t)`, `obj.a = v` to `setattr(obj, "a", t)`.
CPython evaluates the value first, then the target — the temp preserves that
order (and its side effects) exactly. setattr/__setitem__ are the same
mechanisms behind STORE_ATTR / STORE_SUBSCR, so properties, descriptors and
custom containers behave identically. Chained targets share the one hoisted
value — which also fixes chained Name assigns (`x = y = f()` used to call f
twice).

Augmented forms keep the target-first order of the augmented bytecode and
reuse the operator prelude: `d[k] += v` evaluates d and k once into temps,
then `t_d.__setitem__(t_k, iadd(t_d[t_k], v))`.

Slice targets compile their key through _fix_slice into a runtime
slice(lower, upper[, step]) object — what BUILD_SLICE does; a Slice node
itself is not an expression and cannot be spliced into a call argument.
"""



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


def test_aug_slice_tail(run_both):
    src = "n = [0, 1, 2]\nn[1:] += [9]\nprint(n)\n"
    assert run_both(src) == "[0, 1, 2, 9]\n"

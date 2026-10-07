"""for ... else: the else body runs iff the loop finished without a break.

Tests that fail right now are marked xfail(strict=True) -- they are the
acceptance criteria for the remaining work; once they XPASS, promote them
to plain tests.
"""


def test_else_runs_on_normal_completion(run_both):
    src = "for i in range(2):\n    print(i)\nelse:\n    print('else')\n"
    assert run_both(src) == "0\n1\nelse\n"


def test_else_runs_with_continue_body(run_both):
    src = (
        "for i in range(4):\n"
        "    if i % 2:\n"
        "        continue\n"
        "    print(i)\n"
        "else:\n"
        "    print('else')\n"
    )
    assert run_both(src) == "0\n2\nelse\n"


def test_else_runs_on_empty_iterable(run_both):
    src = "for i in []:\n    print(i)\nelse:\n    print('else')\n"
    assert run_both(src) == "else\n"


def test_else_runs_on_empty_iterable_with_break(run_both):
    src = "for i in []:\n    print(i)\n    break\nelse:\n    print('else')\n"
    assert run_both(src) == "else\n"


def test_else_skipped_on_break(run_both):
    src = (
        "for i in range(5):\n"
        "    print(i)\n"
        "    if i == 1:\n"
        "        break\n"
        "else:\n"
        "    print('else')\n"
    )
    assert run_both(src) == "0\n1\n"


def test_else_break_targets_outer_loop(run_both):
    # a break in the else body targets the enclosing loop; this pins the
    # just_breaked timing that keeps the break flag alive past the inner loop
    src = (
        "for i in range(3):\n"
        "    for j in range(1):\n"
        "        print('inner', j)\n"
        "    else:\n"
        "        break\n"
        "print('after')\n"
    )
    assert run_both(src) == "inner 0\nafter\n"


def test_nested_inner_break_with_else(run_both):
    # an inner loop's break must neither trip the outer loop's takewhile
    # predicate nor leak into the outer loop's else decision
    src = (
        "for i in range(2):\n"
        "    for j in range(5):\n"
        "        print('inner', j)\n"
        "        if j == 0:\n"
        "            break\n"
        "    else:\n"
        "        print('inner-else')\n"
        "    print('between', i)\n"
        "else:\n"
        "    print('outer-else')\n"
    )
    assert run_both(src) == "inner 0\nbetween 0\ninner 0\nbetween 1\nouter-else\n"

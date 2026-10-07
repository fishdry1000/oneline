"""for loops: a ListComp over the iterable; break/continue ride the shared
__oneline_break__/__oneline_continue__ flags — break wraps the iterator in
takewhile(lambda: not flag, it), continue short-circuits the remaining body
statements behind `flag or (...)`.

for-else: after the loop, `flag or else_body` runs the else only on normal
completion. The flags are restored unconditionally after the else gate —
"restore only what you consumed": a break raised inside the else body
belongs to an enclosing loop and must stay True past this loop's cleanup.
test_else_break_targets_outer_loop pins that timing.
"""


def test_for_plain(run_both):
    src = "for i in range(3):\n    print(i)\n"
    assert run_both(src) == "0\n1\n2\n"


def test_for_continue(run_both):
    src = "for i in range(6):\n    if i % 2:\n        continue\n    print(i)\n"
    assert run_both(src) == "0\n2\n4\n"


def test_for_break(run_both):
    src = (
        "for i in range(10):\n"
        "    print(i)\n"
        "    if i == 2:\n"
        "        break\n"
        "print('after')\n"
    )
    assert run_both(src) == "0\n1\n2\nafter\n"


def test_for_nested(run_both):
    src = "for i in range(2):\n    for j in range(2):\n        print(i, j)\n"
    assert run_both(src) == "0 0\n0 1\n1 0\n1 1\n"


def test_nested_continue(run_both):
    src = (
        "for i in range(2):\n"
        "    for j in range(1):\n"
        "        if j == 0:\n"
        "            continue\n"
        "        print('unreachable')\n"
        "    if i == 5:\n"
        "        continue\n"
        "    print('tail', i)\n"
    )
    assert run_both(src) == "tail 0\ntail 1\n"


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

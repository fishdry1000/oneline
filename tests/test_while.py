"""while ... else: same flag-based break/continue machinery as for, with the
loop condition re-evaluated before every body run.

The loop compiles to `for _ in takewhile(lambda: (not breaked) and test,
iter(int, 1))`, so a taken break flips the predicate off while a normal
condition exit leaves it on for the else gate.

Bodies use `i = i + 1` rather than `i += 1`: AugAssign is unsupported in its
own right and would mask what these tests are about.
"""

def test_while_plain(run_both):
    src = (
        "i = 0\n"
        "while i < 3:\n"
        "    print(i)\n"
        "    i = i + 1\n"
        "print('after')\n"
    )
    assert run_both(src) == "0\n1\n2\nafter\n"


def test_while_zero_iterations(run_both):
    # the body must not run at all when the condition is false up front
    src = "i = 10\nwhile i < 3:\n    print('never')\nprint('done')\n"
    assert run_both(src) == "done\n"


def test_while_break(run_both):
    src = (
        "i = 0\n"
        "while True:\n"
        "    print(i)\n"
        "    i = i + 1\n"
        "    if i == 3:\n"
        "        break\n"
        "print('after')\n"
    )
    assert run_both(src) == "0\n1\n2\nafter\n"


def test_while_continue(run_both):
    src = (
        "i = 0\n"
        "while i < 6:\n"
        "    i = i + 1\n"
        "    if i % 2:\n"
        "        continue\n"
        "    print(i)\n"
    )
    assert run_both(src) == "2\n4\n6\n"


def test_while_nested(run_both):
    src = (
        "i = 0\n"
        "while i < 2:\n"
        "    j = 0\n"
        "    while j < 2:\n"
        "        print(i, j)\n"
        "        j = j + 1\n"
        "    i = i + 1\n"
    )
    assert run_both(src) == "0 0\n0 1\n1 0\n1 1\n"


def test_while_else_runs_on_normal_exit(run_both):
    src = (
        "i = 0\n"
        "while i < 2:\n"
        "    i = i + 1\n"
        "else:\n"
        "    print('else', i)\n"
        "print('done')\n"
    )
    assert run_both(src) == "else 2\ndone\n"


def test_while_else_skipped_on_break(run_both):
    src = (
        "i = 0\n"
        "while True:\n"
        "    i = i + 1\n"
        "    if i == 2:\n"
        "        break\n"
        "else:\n"
        "    print('else')\n"
        "print('done', i)\n"
    )
    assert run_both(src) == "done 2\n"


def test_while_nested_inner_break(run_both):
    # an inner break must neither stop the outer loop nor leak into it
    src = (
        "i = 0\n"
        "while i < 3:\n"
        "    j = 0\n"
        "    while True:\n"
        "        j = j + 1\n"
        "        if j == 2:\n"
        "            break\n"
        "    print(i, j)\n"
        "    i = i + 1\n"
    )
    assert run_both(src) == "0 2\n1 2\n2 2\n"


def test_while_break_flag_does_not_leak_into_later_for(run_both):
    # a break consumed by the while must not trip a later for's takewhile
    src = (
        "i = 0\n"
        "while True:\n"
        "    i = i + 1\n"
        "    if i == 2:\n"
        "        break\n"
        "for k in range(5):\n"
        "    if k == 1:\n"
        "        break\n"
        "    print(k)\n"
        "print('ok', i)\n"
    )
    assert run_both(src) == "0\nok 2\n"

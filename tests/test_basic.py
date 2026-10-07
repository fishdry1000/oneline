"""Baseline statements: expression statements pass through untouched, a
single Name assignment compiles to a walrus, and if/elif/else becomes a
conditional expression over the compiled branch tuples.
"""


def test_print_and_expressions(run_both):
    assert run_both("print(1 + 2)\nprint('a', [1, 2])\n") == "3\na [1, 2]\n"


def test_if_without_else(run_both):
    assert run_both("if 1 > 2:\n    print('no')\nprint('done')\n") == "done\n"


def test_if_elif_else(run_both):
    src = (
        "if 1 + 1 > 3:\n"
        "    print('big')\n"
        "elif 2 > 1:\n"
        "    print('mid')\n"
        "else:\n"
        "    print('small')\n"
    )
    assert run_both(src) == "mid\n"

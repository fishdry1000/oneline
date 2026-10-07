"""One-shot try via `with`: try/except/else compiles to a single `with`
statement wrapping the whole line.

A one-line `with` has three evaluation regions that map 1:1 onto try:
- the context expression (evaluated before `__enter__`) holds the statements
  before the try; exceptions there propagate uncaught,
- the with body holds the try body and the else body; exceptions go to
  `__exit__`,
- `__exit__` dispatches the handlers and then runs everything after the try —
  it is called on both the normal and the exceptional path, so post-try code
  executes exactly once either way (inline continuation would be skipped by
  the unwound body).

Handler/rest statements execute inside `__exit__`'s frame, not the module
frame, so their bindings are compiled through `globals().__setitem__`
(module f_locals IS f_globals, so this is exact at module level); reads fall
through to globals on their own.

Constraints ("one-shot"): at most one try per program, top-level only (not
inside functions, if/loop bodies, or another try), no finally; anything else
raises NotSupportedSyntaxError. visit_Module emits the with statement, so
the output is a with statement, not a bare expression.
"""

import pytest


@pytest.mark.xfail(reason="try is not implemented")
def test_try_catches(run_both):
    src = "try:\n    x = 1 / 0\nexcept ZeroDivisionError:\n    x = -1\nprint(x)\n"
    assert run_both(src) == "-1\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_post_code_after_handler(run_both):
    src = (
        "try:\n"
        "    x = 1 / 0\n"
        "except ZeroDivisionError:\n"
        "    x = -1\n"
        'print("post", x)\n'
    )
    assert run_both(src) == "post -1\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_post_code_after_success(run_both):
    src = (
        "x = 0\n"
        "try:\n"
        "    x = 1\n"
        "except ZeroDivisionError:\n"
        "    x = -1\n"
        'print("post", x)\n'
    )
    assert run_both(src) == "post 1\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_as_name(run_both):
    src = (
        "try:\n"
        "    1 / 0\n"
        "except ZeroDivisionError as e:\n"
        '    print("caught", e)\n'
        'print("done")\n'
    )
    assert run_both(src) == "caught division by zero\ndone\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_multiple_handlers(run_both):
    src = (
        'try:\n'
        '    x = int("z")\n'
        "except ZeroDivisionError:\n"
        '    x = "zde"\n'
        "except ValueError:\n"
        '    x = "ve"\n'
        "print(x)\n"
    )
    assert run_both(src) == "ve\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_bare_except(run_both):
    src = 'try:\n    1 / 0\nexcept:\n    x = "bare"\nprint(x)\n'
    assert run_both(src) == "bare\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_else(run_both):
    src = (
        "try:\n"
        "    x = 1\n"
        "except ValueError:\n"
        "    x = 2\n"
        "else:\n"
        '    y = "else"\n'
        "print(x, y)\n"
    )
    assert run_both(src) == "1 else\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_handler_loop(run_both):
    src = (
        "total = 0\n"
        "try:\n"
        "    1 / 0\n"
        "except ZeroDivisionError:\n"
        "    for i in [1, 2, 3]:\n"
        "        total += i\n"
        "print(total)\n"
    )
    assert run_both(src) == "6\n"


@pytest.mark.xfail(reason="try is not implemented")
def test_try_body_loop(run_both):
    src = (
        "try:\n"
        "    t = 0\n"
        "    for i in [1, 2, 3]:\n"
        "        t += i\n"
        "except ValueError:\n"
        "    t = -1\n"
        "print(t)\n"
    )
    assert run_both(src) == "6\n"

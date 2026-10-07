import io
from ast import fix_missing_locations, parse, unparse
from contextlib import redirect_stdout

import pytest

from oneline import OneLine


def _exec(code: str) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        exec(code, {})
    return buf.getvalue()


@pytest.fixture
def compile_one_line():
    """Compile Python source into its one-line form."""

    def compile_(source: str) -> str:
        # the transformer prints debug info while visiting
        buf = io.StringIO()
        with redirect_stdout(buf):
            tree = OneLine().visit(parse(source))
            fix_missing_locations(tree)
        return unparse(tree)

    return compile_


@pytest.fixture
def run_both(compile_one_line):
    """Run source as-is and compiled; assert identical stdout; return it."""

    def run(source: str) -> str:
        expected = _exec(source)
        actual = _exec(compile_one_line(source))
        assert actual == expected, (
            f"compiled output diverged:\n"
            f"-- original: {expected!r}\n"
            f"-- compiled: {actual!r}"
        )
        return actual

    return run

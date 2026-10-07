"""Syntax that must fail compilation with NotSupportedSyntaxError rather than
mis-compile. Samples are chosen to stay unsupported as features land (del is
a statement with no expression form).
"""

import pytest

from oneline import NotSupportedSyntaxError


def test_unsupported_syntax_raises(compile_one_line):
    with pytest.raises(NotSupportedSyntaxError):
        compile_one_line("x = 1\ndel x\n")

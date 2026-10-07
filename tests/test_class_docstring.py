"""Class-body docstring: a leading string statement becomes __doc__, following
CPython's compile.c rule — first statement of the body only, and only str
constants (bytes/numbers/f-strings don't count). The string is peeled off the
body and compiled as `__doc__ := "..."`, so the locals() snapshot carries it
into type(); a later explicit `__doc__ = ...` still wins, as in real Python.

Non-first bare strings keep real-Python behavior: evaluated and discarded,
leaving __doc__ as None.
"""

def test_class_docstring_with_body(run_both):
    src = 'class A:\n    """my doc"""\n    x = 1\nprint(A.__doc__)\n'
    assert run_both(src) == "my doc\n"

def test_class_docstring_only(run_both):
    src = 'class A:\n    """only"""\nprint(A.__doc__)\n'
    assert run_both(src) == "only\n"

def test_class_docstring_non_first_is_not_docstring(run_both):
    src = 'class A:\n    x = 1\n    "late"\nprint(A.__doc__)\n'
    assert run_both(src) == "None\n"

def test_class_docstring_explicit_override_wins(run_both):
    src = 'class A:\n    """auto"""\n    __doc__ = "manual"\nprint(A.__doc__)\n'
    assert run_both(src) == "manual\n"

"""ClassDef -> type(name, bases, ns): the body compiles into a zero-arg
lambda whose locals() snapshot becomes the namespace. A leading str statement
becomes `__doc__ := "..."` (CPython: first statement of the body only, str
constants only — bytes/numbers/f-strings don't count); a later explicit
`__doc__ = ...` still wins. The metaclass= keyword is lifted to the callable
itself.
"""


def test_class_body(run_both):
    assert run_both("class A:\n    x = 1\nprint(A.x)\n") == "1\n"


def test_class_sequential_reference(run_both):
    # later class-body statements can reference earlier class-level names
    assert run_both("class A:\n    x = 1\n    y = x + 1\nprint(A.y)\n") == "2\n"


def test_class_method(run_both):
    src = "class A:\n    def f(self):\n        return 42\nprint(A().f())\n"
    assert run_both(src) == "42\n"


def test_class_no_module_leak(run_both):
    # the class body runs in its own scope: class-level x must not shadow
    # the module-level binding after the statement
    src = 'x = "module"\nclass A:\n    x = "class"\nprint(x, A.x)\n'
    assert run_both(src) == "module class\n"


def test_class_metaclass_kwarg(run_both):
    src = (
        "class Meta(type):\n"
        "    marker = 1\n"
        "class A(metaclass=Meta):\n"
        "    x = 1\n"
        "print(type(A) is Meta, A.marker, A.x)\n"
    )
    assert run_both(src) == "True 1 1\n"


def test_class_inheritance(run_both):
    src = "class A:\n    x = 1\nclass B(A):\n    y = 2\nprint(B().x, B().y)\n"
    assert run_both(src) == "1 2\n"


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

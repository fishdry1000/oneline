"""Regression tests for syntax that compiles and runs correctly today."""


def test_print_and_expressions(run_both):
    assert run_both("print(1 + 2)\nprint('a', [1, 2])\n") == "3\na [1, 2]\n"


def test_assign_single(run_both):
    assert run_both("x = 3\nprint(x)\n") == "3\n"


def test_assign_then_use(run_both):
    assert run_both("x = 3\ny = x * 2\nprint(x, y)\n") == "3 6\n"


def test_assign_chained(run_both):
    assert run_both("a = b = 2\nprint(a, b)\n") == "2 2\n"


def test_for_break(run_both):
    src = (
        "for i in range(10):\n"
        "    print(i)\n"
        "    if i == 2:\n"
        "        break\n"
        "print('after')\n"
    )
    assert run_both(src) == "0\n1\n2\nafter\n"


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


def test_function_return_value(run_both):
    src = "def add(a, b):\n    return a + b\nprint(add(1, 2))\n"
    assert run_both(src) == "3\n"


def test_function_without_return(run_both):
    # falling off the end of a function is an implicit `return None`
    src = "def f():\n    print('in f')\nf()\nprint('ok')\n"
    assert run_both(src) == "in f\nok\n"


def test_function_return_after_if(run_both):
    # the implicit bare return must sit behind the break gate so an early
    # return value is not clobbered when the condition is false
    src = (
        "def f(c):\n"
        "    if c:\n"
        "        return 1\n"
        "    else:\n"
        "        print('no')\n"
        "print(f(True), f(False))\n"
    )
    assert run_both(src) == "no\n1 None\n"


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


def test_for_plain(run_both):
    src = "for i in range(3):\n    print(i)\n"
    assert run_both(src) == "0\n1\n2\n"


def test_for_continue(run_both):
    src = "for i in range(6):\n    if i % 2:\n        continue\n    print(i)\n"
    assert run_both(src) == "0\n2\n4\n"


def test_for_nested(run_both):
    src = "for i in range(2):\n    for j in range(2):\n        print(i, j)\n"
    assert run_both(src) == "0 0\n0 1\n1 0\n1 1\n"


def test_import(run_both):
    assert run_both("import math\nprint(math.pi > 3)\n") == "True\n"


def test_import_as(run_both):
    assert run_both("import math as m\nprint(m.e > 2)\n") == "True\n"


def test_from_import_attribute(run_both):
    assert run_both("from math import sqrt\nprint(sqrt(4))\n") == "2.0\n"


def test_from_import_submodule(run_both):
    # os.path is a submodule: __import__ returns the parent, getattr digs it out
    assert run_both("from os import path\nprint(path.sep == chr(92) or path.sep == '/')\n") == "True\n"


def test_from_import_asname(run_both):
    assert run_both("from math import sqrt as s\nprint(s(9))\n") == "3.0\n"


def test_function_bare_return(run_both):
    src = "def f():\n    print('side')\n    return\nf()\nprint('ok')\n"
    assert run_both(src) == "side\nok\n"


def test_unsupported_syntax_raises(compile_one_line):
    import pytest

    from oneline import NotSupportedSyntaxError

    with pytest.raises(NotSupportedSyntaxError):
        compile_one_line("x = 1\ndel x\n")


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

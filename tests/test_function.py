"""FunctionDef -> a lambda whose body is a flag-driven tuple ending with the
__oneline_return__ flag; [-1][0] unpacks the return value. A body not ending
in Return gets an implicit bare return appended behind the break gates, so
falling off the end yields None without clobbering early returns.
"""


def test_function_return_value(run_both):
    src = "def add(a, b):\n    return a + b\nprint(add(1, 2))\n"
    assert run_both(src) == "3\n"


def test_function_without_return(run_both):
    # falling off the end of a function is an implicit `return None`
    src = "def f():\n    print('in f')\nf()\nprint('ok')\n"
    assert run_both(src) == "in f\nok\n"


def test_function_bare_return(run_both):
    src = "def f():\n    print('side')\n    return\nf()\nprint('ok')\n"
    assert run_both(src) == "side\nok\n"


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

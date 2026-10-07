"""global and nonlocal declarations.

`global x` routes assignments to `globals().__setitem__("x", v)` — reads
resolve to the module global naturally because the name is never walrus-bound
locally. The declaration statement itself compiles to nothing.

`nonlocal x` needs real static scope analysis (three phases: collect
params/bound/decls per scope, resolve each nonlocal to the nearest enclosing
function binding, propagate cell environments top-down). The owning scope
binds the name through a cell dict (`__oneline_cell_x__ := {}` prepended to
the body, `{0: param}` when the owner binds it as a parameter); writes become
`cell.__setitem__(0, v)`, and — the architectural step — free READS of the
name in the owner and every scope below it are rewritten to `cell[0]`,
respecting shadowing by lambda params, walrus targets and comprehension
targets. This is the first feature that rewrites inside pass-through
expressions.

Rejected like real Python: module-level nonlocal, nonlocal with no enclosing
binding, class-level nonlocal, global+nonlocal for one name in a scope.
"""

import pytest

from oneline import NotSupportedSyntaxError


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_global_basic(run_both):
    src = (
        "g = 1\n"
        "def bump():\n"
        "    global g\n"
        "    g = g + 1\n"
        "    return g\n"
        "bump()\n"
        "bump()\n"
        "print(g)\n"
    )
    assert run_both(src) == "3\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_global_augmented(run_both):
    src = "g = 5\ndef bump():\n    global g\n    g += 2\nbump()\nprint(g)\n"
    assert run_both(src) == "7\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_global_declaration_nested_in_if(run_both):
    src = (
        "g = 0\n"
        "def f(c):\n"
        "    if c:\n"
        "        global g\n"
        "        g = 10\n"
        "    return g\n"
        "print(f(True), f(False))\n"
    )
    assert run_both(src) == "10 10\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_module_level_global_is_a_noop(run_both):
    assert run_both("global g\ng = 1\nprint(g)\n") == "1\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_nonlocal_basic(run_both):
    src = (
        "def outer():\n"
        "    x = 1\n"
        "    def inner():\n"
        "        nonlocal x\n"
        "        x = x + 1\n"
        "        return x\n"
        "    inner()\n"
        "    inner()\n"
        "    return x\n"
        "print(outer())\n"
    )
    assert run_both(src) == "3\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_nonlocal_intermediate_free_reader(run_both):
    # mid reads x without binding it: its read must see the cell, not go stale
    src = (
        "def outer():\n"
        "    x = 1\n"
        "    def inner():\n"
        "        nonlocal x\n"
        "        x = 5\n"
        "    def mid():\n"
        "        return x\n"
        "    inner()\n"
        "    return mid()\n"
        "print(outer())\n"
    )
    assert run_both(src) == "5\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_nonlocal_owner_binds_as_parameter(run_both):
    src = (
        "def counter(start):\n"
        "    def inc():\n"
        "        nonlocal start\n"
        "        start += 1\n"
        "        return start\n"
        "    return inc\n"
        "c = counter(10)\n"
        "c()\n"
        "print(c())\n"
    )
    assert run_both(src) == "12\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_nonlocal_shared_cell_between_siblings(run_both):
    src = (
        "def make():\n"
        "    n = 0\n"
        "    def inc():\n"
        "        nonlocal n\n"
        "        n += 1\n"
        "        return n\n"
        "    def get():\n"
        "        return n\n"
        "    return inc, get\n"
        "pair = make()\n"
        "inc = pair[0]\n"
        "get = pair[1]\n"
        "inc()\n"
        "inc()\n"
        "print(get())\n"
    )
    assert run_both(src) == "2\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_nonlocal_conditional_first_assign(run_both):
    # the cell exists from function entry, so either branch can bind it
    src = (
        "def f(c):\n"
        "    if c:\n"
        "        x = 1\n"
        "    else:\n"
        "        x = 2\n"
        "    def g():\n"
        "        nonlocal x\n"
        "        return x\n"
        "    return g()\n"
        "print(f(True), f(False))\n"
    )
    assert run_both(src) == "1 2\n"


def test_local_shadow_without_nonlocal_is_untouched(run_both):
    src = (
        "def outer():\n"
        "    x = 1\n"
        "    def inner():\n"
        "        x = 100\n"
        "        return x\n"
        "    inner()\n"
        "    return x\n"
        "print(outer())\n"
    )
    assert run_both(src) == "1\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_nonlocal_two_levels_with_middle_reader(run_both):
    src = (
        "def outer():\n"
        "    x = 1\n"
        "    def mid():\n"
        "        def inner():\n"
        "            nonlocal x\n"
        "            x = 9\n"
        "        inner()\n"
        "        return x\n"
        "    return mid()\n"
        "print(outer())\n"
    )
    assert run_both(src) == "9\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_global_and_nonlocal_in_one_nest(run_both):
    src = (
        "g = 10\n"
        "def outer():\n"
        "    x = 1\n"
        "    global g\n"
        "    g = 2\n"
        "    def inner():\n"
        "        nonlocal x\n"
        "        x = x + g\n"
        "        return x\n"
        "    return inner()\n"
        "print(outer(), g)\n"
    )
    assert run_both(src) == "3 2\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_cell_read_inside_comprehension(run_both):
    src = (
        "def outer():\n"
        "    x = 2\n"
        "    def inner():\n"
        "        nonlocal x\n"
        "        x = x + 1\n"
        "    inner()\n"
        "    return [i * x for i in range(3)]\n"
        "print(outer())\n"
    )
    assert run_both(src) == "[0, 3, 6]\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_comprehension_target_shadows_cell_name(run_both):
    src = (
        "def outer():\n"
        "    x = 100\n"
        "    def inner():\n"
        "        nonlocal x\n"
        "        x = 5\n"
        "    inner()\n"
        "    return [x for x in range(3)]\n"
        "print(outer())\n"
    )
    assert run_both(src) == "[0, 1, 2]\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_source_walrus_global_statement(run_both):
    # PEP 572: a walrus on a name declared global in this scope writes the
    # global, exactly like a plain assignment
    src = (
        "g = 1\n"
        "def f():\n"
        "    global g\n"
        "    (g := 2)\n"
        "    return g\n"
        "print(f(), g)\n"
    )
    assert run_both(src) == "2 2\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_source_walrus_global_value_kept(run_both):
    src = (
        "g = 1\n"
        "def f():\n"
        "    global g\n"
        "    return (g := 5) + 1\n"
        "print(f(), g)\n"
    )
    assert run_both(src) == "6 5\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_source_walrus_global_in_if_test(run_both):
    src = (
        "g = 0\n"
        "def f():\n"
        "    global g\n"
        "    if (g := 3) > 2:\n"
        "        return 'yes'\n"
        "    return 'no'\n"
        "print(f(), g)\n"
    )
    assert run_both(src) == "yes 3\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_source_walrus_global_in_comprehension(run_both):
    src = (
        "g = 0\n"
        "def f():\n"
        "    global g\n"
        "    return [g := i for i in range(3)]\n"
        "print(f(), g)\n"
    )
    assert run_both(src) == "[0, 1, 2] 2\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_source_walrus_nonlocal(run_both):
    src = (
        "def outer():\n"
        "    x = 1\n"
        "    def inner():\n"
        "        nonlocal x\n"
        "        (x := 5)\n"
        "        return x\n"
        "    inner()\n"
        "    return x\n"
        "print(outer())\n"
    )
    assert run_both(src) == "5\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_lambda_walrus_shadows_global_declaration(run_both):
    # a lambda cannot carry a declaration, so its own walrus stays local
    src = (
        "g = 1\n"
        "def f():\n"
        "    global g\n"
        "    h = lambda: (g := 9)\n"
        "    h()\n"
        "    return g\n"
        "print(f(), g)\n"
    )
    assert run_both(src) == "1 1\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_global_declaration_does_not_leak_across_functions(run_both):
    # b's g is a plain local: a's global declaration must not affect it
    src = (
        "def a():\n"
        "    global g\n"
        "    g = 1\n"
        "    return g\n"
        "def b():\n"
        "    g = 5\n"
        "    return g\n"
        "print(a(), b(), g)\n"
    )
    assert run_both(src) == "1 5 1\n"


@pytest.mark.xfail(reason="global/nonlocal are not implemented")
def test_global_walrus_value_evaluated_once(run_both):
    src = (
        "calls = []\n"
        "def v():\n"
        "    calls.append(1)\n"
        "    return 10\n"
        "g = 0\n"
        "def f():\n"
        "    global g\n"
        "    (g := v())\n"
        "    return g\n"
        "f()\n"
        "print(len(calls))\n"
    )
    assert run_both(src) == "1\n"


# --- rejections (already correct while the feature is absent) ---


def test_module_level_nonlocal_rejected(compile_one_line):
    with pytest.raises(NotSupportedSyntaxError):
        compile_one_line("nonlocal x\n")


def test_nonlocal_without_binding_rejected(compile_one_line):
    with pytest.raises(NotSupportedSyntaxError):
        compile_one_line("def f():\n    nonlocal q\n")


def test_class_level_nonlocal_rejected(compile_one_line):
    with pytest.raises(NotSupportedSyntaxError):
        compile_one_line("def f():\n    class C:\n        nonlocal q\n")


def test_global_nonlocal_clash_rejected(compile_one_line):
    with pytest.raises(NotSupportedSyntaxError):
        compile_one_line("def f():\n    global x\n    nonlocal x\n")

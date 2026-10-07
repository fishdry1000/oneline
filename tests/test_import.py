"""Imports compile to __import__ calls: `import m` binds the top-level
package via fromlist [""], `import m as n` rebinds under the alias.
`from m import x` binds the module into __oneline_mod__ once and reads
attributes off it, mirroring IMPORT_NAME + IMPORT_FROM — which is what makes
submodule imports like os.path work. Relative imports are rejected.
"""


def test_import(run_both):
    assert run_both("import math\nprint(math.pi > 3)\n") == "True\n"


def test_import_as(run_both):
    assert run_both("import math as m\nprint(m.e > 2)\n") == "True\n"


def test_from_import_attribute(run_both):
    assert run_both("from math import sqrt\nprint(sqrt(4))\n") == "2.0\n"


def test_from_import_submodule(run_both):
    # os.path is a submodule: __import__ returns the parent, getattr digs it out
    assert run_both(
        "from os import path\nprint(path.sep == chr(92) or path.sep == '/')\n"
    ) == "True\n"


def test_from_import_asname(run_both):
    assert run_both("from math import sqrt as s\nprint(s(9))\n") == "3.0\n"

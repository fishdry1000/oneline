#!/usr/bin/env python3
"""
oneline -- compile python code into one line

Usage:
    ./oneline.py code.py [out.py]
"""

import sys
from ast import (
    AST,
    And,
    Assign,
    Attribute,
    AugAssign,
    BoolOp,
    Break,
    Call,
    ClassDef,
    Constant,
    Continue,
    Expr,
    For,
    FunctionDef,
    Global,
    If,
    IfExp,
    Import,
    ImportFrom,
    Lambda,
    List,
    ListComp,
    Module,
    Name,
    NamedExpr,
    NodeTransformer,
    Nonlocal,
    Not,
    Or,
    Pass,
    Return,
    Slice,
    Subscript,
    Tuple,
    UnaryOp,
    While,
    arguments,
    comprehension,
    expr,
    fix_missing_locations,
    parse,
    stmt,
    unparse,
)
from collections.abc import Callable
from typing import ClassVar, Literal, get_args


class NotSupportedSyntaxError(ValueError): ...


class _Scope:
    def __init__(self, name: str | None):
        self.name = name
        self.nonlocals: set[str] = set()
        self.globals: set[str] = set()


class OneLine(NodeTransformer):
    type BreakType = Literal["break", "continue", "return"]
    BREAK_TYPES: tuple[BreakType, ...] = get_args(BreakType.__value__)
    type BreakHandler = Callable[[expr | None], None]
    type Feature = BreakType | Literal["aug_assign", "nonlocal"]

    def __init__(self) -> None:
        self.break_handlers: dict[OneLine.BreakType, list[OneLine.BreakHandler]] = {
            t: [] for t in self.BREAK_TYPES
        }
        self.used_features: set[OneLine.Feature] = set()
        self.just_breaked: set[OneLine.BreakType] = set()
        self._scopes: list[_Scope] = [_Scope(None)]

    @staticmethod
    def _gen_name(s: str):
        return f"__oneline_{s}__"

    @staticmethod
    def _gen_break_name(t: BreakType):
        # this satisfies my ide :>
        return f"__oneline_{t}__"

    @staticmethod
    def _load_name(s: str) -> Name:
        return Name(OneLine._gen_name(s))

    @staticmethod
    def _load_break_name(t: BreakType):
        return Name(OneLine._gen_name(t))

    @staticmethod
    def _store_name(s: str, v: expr) -> NamedExpr:
        return NamedExpr(Name(OneLine._gen_name(s)), v)

    @staticmethod
    def _store_break_name(t: BreakType, v: expr) -> NamedExpr:
        return NamedExpr(Name(OneLine._gen_name(t)), v)

    @staticmethod
    def _conj(*es: expr) -> Tuple:
        elts = []
        for e in es:
            if isinstance(e, Tuple):
                elts.extend(e.elts)
            else:
                elts.append(e)
        return Tuple(
            elts,
        )

    def visit(self, node: AST) -> expr:
        print(f"visiting: {type(node).__name__}")
        res = super().visit(node)
        if not isinstance(res, expr):
            raise NotSupportedSyntaxError(node)
        return res

    def list_visit(self, nodes: list[stmt]) -> Tuple:
        print(f"list visiting: {[type(node).__name__ for node in nodes]}")
        return self._conj(*(self.visit(node) for node in nodes))

    def list_visit_breakable(self, nodes: list[stmt], *break_types: BreakType) -> Tuple:
        print(f"breakable list visiting: {[type(node).__name__ for node in nodes]}")
        self.used_features |= set(break_types)
        tup: Tuple = Tuple([])
        cur: list[expr] = tup.elts
        is_breaking, break_value = None, None

        def break_handler(t: OneLine.BreakType, value: expr | None):
            nonlocal is_breaking, break_value
            is_breaking, break_value = t, value

        for break_type in break_types:
            self.break_handlers[break_type].append(
                lambda v, break_type=break_type: break_handler(break_type, v)
            )

        self.just_breaked = set()
        node = None
        for node in nodes:
            cur.append(self._check_scope(self.visit(node)))
            if is_breaking:
                self.just_breaked.add(is_breaking)
                newtup = Tuple([])
                cur.append(BoolOp(Or(), [self._load_break_name(is_breaking), newtup]))
                cur = newtup.elts
                is_breaking, break_value = False, None

        if "return" in break_types and not isinstance(node, Return):
            cur.append(self.visit_Return(Return()))

        for break_type in self.just_breaked:
            tup.elts.insert(0, self._store_break_name(break_type, Constant(None)))

        for break_type in break_types:
            self.break_handlers[break_type].pop()
        return tup

    def bubble_break(self, t: BreakType, value: expr | None = None) -> None:
        if not self.break_handlers[t]:
            raise ValueError(f"{t!r} is not allowed in this scope")
        self.used_features.add(t)
        self.break_handlers[t][-1](value)

    def visit_Return(self, node: Return) -> NamedExpr:
        self.bubble_break("return", node.value)
        return self._store_break_name(
            "return", Tuple([node.value] if node.value else [Constant(None)])
        )

    def visit_Break(self, node: Break) -> NamedExpr:
        self.bubble_break("break")
        return self._store_break_name("break", Constant(True))

    def visit_Continue(self, node: Continue) -> NamedExpr:
        self.bubble_break("continue")
        return self._store_break_name("continue", Constant(True))

    TAKEWHILE = (
        f"({_gen_name('takewhile')} := lambda pred, it: (s := object(), "
        "it := iter(it), iter(lambda: (x := next(it)) if pred() else s, s))[2])"
    )

    def visit_Module(self, node: Module) -> expr:
        try:
            compile(unparse(node), "<oneline>", "exec")
        except SyntaxError as e:
            raise NotSupportedSyntaxError(node) from e
        res = self.list_visit(node.body)
        if "break" in self.used_features:
            res = self._conj(parse(self.TAKEWHILE, mode="eval").body, res)
        if "aug_assign" in self.used_features:
            res = self._conj(
                self._store_name(
                    "operator", Call(Name("__import__"), [Constant("operator")])
                ),
                res,
            )
        for break_type in self.just_breaked:
            res = self._conj(self._store_break_name(break_type, Constant(None)), res)
        return res

    def visit_Expr(self, node: Expr) -> expr:
        return node.value

    def visit_If(self, node: If) -> IfExp:
        return IfExp(
            node.test, self.list_visit(node.body), self.list_visit(node.orelse)
        )

    def visit_For(self, node: For) -> ListComp | Tuple:
        elt = self.list_visit_breakable(node.body, "continue", "break")
        iter = (
            Call(
                self._load_name("takewhile"),
                [
                    Lambda(arguments(), UnaryOp(Not(), self._load_break_name("break"))),
                    node.iter,
                ],
            )
            if "break" in self.just_breaked
            else node.iter
        )

        lc = ListComp(elt, [comprehension(node.target, iter, [], is_async=0)])

        if node.orelse:
            lc = self._conj(
                lc,
                BoolOp(
                    Or(), [self._load_break_name("break"), self.list_visit(node.orelse)]
                )
                if "break" in self.just_breaked
                else self.list_visit(node.orelse),
            )
        for break_type in self.just_breaked:
            lc = self._conj(lc, self._store_break_name(break_type, Constant(None)))

        return lc

    def visit_While(self, node: While) -> ListComp | Tuple:
        elt = self.list_visit_breakable(node.body, "continue", "break")
        iter = Call(
            self._load_name("takewhile"),
            [
                Lambda(
                    arguments(),
                    BoolOp(
                        And(),
                        [UnaryOp(Not(), self._load_break_name("break")), node.test],
                    ),
                )
                if "break" in self.just_breaked
                else Lambda(arguments(), node.test),
                Call(Name("iter"), [Name("int"), Constant(1)]),
            ],
        )

        lc = ListComp(elt, [comprehension(Name("_"), iter, [], is_async=0)])

        if node.orelse:
            lc = self._conj(
                lc,
                BoolOp(
                    Or(), [self._load_break_name("break"), self.list_visit(node.orelse)]
                )
                if "break" in self.just_breaked
                else self.list_visit(node.orelse),
            )
        for break_type in self.just_breaked:
            lc = self._conj(lc, self._store_break_name(break_type, Constant(None)))

        return lc

    def visit_Pass(self, node: Pass) -> Tuple:
        return Tuple([])

    @staticmethod
    def _fix_slice(s: Slice) -> Call:
        args = [e or Constant(None) for e in (s.lower, s.upper)]
        if s.step is not None:
            args.append(s.step)
        return Call(Name("slice"), args)

    def visit_Assign(self, node: Assign) -> Tuple:
        elts = []
        value = node.value
        if len(node.targets) > 1 or not isinstance(node.targets[0], Name):
            elts.append(self._store_name("value", value))
            value = self._load_name("value")
        for target in node.targets:
            match target:
                case Name():
                    elts.append(NamedExpr(target, value))
                case Subscript(val, sli):
                    if isinstance(sli, Slice):
                        sli = self._fix_slice(sli)
                    elts.append(Call(Attribute(val, "__setitem__"), [sli, value]))
                case Attribute(val, attr):
                    elts.append(Call(Name("setattr"), [val, Constant(attr), value]))
                case _:
                    raise NotSupportedSyntaxError(target)
        return self._conj(*elts)

    AUG_TO_IOP: ClassVar = {
        "Add": "iadd",
        "Sub": "isub",
        "Mult": "imul",
        "Div": "itruediv",
        "FloorDiv": "ifloordiv",
        "Mod": "imod",
        "Pow": "ipow",
        "LShift": "ilshift",
        "RShift": "irshift",
        "BitAnd": "iand",
        "BitOr": "ior",
        "BitXor": "ixor",
        "MatMult": "imatmul",
    }

    def visit_AugAssign(self, node: AugAssign) -> NamedExpr | Tuple:
        self.used_features.add("aug_assign")
        iop = Attribute(
            self._load_name("operator"),
            self.AUG_TO_IOP[type(node.op).__name__],
        )
        match node.target:
            case Name():
                return NamedExpr(
                    node.target, Call(iop, [Name(node.target.id), node.value])
                )
            case Subscript(val, sli):
                if isinstance(sli, Slice):
                    sli = self._fix_slice(sli)
                return self._conj(
                    self._store_name("aug_obj", val),
                    self._store_name("aug_key", sli),
                    Call(
                        Attribute(self._load_name("aug_obj"), "__setitem__"),
                        [
                            self._load_name("aug_key"),
                            Call(
                                iop,
                                [
                                    Subscript(
                                        self._load_name("aug_obj"),
                                        self._load_name("aug_key"),
                                    ),
                                    node.value,
                                ],
                            ),
                        ],
                    ),
                )
            case Attribute(val, attr):
                return self._conj(
                    self._store_name("aug_obj", val),
                    Call(
                        Name("setattr"),
                        [
                            self._load_name("aug_obj"),
                            Constant(attr),
                            Call(
                                iop,
                                [
                                    Attribute(self._load_name("aug_obj"), attr),
                                    node.value,
                                ],
                            ),
                        ],
                    ),
                )
            case _:
                raise NotSupportedSyntaxError(node)

    def visit_Import(self, node: Import) -> Tuple:
        if any(name.name.startswith(".") for name in node.names):
            raise NotSupportedSyntaxError(node)
        return self._conj(
            *(
                NamedExpr(
                    Name(name.asname or name.name),
                    Call(
                        Name("__import__"),
                        [
                            Constant(name.name),
                            Call(Name("globals")),
                            Call(Name("locals")),
                            List([Constant("")]),
                        ],
                    ),
                )
                for name in node.names
            )
        )

    def visit_ImportFrom(self, node: ImportFrom) -> Tuple:
        if any(name.name.startswith(".") for name in node.names):
            raise NotSupportedSyntaxError(node)
        return self._conj(
            self._store_name(
                "mod",
                Call(
                    Name("__import__"),
                    [
                        Constant(node.module),
                        Call(Name("globals")),
                        Call(Name("locals")),
                        List([Constant(name.name) for name in node.names]),
                    ],
                ),
            ),
            *(
                NamedExpr(
                    Name(name.asname or name.name),
                    Attribute(self._load_name("mod"), name.name),
                )
                for name in node.names
            ),
        )

    def visit_Nonlocal(self, node: Nonlocal) -> Tuple:
        self._scopes[-1].nonlocals |= set(node.names)
        self.used_features.add("nonlocal")
        return Tuple([])

    def visit_Global(self, node: Global) -> Tuple:
        self._scopes[-1].globals |= set(node.names)
        return Tuple([])

    def _check_scope(self, node: expr) -> expr:
        scope = self._scopes[-1]
        if not scope.globals and not scope.nonlocals:
            return node

        class CheckScope(NodeTransformer):
            def visit_Lambda(self, node: Lambda) -> Lambda:
                return node

            def visit_NamedExpr(self, node: NamedExpr) -> AST:
                if node.target.id in scope.nonlocals and scope.name is not None:
                    fn = Name(scope.name)
                    cell = Subscript(
                        Attribute(fn, "__closure__"),
                        Call(
                            Attribute(
                                Attribute(Attribute(fn, "__code__"), "co_freevars"),
                                "index",
                            ),
                            [Constant(node.target.id)],
                        ),
                    )
                    store = Call(
                        Name("setattr"),
                        [cell, Constant("cell_contents"), OneLine._load_name("value")],
                    )
                    tail = Name(node.target.id)
                elif node.target.id in scope.globals:
                    store = Call(
                        Attribute(Call(Name("globals")), "__setitem__"),
                        [Constant(node.target.id), OneLine._load_name("value")],
                    )
                    tail = OneLine._load_name("value")
                else:
                    return self.generic_visit(node)

                return Subscript(
                    OneLine._conj(
                        OneLine._store_name("value", self.visit(node.value)),
                        store,
                        tail,
                    ),
                    Constant(-1),
                )

        return CheckScope().visit(node)

    def visit_FunctionDef(self, node: FunctionDef) -> NamedExpr:
        self._scopes.append(_Scope(node.name))
        res = NamedExpr(
            Name(node.name),
            Lambda(
                node.args,
                Subscript(
                    Subscript(
                        self._conj(
                            self.list_visit_breakable(node.body, "return"),
                            self._load_break_name("return"),
                        ),
                        Constant(-1),
                    ),
                    Constant(0),
                ),
            ),
        )
        self._scopes.pop()
        return res

    def visit_ClassDef(self, node: ClassDef) -> NamedExpr:
        self._scopes.append(_Scope(None))
        if not node.body:
            raise NotSupportedSyntaxError(node)
        elts = []
        if (
            isinstance(node.body[0], Expr)
            and isinstance(node.body[0].value, Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            elts.append(NamedExpr(Name("__doc__"), Constant(node.body[0].value.value)))
            node.body.pop(0)

        elts.extend(self.list_visit(node.body).elts)
        ns = Subscript(self._conj(*elts, Call(Name("locals"), [])), Constant(-1))

        metaclass = Name("type")
        keywords = []
        for kw in node.keywords:
            if kw.arg == "metaclass":
                metaclass = kw.value
            else:
                keywords.append(kw)
        self._scopes.pop()
        return NamedExpr(
            Name(node.name),
            Call(
                metaclass,
                [
                    Constant(node.name),
                    Tuple(node.bases),
                    Call(Lambda(arguments(), ns), [], []),
                ],
                keywords,
            ),
        )

    def generic_visit(self, node: AST):
        raise NotSupportedSyntaxError(node)


def main() -> int:
    argv_len = len(sys.argv)
    if argv_len <= 1 or argv_len >= 4:
        print("oneline.py: usage: oneline.py <source> [<target>]", file=sys.stderr)
        return 1

    source_file = sys.argv[1]
    target_file = sys.argv[2] if argv_len >= 3 else "output.py"

    with open(source_file) as f:
        try:
            source = f.read()
        except OSError as e:
            print(f"oneline.py: cannot read file {source_file}: {e}", file=sys.stderr)
            return 2

    tree = parse(source)
    tree = OneLine().visit(tree)
    fix_missing_locations(tree)

    target = unparse(tree)

    with open(target_file, mode="w+") as f:
        try:
            source = f.write(target)
        except OSError as e:
            print(f"oneline.py: cannot write file {target_file}: {e}", file=sys.stderr)
            return 2

    print(f"written to {target_file}.")

    print(target)

    return 0


if __name__ == "__main__":
    sys.exit(main())

from ast import parse, unparse

from oneline import OneLine

x = parse(
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

print(unparse(OneLine().visit(x)))

print("---")


def make():
    n = 0

    def inc():
        nonlocal n
        n += 1
        return n

    def get():
        return n

    return inc, get


pair = make()
inc = pair[0]
get = pair[1]
inc()
inc()
print(get())

print("---")

_ = (
    (__oneline_return__ := None),
    (__oneline_mod__ := __import__("sys", globals(), locals(), ["_getframe"])),
    (__oneline__getframe__ := __oneline_mod__._getframe),
    (__oneline_operator__ := __import__("operator")),
    (
        make := (
            lambda: (
                (__oneline_return__ := None),
                ((n := 0),),
                (
                    inc := (
                        lambda: (
                            (__oneline_return__ := None),
                            (),
                            (
                                (__oneline_value__ := __oneline_operator__.iadd(n, 1)),
                                __oneline__getframe__(1).f_locals.__setitem__(
                                    "n", __oneline_value__
                                ),
                                __oneline_value__,
                            )[-1],
                            (__oneline_return__ := (n,)),
                            __oneline_return__ or (),
                            __oneline_return__,
                        )[-1][0]
                    )
                ),
                (
                    get := (
                        lambda: (
                            (__oneline_return__ := None),
                            (__oneline_return__ := (n,)),
                            __oneline_return__ or (),
                            __oneline_return__,
                        )[-1][0]
                    )
                ),
                (__oneline_return__ := ((inc, get),)),
                __oneline_return__ or (),
                __oneline_return__,
            )[-1][0]
        )
    ),
    (pair := make()),
    (inc := pair[0]),
    (get := pair[1]),
    inc(),
    inc(),
    print(get()),
)

def foo():
    x = 1

    def bar():
        nonlocal x
        x = 2

    bar()
    print(x)


foo()

print("---")

from sys import _getframe

oh = 1
_ = (
    foo2 := lambda: (
        x := 1,
        bar2 := lambda: _getframe(1).f_locals.__setitem__("x", 2),
        bar2(),
        print(x),
    ),
    foo2(),
)

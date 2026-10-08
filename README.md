# oneline.py

Write your Python code in one line.  
把你的 python 代码写成一行

Usage:  
用法：

```sh
wget https://github.com/fishdry1000/oneline/raw/main/src/oneline/oneline.py
./oneline.py code.py [out.py]
```

Example:  
例子：

**add.py**
```python
#!/usr/bin/env python3
"""
add -- add numbers

Usage:
    ./add.py 1 3 5
"""

import sys


def main() -> int:
    acc = 0
    for arg in sys.argv[1:]:
        acc += float(arg)
    print(acc)
    return 0


if __name__ == "__main__":
    sys.exit(main())

```

**output.py** (formatted)
```python
(
    (__oneline_operator__ := __import__("operator")),
    (__doc__ := "\nadd -- add numbers\n\nUsage:\n    ./add.py 1 3 5\n"),
    (sys := __import__("sys", globals(), locals(), [""])),
    (
        main := (
            lambda: (
                (acc := 0),
                [
                    ((acc := __oneline_operator__.iadd(acc, float(arg))),)
                    for arg in sys.argv[1:]
                ],
                print(acc),
                (__oneline_return__ := (0,)),
                __oneline_return__,
            )[-1][0]
        )
    ),
    (sys.exit(main()),) if __name__ == "__main__" else (),
)

```
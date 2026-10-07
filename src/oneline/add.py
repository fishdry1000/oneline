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
        #        try:
        acc = acc + float(arg)
    #        except ValueError:
    #            print(f"add: except number, reveieved: {arg}", file=sys.stderr)
    #            return 1
    print(acc)
    return 0


if __name__ == "__main__":
    sys.exit(main())

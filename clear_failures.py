#!/usr/bin/env python3
from pathlib import Path
import sys

try:
    query = sys.argv[1]
except IndexError:
    query = ""

for outcome in Path("output").glob("**/outcome"):
    if outcome.read_text() == "failed":
        do = False
        if query:
            for fn in Path(outcome.parent).glob("round*.stderr"):
                stderr = fn.read_text()
                if query.lower() in stderr.lower():
                    do = True
        else:
            do = True
        if do:
            print(outcome)
           # outcome.unlink()
    if not outcome.with_name("result").exists():
        print(outcome)


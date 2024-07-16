#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from packaging.version import Version


def normalise_package_name(name):
    parts = re.split("[_.-]+", name.lower())
    parts = [x for x in parts if x]
    return "-".join(parts)


if "/" in sys.argv[1]:
    path = Path(sys.argv[1])
else:
    pkg = normalise_package_name(sys.argv[1])
    path = Path("output") / pkg
    try:
        ver = sys.argv[2]
    except IndexError:
        ver = [x.name for x in path.glob("*") if x.is_dir()]
        try:
            ver.sort(key=Version)
        except:
            ver.sort()
        ver = ver[-1]
    path = path / ver

rounds = list(path.glob("round*.stderr"))
rounds.sort()
try:
    round = rounds[-1]
    print(round.read_text())




except:
    poetry_error = (path / "poetry.stderr").read_text()
    print(poetry_error)

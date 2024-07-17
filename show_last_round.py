#!/usr/bin/env python3
import subprocess
import os
import re
import shared
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
    pkg = sys.argv[1].split("/")[-2]
    ver = sys.argv[1].split("/")[-1]
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
    rt = round.read_text()
    print(rt)
except:
    poetry_error = (path / "poetry.stderr").read_text()
    print(poetry_error)
    sys.exit()

failed_builders = re.findall("error: builder for '([^']+)'", rt)
if failed_builders:
    print("")
    if len(failed_builders) > 1:
        for ii, builder in enumerate(failed_builders, 1):
            name = shared.pkg_from_derivation_name(builder)
            print(f"Builder {ii}: {name}")
        chosen = input("Choose builder: ")
    else:
        chosen = 0
    chosen = int(chosen)
    chosen_builder = failed_builders[chosen - 1]
    chosen_name = shared.pkg_from_derivation_name(chosen_builder)

    full_log = subprocess.check_output(["nix", "log", chosen_builder]).decode("utf-8")
    print(full_log)
    source = re.findall("unpacking source archive (.+)$", full_log, re.MULTILINE)[0]
    if source.endswith(".tar.gz"):
        target = os.path.expanduser(f"~/shu/sha/{chosen_name}")
        os.makedirs(target, exist_ok=True)
        subprocess.run(["tar", "xf", source], cwd=target)
        subprocess.Popen(["kitty", "-d", target])
    subprocess.Popen(["kitty", "-d", "output/" + pkg + "/" + ver])

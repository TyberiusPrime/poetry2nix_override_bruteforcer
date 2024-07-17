#!/usr/bin/env python
from pathlib import Path
import sys
import shutil
import collections
from shared import known_failing

count = collections.Counter()


count["known_failing"] = len(known_failing)

for dir in Path("output").glob("*"):
    if dir.is_dir():
        if dir.name in known_failing:
            continue
        for subdir in dir.glob("*"):
            if subdir.is_dir():
                if (subdir / "result").exists():
                    if (subdir / "build-systems.json").stat().st_size == 2 and (
                        (subdir / "overrides.nix").read_text().count("final: prev") == 1
                    ):
                        count["upstream"] += 1
                    else:
                        count["patched"] += 1
                elif (subdir / "outcome").exists() or (
                    subdir / "round1.stderr"
                ).exists():
                    count["fail"] += 1
                    print(subdir)
                    if "--nuke" in sys.argv:
                        shutil.rmtree(dir)
                else:
                    count["other"] += 1
for k, v in count.items():
    print(k, v)

print("total", sum(count.values()))

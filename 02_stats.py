#!/usr/bin/env python
from pathlib import Path
import sys
import shutil
import collections
from . sharded import known_failing
count = collections.Counter()




count["known_failing"] = len(known_failing)

for dir in Path("output").glob("*"):
    if dir.is_dir():
        for subdir in dir.glob("*"):
            if subdir.is_dir():
                if (subdir / "result").exists():
                    if not (subdir / "round2.stdout").exists():
                        count["upstream"] += 1
                    else:
                        count["patched"] += 1
                else:
                    count["fail"] += 1
                    print(subdir)
                    if "--nuke" in sys.argv:
                        shutil.rmtree(dir)
for k, v in count.items():
    print(k, v)

print("total", sum(count.values()))

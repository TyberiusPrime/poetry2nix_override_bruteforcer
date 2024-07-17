#!/usr/bin/env python
from pathlib import Path
import sys
import shutil
import collections
from shared import known_failing, normalise_package_name, autodetected
import shared

count = collections.Counter()

entries = shared.entries[:]

op = Path("output")

for pkg, version in entries:
    output_path = op / pkg / version
    what = "???"
    if not output_path.exists():
        if pkg in known_failing or (pkg + "-" + version) in known_failing:
            what = "missing:expected"
        else:
            what = "missing:not-done?"
    else:
        if (output_path / "result").exists():
            needed_patch = (output_path / "round2.stderr").exists()
            if needed_patch:
                what = "success:needed_patch"
            else:
                what = "success:upstream"
        else:
            if (output_path / "round1.stderr").exists():
                if pkg in known_failing or (pkg + "-" + version) in known_failing:
                    if pkg in autodetected or (pkg + "-" + version) in autodetected:
                        what = "fail:expected-autodetected"
                    else:
                        what = "fail:expected-manual"
                else:
                    what = "fail:unexpected"
            else:
                what = "missing:not-done"
    count[what] += 1
    if pkg == "zha":
        print(pkg, version, what)


for k, v in count.items():
    print(k, v)

print("total", sum(count.values()), len(entries))
print(
    "% without patch", "%.2f" % (100 * count["success:upstream"] / sum(count.values()))
)
print(
    "% after patch",
    "%.2f"
    % (
        100
        * (count["success:upstream"] + count["success:needed_patch"])
        / sum(count.values())
    ),
)

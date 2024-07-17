#!/usr/bin/env python
from pathlib import Path
import sys
import shutil
import collections
from shared import known_failing, normalise_package_name, autodetected
import shared

count = collections.Counter()

entries = shared.entries[:]

op = Path('output')

for pkg, version in entries:
    output_path = op / pkg / version
    if not output_path.exists():
        if pkg in known_failing or (pkg + '-' + version) in known_failing:
            count['missing:expected'] += 1
        else:
            count["missing:not-done?"] += 1
        #print(output_path)
        continue
    if (output_path / "result").exists():
        needed_patch = (output_path / "round2.stderr").exists()
        if needed_patch:
            count['success:needed_patch'] += 1
        else:
            count['success:upstream'] += 1
    else:
        if (output_path / "round1.stderr").exists():
            if pkg in known_failing or (pkg + '-' + version) in known_failing:
                if pkg in autodetected or (pkg + '-' + version) in autodetected:
                    count['fail:expected-autodetected'] += 1
                else:
                    count['fail:expected-manual'] += 1
            else:
                count['fail:unexpected'] += 1
        else:
            count['missing:not-done'] += 1
    

for k, v in count.items():
    print(k, v)

print("total", sum(count.values()), len(entries))

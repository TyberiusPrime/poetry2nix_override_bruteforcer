#!/usr/bin/env python
from pathlib import Path
import sys
import json
import shutil
import collections
from shared import known_failing, normalise_package_name, autodetected
import shared


outcomes = shared.examine_results()[1]
op = Path("output")

build_systems = collections.defaultdict(set)

for (pkg, version), outcome in outcomes.items():
    if outcome == 'success:needed_patch':
        bs = json.loads((op / pkg / version / 'build-systems.json').read_text())
        for k,v in bs.items():
            build_systems[k].add(frozenset(v))

counts =collections.Counter()
sweep_path = Path("autodetected/needs_sweep")
sweep_path.mkdir(exist_ok=True, parents=True)
for pkg, info in build_systems.items():
    if len(info) == 1:
        counts['one'] += 1
    elif len(info) == 1:
        counts['all_same'] += 1
    else:
        counts['different'] += 1
        (sweep_path / pkg).write_text("yes")

print(counts)

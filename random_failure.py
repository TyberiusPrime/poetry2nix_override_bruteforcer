#!/usr/bin/env python
from pathlib import Path
import subprocess
import random

import shared

fails = []

for dir in Path("output").glob("*"):
    if dir.is_dir():
        if dir.name in shared.known_failing:
            continue
        for subdir in dir.glob("*"):
            if subdir.is_dir():
                if (subdir / "result").exists():
                    if not (subdir / "round2.stdout").exists():
                        continue
                    else:
                        continue
                else:
                    if (subdir / "round1.stderr").exists():
                        fails.append(subdir)

f = random.choice(fails)
print(f)

subprocess.run(['python','show_last_round.py', f])

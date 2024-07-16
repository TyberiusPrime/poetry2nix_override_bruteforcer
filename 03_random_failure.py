#!/usr/bin/env python
from pathlib import Path
import subprocess
import random

fails = []

for dir in Path("output").glob("*"):
    if dir.is_dir():
        for subdir in dir.glob("*"):
            if subdir.is_dir():
                if (subdir / "result").exists():
                    if not (subdir / "round2.stdout").exists():
                        continue
                    else:
                        continue
                else:
                    fails.append(subdir)

f = random.choice(fails)
print(f)

subprocess.run(['python','show_last_round.py', f])

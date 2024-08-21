import sys
from pathlib import Path
import shutil
import subprocess

input_pkgs = [x for x in sys.argv[1:] if not x.startswith('--')]
pkgs = set()

for pkg in input_pkgs:

    cache_file = Path(f"cache/remove_and_rebuild_{pkg}")
    if not cache_file.exists():
        #subprocess.check_call(['fd','-L',pkg], cwd='output', stdout=cache_file.open('w'))
        print(f"Could not find cache file {cache_file} - did 05_assemble.py redirect you here?")
        sys.exit(1)

    raw = cache_file.read_text()
    for line in raw.strip().split("\n"):
        pkg = line.split("/")[0]
        pkgs.add(pkg)

    print(pkgs)

    if not '--no-remove' in sys.argv:
        for pkg in pkgs:
            p =  Path("output") / pkg
            if p.exists():
                print("removing", p)
                shutil.rmtree(p)

print("starting rebuild")
subprocess.check_call(['python','02_build_packages.py', '|'.join(pkgs)])

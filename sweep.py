from pathlib import Path
import os

to_sweep = Path("autodetected/needs_sweep").glob("*")

print("build package list")
os.system('python 01_assemble_package_list.py')


cmd = ['python', '02_build_packages.py', '|'.join([x.name for x in to_sweep])]
print(" ".join(cmd))



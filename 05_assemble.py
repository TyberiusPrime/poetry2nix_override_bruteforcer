#!/usr/bin/env python
import subprocess
import re
from packaging.version import Version
import toml
from pathlib import Path
import sys
import json
import shutil
import collections
import shared


outcomes = shared.examine_results()[1]
ip = Path("output")

build_systems = collections.defaultdict(set)
build_systems_by_version = collections.defaultdict(dict)

overrides = collections.defaultdict(set)


def load_versions(pkg_path):
    poetry_lock = toml.loads(Path(pkg_path / "poetry.lock").read_text())
    res = {}
    for package in poetry_lock["package"]:
        res[package["name"]] = package["version"]
    return res


def extract_overrides(overrides_path):
    raw = overrides_path.read_text()
    start = raw.find("buildSystems)")
    raw = raw[start:]
    raw = raw[raw.find("\n") : raw.rfind("]")].strip()
    blocks = raw.split("(final:")
    res = collections.defaultdict(list)
    for b in blocks:
        if not b.strip():
            continue
        c = b[b.find("{") : b.rfind("}")]
        try:
            pkg = re.findall('"([^"]+)"', c)[0]
        except IndexError:
            print("b is ", repr(b))
            raise
        res[pkg].append(c)
    return res


for (pkg, version), outcome in outcomes.items():
    if outcome == "success:needed_patch":
        bs = json.loads((ip / pkg / version / "build-systems.json").read_text())
        for k, v in bs.items():
            build_systems[k].add(frozenset(v))
        ov = extract_overrides(ip / pkg / version / "overrides.nix")
        for k, v in ov.items():
            overrides[k].add(frozenset(v))

import pprint


counts = collections.Counter()
sweep_path = Path("autodetected/needs_sweep")
needs_sweep = []
sweep_path.mkdir(exist_ok=True, parents=True)
for pkg, info in build_systems.items():
    if len(info) == 1:
        counts["one"] += 1
    else:
        counts["different"] += 1
        if not (sweep_path / pkg).exists():
            (sweep_path / pkg).write_text("buildsystem")
            needs_sweep.append(pkg)
        else:
            for version in (ip / pkg).glob("*"):
                if (version / "result").exists():
                    version = version.name
                    bs = json.loads(
                        (ip / pkg / version / "build-systems.json").read_text()
                    )
                    v = bs.get(pkg, "")
                    build_systems_by_version[pkg][version] = frozenset(v)
counts_overrides = collections.Counter()

for pkg, info in overrides.items():
    if len(info) == 1:
        counts_overrides["one"] += 1
    else:
        counts_overrides["different"] += 1
        if not (sweep_path / pkg).exists():
            (sweep_path / pkg).write_text("overrides")
            needs_sweep.append(pkg)
        else:
            for version in (ip / pkg).glob("*"):
                if (version / "result").exists():
                    version = version.name
                    bs = extract_overrides(ip / pkg / version / "overrides.nix")
                    v = bs.get(pkg, "")
                    build_systems_by_version[pkg][version] = frozenset(v)


print("build systems", counts)
print("overrides", counts_overrides)

if needs_sweep:
    raise ValueError(
        'New needs sweep packages - rerun python 01_assemble_package_list.py && python 02_build_packages.py "'
        + "|".join(needs_sweep)
        + '"'
    )

op = Path("poetry2nix-ready-files")
if op.exists():
    shutil.rmtree(op)
shutil.copytree('patches',op)
shutil.copytree('cargo.locks',op)
op.mkdir(exist_ok=True, parents=True)
build_systems_output_filename = op / "auto-build_systems.json"
overrides_output_filename = op / "auto-overrides.nix"

out = {}
for pkg, info in sorted(build_systems.items()):
    if len(info) == 1:
        out[pkg] = list(list(info)[0])
    else:
        start = None
        runs = []
        current = None
        last = None
        for k, v in sorted(
            build_systems_by_version[pkg].items(), key=lambda x: Version(x[0])
        ):
            if last != v:
                last = v
                if current:
                    runs.append((start, k, current))
                    start = k
            current = v
        if current:
            runs.append((start, None, current))
            current = []
            start = k
            print(k)
        this = []
        for start, stop, build_systems in runs:
            for bs in build_systems:
                d = {"buildSystem": bs}
                if stop:
                    d["until"] = stop
                if start:
                    d["from"] = start
                this.append(d)
        out[pkg] = this


build_systems_output_filename.write_text(json.dumps(out, indent=2))


def format_overrides(ovs, pkg):
    oovs = []
    for ov in ovs:
        if not "override " in ov:
            ov = (
                ov.strip()[1:-1].replace(
                    " {", " lib.optionalAttrs (!(old.src.isWheel or false)) {", 1
                )
                + ";"
            )
        else:
            ov = ov.strip()[1:] # remove }
        oovs.append(ov)
    if len(oovs) > 1:
        print("WARN", pkg)
        res = "\n".join(oovs)
        res = res.split("\n")
        res = "# Needs manual merging\n" + "\n".join(["#" + x for x in res])
        return res
    else:
        return "\n".join(oovs)


out = []
for pkg, info in sorted(overrides.items()):
    if len(info) == 1:
        out.append(format_overrides(list(info)[0], pkg))
    else:
        continue
        start = None
        runs = []
        current = None
        last = None
        for k, v in sorted(
            overrides_by_version[pkg].items(), key=lambda x: Version(x[0])
        ):
            if last != v:
                last = v
                if current:
                    runs.append((start, k, current))
                    start = k
            current = v
        if current:
            runs.append((start, None, current))
            current = []
            start = k
            print(k)
        this = []
        # for start, stop, build_systems in runs:
        #     for bs in build_systems:
        #         d = {"buildSystem": bs}
        #         if stop:
        #             d["until"] = stop
        #         if start:
        #             d["from"] = start
        #         this.append(d)
        # out[pkg] = this

override_str = Path("templates/overrides.nix").read_text().replace("#here", 
"""(final: prev: {"""  +"\n\n".join(out) + "})\n") 

overrides_output_filename.write_text(override_str)
subprocess.check_call(["nixfmt", str(overrides_output_filename)])

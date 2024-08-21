#!/usr/bin/env python
import pprint
import functools
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

from shared import nix_format, nix_identifier

outcomes = shared.examine_results()[1]
ip = Path("output")

build_systems = collections.defaultdict(set)
build_systems_by_version = collections.defaultdict(dict)

overrides = collections.defaultdict(set)
override_sources = collections.defaultdict(set)


def load_versions(pkg_path):
    poetry_lock = toml.loads(Path(pkg_path / "poetry.lock").read_text())
    res = {}
    for package in poetry_lock["package"]:
        res[package["name"]] = package["version"]
    return res


def combine_cargo_dep_overrides(pkg, pkg_overrides):
    """Combine cargo dependencies that need outputHashes.
    The usual 'we have a hash for the lock file' case is covered
    by standardMaturin / offlineMaturin,
    this is just for the cases where we have additional outputHashes
    (for git dependencies etc) that apperantly are missing from Cargo.lock.
    """

    res = []
    output_hashes_per_version = {}
    template = None
    for ov_set in pkg_overrides:
        new_set = set()
        had_lockFile = False
        for ov in ov_set:
            if (
                "lockFile" in ov and not "${old.version}.lock" in ov
            ):  # the latter are the manual_overriden ones.
                ov_pkg_version = re.findall(r"([0-9.]+)\.lock", ov)[0]
                output_hashes = re.findall(r"outputHashes = ({[^}]+})", ov, re.DOTALL)[
                    0
                ]
                output_hashes = re.findall('"([^"]+)" = "([^"]+)";', output_hashes)
                output_hashes = {k: v for k, v in output_hashes}
                output_hashes_per_version[ov_pkg_version] = output_hashes
                if not template:
                    template = ov
                had_lockFile = True
            else:
                new_set.add(ov)
        res.append((new_set, had_lockFile))
    if template:
        new_ov = re.sub(
            "lockFile = [^;]+;",
            "lockFile = ./cargo.locks/" + pkg + "/${old.version}.lock;",
            template,
        )
        nixified_output_hashes = nix_format(output_hashes_per_version)
        new_ov = re.sub(
            r"outputHashes = ({[^}]+})",
            """
        outputHashes =
            let lookup = """
            + nixified_output_hashes
            + """;
            in
            lookup.${old.version} or {}
        """,
            new_ov,
        )
        for new_set, had_lockFile in res:
            if had_lockFile:
                new_set.add(new_ov)

    return {frozenset(x[0]) for x in res}


def normalize_naming_quotes(ov):
    return re.sub(
        '"?([^" ]+)"?[ ]+= prev."?[^".]+"?.',
        lambda x: nix_identifier(x.group(1))
        + " = prev."
        + nix_identifier(x.group(1))
        + ".",
        ov,
    )


def combine_overrides_with_and_without_quotes(pkg, pkg_overrides):
    """We used to have "pkg" = prev."pkg". in the overrides,
    and fixed it to be pkg = prev.pkg...
    and now we have all these fake conflicts"""
    res = []
    for ov_set in pkg_overrides:
        new = set()
        for ov in ov_set:
            new.add(normalize_naming_quotes(ov))
        res.append(new)
    return {frozenset(x) for x in res}


def combine_overrides_with_scars(pkg, pkg_overrides):
    """Another scar, triggered by wrong postPath handling
    and now we have all these conflicts to patch over"""
    res = []
    for ov_set in pkg_overrides:
        new = set()
        for ov in ov_set:
            # postPatch missing old
            ov = ov.replace(
                "(old.postPatch or \"\") +''", "(old.postPatch or \"\") + ''"
            )
            ov = ov.replace(
                "postPatch = ''", "postPatch = (old.postPatch or \"\") + ''"
            )
            # standard maturin arguments...
            ov = ov.replace(
                "(old: (standardMaturin {}) old)",
                "(old: ((standardMaturin { furtherArgs = {};}) old))",
            )
            ov = ov.replace(
                "(old: ((standardMaturin {}) old))",
                "(old: ((standardMaturin { furtherArgs = {};}) old))",
            )
            ov = ov.replace(
                "(old: ((offlineMaturin {}) old))",
                "(old: ((offlineMaturin { furtherArgs = {};}) old))",
            )
            # exist vs is a file
            ov = ov.replace("if [ -e setup.py ]; then", "if [ -f setup.py ]; then")
            new.add(ov)
        res.append(new)
    return {frozenset(x) for x in res}


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
            pkg = re.findall('"?([^ "]+)"?[ ]+=', c)[0]
            if pkg.strip() == "":
                raise ValueError(c)

        except IndexError:
            print("b is ", repr(b))
            raise
        res[pkg].append(c)
        override_sources[k].add(overrides_path)
    return res


for (pkg, version), outcome in outcomes.items():
    if outcome.startswith("success"):
        try:
            bs = json.loads(
                (ip / pkg / version / "final.build-systems.json").read_text()
            )
        except FileNotFoundError:
            bs = json.loads((ip / pkg / version / "build-systems.json").read_text())
        for k, v in bs.items():
            try:
                build_systems[k].add(frozenset(v))
            except TypeError:
                if (Path("manual_overrides") / f"{k}.json").exists():
                    build_systems[k].add("manual")
                else:
                    raise
        try:
            ov = extract_overrides(ip / pkg / version / "final.overrides.nix")
        except FileNotFoundError:
            ov = extract_overrides(ip / pkg / version / "overrides.nix")

        for k, v in ov.items():
            overrides[k].add(frozenset(v))
            override_sources[k].add(f"{pkg}/{version}")

for k, v in overrides.items():
    v = combine_overrides_with_and_without_quotes(k, v)
    v = combine_overrides_with_scars(k, v)
    v = combine_cargo_dep_overrides(k, v)

    overrides[k] = v

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
                    try:
                        build_systems_by_version[pkg][version] = frozenset(v)
                    except TypeError:
                        pass
counts_overrides = collections.Counter()

# if we had to copy a lock file to poetry2nix,
# we need to sweep the package
for lock_file in Path("output").glob("cargo.locks/**/*.lock"):
    pkg = lock_file.parent.name
    if not (sweep_path / pkg).exists() and not pkg in needs_sweep:
        needs_sweep.append(pkg)


for pkg, info in overrides.items():
    if len(info) == 1:
        counts_overrides["one"] += 1
    else:
        counts_overrides["different"] += (
            1  # that's multiple different override sets depending on verison
        )
        if not (sweep_path / pkg).exists():
            (sweep_path / pkg).write_text("overrides")
            needs_sweep.append(pkg)
        else:
            continue
        # this stuff never worked
        # for version in (ip / pkg).glob("*"):
        #     if (version / "result").exists():
        #         version = version.name
        #         bs = extract_overrides(ip / pkg / version / "overrides.nix")
        #         v = bs.get(pkg, "")
        #         overrides[k].add(frozenset(v))
        #         override_sources[k].add(f"{pkg}/{version}")


print("build systems", counts)
print("overrides", counts_overrides)

if needs_sweep:
    print(
        'New needs sweep packages - rerun python 01_assemble_package_list.py && python 02_build_packages.py "'
        + "|".join(needs_sweep)
        + '"'
    )

op = Path("poetry2nix-ready-files")
if op.exists():
    shutil.rmtree(op)
shutil.copytree("patches", op / "patches")
shutil.copytree("cargo.locks", op / "cargo.locks")
op.mkdir(exist_ok=True, parents=True)
build_systems_output_filename = op / "auto-build_systems.json"
overrides_output_filename = op / "auto-overrides.nix"


def key_build_system(a):
    if isinstance(a, str):
        return a
    else:
        return Version(a.get("from", "0.0.0")), a.get("buildSystem")


out = {}
for pkg, info in sorted(build_systems.items()):
    if 'manual' in info:
        # manual trumps whatever else we found. I suppose it should be alone?
        out[pkg] = json.loads((Path("manual_overrides") / f"{pkg}.json").read_text())
        continue
    if len(info) == 1:
        input = list(info)[0]
        out[pkg] = sorted(input, key=key_build_system)
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
            # print(k)
        this = []
        for start, stop, build_systems in runs:
            for bs in build_systems:
                d = {"buildSystem": bs}
                if stop:
                    d["until"] = stop
                if start:
                    d["from"] = start
                this.append(d)
        if not any(("until" in v or "from" in v for v in this)):
            this = [x["buildSystem"] for x in this]
        this = sorted(this, key=key_build_system)
        out[pkg] = this


build_systems_output_filename.write_text(json.dumps(out, indent=2))


def format_overrides(ovs, pkg):
    oovs = []
    for ov in ovs:
        if not "override " in ov:
            if "standardMaturin" in ov or "offlineMaturin" in ov:
                ov = ov.strip()[1:]  # remove {
            elif "old.src.isWheel" in ov:
                ov = ov.strip()[1:-1] + ";"
            else:
                ov = (
                    ov.strip()[1:-1].replace(
                        " {", " lib.optionalAttrs (!(old.src.isWheel or false)) {", 1
                    )
                    + ";"
                )
        else:
            ov = ov.strip()[1:]  # remove {
        oovs.append(ov)
    if len(oovs) > 1:
        # that's this version combines multiple overrides
        print(
            f"""WARN - {pkg} needs manual merging. 
Craft manual_overrides/{pkg}.nix (you can use the comments in poetry2nix-ready-files/auto-overrides.nix), remove output/{pkg}, run python 02_build_packages.py {pkg}, rerun 05_assemble.py.
if this keeps coming up, rebuild all packages that use {pkg}: {override_sources[pkg]}

""",
        )
        res = "\n".join(oovs)
        res = res.split("\n")
        res = "# Needs manual merging\n" + "\n".join(["#" + x for x in res])
        return res
    else:
        return "\n".join(oovs)


def comment_out(text):
    return "\n".join(["#" + x for x in text.split("\n")])


out = []
needs_remove_and_rebuild = []
for pkg, info in sorted(overrides.items()):
    info = set(info)
    if len(info) == 1:
        out.append(format_overrides(list(info)[0], pkg))
    else:
        print("Package had multiple diverging (version different) overrides", pkg)
        print("You need to craft a manual_override covering all of them")
        print("And then nuke & rebuild everything that uses this package")
        print(f"use remove_and_rebuild.py {pkg} to do the latter")
        print("")
        needs_remove_and_rebuild.append(pkg)
        out.append("#Needs manual override to merge version dependencies:\n")
        for entry in list(set(info)):
            out.append(comment_out(format_overrides(entry, pkg)))
        sources = set()
        for path_or_str in override_sources[pkg]:
            if isinstance(path_or_str, str):
                sources.add(path_or_str)
            else:
                s = str(path_or_str).replace("output/", "")
        Path("cache/remove_and_rebuild_" + pkg).write_text("\n".join(sources))

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

if needs_remove_and_rebuild:
    print("Run remove_and_rebuild.py " + " ".join(needs_remove_and_rebuild))


def get_override_funcs():
    raw = Path("templates/overrides.nix").read_text()
    start = raw.find("#Copy-into-auto-overrides")
    end = raw.find("#end-Copy-into-auto-overrides")
    start = raw.find("\n", start)
    return raw[start:end].strip()


override_str = (
    """
{
  pkgs,
  lib,
}: let
"""
    + get_override_funcs()
    + """
in
(final: prev: {"""
    + "\n\n".join(out)
    + "})\n"
)

overrides_output_filename.write_text(override_str)
subprocess.check_call(["nixfmt", "poetry2nix-ready-files"])
subprocess.check_call(["nix", "fmt", "poetry2nix-ready-files"])

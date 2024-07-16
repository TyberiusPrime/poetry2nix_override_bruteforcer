#!/usr/bin/env python
from typing import override
import pypipegraph2 as ppg
import gzip
import tarfile
import deepdiff
import toml
import sys
import collections
import textwrap
import re
import shutil
import json
import subprocess
from pathlib import Path
from shared import known_failing
import os

ppg.new()

variations = [
    "with_patch",
    # "without_patch"
]

template_jobs = {
    "pyproject.toml": ppg.FileInvariant("templates/pyproject.toml"),
    "flake.nix": ppg.FileInvariant("templates/flake.nix"),
    "flake.lock": ppg.FileInvariant("templates/flake.lock"),
    "overrides.nix": ppg.FileInvariant("templates/overrides.nix"),
    "build-systems.json": ppg.FileInvariant("templates/build-systems.json"),
}

templates = {k: v.files[0].read_text() for k, v in template_jobs.items()}

entries = [
    # ("uuid7", "0.1.0", ""),
    # ("acquisition-sanitizer", "0.4.1", ""),
    # ("adafruit-io", "2.7.2", ""),
    # ("anndata", "0.10.8", ""),
    # ("allianceauth", "4.1.0", ""),
    ("2to3", "1.0"),
    ("zxing-cpp", "2.2.0"),
    ("django-feed-reader", "1.1.0"),
    ("python-ldap", "3.4.4"),
]

entries.extend(json.loads(Path("input.json").read_text())[: 1280 * 4])


def normalise_package_name(name):
    parts = re.split("[_.-]+", name.lower())
    parts = [x for x in parts if x]
    return "-".join(parts)


entries = [(normalise_package_name(k), v) for (k, v) in entries]

top_path = Path("output")
blacklist = []

add_constraints = toml.loads(Path("input/constraints.toml").read_text())


def write_template(pkg, version, constraints):
    def inner(output_files):
        top = top_path / pkg / version
        top.mkdir(exist_ok=True, parents=True)
        here = f'"{pkg}"="{version}"'
        if constraints:
            here += "\n" + constraints
        (top / "pyproject.toml").write_text(
            templates["pyproject.toml"].replace("#here", here)
        )
        for k in templates:
            if k != "pyproject.toml":
                (top / k).write_text(templates[k])

    return ppg.MultiFileGeneratingJob(
        {k: top_path / pkg / version / k for k in templates}, inner
    )


poetry_env = os.environ.copy()
poetry_env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.fail.Keyring"
poetry_env["POETRY_VIRTUALENVS_CREATE"] = "false"


def poetry_lock(pkg, version):
    def lock(files):
        try:
            p = subprocess.run(
                [
                    # "nix",
                    # "shell",
                    # "nixpkgs#python312",
                    # "--command",
                    "poetry",
                    "lock",
                    "--no-update",
                    "--no-interaction",
                ],
                cwd=top_path / pkg / version,
                env=poetry_env,
                timeout=60,
                stdout=open(files["status"].with_suffix(".stdout"), "w"),
                stderr=open(files["status"].with_suffix(".stderr"), "w"),
            )
        except subprocess.TimeoutExpired:
            files["status"].write_text("timeout")
            return
        if not p.returncode == 0:
            files["status"].write_text("failure")
            pass
        else:
            files["status"].write_text("OK")

    return ppg.MultiFileGeneratingJob(
        {
            "status": top_path / pkg / version / "poetry.sentinel",
            "lock": top_path / pkg / version / "poetry.lock",
        },
        lock,
    )


def try_nix_build(path, prefix):
    p = subprocess.Popen(
        [
            "nix",
            "build",
            "--no-allow-import-from-derivation",
            "--keep-going",
            "--cores",
            "0",
        ],
        cwd=path,
        stdout=open(path / (prefix + ".stdout"), "wb"),
        stderr=open(path / (prefix + ".stderr"), "wb"),
    )
    p.communicate()
    if p.returncode != 0:
        stderr = Path(path / (prefix + ".stderr")).read_text()
        if "error: infinite recursion encountered" in stderr:
            failed_derivations = [":::infinite-recursion"]
        else:
            failed_derivations = re.findall(
                "error: builder for '([^']+)' failed", stderr
            )
        return (False, failed_derivations)
    else:
        return (True, [])


def format_build_systems(build_systems):
    return json.dumps(build_systems, indent=2)


def format_overrides(overrides):
    raw = templates["overrides.nix"]
    text = ""
    for k, vs in overrides.items():
        for v in vs:
            if not v.startswith("override"):
                text += f"""
            (final: prev: (
                {{
                    "{k}"  = prev."{k}".overridePythonAttrs (old: {v});
                }}
            ))\n\n
 """  # these stupid things don't stack either way.
            else:
                text += f"""
            (final: prev: (
                {{
                    "{k}"  = prev."{k}".{v};
                }}
            ))\n\n
                """
    return raw.replace("#here", text)


def pkg_from_derivation_name(derivation):
    if "spinnmachine-" in derivation:
        return "spinnmachine"
    elif "spinnutilities-" in derivation:
        return "spinnutilities"
    elif "spinnstoragehandlers-" in derivation:
        return "spinnstoragehandlers"
    derivation = derivation.replace("/nix/store/", "")
    hash_len = 33
    derivation = derivation[hash_len:]
    if "/" in derivation:
        derivation = derivation.split("/", 1)[0]
    if re.match("python\\d\\.\\d+-", derivation):
        derivation = derivation.split("-", 1)[1]
    return derivation.rsplit("-", 1)[0]


def pkg_and_version_from_derivation_name(derivation):
    pkg = pkg_from_derivation_name(derivation)
    version = derivation.split(pkg)[1][1:].replace(".drv", "")
    return (pkg, version)


def guess_overrides(derivation, overrides, build_systems, outer_pkg, outer_version):
    full = subprocess.check_output(["nix", "log", derivation]).decode("utf-8")
    pkg, version = pkg_and_version_from_derivation_name(derivation)
    if Path(f"manual_overrides/{pkg}.nix").exists() and overrides[pkg] == []:
        overrides[pkg].append(Path(f"manual_overrides/{pkg}.nix").read_text())

    if "env" in full and "collision" in full:
        hits = re.findall("error: collision between `([^']+)' and `([^']+)'", full)
        pkg1 = pkg_from_derivation_name(hits[0][0])
        overrides[pkg1].append("{meta.priority = 1;}")
        return

    if "Error compiling Cython file:" in full and "cython" in build_systems[pkg]:
        build_systems[pkg].remove("cython")
        build_systems[pkg].append("cython_0")

    queries = {
        "ModuleNotFoundError: No module named 'setuptools'": "setuptools",
        "Setuptools not found/distribute setup failed;": "setuptools",
        "Can not execute `setup.py` since setuptools": "setuptools",
        "ModuleNotFoundError: No module named 'pkg_resources": "setuptools",
        # "ModuleNotFoundError: No module named 'distutils'": "setuptools",
        "ModuleNotFoundError: No module named 'poetry'": "poetry-core",
        "ModuleNotFoundError: No module named 'poetry.masonry'": "poetry-core",
        "ModuleNotFoundError: No module named 'poetry_dynamic_versioning'": "poetry-dynamic-versioning",
        "ModuleNotFoundError: No module named 'hatchling'": "hatchling",
        "hatchling.plugin.exceptions.UnknownPluginError: Unknown build hook: vcs": "hatch-vcs",
        "Unknown metadata hook: requirements_txt": "hatch-requirements-txt",
        "ModuleNotFoundError: No module named 'flit_core'": "flit-core",
        "ModuleNotFoundError: No module named 'flit_scm'": "flit-scm",
        "No matching distribution found for vcversioner": "vcversioner",
        "No matching distribution found for pytest-runner": "pytest-runner",
        "No matching distribution found for setuptools_git": "setuptools-git",
        "No matching distribution found for setuptools-git-versioning": "setuptools-git-versioning",
        "No matching distribution found for setuptools-scm": "setuptools-scm",
        "No matching distribution found for setuptools_scm": "setuptools-scm",
        "No matching distribution found for pbr": "pbr",
        "No matching distribution found for pytest": "pytest",
        "ModuleNotFoundError: No module named 'expandvars'": "expandvars",
        "ModuleNotFoundError: No module named 'setuptools_rust'": "setuptools-rust",
        # "ModuleNotFoundError: No module named 'wheel'": "wheel",
        "ModuleNotFoundError: No module named 'mesonpy'": "meson-python",
        "ModuleNotFoundError: No module named 'mesonpy'": "meson-python",
        "ModuleNotFoundError: No module named 'packaging'": "packaging",
        "ModuleNotFoundError: No module named 'skbuild'": "scikit-build",
        "ModuleNotFoundError: No module named 'pdm'": "pdm-backend",
        "No such file or directory: 'cmake'": "cmake",
        "Cannot find CMake executable.": "cmake",
        "Missing CMake executable": "cmake",
        "Cannot find cmake.": "cmake",
        "installing from https://github.com/ebiggers/libdeflate.git": [
            "cmake",
            "pkgconfig",
        ],
        "No module named 'scikit_build_core'": "scikit-build-core",
        "Could NOT find pybind11": "pybind11",
        "could not find git for clone of pybind11-populate": "pybind11",
        'CMake was unable to find a build program corresponding to "Ninja".': "ninja",
        "Problem with the CMake installation": "cmake",
        # "from distutils.util import byte_compile": "cython_0",
        # "No matching distribution found for wheel": "wheel",
        "No matching distribution found for Cython": "cython",
        "No module named 'Cython'": "cython",
        "Could NOT find PkgConfig": "pkgconfig",
        "Command 'sip-module": "sip",
    }

    for q, vs in queries.items():
        if q in full:
            if isinstance(vs, str):
                vs = [vs]
                for v in vs:
                    if not v in build_systems[pkg]:
                        build_systems[pkg].append(v)
    override_queries = {
        "CMake step for": "{ dontUseCmakeConfigure = true; }",
        "CMakeLists.txt:": "{ dontUseCmakeConfigure = true; }",
        " does not appear to contain CMakeLists.txt.": "{ dontUseCmakeConfigure = true; }",
        "ModuleNotFoundError: No module named 'poetry.masonry'": """{postPatch = ''
                  substituteInPlace pyproject.toml --replace "poetry.masonry.api" "poetry.core.masonry.api"
                '';}
            """,
        "use_2to3 is invalid.": """{ postPatch = ''
              substituteInPlace setup.py \
                --replace-quiet "use_2to3=True," "" \
                --replace-quiet "use_2to3=True" "" \
            '';
        }""",
        "error: command 'swig' failed: No such file or directory": """{
            nativeBuildInputs = [ pkgs.swig ];
        }""",
        "mysql_config not found": """{nativeBuildInputs = [pkgs.libmysqlclient];}""",
        "error: can't find Rust compiler": """{nativeBuildInputs = [ pkgs.rustc pkgs.cargo];}""",
        # this will probably need to be extendend / configured
        "AttributeError: module 'configparser' has no attribute 'SafeConfigParser'.": """{
            postPatch = ''
              substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \\
                --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \\
            '';
          }""",
        "No such file or directory: 'gfortran'": """
        {nativeBuildInputs = [pkgs.gfortran];}
        """,
    }
    for q, v in override_queries.items():
        if q in full:
            overrides[pkg].append(v)

    if "ModuleNotFoundError: No module named 'maturin'" in full:
        if not pkg in overrides:
            version = pkg_and_version_from_derivation_name(derivation)[1]
            overrides[pkg].append("(standardMaturin {}) old")
            copy_cargo_locks(pkg, version, full, outer_pkg, outer_version, overrides)
            # error: getting status of '/nix/store/057nzl5sq90k3v37zk9cmh1hkplnbwrw-sourcecargo.locks/accelerate/0.32.1.lock': No such file or directory


def extract_cargo_lock_from_derivation(full_log, output_path):
    source = re.findall("unpacking source archive (.+)$", full_log, re.MULTILINE)[0]
    tf = tarfile.open(source, "r:gz")
    candidates = []
    for fn in tf.getnames():
        if fn.endswith("Cargo.lock"):
            candidates.append(fn)
    candidates.sort()
    fh = tf.extractfile(candidates[0])
    output_path.parent.mkdir(exist_ok=True, parents=True)
    with open(output_path, "wb") as op:
        op.write(fh.read())
        return candidates[0]


def copy_cargo_locks(pkg, version, full, outer_pkg, outer_version, overrides):
    input_path = Path("cargo.locks") / pkg / f"{version}.lock"
    input_path_path = Path("cargo.locks") / pkg / f"{version}.path"
    path_inside_derivation = None
    if not input_path.exists():
        path_inside_derivation = extract_cargo_lock_from_derivation(full, input_path)

    if not input_path_path.exists():
        if path_inside_derivation is None:
            path_inside_derivation = extract_cargo_lock_from_derivation(
                full, input_path
            )
        input_path_path.write_text(path_inside_derivation)
    path_inside_derivation = input_path_path.read_text()
    if path_inside_derivation.endswith("/Cargo.lock"):
        path_inside_derivation = path_inside_derivation[:-len('/Cargo.lock')]
    if path_inside_derivation.startswith(pkg + '-' + version + '/'):
        path_inside_derivation = path_inside_derivation.split('/',1)[1]

    if path_inside_derivation != "Cargo.lock":

        overrides[pkg] = [x for x in overrides[pkg] if not "Maturin" in x]
        overrides[pkg].append(
            f"""
                standardMaturin {{
                      furtherArgs = {{
                        cargoRoot = "{path_inside_derivation}";
                      }};
                 }}
                old
                """
        )

    output_path = (
        top_path / outer_pkg / outer_version / "cargo.locks" / pkg / f"{version}.lock"
    )
    output_path.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy(input_path, output_path)
    subprocess.check_call(
        ["git", "add", "cargo.locks"], cwd=top_path / outer_pkg / outer_version
    )


def try_to_build(pkg, version):
    cwd = top_path / pkg / version

    def inner(output_files):
        git_done = cwd / "git.sentinel"
        if not git_done.exists():
            subprocess.check_call(
                ["git", "init"],
                cwd=cwd,
                env=poetry_env,
                timeout=60,
            )
            subprocess.check_call(
                [
                    "git",
                    "add",
                    "flake.nix",
                    "flake.lock",
                    "poetry.lock",
                    "pyproject.toml",
                    "overrides.nix",
                    "build-systems.json",
                ],
                cwd=cwd,
                env=poetry_env,
                timeout=60,
            )
            git_done.write_text("done")
        if Path(cwd / "result").exists():
            output_files["sentinel"].write_text("skipped")
            return
        round = 1
        seen_before = set()
        overrides = collections.defaultdict(list)
        build_systems = collections.defaultdict(list)
        for fn in cwd.glob("round*"):
            fn.unlink()
        try:
            if Path(f"manual_overrides/{pkg}.nix").exists() and overrides[pkg] == []:
                overrides[pkg].append(Path(f"manual_overrides/{pkg}.nix").read_text())
            add_overrides_for_known_packages(pkg, version, overrides)

            while True:
                override_hash = deepdiff.DeepHash(overrides)[overrides]
                build_system_hash = deepdiff.DeepHash(build_systems)[build_systems]
                (cwd / "overrides.nix").write_text(format_overrides(overrides))
                (cwd / "build-systems.json").write_text(
                    format_build_systems(build_systems)
                )
                ok, failed_drv = try_nix_build(cwd, f"round{round}")
                if ok:
                    break
                else:
                    if ":::infinite-recursion" in failed_drv:
                        (Path("infinite-recursions") / pkg / version).write_text(
                            "infinite recursion"
                        )
                    round += 1
                    if round > 10:
                        raise ValueError("round10")
                        break
                    err_repeat = False
                    for drv in failed_drv:
                        if drv in seen_before:
                            err_repeat = drv
                            break
                    if err_repeat:
                        raise ValueError(
                            "error repeat",
                            err_repeat,
                            pkg_from_derivation_name(err_repeat),
                            pkg_from_derivation_name(err_repeat) in known_failing,
                        )
                    for drv in failed_drv:
                        drv_pkg, drv_version = pkg_and_version_from_derivation_name(drv)
                        if (
                            drv_pkg in known_failing
                            or "{drv_pkg}-{drv_version}" in known_failing
                        ):
                            raise ValueError("known_failing", drv_pkg)
                        guess_overrides(drv, overrides, build_systems, pkg, version)
                        seen_before.add(drv)
                    if (
                        override_hash == deepdiff.DeepHash(overrides)[overrides]
                        and build_system_hash
                        == deepdiff.DeepHash(build_systems)[build_systems]
                    ):
                        raise ValueError(
                            "No more changes",
                            round,
                            build_systems,
                        )
                        break
        except ValueError as e:
            if "known_failing" in str(e):
                output_files["sentinel"].write_text(
                    "failure: known_failing " + e.args[1]
                )
            else:
                raise ValueError(pkg, version, e)

        if Path(cwd / "result").exists():
            output_files["sentinel"].write_text("OK")
        else:
            # output_files["sentinel"].write_text(f"failed round {round}")
            pass

    return ppg.MultiFileGeneratingJob({"sentinel": cwd / "outcome"}, inner)


def add_overrides_for_known_packages(pkg, version, overrides):
    poetry_lock = toml.loads((top_path / pkg / version / "poetry.lock").read_text())
    for entry in poetry_lock["package"]:
        pkg = normalise_package_name(entry["name"])
        version = entry["version"]
        if pkg in known_failing or f"{pkg}-{version}" in known_failing:
            raise ValueError("known failing", pkg)
        if Path(f"manual_overrides/{pkg}.nix").exists() and overrides[pkg] == []:
            print("bingo", pkg)
            overrides[pkg].append(Path(f"manual_overrides/{pkg}.nix").read_text())


if len(sys.argv) > 2:
    limit = sys.argv[1].lower(), sys.argv[2].lower()
elif len(sys.argv) > 1:
    limit = sys.argv[1].lower(), None
else:
    limit = None

# so you can run arbitrary things...
if limit and limit[1] and not limit in entries:
    entries.append(limit)

jobs = {}
for pkg, ver in entries:
    if pkg in known_failing:
        continue
    if (
        limit is None
        or (limit[1] is None and limit[0] == pkg)
        or (limit[1] == ver and limit[0] == pkg)
    ):
        constraints = add_constraints.get(pkg, "")
        if (pkg + "-" + ver) in add_constraints:
            constraints = add_constraints[pkg + "-" + ver]
        constraints = constraints.replace("\\n", "\n")
        j1 = write_template(pkg, ver, constraints).depends_on(template_jobs.values())
        j2 = poetry_lock(pkg, ver).depends_on(j1)
        # j2 = do_git(pkg).depends_on(j1['flake.nix'])
        j3 = try_to_build(pkg, ver).depends_on(j2).depends_on_func(try_nix_build).self
        jobs[pkg, ver] = j3
print(jobs)
if not jobs:
    print("No jobs matched")
else:
    ppg.run()

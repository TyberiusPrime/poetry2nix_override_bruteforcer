#!/usr/bin/env pnot ython
import tempfile
import time
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
from shared import (
    get_entries,
    get_known_failing,
    normalise_package_name,
    nix_identifier,
)
import shared
import os

ppg.new()  # overrides.nixcores=6)

known_failing, autodetected = get_known_failing()
template_jobs = {
    "pyproject.toml": ppg.FileInvariant("templates/pyproject.toml"),
    "flake.nix": ppg.FileInvariant("templates/flake.nix"),
    "flake.lock": ppg.FileInvariant("templates/flake.lock"),
}

non_template_jobs = {
    "overrides.nix": ppg.FileInvariant("templates/overrides.nix"),
    "build-systems.json": ppg.FileInvariant("templates/build-systems.json"),
}

templates = {k: v.files[0].read_text() for k, v in template_jobs.items()}
non_templates = {k: v.files[0].read_text() for k, v in non_template_jobs.items()}

entries = shared.get_entries()

top_path = Path("output")
blacklist = []

add_constraints = toml.loads(Path("input/constraints.toml").read_text())

gast_downgrades = set()
for fn in Path("autodetected_failures/gast_0.5").glob("**/*"):
    if fn.is_file():
        gast_downgrades.add((fn.parent.name, fn.name))


def write_template(pkg, version, constraints):
    def inner(output_files):
        top = top_path / pkg / version
        top.mkdir(exist_ok=True, parents=True)
        here = f'"{pkg}"="{version}"'
        if constraints:
            here += "\n" + constraints
        if (pkg, version) in gast_downgrades:
            here += """\ngast="<0.6.0"\n"""
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
                check=False,
            )
        except subprocess.TimeoutExpired:
            files["status"].write_text("timeout")
            return
        except:
            raise
        if not p.returncode == 0:
            files["status"].write_text("failure")
            stderr = files["status"].with_suffix(".stderr").read_text()
            line = None
            if "which requires Python":
                line = [x for x in stderr.split("\n") if "which requires Python" in x]
            elif "Invalid python versions" in stderr:
                line = [x for x in stderr.split("\n") if "Invalid python versions" in x]

            if line:
                op = Path("autodetected_failures/python-version") / pkg / version
                op.parent.mkdir(exist_ok=True, parents=True)
                op.write_text("python-version\n" + "\n".join(line))
                raise ValueError("python-version")

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
    print("try nix build", prefix)
    p = subprocess.Popen(
        [
            "nix",
            "build",
            "--no-allow-import-from-derivation",
            "--keep-going",
            "--cores",
            "6",
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
        elif "multiple exception types must be parenthesized" in stderr:
            failed_derivations = [":::python2-only"]
        elif "distribute-0.7.3.drv' failed" in stderr:
            failed_derivations = [":::no-312"]
        elif "OpenSSL 1.1 is reaching its end" in stderr:
            failed_derivations = [":::openssl-1.1"]
        else:
            failed_derivations = re.findall(
                "error: builder for '([^']+)' failed", stderr
            )
        print("failed derivations", failed_derivations)
        return (False, failed_derivations)
    else:
        return (True, [])


def format_build_systems(build_systems):
    return json.dumps(build_systems, indent=2)


def format_overrides(overrides):
    raw = non_templates["overrides.nix"]
    text = ""
    for k, vs in overrides.items():
        for v in vs:
            if not v.startswith("override"):
                text += f"""
            (final: prev: (
                {{
                    {nix_identifier(k)}  = prev.{nix_identifier(k)}.overridePythonAttrs (old: {v});
                }}
            ))\n\n
 """  # these stupid things don't stack either way.
            else:
                text += f"""
            (final: prev: (
                {{
                    {nix_identifier(k)}  = prev.{nix_identifier(k)}.{v};
                }}
            ))\n\n
                """
    return raw.replace("#here", text)


from shared import pkg_and_version_from_derivation_name, pkg_from_derivation_name


def guess_overrides(
    derivation, overrides, build_systems, outer_pkg, outer_version, round, cwd
):
    full = subprocess.check_output(["nix", "log", derivation]).decode("utf-8")
    retries = 5
    if not full.strip() and retries:
        time.sleep(3)  # hooray for race conditions.
        full = subprocess.check_output(["nix", "log", derivation]).decode("utf-8")
        if retries == 3:
            time.sleep(30)
        elif retries == 2:
            time.sleep(60)
        elif retries == 1:
            time.sleep(120)
        retries = retries - 1
    if not full.strip():
        raise ValueError(
            "nix log for",
            derivation,
            "was empty even after waiting a few seconds and retrying",
        )

    (cwd / derivation.split("/")[-1]).write_text(full)
    pkg, version = pkg_and_version_from_derivation_name(derivation)
    if Path(f"manual_overrides/{pkg}.nix").exists() and overrides[pkg] == []:
        overrides[pkg].append(Path(f"manual_overrides/{pkg}.nix").read_text())

    if "collision between" in full:
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
        "Can not execute `setup.py` since setuptools is not available": "setuptools",
        # "ModuleNotFoundError: No module named 'distutils'": "setuptools", # it's not 100%, but worth a try
        "ModuleNotFoundError: No module named 'poetry'": "poetry-core",
        "ModuleNotFoundError: No module named 'poetry.masonry'": "poetry-core",
        "ModuleNotFoundError: No module named 'poetry_dynamic_versioning'": "poetry-dynamic-versioning",
        "ModuleNotFoundError: No module named 'hatchling'": "hatchling",
        "hatchling.plugin.exceptions.UnknownPluginError: Unknown build hook: vcs": "hatch-vcs",
        "hatchling.plugin.exceptions.UnknownPluginError: Unknown metadata hook: fancy-pypi-readme": "hatch-fancy-pypi-readme",
        "hatchling.plugin.exceptions.UnknownPluginError: Unknown build hook: jupyter-builder": "hatch-jupyter-builder",
        "Unknown metadata hook: requirements_txt": "hatch-requirements-txt",
        "ModuleNotFoundError: No module named 'flit'": "flit",
        "ModuleNotFoundError: No module named 'flit_core'": "flit-core",
        "ModuleNotFoundError: No module named 'flit_scm'": "flit-scm",
        "No matching distribution found for vcversioner": "vcversioner",
        "No matching distribution found for pytest-runner": "pytest-runner",
        "No matching distribution found for setuptools_git": "setuptools-git",
        "No matching distribution found for setuptools-git-versioning": "setuptools-git-versioning",
        # "No matching distribution found for setuptools-twine": "setuptools-twine", todo: setuptools-twien
        "No matching distribution found for setuptools-scm": "setuptools-scm",
        "No matching distribution found for setuptools_scm": "setuptools-scm",
        "ModuleNotFoundError: No module named 'setuptools_scm'": "setuptools-scm",
        "No matching distribution found for setuptools_scm_git_archive": "setuptools-scm-git-archive",  # even though it's broken in 24.05
        "No matching distribution found for pbr": "pbr",
        # "ModuleNotFoundError: No module named 'pytoml'": "pytoml",
        "No matching distribution found for pytest": "pytest",
        "No matching distribution found for grpcio-tools": "grpcio-tools",
        "No matching distribution found for pytest-benchmark": "pytest-benchmark",
        "ModuleNotFoundError: No module named 'expandvars'": "expandvars",
        "ModuleNotFoundError: No module named 'setuptools_rust'": "setuptools-rust",
        # "ModuleNotFoundError: No module named 'wheel'": "wheel",
        "ModuleNotFoundError: No module named 'mesonpy'": "meson-python",
        "ModuleNotFoundError: No module named 'mesonpy'": "meson-python",
        "ModuleNotFoundError: No module named 'packaging'": "packaging",
        "ModuleNotFoundError: No module named 'skbuild'": "scikit-build",
        "ModuleNotFoundError: No module named 'pdm'": "pdm-backend",
        "ModuleNotFoundError: No module named 'pdm.backend'": "pdm-backend",
        "ModuleNotFoundError: No module named 'pdm.pep517": "pdm-pep517",
        "No such file or directory: 'cmake'": "cmake",
        "command 'cmake' failed: No such file or directory": "cmake",
        "Cannot find CMake executable.": "cmake",
        "Missing CMake executable": "cmake",
        "Cannot find cmake.": "cmake",
        "compilation requires cmake.": "cmake",
        "is `cmake` not installed?": "cmake",
        "installing from https://github.com/ebiggers/libdeflate.git": [
            "cmake",
            "pkgconfig",
        ],
        "Did not find pkg-config by name 'pkg-config'": "pkgconfig",
        "No matching distribution found for pkgconfig": "pkgconfig",
        "Did not find CMake 'cmake'": "cmake",
        "No module named 'scikit_build_core'": "scikit-build-core",
        "Could NOT find pybind11": "pybind11",
        "ModuleNotFoundError: No module named 'whey'": "whey",
        "could not find git for clone of pybind11-populate": "pybind11",
        "No module named 'pybind11'": "pybind11",
        'CMake was unable to find a build program corresponding to "Ninja".': "ninja",
        "Problem with the CMake installation": "cmake",
        # "from distutils.util import byte_compile": "cython_0",
        # "No matching distribution found for wheel": "wheel",
        "No matching distribution found for Cython": "cython",
        "No module named 'Cython'": "cython",
        "Could NOT find PkgConfig": "pkgconfig",
        'prefix of "nanobind" to CMAKE_PREFIX_PATH': "nanobind",
        "Command 'sip-module": "sip",
        "ModuleNotFoundError: No module named 'extension_helpers'": "astropy-extension-helpers",
        "ModuleNotFoundError: No module named 'jupyter_packaging'": "jupyter-packaging",
        "is `meson` not installed?": "meson",
        "ModuleNotFoundError: No module named 'typing_extensions'": "typing-extensions",
        "ModuleNotFoundError: No module named 'yaml'": "yaml",
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
        "ModuleNotFoundError: No module named 'poetry.masonry'": """{postPatch = (old.postPatch or "") + ''
                  substituteInPlace pyproject.toml --replace "poetry.masonry.api" "poetry.core.masonry.api"
                '';}
            """,
        "use_2to3 is invalid.": """{ postPatch = (old.postPatch or "") + ''
            if [ -f setup.py ]; then
              substituteInPlace setup.py \
                --replace-quiet "use_2to3=True," "" \
                --replace-quiet "use_2to3=True" "" \
                --replace-quiet "use_2to3 = True," "" \
                --replace-quiet "use_2to3= bool(python_version >= 3.0)," "" \
                --replace-quiet "extra_setup_params[\\\"use_2to3\\\"] = True" ""
            fi
            '';
        }""",
        "error: command 'swig' failed: No such file or directory": """{
            nativeBuildInputs = [ pkgs.swig ];
        }""",
        "mysql_config not found": """{nativeBuildInputs = [pkgs.libmysqlclient];}""",
        # this will probably need to be extendend / configured
        "AttributeError: module 'configparser' has no attribute 'SafeConfigParser'.": """{
            postPatch = (old.postPatch or "") + ''
            if [ -e setup.py ]; then
              substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \\
                --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \\
                --replace-quiet "cmdclass=versioneer.get_cmdclass()" "" 
            fi
            '';
          }""",
        "No such file or directory: 'gfortran'": """
        {nativeBuildInputs = [pkgs.gfortran];}
        """,
        "fatal error: openssl/aes.h: " "No such file or directory: 'gfortran'": """
            {buildInputs = [pkgs.openssl_3];}
        """,
        "ERROR: pkg-config binary 'pkg-config' not found": """
            {nativeBuildInputs = [pkgs.pkg-config];}
        """,
        re.compile("No such file or directory: '[^']*requirements.txt'"): """
        {
            postPatch = (old.postPatch or "") +''
                touch requirements.txt
            '';
        }""",
        "No such file or directory: 'CHANGES.md'": """
        {
            postPatch = (old.postPatch or "") + ''
                touch CHANGE.md
            '';
        }
        """,
        "No such file or directory: 'HISTORY.rst'": """
        {
            postPatch = (old.postPatch or "") + ''
                touch HISTORY.rst
            '';
        }""",
        "No such file or directory: 'readme.md'": """
        {
            postPatch = (old.postPatch or "") + ''
                touch readme.md
            '';
        }""",
        "No such file or directory: 'README.md'": """
        {
            postPatch = (old.postPatch or "") + ''
                touch README.md
            '';
        }""",
        "No matching distribution found for babel": """
        {
                buildInputs = (old.builtInputs or []) ++ [prev.babel];
        }
        """,
        (
            "from distutils.util import byte_compile",
            "writing byte-compilation script",
        ): """
        {
        nativeBuildInputs =
          (old.nativeBuildInputs
            or []) ++[
            (prev.setuptools.overrideAttrs {
              postPatch = (old.postPatch or "") + ''
                substituteInPlace setuptools/_distutils/util.py \
                  --replace-fail \
                    "from distutils.util import byte_compile" \
                    "from setuptools._distutils.util import byte_compile"
              '';
            })
          ];
        }
        """,  #  a perfectly horrible hack from https://github.com/NixOS/nixpkgs/pull/326321
        'prefix of "nanobind" to CMAKE_PREFIX_PATH': """{
                CMAKE_PREFIX_PATH = "${prev.nanobind}/lib/python${lib.versions.majorMinor final.python.version}/site-packages/nanobind/cmake";

        }""",
        "Pkg-config for machine host machine not found": """
        {
                nativeBuildInputs = (old.nativeBuildInputs or []) ++ [pkgs.pkg-config];
        }
        """,
        "Run-time dependency glib-2.0 found: NO": """
        {
                buildInputs = (old.buildInputs or []) ++ [pkgs.glib];
        }""",
        "Did not find the 'go' binary. ": """
        {
                nativeBuildInputs = (old.nativeBuildInputs or []) ++ [pkgs.go];
        }""",
        # "No matching distribution found for pytest-django": """
        #     {
        #         nativeBuildInputs = (old.nativeBuildInputs or []) ++ [prev.pytest-django];
        #         propagatedBuildInputs = (old.propagatedBuildInputs or []) ++ [prev.pytest-django];
        #     }
        #     """,
        # """dist: No such file or directory""":
        # """
        # {
        #   preBuild = ''
        #         # go to the directory of setup.py
        #         # it get's lost in cmake.
        #         cd /build
        #         SETUP_PATH=`find . -name "setup.py" | sort | head -n 1`
        #         echo "SETUP_PATH: $SETUP_PATH"
        #         cd $(dirname $SETUP_PATH)
        #       '';
        #   }
        # """
    }
    for qs, v in override_queries.items():
        if not isinstance(qs, tuple):
            qs = (qs,)
        for q in qs:
            if (isinstance(q, str) and q in full) or (
                not isinstance(q, str) and q.search(full)
            ):
                if not v in overrides[pkg]:
                    overrides[pkg].append(v)

    rust = False
    if "ModuleNotFoundError: No module named 'maturin'" in full:
        rust = "maturin"
    elif "ModuleNotFoundError: No module named 'setuptools_rust'" in full:
        rust = "setuptools_rust"

    if "error: can't find Rust compiler" in full:
        if not any("maturin" in x for x in overrides[pkg]):
            overrides[pkg].append(
                """{nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ pkgs.rustc pkgs.cargo];}"""
            )
        else:
            new = []
            for x in overrides[pkg]:
                if "Maturin" in x:
                    new.append(
                        x.replace(
                            "furtherArgs = {",
                            "furtherArgs = {nativeBuildInputs = (old.nativeBuildInputs or []) ++ [ pkgs.rustc pkgs.cargo];",
                        )
                    )

                else:
                    new.append(x)
                    # ) ) )
            overrides[pkg] = new

    if rust:
        if not any("maturin" in x for x in overrides[pkg]):
            version = pkg_and_version_from_derivation_name(derivation)[1]
            if rust == "setuptools_rust":
                overrides[pkg].append(
                    "((standardMaturin {maturinHook = null; furtherArgs = {};}) old)"
                )
            else:
                overrides[pkg].append("((standardMaturin { furtherArgs = {};}) old)")
        copy_cargo_locks(
            pkg,
            version,
            full,
            outer_pkg,
            outer_version,
            overrides,
            rust == "setuptools_rust",
        )

        if (Path("cargo.locks") / pkg / f"{version}.copy").exists():
            overrides[pkg][-1] += """ //{
                    postPatch = let 
                      cargo_lock_filename = ./. + "/cargo.locks/${old.pname}/${old.version}.lock";
                      cargo_lock = if builtins.pathExists cargo_lock_filename then cargo_lock_filename else throw "poetry2nix has no cargo.lock available for ${old.pname} ${old.version} and the python package does not include it.";
                    in
                    (old.postPatch or "") +
                    ''
                        cp ${cargo_lock} Cargo.lock
                    '';
            }"""

            # error: getting status of '/nix/store/057nzl5sq90k3v37zk9cmh1hkplnbwrw-sourcecargo.locks/accelerate/0.32.1.lock': No such file or directory

    if "gast~=0.5.0 not satisfied by version 0.6.0" in full:
        downgrade_gast(outer_pkg, outer_version)

    if "`#![feature]` may not be used on the stable release channel" in full:
        p = Path("autodetected_failures/rust-nightly") / pkg / version
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_text("yes")
        raise ValueError("requires rust nightly")

    if "ModuleNotFoundError: No module named 'imp'" in full:
        p = Path("autodetected_failures/no-312") / pkg / version
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_text("yes")
        raise ValueError("requires python <3.12, imp module")

    if "SyntaxError" in full and re.findall("raise [^,]+,", full):
        p = Path("autodetected_failures/python2-only") / pkg / version
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_text("raise something, syntax error")
        raise ValueError("python2-only")
    if (
        "implicit declaration of function ‘PyString_FromStringAndSize’; did you mean ‘PyBytes_FromStringAndSize"
        in full
    ) or ("implicit declaration of function ‘PyUnicode_AsUnicode’;" in full):
        p = Path("autodetected_failures/python2-only") / pkg / version
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_text("c-api PyString_*/ PyUnicode")
        raise ValueError("python2-only")
    if " name 'execfile' is not defined" in full:
        p = Path("autodetected_failures/python2-only") / pkg / version
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_text("execfile")
        raise ValueError("python2-only")

    if "scikit-build-core version 0.8.2 is too old." in full:
        p = Path("autodetected_failures/scikit-build-core-too-old") / pkg / version
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_text("0.8.2")
        raise ValueError("scikit-build-core too old")

    if (
        "If you want to try to generate the lock file without accessing the network, remove the --frozen flag and use --offline instead."
        in full
    ):
        overrides[pkg] = [
            x.replace("standardMaturin", "offlineMaturin") for x in overrides[pkg]
        ]
    if any(
        ("offlineMaturin" in x for x in overrides[pkg])
    ):  # might be set from manual_overrides
        shutil.copy(
            "templates/offline-maturin-build-hook.sh",
            top_path / outer_pkg / outer_version / "offline-maturin-build-hook.sh",
        )
        subprocess.check_call(
            ["git", "add", "offline-maturin-build-hook.sh"],
            cwd=top_path / outer_pkg / outer_version,
        )

    if (
        "Can not execute `setup.py` since setuptools is not available in the build environment."
        in full
    ):
        # try to downgrade pytohn
        nix_flake_path = top_path / outer_pkg / outer_version / "flake.nix"
        nix_flake = nix_flake_path.read_text()
        if "python312" in nix_flake:
            nix_flake_path.write_text(nix_flake.replace("python312", "python311"))
            return True


def downgrade_gast(pkg, version):
    p = Path("autodetected_failures/gast_0.5") / pkg / version
    p.parent.mkdir(exist_ok=True, parents=True)
    p.write_text("yes")


def extract_cargo_lock_from_derivation(full_log, output_path):
    source = re.findall("unpacking source archive (.+)$", full_log, re.MULTILINE)[0]
    tf = tarfile.open(source, "r:gz")
    candidates = []
    for fn in tf.getnames():
        if fn.endswith("Cargo.lock"):
            candidates.append(fn)
    candidates.sort()
    if not candidates:
        print("no cargo lock found")
        path_inside_derivation = try_to_build_cargo_lock(full_log, output_path, tf)
        if path_inside_derivation:
            return path_inside_derivation
        raise ValueError("No Cargo.lock found")
    fh = tf.extractfile(candidates[0])
    output_path.parent.mkdir(exist_ok=True, parents=True)
    with open(output_path, "wb") as op:
        op.write(fh.read())
        return candidates[0]

def try_to_build_cargo_lock(full_log, output_path, tf):
    """When a package has a Cargo.toml but no Cargo.lock...
    we will try to lock it and use that one.
    """
    candidates = []
    for fn in tf.getnames():
        if fn.endswith("Cargo.toml"):
            candidates.append(fn)
    candidates.sort()
    if not candidates:
        raise ValueError("No Cargo.lock and no Cargo.toml found")
    td = tempfile.TemporaryDirectory()
    tf.extractall(td.name)
    print("calling cargo check to build Cargo.lock", td, candidates)
    subprocess.check_call(['cargo', 'check'], cwd=Path(td.name) / Path(candidates[0]).parent)
    try:
        shutil.copy(Path(td.name) / Path(candidates[0]).parent / "Cargo.lock", output_path)
        output_path.with_suffix(".copy").touch()
        output_path.with_suffix(".path").write_text(str(Path(candidates[0]).parent))
        return Path(candidates[0]).with_name('Cargo.lock')
    except FileNotFoundError:
        raise ValueError("Cargo.lock not found, and also failed to generate one")
    return False



def format_nix_dictionary(d):
    res = "{"
    for k, v in d.items():
        if re.search("[^a-zA-Z0-9-]", k):
            k = f'"{k}"'
        res += f'{k} = "{v}";\n'
    res += "}"
    return res


def copy_cargo_locks(
    pkg, version, full, outer_pkg, outer_version, overrides, setuptools_rust
):
    input_path = Path("cargo.locks") / pkg / f"{version}.lock"
    input_path_path = Path("cargo.locks") / pkg / f"{version}.path"
    input_path_output_hashes = Path("cargo.locks") / pkg / f"{version}.outputHashes"
    path_inside_derivation = None
    if not input_path.exists():
        path_inside_derivation = extract_cargo_lock_from_derivation(full, input_path)

    if not input_path_path.exists():
        if path_inside_derivation is None:
            # Control flow issue when input_path.exists but input_path_path doesn.t
            path_inside_derivation = extract_cargo_lock_from_derivation(
                full, input_path
            )
        input_path_path.write_text(path_inside_derivation)

    if not input_path_output_hashes.exists():
        input_path_output_hashes.write_text(
            json.dumps(extract_output_hashes(input_path))
        )
    output_hashes = json.loads(input_path_output_hashes.read_text())

    path_inside_derivation = input_path_path.read_text()
    if path_inside_derivation.endswith("/Cargo.lock"):
        path_inside_derivation = path_inside_derivation[: -len("/Cargo.lock")]
    if path_inside_derivation.startswith(pkg + "-" + version + "/"):
        path_inside_derivation = path_inside_derivation[
            len(pkg + "-" + version + "/") :
        ]
    # python package names are funky
    if normalise_package_name(
        path_inside_derivation.split("/")[0]
    ) == normalise_package_name(pkg + "-" + version):
        path_inside_derivation = "/".join(path_inside_derivation.split("/")[1:])

    if path_inside_derivation == pkg + "-" + version:
        path_inside_derivation = False
    path_inside_derivation = path_inside_derivation.strip()

    if (
        path_inside_derivation
        and path_inside_derivation != "Cargo.lock"
        or output_hashes
    ):
        overrides[pkg] = [x for x in overrides[pkg] if not "Maturin" in x]
        if output_hashes:
            str_output_hashes = f"""
                    cargoDeps = (pkgs.rustPlatform.importCargoLock {{
                        lockFile = ./{str(input_path)};
                        outputHashes = {format_nix_dictionary(output_hashes)};
                    }});
                    """
        else:
            str_output_hashes = ""
        if setuptools_rust:
            overrides[pkg].append(
                f"""
                    (standardMaturin {{
                        maturinHook = null;
                          furtherArgs = {{
                            cargoRoot = "{path_inside_derivation}";
                            {str_output_hashes}
                            nativeBuildInputs = [pkgs.cargo pkgs.rustc];
                          }};
                     }}
                    old)
                    """
            )

        else:
            overrides[pkg].append(
                f"""
                    (standardMaturin {{
                          furtherArgs = {{
                            cargoRoot = "{path_inside_derivation}";
                            {str_output_hashes}
                          }};
                     }}
                    old)
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


def extract_output_hashes(cargo_lock):
    t = toml.loads(cargo_lock.read_text())
    out = {}
    for pkg in t["package"]:
        if pkg.get("source", "").startswith("git+https"):
            if "?tag=" in pkg["source"]:
                url, tag = pkg["source"].split("?tag=")
            elif re.search("#[a-z0-9]{40}$", pkg["source"]):
                url, tag = pkg["source"].rsplit("#", 1)
            else:
                raise ValueError("can not parse", pkg["source"])
            if "#" in tag:
                tag = tag[tag.index("#") + 1 :]
            hash = prefetch_git_hash(url, tag)
            out[f"{pkg['name']}-{pkg['version']}"] = hash
    return out


def prefetch_git_hash(url, tag):
    output = subprocess.check_output(["nurl", url, tag]).decode("utf-8").split("\n")
    hash_line = [x for x in output if "hash = " in x][0]
    hash = hash_line[hash_line.find('"') + 1 : hash_line.rfind('"')]
    return hash


def try_to_build(pkg, version):
    cwd = top_path / pkg / version

    def inner(output_files, cwd=cwd):
        if Path(cwd / "result").exists():
            rebuild_file = Path(cwd / "do_rebuild")
            if not rebuild_file.exists():
                output_files["sentinel"].write_text("skipped")
                return
            else:
                rebuild_file.unlink()
        for k, v in non_templates.items():
            (cwd / k).write_text(v)

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
        round = 1
        seen_before = set()
        overrides = collections.defaultdict(list)
        build_systems = collections.defaultdict(list)
        for fn in cwd.glob("round*"):
            fn.unlink()
        try:
            if Path(f"manual_overrides/{pkg}.nix").exists() and overrides[pkg] == []:
                print("bingo manual", pkg)
                overrides[pkg].append(Path(f"manual_overrides/{pkg}.nix").read_text())
            add_overrides_for_known_packages(
                pkg, version, overrides
            )  # rom the poetry lock file.
            add_build_systems_for_known_packages(pkg, version, build_systems)

            while True:
                override_hash = deepdiff.DeepHash(overrides)[overrides]
                build_system_hash = deepdiff.DeepHash(build_systems)[build_systems]
                if (cwd / "overrides.nix").exists():
                    (cwd / "overrides.nix").unlink()
                (cwd / "overrides.nix.out").write_text(format_overrides(overrides))
                (cwd / "overrides.nix.out").rename(cwd / "overrides.nix")

                if (cwd / "build-systems.json").exists():
                    (cwd / "build-systems.json").unlink()
                (cwd / "build-systems.json.out").write_text(
                    format_build_systems(build_systems)
                )
                (cwd / "build-systems.json.out").rename(cwd / "build-systems.json")

                if any(
                    ("offlineMaturin" in x for x in overrides[pkg])
                ):  # might be set from manual_overrides
                    shutil.copy(
                        "templates/offline-maturin-build-hook.sh",
                        top_path / pkg / version / "offline-maturin-build-hook.sh",
                    )
                    subprocess.check_call(
                        ["git", "add", "offline-maturin-build-hook.sh"],
                        cwd=top_path / pkg / version,
                    )

                ok, failed_drv = try_nix_build(cwd, f"round{round}")
                if ok:
                    shutil.copy(cwd / "overrides.nix", cwd / "final.overrides.nix")
                    shutil.copy(
                        cwd / "build-systems.json", cwd / "final.build-systems.json"
                    )
                    break
                else:
                    for k in "infinite-recursion", "python2-only", "no-312":
                        if ":::" + k in failed_drv:
                            (Path("autodetected_failures/") / k / pkg).mkdir(
                                exist_ok=True, parents=True
                            )
                            (
                                Path("autodetected_failures") / k / pkg / version
                            ).write_text(k)
                            raise ValueError(k)

                    round += 1
                    if round > 15:
                        raise ValueError("maximum round exceeded")
                        break
                    err_repeat = False
                    for drv in failed_drv:
                        if (
                            (
                                drv
                                in seen_before  # because changing an override would get us an new hash. Right?
                            )
                            and not drv.endswith("-env.drv")
                        ):
                            err_repeat = drv
                            break
                    if err_repeat:
                        raise ValueError(
                            "error repeat",
                            err_repeat,
                            pkg_from_derivation_name(err_repeat),
                            pkg_from_derivation_name(err_repeat) in known_failing,
                        )
                    any_override_applied = False
                    for drv in failed_drv:
                        if drv.startswith(":::"):
                            print("Continue because of :::", drv)
                            continue
                        drv_pkg, drv_version = pkg_and_version_from_derivation_name(drv)
                        if (
                            drv_pkg in known_failing
                            or "{drv_pkg}-{drv_version}" in known_failing
                        ):
                            raise ValueError("known_failing", drv_pkg)

                        print(
                            "Guess overrides",
                            drv,
                            len(overrides.get(drv_pkg, [])),
                            len(build_systems.get(drv_pkg, [])),
                        )
                        any_override_applied |= bool(
                            guess_overrides(
                                drv, overrides, build_systems, pkg, version, round, cwd
                            )
                        )
                        print(
                            "after overrides",
                            drv,
                            len(overrides.get(drv_pkg, [])),
                            len(build_systems.get(drv_pkg, [])),
                        )
                        seen_before.add(drv)
                    if (
                        override_hash == deepdiff.DeepHash(overrides)[overrides]
                        and build_system_hash
                        == deepdiff.DeepHash(build_systems)[build_systems]
                        and not any_override_applied
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
                raise
                raise ValueError(pkg, version, e)

        if Path(cwd / "result").exists():
            output_files["sentinel"].write_text("OK")
        else:
            # output_files["sentinel"].write_text(f"failed round {round}")
            pass

    return ppg.MultiFileGeneratingJob({"sentinel": cwd / "outcome"}, inner)


def add_overrides_for_known_packages(outer_pkg, outer_version, overrides):
    poetry_lock = toml.loads(
        (top_path / outer_pkg / outer_version / "poetry.lock").read_text()
    )
    for entry in poetry_lock["package"]:
        pkg = normalise_package_name(entry["name"])
        version = entry["version"]
        if pkg in known_failing or f"{pkg}-{version}" in autodetected:
            raise ValueError("known failing", pkg)
        if Path(f"manual_overrides/{pkg}.nix").exists() and overrides[pkg] == []:
            print("bingo", pkg)
            overrides[pkg].append(Path(f"manual_overrides/{pkg}.nix").read_text())
        if (Path("patches") / pkg).exists():
            (top_path / outer_pkg / outer_version / "patches").mkdir(
                exist_ok=True, parents=True
            )
            shutil.copytree(
                Path("patches") / pkg,
                (top_path / outer_pkg / outer_version / "patches" / pkg),
                dirs_exist_ok=True,
            )
            subprocess.check_call(
                ["git", "add", "patches"], cwd=(top_path / outer_pkg / outer_version)
            )
        if (Path("cargo.locks") / pkg).exists():
            (top_path / outer_pkg / outer_version / "cargo.locks").mkdir(
                exist_ok=True, parents=True
            )
            shutil.copytree(
                Path("cargo.locks") / pkg,
                (top_path / outer_pkg / outer_version / "cargo.locks" / pkg),
                dirs_exist_ok=True,
            )
            subprocess.check_call(
                ["git", "add", "cargo.locks"],
                cwd=(top_path / outer_pkg / outer_version),
            )


def add_build_systems_for_known_packages(pkg, version, build_systems):
    poetry_lock = toml.loads((top_path / pkg / version / "poetry.lock").read_text())
    for entry in poetry_lock["package"]:
        pkg = normalise_package_name(entry["name"])
        version = entry["version"]
        if pkg in known_failing or f"{pkg}-{version}" in autodetected:
            raise ValueError("known failing", pkg)
        if Path(f"manual_overrides/{pkg}.json").exists():
            print("bingo build-system", pkg)
            build_systems[pkg] = json.loads(
                Path(f"manual_overrides/{pkg}.json").read_text()
            )
            try: # if it's a 'complicated' version dependend system, just keep it as is .
                build_systems[pkg] = sorted(set(build_systems[pkg]))
            except TypeError:
                pass
        scm_file = Path(f"autodetected/needs_scm/{pkg}.json")
        if scm_file.exists():
            build_systems[pkg].append(json.loads(scm_file.read_text()))


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
    if f"{pkg}-{ver}" in known_failing:
        continue
    if (
        limit is None
        or (limit[1] is None and re.search(limit[0], pkg))
        or (limit[1] == ver and limit[0] == pkg)
    ):
        constraints = add_constraints.get(pkg, "")
        if (pkg + "-" + ver) in add_constraints:
            constraints = add_constraints[pkg + "-" + ver]
        j1 = (
            write_template(pkg, ver, constraints)
            .depends_on(template_jobs.values())
            .depends_on_params(gast_downgrades)
        )
        j2 = poetry_lock(pkg, ver).depends_on(j1)
        # j2 = do_git(pkg).depends_on(j1['flake.nix'])
        j3 = try_to_build(pkg, ver).depends_on(j2).depends_on_func(try_nix_build).self
        j2.depends_on(non_template_jobs.values())
        jobs[pkg, ver] = j3
# print(jobs)
if not jobs:
    print("No jobs matched")
else:
    ppg.run()
# print(jobs)
if not jobs:
    print("No jobs matched")
else:
    ppg.run()
    ppg.run()

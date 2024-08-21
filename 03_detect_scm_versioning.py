"""
Detect versions that were build with 0.0.0.0 as version string,
indicating a failure to determine 'source code version' by pip,
which means we're lacking things like setuptools-scm
"""

from pathlib import Path
import toml
import tarfile
import zipfile
import json
import subprocess
import sys
import shutil
from shared import normalise_package_name
import shared


def extract_file(src_filename, filename):
    try:
        return inner_extract_file(src_filename, filename)
    except FileNotFoundError:
        subprocess.check_call(["nix", "build", src_filename])
        return inner_extract_file(src_filename, filename)


def inner_extract_file(src_filename, filename):
    if src_filename.endswith(".zip"):
        return extract_file_zip(src_filename, filename)
    else:
        return extract_file_tar(src_filename, filename)


def extract_file_zip(src_filename, filename):
    with zipfile.ZipFile(src_filename, "r") as zf:
        candidates = []
        for fn in zf.namelist():
            if fn.endswith(filename):
                candidates.append(fn)
        candidates.sort()
        if not candidates:
            raise ValueError(f"No {filename} found")
        if len(candidates) > 1:
            candidates.sort(key=lambda x: len(x))
        fh = zf.open(candidates[0])
        return fh.read().decode("utf-8")


def extract_file_tar(src_filename, filename):
    tf = tarfile.open(src_filename, "r")
    candidates = []
    for fn in tf.getnames():
        if fn.endswith(filename):
            candidates.append(fn)
    candidates.sort()
    if not candidates:
        raise ValueError(f"No {filename} found")

    if len(candidates) > 1:
        candidates.sort(key=lambda x: len(x))

    fh = tf.extractfile(candidates[0])
    return fh.read().decode("utf-8")


def detect_scm_tool(src_filename):
    try:
        raw = extract_file(src_filename, "pyproject.toml")
        try:
            data = toml.loads(raw)
        except toml.decoder.TomlDecodeError:
            print("failed to read pyproject.toml toml", pkg)
            if "setuptools_scm" in raw:
                return "setuptools-scm"
            else:
                data = {}
        bsr = data.get("build-system", {}).get("requires", [])
        for r in bsr:
            if r.startswith("setuptools-scm") or r.startswith("setuptools_scm"):
                return "setuptools-scm"
            if r.startswith("versioningit"):
                return "versioningit"
            if r.startswith("setuptools-git-versioning"):
                return "setuptools-git-versioning"
            if r.startswith("vcversioner"):
                return "vcversioner"
            if r.startswith("scmver"):
                return "scmver"
        if "tool.setuptools_scm" in raw:
            return "setuptools-scm"
        if not "build-system" in raw and "[tool.poetry]" in raw:
            return "poetry-core"  # not quite clean, since it's not a scm-thing, but, whatever.
    except Exception as e:
        if "No pyproject.toml found" in str(e):
            pass
        else:
            raise
    try:
        setuppy = extract_file(src_filename, "setup.py")
    except ValueError:
        setuppy = None
    if setuppy and "use_scm_version" in setuppy:
        return "setuptools-scm"


excluded = {
    "datadogpy",  # release 0.0.0 is 'real'
    "zmq",  # pkgs's with bona fida 0.0.0 releases.
    "bs4",  # release 0.0.0. is real
    "li-pagador",  # release 0.0.0.1
    "can",  # true 0.0.0 release
    "tmb",  # needs VERSION to be set - we're doing it in a manual override
    "g4f",  # needs G4F_VERSION to be set - we're doing it in a manual override
    "uuid6",  # needs env variable
    "anybadge",  # needs env variable
    "django-rest-passwordreset",  # needs env variable
    "forecast-solar",  # needs env variable
    "spaceone-api",  # needs env variable
    "kink",  # needed poetry, in manual-overrides now
    "distro-info",  # debian only module
    "marshmallow-objects",  # needed a patch to have version information
    "pickley",  # needed a patch to have version information
    "influxdb3-python",  # needed a patch to have version information
    "stringcoercion",  # 0.0.0.35 version...
}

pkgs_to_rebuild = set()
pkgs_to_examine = {}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(detect_scm_tool(sys.argv[1]))

    else:
        cache_path = Path("cache/03_detect_scm_versioning")
        if not cache_path.exists():
            hits = (
                subprocess.check_output(
                    [
                        "fd",
                        "-L",
                        "--",
                        "-0[.]0[.]0",
                    ],
                    cwd="output",
                )
                .decode("utf-8")
                .split("\n")
            )
            cache_path.write_text(json.dumps(hits))
        else:
            hits = json.loads(cache_path.read_text())
        print("hit count", len(hits))
        for h in hits:
            if not ".dist-info" in h:
                continue
            if "0.0.0.1" in h:
                continue
            if h:
                parts = h.split("/")
                if parts[-3] != "site-packages":
                    continue
                affected_pkg = parts[-2].split("-0.0.0", 1)[0]
                affected_pkg = normalise_package_name(affected_pkg)
                pkgs_to_rebuild.add(parts[0] + "/" + parts[1])
                pkgs_to_examine[affected_pkg] = Path(h)
        pkgs_to_rebuild = {
            k for k in pkgs_to_rebuild if k.split("/", 1)[0] not in excluded
        }
        pkgs_to_examine = {
            k: v for k, v in pkgs_to_examine.items() if k not in excluded
        }
        print("pkgs_to_rebuild", len(pkgs_to_rebuild))
        print("pkgs_to_examine", len(pkgs_to_examine))
        # print(pkgs_to_rebuild)
        # print(pkgs_to_examine)

        for pkg_plus_ver in sorted(pkgs_to_rebuild):
            pkg, _ = pkg_plus_ver.split("/")
            if pkg == "zmq":
                print("zmq", "zmq" in excluded, pkg in excluded)
            if pkg in excluded:
                continue
            p = Path(f"output/{pkg_plus_ver}/outcome")
            print("rebuild needed", p)
            if p.exists():
                p.unlink()
                p.with_name(
                    "do_rebuild"
                ).touch()  # we don't throw away the result, or we couln't run the examiner

        for pkg, path in pkgs_to_examine.items():
            print("examining", pkg)
            if pkg in excluded:
                continue
            output_file = Path("autodetected") / "needs_scm" / f"{pkg}.json"
            if not output_file.exists():
                if not Path("output/" + str(path)).exists():
                    # print("skipping", pkg)
                    continue
                try:
                    drv = json.loads(
                        subprocess.check_output(
                            ["nix", "derivation", "show", "output/" + str(path)]
                        ).decode("utf-8")
                    )
                except:
                    print(pkg, path)
                    raise
                key = list(drv)[0]
                src = drv[key]["env"]["src"]
                if "-0.0.0.tar.gz" in src:
                    print("skipping because of true 0.0.0. release", pkg)
                    continue
                try:
                    found = detect_scm_tool(src)
                except:
                    print(pkg, src)
                    raise

                if found:
                    print(f"{pkg} -> {found}")
                    output_file.write_text(json.dumps(found))
                else:
                    raise ValueError("failed to detect for", src)

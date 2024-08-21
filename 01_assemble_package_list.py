import urllib.request
import toml
import json
from pathlib import Path
from shared import is_prerelease, get_info
from packaging.version import Version

read_dir = Path(__file__).parent / "input"
pypi_dir = read_dir / "pypi_info"
pypi_dir.mkdir(exist_ok=True)


def get_entries():
    entries = set(json.loads((read_dir / "packages.json").read_text()))
    entries2 = [
        x["project"]
        for x in json.loads(
            (read_dir / "top-pypi-packages-30-days.min.json").read_text()
        )["rows"]
    ]
    entries.update(entries2)
    del entries2
    entries.update(json.loads((read_dir / "tp_packages.json").read_text()))
    entries.update((read_dir / "nixpkgs.json").read_text().strip().split("\n"))
    entries.update(json.loads((read_dir / "much_needed.json").read_text()))
    entries.update(json.loads((read_dir / "other_packages.json").read_text()))
    all_pypi_packages = json.loads((read_dir / "all_pypi_packages.json").read_text())
    known_pypi_errors = json.loads((read_dir / "known_pypi_errors.json").read_text())
    known_py2_only = json.loads((read_dir / "known_py2_only.json").read_text())
    known_infinite_recursion = toml.loads(
        Path(read_dir / "known_infinite_recursion.toml").read_text()
    )["infinite"]

    # stdlib = json.loads(Path("input/stdlib.json").read_text())
    # entries = entries.difference(stdlib)
    # nixpkgs and the  much_needed list from pypi deps db
    # contain a large number of packages that are not in pypi
    # (or are misparsed from the requirements?)
    # anyway, we filter to those actually on pyi
    entries = entries.intersection(all_pypi_packages)
    entries = entries.difference(known_pypi_errors)
    entries = entries.difference(known_py2_only)
    entries = entries.difference(known_infinite_recursion)
    entries = sorted(entries)
    entries = entries[:]
    return entries


def extract_date(kv):
    k, v = kv
    str_upload = v["upload_time_iso_8601"]
    return str_upload


def add_latest(wo_versions):
    result = []
    for entry in wo_versions:
        try:
            info = get_info(entry)
        except KeyError:
            continue
        # import pprint
        # pprint.pprint(info['releases'])
        releases = []
        for k, v in info["releases"].items():
            if not v:
                continue
            v = [x for x in v if not "whl" in x["url"]]  # I want only source releases
            # it's a list of all wheels and source files..
            if not v:
                continue
            if (not v[0].get("yanked")) and (("." in k) or k.isnumeric()):
                if not is_prerelease(k):
                    releases.append((k, v[0]))

        releases.sort(key=extract_date)
        if not releases:
            print(f"no versions for {entry}", releases)
            continue
        result.append((entry, releases[-1][0]))
    return result


list_without_versions = get_entries()


with_versions = add_latest(list_without_versions)


# these are packages we noted to have shitfting build-systems / overrides
# so we do them all to determine the cutover points.

sweep_excluded = {
    ("jsonschema", "0.2"),
    ("jsonschema", "2.5.0"),
    ("lxml", "1.3.2"),  # py2.7 only
    ("lxml", "1.3.3"),  # py2.7 only
    ("lxml", "1.3.4"),  # py2.7 only
    ("lxml", "1.3.5"),  # py2.7 only
    ("lxml", "1.3.6"),  # py2.7 only
    ("lxml", "2.0"),  # py2.7 only
    ("lxml", "2.0.10"),  # py2.7 only
    ("lxml", "2.0.11"),  # py2.7 only
    ("lxml", "2.0.4"),  # py2.7 only
    ("lxml", "2.0.5"),  # py2.7 only
    ("lxml", "2.0.6"),  # py2.7 only
    ("lxml", "2.0.7"),  # py2.7 only
    ("lxml", "2.0.8"),  # py2.7 only
    ("lxml", "2.0.9"),  # py2.7 only
    ("lxml", "2.1"),  # py2.7 only
    ("lxml", "2.1.1"),  # py2.7 only
    ("lxml", "2.1.2"),  # py2.7 only
    ("lxml", "2.1.3"),  # py2.7 only
    ("lxml", "2.1.4"),  # py2.7 only
    ("lxml", "2.1.5"),  # py2.7 only
    ("lxml", "2.2"),  # py2.7 only
    ("lxml", "2.2.1"),  # py2.7 only
    ("lxml", "2.2.2"),  # py2.7 only
    ("lxml", "2.2.3"),  # py2.7 only
    ("lxml", "2.2.4"),  # py2.7 only
    ("lxml", "2.2.5"),  # py2.7 only
    ("lxml", "2.2.6"),  # py2.7 only
    ("lxml", "2.2.7"),  # py2.7 only
    ("lxml", "2.2.8"),  # py2.7 only
    ("lxml", "2.3"),  # py2.7 only
    ("lxml", "2.3.1"),  # py2.7 only
    ("lxml", "2.3.2"),  # py2.7 only
    ("lxml", "2.3.3"),  # py2.7 only
    ("lxml", "2.3.4"),  # py2.7 only
    ("lxml", "2.3.5"),  # py2.7 only
    ("lxml", "2.3.6"),  # py2.7 only
    ("lxml", "3.0"),  # py2.7 only
    ("lxml", "3.0.2"),  # py2.7 only
    ("lxml", "3.1.0"),  # py2.7 only
    ("lxml", "3.1.1"),  # py2.7 only
    ("lxml", "3.1.2"),  # py2.7 only
    ("lxml", "3.2.0"),  # py2.7 only
    ("lxml", "3.2.1"),  # py2.7 only
    ("lxml", "3.2.2"),  # py2.7 only
    ("lxml", "3.2.3"),  # py2.7 only
    ("lxml", "3.2.4"),  # py2.7 only
    ("lxml", "3.2.5"),  # py2.7 only
    ("docutils", "0.5"),  # py2.7 only Do not ask me about 0.4
    ("cairocffi", "0.1"),  # pre 2015
    ("cairocffi", "0.2"),  # pre 2015
    ("cairocffi", "0.3"),  # pre 2015
    ("cairocffi", "0.3.1"),  # pre 2015
    ("cairocffi", "0.3.2"),  # pre 2015
    ("cairocffi", "0.4"),  # pre 2015
    ("cairocffi", "0.4.1"),  # pre 2015
    ("cairocffi", "0.4.2"),  # pre 2015
    ("cairocffi", "0.4.3"),  # pre 2015
    ("cairocffi", "0.5"),  # pre 2015
    ("cairocffi", "0.5.1"),  # pre 2015
    ("cairocffi", "0.5.2"),  # pre 2015
    ("cairocffi", "0.5.3"),  # pre 2015
    ("cairocffi", "0.5.4"),  # pre 2015
    ("cairocffi", "0.6"),  # pre 2015
    ("cairocffi", "0.7"),  # pre 2015
    ("cairocffi", "0.7.1"),  # pre 2015
    ("tpdcc-libs-python", "0.0.1"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.2"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.3"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.4"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.5"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.6"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.7"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.8"),  # need  npm via dependency
    ("tpdcc-libs-python", "0.0.9"),  # need  npm via dependency
    ("python-calamine", "0.0.2"),  # no cargo lock
    ("python-calamine", "0.0.3"),  # no cargo lock
    ("python-calamine", "0.0.4"),  # no cargo lock
}
for fn in Path("autodetected/needs_sweep").glob("*"):
    text = fn.read_text().strip() 
    if text != "no":
        if text.startswith('>'):
            threshold = Version(text[1:])
        else:
            threshold = None
        info = get_info(fn.name)
        for k, v in info["releases"].items():
            v = [x for x in v if not "whl" in x["url"]]  # I want only source releases
            if not v:
                continue
            if (not v[0].get("yanked")) and (("." in k) or k.isnumeric()):
                if not is_prerelease(k):
                    if not (fn.name, k) in sweep_excluded:
                        if threshold is None or Version(k) >= threshold:
                            with_versions.append((fn.name, k))

with_versions.extend(
    [
        ("scikit-learn", "0.24.2"),
        # ("h5py", "2.10.0"),
        ("cirrocumulus", "1.1.57"),
    ]
)


if __name__ == "__main__":
    output_path = Path("input.json")
    output = []
    for pkg, version in with_versions:
        output.append((pkg, version))

    # output = [(k, v) for (k, v) in output if k != "python-axolotl-curve25519"]
    # output.append(("python-axolotl-curve25519", "0.4.1post2"))
    output_path.write_text(json.dumps(output, indent=2))


version_constraints = {
    "pyqt6": "<6.7.0",
    "pyqt6-qt6": "<6.7.0",
    "fastscript": ">=0.0.0.11",
}

for p in Path("cache").glob("remove_and_rebuild_"):
    print("Remove remove_and_rebuild cache for", p)
    p.unlink()

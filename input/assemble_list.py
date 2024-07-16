import urllib.request
import toml
import json
from pathlib import Path

read_dir = Path(__file__).parent
Path("pypi_info").mkdir(exist_ok=True)


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


def get_info(pkg):
    url = f"https://pypi.org/pypi/{pkg}/json"
    if not Path(f"pypi_info/{pkg}.json").exists():
        try:
            urllib.request.urlretrieve(url, f"pypi_info/{pkg}.json")
        except Exception as e:
            print("could not find / http issue", pkg, e)
            raise KeyError(pkg)
    return json.loads(Path(f"pypi_info/{pkg}.json").read_text())


def extract_date(kv):
    k, v = kv
    str_upload = v["upload_time_iso_8601"]
    return str_upload


def is_prerelease(version):
    # pep440
    return any(x in version.split(".")[-1] for x in ("a", "b", "rc", "dev", "post"))


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

with_versions.update(
    [
        ("scikit-learn", "0.24.2"),
        ("h5py", "2.10.0"),
    ]
)


if __name__ == "__main__":
    output_path = Path("../input.json")
    output = []
    for pkg, version in with_versions:
        output.append((pkg, version))
    output_path.write_text(json.dumps(output, indent=2))


version_constraints = {
    "pyqt6": "<6.7.0",
    "pyqt6-qt6": "<6.7.0",
    "fastscript": ">=0.0.0.11",
}

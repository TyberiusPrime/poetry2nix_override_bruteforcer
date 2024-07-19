from pathlib import Path
import collections
import re
import json
import toml

file_path = Path(__file__).parent

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

entries.extend(json.loads(Path("input.json").read_text())[:])

entries = [(k, v) for (k, v) in entries if k != "python-axolotl-curve25519"]
entries.append(("python-axolotl-curve25519", "0.4.1post2"))

def is_prerelease(version): # todo: refactor with assemble_list.py
    # pep440
    return any(x in version.split(".")[-1] for x in ("a", "b", "rc", "dev", "post"))

# these are packages we noted to have shitfting build-systems / overrides
# so we do them all to determine the cutover points.
for fn in Path('autodetected/needs_sweep').glob("*"):
    if fn.read_text().strip() == 'yes':
        info = shared.get_info(fn.name)
        for k, v in info["releases"].items():
            v = [x for x in v if not "whl" in x["url"]]  # I want only source releases
            if not v:
                continue
            if (not v[0].get("yanked")) and (("." in k) or k.isnumeric()):
                if not is_prerelease(k):
                    print(fn.name, k)
                    entries.append((fn.name, k))

def normalise_package_name(name):
    parts = re.split("[_.-]+", name.lower())
    parts = [x for x in parts if x]
    return "-".join(parts)


entries = [(normalise_package_name(k), v) for (k, v) in entries]


known_poetry_errors = set(
    json.loads(Path("input/known_poetry_errors.json").read_text())
)
known_312_errors = set(json.loads(Path("input/known_312_errors.json").read_text()))
known_py2_only = set(json.loads(Path("input/known_py2_only.json").read_text()))
known_infinite = set(
    toml.loads(Path("input/known_infinite_recursion.toml").read_text())["infinite"]
)
known_maconly = toml.loads(Path("input/known_maconly.toml").read_text())["maconly"]

known_other_erros = set(json.loads(Path("input/known_other_errors.json").read_text()))

autodetected = set()
for k in [
    "infinite-recursions",
    "python2-only",
    "python-version",
    "no-312",
    "openssl-1.1",
    "rust-nightly",
    "scikit-build-core version 0.8.2 is too old.",
]:
    for fn in (Path("autodetected_failures/") / k).glob("**/*"):
        if fn.is_file():
            autodetected.add(fn.parent.name + "-" + fn.name)

known_failing = set()
known_failing.update(known_poetry_errors)
known_failing.update(known_312_errors)
known_failing.update(known_py2_only)
known_failing.update(known_infinite)
known_failing.update(known_other_erros)
known_failing.update(known_maconly)
known_failing.update(autodetected)


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

    parts = derivation.split("-")
    for ii, p in enumerate(parts):
        if p[0].isnumeric() and ii > 0:
            break
    return "-".join(parts[:ii])

    return derivation.rsplit("-", 1)[0]


def pkg_and_version_from_derivation_name(derivation):
    pkg = pkg_from_derivation_name(derivation)
    version = derivation.split(pkg)[1][1:].replace(".drv", "")
    return (pkg, version)


assert pkg_and_version_from_derivation_name(
    "/nix/store/4q5x2hv3az5c6qjwmxf70w0jmbxbm4sc-python3.12-sphinx-autodoc-annotation-1.0-1.drv"
) == ("sphinx-autodoc-annotation", "1.0-1")
assert pkg_and_version_from_derivation_name(
    "/nix/store/iyp61gfvz7mhyz72a5gg4dlr25p2j70q-python3.12-2captcha-python-1.2.8.drv"
) == ("2captcha-python", "1.2.8")

assert (
    pkg_from_derivation_name(
        "/nix/store/4q5x2hv3az5c6qjwmxf70w0jmbxbm4sc-python3.12-sphinx-1.34"
    )
    == "sphinx"
)
assert (
    pkg_from_derivation_name(
        "/nix/store/4q5x2hv3az5c6qjwmxf70w0jmbxbm4sc-python3.12-sphinx-1.34"
    )
    == "sphinx"
)


def examine_results():
    op = Path("output")
    count = collections.Counter()
    classified = {}

    for pkg, version in entries:
        output_path = op / pkg / version
        what = "???"
        if not output_path.exists():
            if pkg in known_failing or (pkg + "-" + version) in known_failing:
                if pkg in autodetected or (pkg + "-" + version) in autodetected:
                    what = "fail:expected-autodetected"
                else:
                    what = "fail:expected-manual"

            else:
                what = "missing:not-done?"
                print(what, pkg)
        else:
            if (output_path / "result").exists():
                needed_patch = (output_path / "round2.stderr").exists()
                if needed_patch:
                    what = "success:needed_patch"
                else:
                    what = "success:upstream"
            else:
                if (output_path / "round1.stderr").exists():
                    if pkg in known_failing or (pkg + "-" + version) in known_failing:
                        if pkg in autodetected or (pkg + "-" + version) in autodetected:
                            what = "fail:expected-autodetected"
                        else:
                            what = "fail:expected-manual"
                    else:
                        what = "fail:unexpected"
                else:
                    if pkg in known_failing or (pkg + "-" + version) in known_failing:
                        if pkg in autodetected or (pkg + "-" + version) in autodetected:
                            what = "fail:expected-autodetected"
                        else:
                            what = "fail:expected-manual"
                    else:
                        what = "missing:not-done"
        count[what] += 1
        classified[(pkg, version)] = what
    return count, classified


def is_prerelease(version):
    # pep440
    return any(x in version.split(".")[-1] for x in ("a", "b", "rc", "dev", "post"))

def get_info(pkg):
    url = f"https://pypi.org/pypi/{pkg}/json"
    if not (file_path / f"pypi_info/{pkg}.json").exists():
        try:
            urllib.request.urlretrieve(url, f"pypi_info/{pkg}.json")
        except Exception as e:
            print("could not find / http issue", pkg, e)
            raise KeyError(pkg)
    return json.loads(Path(f"pypi_info/{pkg}.json").read_text())




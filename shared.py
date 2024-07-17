from pathlib import Path
import re
import json
import toml

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
for k in "infinite-recursions", "python2-only", "python-version", "no-312":
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
        if p[0].isnumeric():
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

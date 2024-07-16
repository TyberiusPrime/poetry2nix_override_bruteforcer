from pathlib import Path
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

infinite_recursions = set()
for fn in Path("infinite-recursion").glob("*"):
    infinite_recursions.add(fn.name)

known_failing = set()
known_failing.update(known_poetry_errors)
known_failing.update(known_312_errors)
known_failing.update(known_py2_only)
known_failing.update(known_infinite)
known_failing.update(known_other_erros)
known_failing.update(known_maconly)
known_failing.update(infinite_recursions)

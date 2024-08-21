if (lib.versionOlder old.version "2.2")
then {
  # disable buliding of the c extension, requires distutils
  postPatch = ''
    echo "def build(*args, **kwargs): pass" > build.py
    if [ -f pyproject.toml ]; then
      substituteInPlace pyproject.toml --replace-quiet "poetry.masonry.api" "poetry.core.masonry.api"
    fi
  '';
}
else
  (standardMaturin {
      furtherArgs = {
        cargoRoot = "rust";
      };
    }
    old)

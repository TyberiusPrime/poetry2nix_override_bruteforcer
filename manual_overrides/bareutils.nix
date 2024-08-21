{
  postPatch =
    (old.postPatch or "")
    + ''
      if [ -f "pyproject.toml" ]; then
        substituteInPlace pyproject.toml --replace-quiet "poetry.masonry.api" "poetry.core.masonry.api"
      fi
      touch requirements.txt
    '';
}

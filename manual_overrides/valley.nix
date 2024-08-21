{
  postPatch =
    (old.postPatch or "")
    + ''
      if [ -f pyproject.toml ]; then
        substituteInPlace pyproject.toml --replace "poetry.masonry.api" "poetry.core.masonry.api"
      fi
      touch requirements.txt
    '';
}

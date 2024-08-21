{
  postPatch =
    (old.postPatch or "")
    + ''
      touch requirements.txt
      if [ -f pyproject.toml ]; then
         substituteInPlace pyproject.toml --replace "poetry.masonry.api" "poetry.core.masonry.api"
      fi
    '';
}

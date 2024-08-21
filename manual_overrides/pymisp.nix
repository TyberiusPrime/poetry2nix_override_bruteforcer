{
  postPatch =
    (old.postPatch or "")
    + ''
       touch README.md
       if [ -f pyproject.toml ]; then
         substituteInPlace pyproject.toml --replace "poetry.masonry.api" "poetry.core.masonry.api"
      fi
    '';
}

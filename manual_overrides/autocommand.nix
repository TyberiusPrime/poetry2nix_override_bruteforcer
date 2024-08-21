{
  postPatch = ''
  if [ -f pyproject.toml ]; then
    substituteInPlace pyproject.toml --replace-quiet "requires-python" "license={ text = 'LGPLv3' } # requires-python"
  fi
  '';
}

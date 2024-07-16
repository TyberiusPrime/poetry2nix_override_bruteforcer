{
  postPatch = ''
    substituteInPlace pyproject.toml --replace-quiet "requires-python" "license={ text = 'LGPLv3' } # requires-python"
  '';
}

{
  postPatch = ''
    substituteInPlace 'setup.cfg' --replace-warn "setuptools-twine" ""
  '';
}

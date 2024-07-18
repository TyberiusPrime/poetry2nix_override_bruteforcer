{
  postPatch = ''
    substituteInPlace 'setup.py' --replace-warn "rmtree(directory, ignore_errors=True)" "pass"
  '';
}

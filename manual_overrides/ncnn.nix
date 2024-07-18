{
  postPatch = ''
    substituteInPlace setup.py --replace-warn "find_version()," "'${old.version}',"
  '';
}

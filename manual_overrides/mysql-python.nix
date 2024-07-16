{
  postPatch = ''
  substituteInPlace setup_posix.py --replace-quiet "from ConfigParser import SafeConfigParser" ""
  '';
}

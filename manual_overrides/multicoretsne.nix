{
  postPatch = ''
    substituteInPlace setup.py --replace-fail 'self.cmake_args or "--"' 'self.cmake_args or ""'

  '';
}

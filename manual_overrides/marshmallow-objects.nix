{
  postPatch = ''
    substituteInPlace setup.py --replace-fail ')' ', version="${old.version}")'
  '';
}

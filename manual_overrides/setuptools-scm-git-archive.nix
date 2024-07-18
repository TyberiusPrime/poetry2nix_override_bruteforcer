{
  postPatch = ''
    substituteInPlace setup.py --replace-quiet "setuptools-scm<8" "setuptools-scm"
  '';
}

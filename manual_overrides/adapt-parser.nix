{
  postPatch = ''
    substituteInPlace setup.py --replace-fail "required('requirements.txt')" "['six']"
  '';
}

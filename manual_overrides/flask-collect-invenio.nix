{
  postPatch = ''
    substituteInPlace setup.py --replace-quiet "pytest-runner>=3.0,<5" "pytest-runner>=3.0"
  '';
}

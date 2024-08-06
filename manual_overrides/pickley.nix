{
  postPatch = ''
  substituteInPlace setup.py --replace-fail 'versioning="dev"' 'version="${old.version}"'
  '';
}

{
  postPatch = ''
    substituteInPlace --replace-warn setup.py "readfp" "read_file"
  '';
}

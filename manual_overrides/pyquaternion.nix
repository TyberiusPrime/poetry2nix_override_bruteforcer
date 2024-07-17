{
  postPatch = ''
    echo "${old.version}" >VERSION.txt
  '';
}

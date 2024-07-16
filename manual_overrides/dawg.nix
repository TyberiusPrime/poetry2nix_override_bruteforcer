{
  buildInputs = [prev.cython_0];
  preBuild = ''
    PATH=$PATH:${prev.cython_0}/bin/ bash ./update_cpp.sh
  '';
}

{
  postPatch = ''
    patchShebangs skimage/_build_utils/{version,cythoner}.py
  '';
}

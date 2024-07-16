{
  postPatch = ''
  substituteInPlace "setup.py" \
    --replace-quiet "from distribute_setup import use_setuptools" "" \
    --replace-quiet "use_setuptools()" "" \
  '';

}

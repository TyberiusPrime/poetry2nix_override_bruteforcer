{
  # force cython regeneration
  buildInputs = old.buildInputs or [] ++ [final.cython_0];
  postPatch = ''
    find -name '*.c' -print0 | xargs -0 -r rm
  '';
}

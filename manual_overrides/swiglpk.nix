{
  buildInputs = old.buildInputs or [] ++ [pkgs.glpk];
  nativeBuildInputs = old.nativeBuildInputs or [] ++ [pkgs.swig];
  env = {GLPK_HEADER_PATH = "${pkgs.glpk}/include";};
}

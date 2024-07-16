{
  buildInputs = old.buildInputs or [] ++ [pkgs.openexr pkgs.ilmbase pkgs.libdeflate pkgs.clang-tools_17];
  NIX_CFLAGS_COMPILE = ["-I${pkgs.openexr.dev}/include/OpenEXR" "-I${pkgs.ilmbase.dev}/include/OpenEXR"];
}

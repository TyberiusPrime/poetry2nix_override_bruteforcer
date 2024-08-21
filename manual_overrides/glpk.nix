{
  buildInputs = old.buildInputs or [] ++ [pkgs.glpk];
}

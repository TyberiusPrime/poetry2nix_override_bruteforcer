let
  blas = old.passthru.args.blas or pkgs.openblasCompat;
in {
  buildInputs = old.buildInputs or [] ++ [blas pkgs.lapack];
}

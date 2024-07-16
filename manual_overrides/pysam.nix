{
  buildInputs = old.buildInputs or [] ++ [pkgs.zlib pkgs.bzip2 pkgs.xz pkgs.curl];
}

{
  patches = pkgs.python3Packages.dm-tree.patches;
  buildInputs = [pkgs.abseil-cpp];
}

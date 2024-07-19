{
  nativeBuildInputs = (old.nativeBuildInputs or []) ++ [pkgs.git];
}

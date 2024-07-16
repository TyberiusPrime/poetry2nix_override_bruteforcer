{
  nativeBuildInputs = [pkgs.icu prev.setuptools];
  format = "pyproject";
  buildInputs = [pkgs.icu];
}

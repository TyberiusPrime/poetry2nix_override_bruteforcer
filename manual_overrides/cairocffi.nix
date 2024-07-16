{
  buildInputs = old.buildInputs or [] ++ [final.pytest-runner];
  postInstall = "";
  patches = [];
}

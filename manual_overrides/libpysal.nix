lib.optionalAttrs (old.version == "4.1.0") {
  postPatch = ''
    touch requirements_plus_conda.txt
    touch requirements_plus_pip.txt
    touch requirements_docs.txt
  '';
}

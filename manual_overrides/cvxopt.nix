let
  blas = old.passthru.args.blas or pkgs.openblasCompat;
in {
  buildInputs = old.buildInputs or [] ++ [blas pkgs.suitesparse];

  postPatch =
    (old.postPatch or "")
    + ''
      if [ -f setup.py ]; then
        substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()" ""
      fi
    '';
}

{
  nativeBuildInputs = old.nativeBuildInputs or [] ++ [pkgs.gdal];
  preBuild =
    (old.preBuild or "")
    + lib.optionalString (!(old.src.isWheel or false)) ''
      substituteInPlace setup.cfg \
        --replace "../../apps/gdal-config" '${pkgs.gdal}/bin/gdal-config'
    '';
}

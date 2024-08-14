{
  nativeBuildInputs = prev.rpy2.nativeBuildInputs or [] ++ [pkgs.R];
  builtInputs =
    (old.buildInputs
      or [])
    ++ [
      (
        (with pkgs.rPackages; [
          # packages expected by the test framework
          ggplot2
          dplyr
          RSQLite
          broom
          DBI
          dbplyr
          hexbin
          lazyeval
          lme4
          tidyr
        ])
        ++ pkgs.rWrapper.recommendedPackages
      )
    ];
  # buildInputs is not enough with the poetry2nix hooks
  NIX_LDFLAGS =
    (lib.optionalString (lib.versionAtLeast old.version "3.5.13") "-L${pkgs.bzip2.out}/lib -L${pkgs.xz.out}/lib -L${pkgs.zlib.out}/lib -L${pkgs.icu.out}/lib")
    + (lib.optionalString (lib.versionOlder old.version "3.0.0") "-L${pkgs.readline.out}/lib");
}

{
  nativeBuildInputs = prev.rpy2.nativeBuildInputs or [] ++ [pkgs.R];
  builtInputs =
    old.buildInputs
    or []
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
}

(standardMaturin {
  furtherArgs = {
    cargoRoot = "";

    cargoDeps = (
      pkgs.rustPlatform.importCargoLock {
        lockFile = ./cargo.locks/h3ronpy/${old.version}.lock;

        outputHashes =
          let
            lookup = {
              "0.19.2" = {
                "h3arrow-0.2.0" = "sha256-AWPD9J98uoKoXAbOSdTJc/uCwMZr8Dm9DAoXC4rqtuU=";
              };
              "0.19.0" = {
                "h3arrow-0.2.0" = "sha256-AWPD9J98uoKoXAbOSdTJc/uCwMZr8Dm9DAoXC4rqtuU=";
              };
              "0.17.0" = {
                "geoarrow-0.0.1" = "sha256-++NQQ3wx1NoM0o+gQhp876E94u4o/WlDlBO7DShaKqk=";
                "h3arrow-0.1.0" = "sha256-ZlIDgKt9V/ZADtvdB3JEbYobRgKA/iidfCl2txFN64g=";
                "rasterh3-0.3.0" = "sha256-jp5Gbmyiw+pCP5QZwQF/3wxzpqEG5nMaXQ0Uu9mcwwo=";
              };
              "0.19.1" = {
                "h3arrow-0.2.0" = "sha256-AWPD9J98uoKoXAbOSdTJc/uCwMZr8Dm9DAoXC4rqtuU=";
              };
            };
          in
          lookup.${old.version} or { };
      }
    );
  };
} old)

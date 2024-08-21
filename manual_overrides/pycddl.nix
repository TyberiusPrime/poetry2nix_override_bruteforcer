(standardMaturin {
  furtherArgs = {
    cargoRoot = "";

    cargoDeps = (
      pkgs.rustPlatform.importCargoLock {
        lockFile = ./cargo.locks/pycddl/${old.version}.lock;

        outputHashes =
          let
            lookup = {
              "0.5.1" = {
                "cddl-0.9.1" = "sha256-YTXobgdSRvhirOMTpBoTLxsH83VXwLqjxD02QJFVMLE=";
              };
            };
          in
          lookup.${old.version} or { };
      }
    );
  };
} old)

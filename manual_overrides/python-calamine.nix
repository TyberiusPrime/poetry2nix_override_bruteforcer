dardMaturin {
  furtherArgs = {
    cargoRoot = "";

    cargoDeps = (
      pkgs.rustPlatform.importCargoLock {
        lockFile = ./cargo.locks/python-calamine/${old.version}.lock;

        outputHashes =
          let
            lookup = {
              "0.1.6" = {
                "calamine-0.21.2" = "sha256-LreW3N6+nqXK1Sm30A1hxJB0y3cprH57wpjLiBtL9YE=";
              };
              "0.1.2" = {
                "calamine-0.19.1" = "sha256-XgcV0BFg/OQA4Eg+P8RWr3SIFGInfTRL02o6WtSkIFg=";
                "pyo3-file-0.6.0" = "sha256-d3OnzA/0C0IxEAJUKJBvNuXcxB2j9tjg2Ax8cuuiMyI=";
              };
              "0.1.3" = {
                "pyo3-file-0.6.0" = "sha256-d3OnzA/0C0IxEAJUKJBvNuXcxB2j9tjg2Ax8cuuiMyI=";
              };
              "0.2.0" = {
                "pyo3-file-0.7.0" = "sha256-8bdLTVrzPDA8FVfc4uXB9TLXUkwuFNZ3hrJU2dUFbBM=";
              };
              "0.1.5" = {
                "calamine-0.21.2" = "sha256-LreW3N6+nqXK1Sm30A1hxJB0y3cprH57wpjLiBtL9YE=";
              };
              "0.1.1" = {
                "calamine-0.19.1" = "sha256-mKmVSOKIdEhB/PKs6aIlbA5Dp206T3Zi5aY7l4K8/ic=";
                "pyo3-file-0.6.0" = "sha256-d3OnzA/0C0IxEAJUKJBvNuXcxB2j9tjg2Ax8cuuiMyI=";
              };
              "0.1.0" = {
                "pyo3-file-0.6.0" = "sha256-d3OnzA/0C0IxEAJUKJBvNuXcxB2j9tjg2Ax8cuuiMyI=";
              };
              "0.2.3" = {
                "pyo3-file-0.8.1" = "sha256-EqeXykP7CF8SU5LgT9+y/FDy79E/DAJT2fc1OrmlOZE=";
              };
            };
          in
          lookup.${old.version} or { };
      }
    );
  };
} old)


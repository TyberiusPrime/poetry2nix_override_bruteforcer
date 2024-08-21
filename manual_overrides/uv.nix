(offlineMaturin {
  furtherArgs = {
    dontUseCmakeConfigure = true;
    cargoRoot = "";

    cargoDeps = (
      pkgs.rustPlatform.importCargoLock {
        lockFile = ./cargo.locks/uv/${old.version}.lock;

        outputHashes =
          let
            lookup = {
              "0.2.24" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
                "reqwest-middleware-0.3.2" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
                "reqwest-retry-0.7.0" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
              };
              "0.2.18" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
              };
              "0.2.14" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
              };
              "0.2.22" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
                "reqwest-middleware-0.3.2" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
                "reqwest-retry-0.7.0" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
              };
              "0.2.6" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-DtUK5k7Hfl5h9nFSSeD2zm4wBiVo4tScvFTUQWxTYlU=";
              };
              "0.2.17" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
              };
              "0.2.23" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
                "reqwest-middleware-0.3.2" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
                "reqwest-retry-0.7.0" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
              };
              "0.2.11" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-i1Eaip4J5VXb66p1w0sRjP655AngBLEym70ChbAFFIc=";
              };
              "0.2.19" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
                "reqwest-middleware-0.3.2" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
                "reqwest-retry-0.7.0" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
              };
              "0.2.7" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-DtUK5k7Hfl5h9nFSSeD2zm4wBiVo4tScvFTUQWxTYlU=";
              };
              "0.2.9" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-i1Eaip4J5VXb66p1w0sRjP655AngBLEym70ChbAFFIc=";
              };
              "0.2.16" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
              };
              "0.2.10" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-i1Eaip4J5VXb66p1w0sRjP655AngBLEym70ChbAFFIc=";
              };
              "0.2.8" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-i1Eaip4J5VXb66p1w0sRjP655AngBLEym70ChbAFFIc=";
              };
              "0.2.13" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-i1Eaip4J5VXb66p1w0sRjP655AngBLEym70ChbAFFIc=";
              };
              "0.2.21" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
                "reqwest-middleware-0.3.2" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
                "reqwest-retry-0.7.0" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
              };
              "0.2.15" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
              };
              "0.2.12" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-i1Eaip4J5VXb66p1w0sRjP655AngBLEym70ChbAFFIc=";
              };
              "0.2.20" = {
                "async_zip-0.0.17" = "sha256-Q5fMDJrQtob54CTII3+SXHeozy5S5s3iLOzntevdGOs=";
                "pubgrub-0.2.1" = "sha256-6tr+HATYSn1A1uVJwmz40S4yLDOJlX8vEokOOtdFG0M=";
                "reqwest-middleware-0.3.2" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
                "reqwest-retry-0.7.0" = "sha256-OiC8Kg+F2eKy7YNuLtgYPi95DrbxLvsIKrKEeyuzQTo=";
              };
            };
          in
          lookup.${old.version} or { };
      }
    );
  };
} old)

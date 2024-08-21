(standardMaturin {
    furtherArgs = lib.optionalAttrs (lib.versionOlder old.version "0.14.0") {
      cargoRoot = "bindings/python";
    };
  }
  old)

standardMaturin {
  maturinHook = null;

  furtherArgs = {
    postPatch = let
      cargo_lock = ./. + "/cargo.locks/${old.pname}/${old.version}.lock";
    in
      (old.postPatch or "")
      + ''
        cp ${cargo_lock} Cargo.lock
      '';
    nativeBuildInputs = (old.nativeBuildInputs or []) ++ [pkgs.rustc pkgs.cargo];
  };
} old

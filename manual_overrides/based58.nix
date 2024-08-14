(standardMaturin {
  furtherArgs = {
    postPatch = let
      cargo_lock = ./. + "/cargo.locks/${old.pname}/${old.version}.lock";
    in (
      (old.postPatch or "")
      + ''
        touch LICENSE
        cp ${cargo_lock} Cargo.lock
      ''
    );
  };
})
old

{
  defaultPoetryOverrides,
  pkgs,
  lib,
}: let
  addBuildSystem' = {
    final,
    drv,
    attr,
    extraAttrs ? [],
  }: let
    buildSystem =
      if builtins.isAttrs attr
      then let
        fromIsValid =
          if builtins.hasAttr "from" attr
          then lib.versionAtLeast drv.version attr.from
          else true;
        untilIsValid =
          if builtins.hasAttr "until" attr
          then lib.versionOlder drv.version attr.until
          else true;
        intendedBuildSystem =
          if lib.elem attr.buildSystem ["cython" "cython_0"]
          then (final.python.pythonOnBuildForHost or final.python.pythonForBuild).pkgs.${attr.buildSystem}
          else final.${attr.buildSystem};
      in
        if fromIsValid && untilIsValid
        then intendedBuildSystem
        else null
      else if lib.elem attr ["cython" "cython_0"]
      then (final.python.pythonOnBuildForHost or final.python.pythonForBuild).pkgs.${attr}
      else final.${attr};
  in
    if (attr == "flit-core" || attr == "flit" || attr == "hatchling") && !final.isPy3k
    then drv
    else if drv == null
    then null
    else if !drv ? overridePythonAttrs
    then drv
    else
      drv.overridePythonAttrs (
        old:
        # We do not need the build system for wheels.
          if old ? format && old.format == "wheel"
          then {}
          else if attr == "poetry"
          then {
            # replace poetry
            postPatch =
              (old.postPatch or "")
              + ''
                if [ -f pyproject.toml ]; then
                  toml="$(mktemp)"
                  yj -tj < pyproject.toml | jq --from-file ${./poetry-to-poetry-core.jq} | yj -jt > "$toml"
                  mv "$toml" pyproject.toml
                fi
              '';
            nativeBuildInputs =
              old.nativeBuildInputs
              or []
              ++ [final.poetry-core final.pkgs.yj final.pkgs.jq]
              ++ map (a: final.${a}) extraAttrs;
          }
          else {
            nativeBuildInputs =
              old.nativeBuildInputs
              or []
              ++ lib.optionals (!(builtins.isNull buildSystem)) [buildSystem]
              ++ map (a: final.${a}) extraAttrs;
          }
      );

  buildSystems = lib.importJSON ./build-systems.json;
  #Copy-into-auto-overrides
  standardMaturin = {
    furtherArgs ? {},
    maturinHook ? pkgs.rustPlatform.maturinBuildHook,
  }: old:
    lib.optionalAttrs (!(old.src.isWheel or false)) (
      {
        cargoDeps = pkgs.rustPlatform.importCargoLock {
          lockFile = ./. + "/cargo.locks/${old.pname}/${old.version}.lock";
        };
        nativeBuildInputs =
          (old.nativeBuildInputs or [])
          ++ [
            pkgs.rustPlatform.cargoSetupHook
            maturinHook
          ]
          ++ (furtherArgs.nativeBuildInputs or []);
      }
      # furtherargs without nativeBuildInputs
      // lib.attrsets.filterAttrs (name: _value: name != "nativeBuildInputs") furtherArgs
    );
  offlineMaturinHook = pkgs.callPackage ({pkgsHostTarget}:
    pkgs.makeSetupHook {
      name = "offline-maturin-build-hook.sh";
      propagatedBuildInputs = [
        pkgsHostTarget.maturin
        pkgsHostTarget.cargo
        pkgsHostTarget.rustc
      ];
      substitutions = {
        inherit (pkgs.rust.envVars) rustTargetPlatformSpec setEnv;
      };
    }
    ./offline-maturin-build-hook.sh) {};
  offlineMaturin = args:
    standardMaturin (args
      // {
        maturinHook = offlineMaturinHook;
      });
  #end-Copy-into-auto-overrides
in [
  defaultPoetryOverrides

  (final: prev: let
    buildSystems = lib.importJSON ./build-systems.json;
  in
    lib.mapAttrs
    (attr: systems:
      builtins.foldl'
      (drv: attr:
        addBuildSystem' {
          inherit drv final attr;
        })
      (prev.${attr} or null)
      systems)
    buildSystems)

  
            (final: prev: (
                {
                    jiter  = prev.jiter.overridePythonAttrs (old: ((offlineMaturin { furtherArgs = {};}) old));
                }
            ))


 
]

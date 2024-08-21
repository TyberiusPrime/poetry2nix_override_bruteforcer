{ pkgs, lib, ... }:
{
  # Used to find the project root
  projectRootFile = "flake.lock";

  settings.formatter = {
    build-systems = {
      command = "sh";
      options = [
        "-eucx"
        ''
          for i in "$@"; do
            ${lib.getExe pkgs.jq} --from-file poetry2nix-ready-files/auto-build_systems.json  --raw-output --sort-keys < f"$i" | ${lib.getBin pkgs.moreutils}/bin/sponge "$i"
          done
        ''
        "--"
      ];
      includes = [ "overrides/build-systems.json" ];
      excludes = [ ];
    };

    black.excludes = [ "vendor/**.py" ];
  };

  programs.deadnix.enable = true;
  programs.statix.enable = true;
  programs.black.enable = true;
}

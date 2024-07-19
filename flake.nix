#shu
{
  description = "Application packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/24.05";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    rust-overlay.url = "github:oxalica/rust-overlay";
    rust-overlay.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    poetry2nix,
    rust-overlay,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      overlays = [(import rust-overlay)];
      pkgs = import nixpkgs {inherit system overlays;};
      inherit (poetry2nix.lib.mkPoetry2Nix {inherit pkgs;}) mkPoetryEnv defaultPoetryOverrides;
    in {
      packages = {
        myapp = mkPoetryEnv {
          projectDir = self;
          python = pkgs.python312;
          overrides = defaultPoetryOverrides.extend (final: prev: {
            polars = prev.polars.override {preferWheel = true;}; #.overridePythonAttrs (old: { preferWheel = true; });
            pyzstd = prev.pyzstd.override {preferWheel = true;}; #.overridePythonAttrs (old: { preferWheel = true; });
            #pypipegraph2 = prev.pypipegraph2.override {preferWheel = true;}; #.overridePythonAttrs (old: { preferWheel = true; });
            pypipegraph2 = prev.pypipegraph2.overridePythonAttrs (old: {
              cargoDeps = pkgs.rustPlatform.importCargoLock {
                lockFile = "${prev.pypipegraph2.src}/Cargo.lock";
              };

              nativeBuildInputs =
                prev.pypipegraph2.nativeBuildInputs
                ++ [
                  pkgs.rustPlatform.cargoSetupHook
                  pkgs.rustPlatform.maturinBuildHook
                ];
            });
            numpy = prev.numpy.override {preferWheel = true;}; #.overridePythonAttrs (old: { preferWheel = true; });
          });
          #preferWheels = true;
        };
      };

      defaultPackage = self.packages.${system}.myapp;

      # Shell for app dependencies.
      devShells.default = pkgs.mkShell {
        #inputsFrom = [self.packages.${system}.myapp];
        buildInputs = [self.packages.${system}.myapp pkgs.poetry pkgs.nixfmt-rfc-style];
      };

      # Shell for poetry.
      devShells.poetry = pkgs.mkShell {
        packages = [pkgs.poetry];
      };
    });
}

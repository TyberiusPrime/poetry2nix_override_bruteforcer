{
  description = "Application packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/24.05";
    poetry2nix = {
      #url = "github:nix-community/poetry2nix";
      url = "github:TyberiusPrime/poetry2nix/orjson_removed";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    poetry2nix,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      inherit (poetry2nix.lib.mkPoetry2Nix {inherit pkgs;}) mkPoetryEnv defaultPoetryOverrides;
    in {
      packages = {
        myapp = mkPoetryEnv {
          projectDir = self;
          python = pkgs.python312;
          overrides = import ./overrides.nix {
            inherit defaultPoetryOverrides;
            inherit pkgs;
            inherit (pkgs) lib;
          }; 
          preferWheels = false;
        };
      };

      defaultPackage = self.packages.${system}.myapp;

      # Shell for app dependencies.
      devShells.default = pkgs.mkShell {
        inputsFrom = [self.packages.${system}.myapp];
      };

      # Shell for poetry.
      devShells.poetry = pkgs.mkShell {
        packages = [pkgs.poetry];
      };
    });
}

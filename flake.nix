{
  description = "Convert Vector JSONL telemetry files to MCAP format";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python overlay to add our package to pythonPackages
        pythonOverlay = final: prev: {
          pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
            (python-final: python-prev: {
              vector2mcap = python-final.callPackage ./default.nix { };
            })
          ];
        };
        
        # Apply the overlay
        pkgsWithOverlay = import nixpkgs {
          inherit system;
          overlays = [ pythonOverlay ];
        };
        
        # Our package
        vector2mcap = pkgsWithOverlay.python3Packages.vector2mcap;
      in
      {
        # Make the package available as the default package
        packages.default = vector2mcap;
        packages.vector2mcap = vector2mcap;
        
        # Apps for nix run
        apps.default = {
          type = "app";
          program = "${vector2mcap}/bin/vector2mcap";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            uv
            ruff
            pyright

            mcap-cli
          ];
        };
      }
    );
}

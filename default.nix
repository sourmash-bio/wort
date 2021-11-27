let
  sources = import ./nix/sources.nix;
  pkgs = import sources.nixpkgs {
    config = { };
    overlays = [
      (import ./nix/overlay.nix)
    ];
  };
in
pkgs.wort

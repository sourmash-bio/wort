# shell.nix
let
  sources = import ./nix/sources.nix;
  rustPlatform = import ./nix/rust.nix { inherit sources; };
  pkgs = import sources.nixpkgs { };
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    rustPlatform.rust.cargo
    openssl
    pkgconfig

    wasm-pack
    wasmtime
    wasm-bindgen-cli

    nixpkgs-fmt

    (python310.withPackages (ps: with ps; [ flit pip-tools biopython pandas pipx ] ))
    curl
  ];
}

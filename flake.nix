{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";

    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "utils";
      };
    };
  };

  outputs = { self, nixpkgs, rust-overlay, utils }:
    utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };
        rustVersion = pkgs.rust-bin.stable.latest.default.override {
          #extensions = [ "rust-src" ];
          targets = [ "wasm32-wasi" "wasm32-unknown-unknown" "x86_64-unknown-linux-musl" ];
        };
        rustPlatform = pkgs.makeRustPlatform {
          cargo = rustVersion;
          rustc = rustVersion;
        };
      in

      with pkgs;
      {
        devShell = mkShell {
          nativeBuildInputs = with rustPlatform; [ bindgenHook ];

          buildInputs = [
            rustVersion
            openssl
            pkgconfig

            git
            stdenv.cc.cc.lib
            (python311.withPackages (ps: with ps; [ flit pip-tools biopython pandas pipx ]))

            wasmtime
            wasm-pack
            nodejs_20
            wasm-bindgen-cli

            curl
            cargo-watch
            cargo-limit
            cargo-outdated
            cargo-udeps
            cargo-deny
            nixpkgs-fmt
          ];

          # workaround for https://github.com/NixOS/nixpkgs/blob/48dfc9fa97d762bce28cc8372a2dd3805d14c633/doc/languages-frameworks/python.section.md#python-setuppy-bdist_wheel-cannot-create-whl
          SOURCE_DATE_EPOCH = 315532800; # 1980
        };
      });
}

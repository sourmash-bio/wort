# import niv sources and the pinned nixpkgs
{ sources ? import ../sources.nix
, pkgs ? import sources.nixpkgs {
    #    crossSystem = {
    #      isStatic = true;
    #      config = "x86_64-unknown-linux-musl";
    #    };
  }
}:
let
  # import rust compiler
  rustPlatform = import ../rust.nix { inherit sources; };
in
rustPlatform.buildRustPackage rec {
  pname = "wort";
  version = "0.1";

  src = pkgs.fetchFromGitHub {
    owner = "dib-lab";
    repo = "wort";
    rev = "1d39cb4987f1fd916a42c4767b582691d3522d6c";
    sha256 = "17v3rw9p82z0anhsvdhvwm43lgvgrd8chqbd7f5bhb2f990618w6";
  };

  nativeBuildInputs = [ pkgs.pkg-config ];

  buildInputs = [ pkgs.openssl pkgs.dbus pkgs.glibc ];

  #target = "x86_64-unknown-linux-musl";

  cargoSha256 = "05a9370bwvymp4rd1yyzajrj5b8vd1dzskh9g268h3yd7b6gnhgf";

  # TODO: how to activate specific members?
  #members = ["crates/local" "crates/server" "crates/frontend" "crates/p2p" "crates/api"];

  meta = with pkgs.lib; {
    description = "Searching large sequencing databases";
    homepage = "https://github.com/dib-lab/wort";
    license = licenses.agpl3;
    maintainers = [ maintainers.luizirber ];
  };
}

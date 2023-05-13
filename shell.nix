{ pkgs ? import <nixpkgs> {}}:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.python3Packages.twine
    pkgs.python3Packages.setuptools
    pkgs.python3Packages.wheel
  ];
}

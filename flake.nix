{

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
    systems.url = "github:nix-systems/default";
    nix-vscode-extensions.url = "github:nix-community/nix-vscode-extensions";
  };

  outputs =
    { self
    , nixpkgs
    , systems
    , nix-vscode-extensions
    , ...
    } @ inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      devShells = forEachSystem
        (system:
          let
            pkgs = import nixpkgs {
              system = system;
              config.allowUnfree = true;
            };
            extensions = nix-vscode-extensions.extensions.${system};
            codeWithExtensions =
              let
                inherit (pkgs) vscode-with-extensions;
                someExtensions = with (extensions.forVSCodeVersion pkgs.vscode.version).vscode-marketplace; [
                  usernamehw.errorlens
                  ms-python.python
                  ms-python.debugpy
                  ms-python.vscode-pylance
                ];
              in
              (vscode-with-extensions.override {
                vscodeExtensions = someExtensions;
              });
          in
          {
            default = pkgs.mkShell {

              NIX_PATH = "nixpkgs=" + pkgs.path;

              buildInputs = with pkgs;[
                python312Packages.pyserial
                socat
              ] ++ [ codeWithExtensions ];

            };
          });

    };

}

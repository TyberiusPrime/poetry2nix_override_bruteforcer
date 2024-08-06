# we have to keep our own patchset to support multiple cairocffi versions
# independent of the nixpkgs version
let
  patch_path =
    if (lib.versionAtLeast old.version "1.7")
    then ./patches/cairocffi/1.7.0
    else patches/cairocffi/1.6.2;
  patches = with pkgs; [
    # OSError: dlopen() failed to load a library: gdk-pixbuf-2.0 / gdk-pixbuf-2.0-0
    (substituteAll {
      src = patch_path + "/dlopen-paths.patch";
      ext = stdenv.hostPlatform.extensions.sharedLibrary;
      cairo = cairo.out;
      glib = glib.out;
      gdk_pixbuf = gdk-pixbuf.out;
    })
    (patch_path + "/fix_test_scaled_font.patch")
  ];
in
  {
    buildInputs = old.buildInputs or [] ++ [final.pytest-runner];
    postInstall = lib.optionalString (old.src.isWheel or false) ''
      pushd "$out/${final.python.sitePackages}"
      for patch in ${lib.concatMapStringsSep " " (p: "${p}") patches}; do
        patch -p1 < "$patch"
      done
      popd
    '';
  }
  // lib.optionalAttrs (!(old.src.isWheel or false)) {
    inherit patches;
  }

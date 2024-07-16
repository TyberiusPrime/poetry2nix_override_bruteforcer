# might want to import this from nixpkgs instead?
let
  # PyMuPDF needs the C++ bindings generated
  mupdf-cxx = mupdf.override {
    enableOcr = true;
    enableCxx = true;
    enablePython = true;
    python3 = python;
  };
in {
  postPatch = ''
    substituteInPlace pyproject.toml \
      --replace-fail '"swig",' "" \
      --replace-fail "libclang" "clang"
  '';

  nativeBuildInputs = [
    libclang
    swig
    psutil
    setuptools
  ];

  buildInputs =
    [
      freetype
      harfbuzz
      openjpeg
      jbig2dec
      libjpeg_turbo
      gumbo
    ]
    ++ lib.optionals (stdenv.system == "x86_64-darwin") [memstreamHook];

  propagatedBuildInputs = [mupdf-cxx];

  env = {
    # force using system MuPDF (must be defined in environment and empty)
    PYMUPDF_SETUP_MUPDF_BUILD = "";
    # provide MuPDF paths
    PYMUPDF_MUPDF_LIB = "${lib.getLib mupdf-cxx}/lib";
    PYMUPDF_MUPDF_INCLUDE = "${lib.getDev mupdf-cxx}/include";
  };

  # TODO: manually add mupdf rpath until upstream fixes it
  postInstall = lib.optionalString stdenv.isDarwin ''
    for lib in */*.so $out/${python.sitePackages}/*/*.so; do
      install_name_tool -add_rpath ${lib.getLib mupdf-cxx}/lib "$lib"
    done
  '';
}

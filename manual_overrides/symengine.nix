{
  env = {
    SymEngine_DIR = "${pkgs.symengine}";
  };

  patches = [
    # Distutils has been removed in python 3.12
    # See https://github.com/symengine/symengine.py/pull/478
    (pkgs.fetchpatch {
      name = "no-distutils.patch";
      url = "https://github.com/symengine/symengine.py/pull/478/commits/e72006d5f7425cd50c54b22766e0ed4bcd2dca85.patch";
      hash = "sha256-kGJRGkBgxOfI1wf88JwnSztkOYd1wvg62H7wA6CcYEQ=";
    })
  ];

  postPatch = ''
    substituteInPlace setup.py \
      --replace-fail "\"cmake\"" "\"${lib.getExe' pkgs.cmake "cmake"}\"" \
      --replace-fail "'cython>=0.29.24'" "'cython'"

    export PATH=${prev.cython}/bin:$PATH
  '';
}

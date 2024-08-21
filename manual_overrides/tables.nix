{
  nativeBuildInputs = old.nativeBuildInputs or [] ++ [pkgs.pkg-config];
  postPatch = ''    substituteInPlace setup.py \
            --replace-warn "shutil.copy(libdir / \"libblosc2.so\", ROOT / \"tables\")" ""
  '';
  buildInputs =
    old.buildInputs
    or []
    ++ (with pkgs; [
      bzip2
      c-blosc
      c-blosc2
      hdf5
      lzo
    ]);
  LZO_DIR = "${lib.getDev pkgs.lzo}";
  BZIP2_DIR = "${lib.getDev pkgs.bzip2}";
  HDF5_DIR = "${lib.getDev pkgs.hdf5}";
  BLOSC_DIR = "${lib.getDev pkgs.c-blosc}";
  BLOSC2_DIR = "${lib.getDev pkgs.c-blosc2}";
}

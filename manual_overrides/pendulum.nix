lib.optionalAttrs (lib.versionOlder old.version "2.2") {
  # disable buliding of the c extension, requires distutils
  postPatch = ''
    echo "" > build.py
  '';
}

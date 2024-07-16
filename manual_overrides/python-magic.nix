let
  sharedLibExt = pkgs.stdenv.hostPlatform.extensions.sharedLibrary;
  libPath = "${lib.getLib pkgs.file}/lib/libmagic${sharedLibExt}";
  fixupScriptText = ''
  if [ -f magic/loader.py ]; then
    substituteInPlace magic/loader.py \
      --replace "find_library('magic')" "'${libPath}'"
  else
    substituteInPlace magic.py \
      --replace-fail "ctypes.util.find_library('magic')" "'${libPath}'" \
      --replace-fail "ctypes.util.find_library('magic1')" "'${libPath}'"
  fi
  '';
  isWheel = old.src.isWheel or false;
in {
  postPatch = lib.optionalString (!isWheel) fixupScriptText;
  postFixup = lib.optionalString isWheel ''
    cd $out/${final.python.sitePackages}
    ${fixupScriptText}
  '';
  pythonImportsCheck = old.pythonImportsCheck or [] ++ ["magic"];
}

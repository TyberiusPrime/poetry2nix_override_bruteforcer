{
  postPatch =
    (old.postPatch or "")
    + (lib.optionalString (lib.versionOlder old.version  "1.0.1")
      ''
        touch requirements.txt
      '')
    + ''
      if [ -f setup.py ]; then
        substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()" ""
      fi
    '';
}

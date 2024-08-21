{
  postPatch =
    (old.postPatch or "")
    + ''
      if [ -f setup.py ]; then
        substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()" ""
      fi
    ''
    + (
      lib.optionalString (lib.versionOlder old.version "0.1.5") ''
        touch README.md
      ''
    );
}

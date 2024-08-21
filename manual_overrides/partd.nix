{
  postPatch =
    (old.postPatch or "")
    + ''
      if [ -e setup.py ]; then
        substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \
          --replace-quiet "cmdclass=versioneer.get_cmdclass()" ""
      fi
      touch requirements.txt
    '';
}

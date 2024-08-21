{
  postPatch =
    (old.postPatch or "")
    + ''
      substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \
        --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \
        --replace-quiet "cmdclass=versioneer.get_cmdclass()" ""             '';
  meta.priority = 2;
}

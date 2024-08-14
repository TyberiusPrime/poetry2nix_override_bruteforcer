{
  meta.priority = 1;

  postPatch = ''
    substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \
      --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \
     --replace-quiet "cmdclass=versioneer.get_cmdclass()" ""             '';
}

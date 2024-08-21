{
  postPatch = ''
    if [ -f setup.py ]; then
      substituteInPlace setup.py --replace-quiet "versioneer.get_version()" "'${old.version}'" \
        --replace-quiet "cmdclass=versioneer.get_cmdclass()," "" \
        --replace-quiet "cmdclass = versioneer.get_cmdclass()" "" \
        --replace-quiet "cmdclass=cmdclass," "" \
        --replace-quiet "cmdclass=dict(clean=Clean, **versioneer.get_cmdclass())," "" \
        --replace-quiet "cmdclass.update(clean=NumpyGroupiesClean)" "" \
        --replace-quiet "cmdclass=dict(clean=NumpyGroupiesClean, **versioneer.get_cmdclass())," "" \
        --replace-quiet "cmdclass=versioneer.get_cmdclass()" ""
    fi
  '';
}

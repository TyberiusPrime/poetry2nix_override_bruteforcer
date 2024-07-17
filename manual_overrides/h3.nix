{
  # have to throw away the old preBuild
  preBuild = ''
    if [ -f h3/h3.py ]; then
      substituteInPlace h3/h3.py \
        --replace "'{}/{}'.format(_dirname, libh3_path)" '"${pkgs.h3}/lib/libh3${sharedLibExt}"'
        fi
  '';
}

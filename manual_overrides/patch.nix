{
  unpackPhase = ''
    cd /build
    mkdir ${old.pname}-${old.version}
    cd ${old.pname}-${old.version}
    unzip ${old.src}
  '';
}

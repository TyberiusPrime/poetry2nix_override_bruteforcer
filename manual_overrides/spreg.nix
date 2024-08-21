lib.optionalAttrs (lib.versionOlder old.version "1.0.1")
{
  postPatch = (old.patchPhase or "") + ''
  ls -la 
  cd /build/${old.pname}-${old.version}
    touch requirements.txt
    touch requirements_plus.txt
    touch requirements_dev.txt
  ls -la
  '';
}

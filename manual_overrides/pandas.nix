{
  postPatch = (old.postPatch or "") + ''
  if [ -f versioneer.py ]; then
    substituteInPlace versioneer.py \
      --replace-quiet "SafeConfigParser" "ConfigParser" \
      --replace-quiet "readfp" "read_file"
  fi
  '';
}

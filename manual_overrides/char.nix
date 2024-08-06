{
  postPatch = ''
  substituteInPlace setup.py \
    --replace-fail 'use_pyscaffold=True' 'use_pyscaffold=True, version="${old.version}"'
  '';
}

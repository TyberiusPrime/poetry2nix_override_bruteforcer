{
  postPatch = ''
    substituteInPlace setup.py \
     --replace-fail "observed_version = [int(x) for x in setuptools.__version__.split('.')]" "observed_version = [70,]"
  ''; # anything over 36.2.0 should be ok.
}

{
  postPatch =
    (old.postPatch or "")
    + ''
      touch README.md
      if [ -e setup.py ]; then
      substituteInPlace setup.py \
        --replace-quiet "use_2to3=True," "" \
        --replace-quiet "use_2to3=True" "" \
        --replace-quiet "use_2to3 = True," "" \
        --replace-quiet "use_2to3= bool(python_version >= 3.0)," "" \
        --replace-quiet "extra_setup_params[\"use_2to3\"] = True" ""
      fi
    '';
}

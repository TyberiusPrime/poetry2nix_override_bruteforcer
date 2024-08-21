{
  postPatch =
    if (old.version == "0.0.0")
    then ''
      touch requirements.txt
    ''
    else ''
      mkdir requirements
      touch requirements/requirements.txt
      touch requirements/extras.txt
    '';
}

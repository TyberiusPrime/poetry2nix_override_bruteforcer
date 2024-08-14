{
  buildInputs = (old.buildInputs or []) ++ pkgs.rdkafka;
}

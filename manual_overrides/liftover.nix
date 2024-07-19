{
  buildInputs = (old.buildInputs or {}) ++ [ pkgs.zlib ];
}

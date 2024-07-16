{
  postConfigure = ''
    export PYSTEMMER_SYSTEM_LIBSTEMMER="${lib.getDev libstemmer}/include"
  '';

  env.NIX_CFLAGS_COMPILE = toString ["-I${lib.getDev libstemmer}/include"];

  NIX_CFLAGS_LINK = ["-L${libstemmer}/lib"];
}

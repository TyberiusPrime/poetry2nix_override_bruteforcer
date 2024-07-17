{
  # from nixpkgs.
  prePatch = ''
    ln -s ${pkgs.unicorn-emu}/lib/libunicorn.* prebuilt/
  '';
}

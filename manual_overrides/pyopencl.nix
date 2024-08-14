{
  CMAKE_PREFIX_PATH = "${prev.nanobind}/lib/python${lib.versions.majorMinor final.python.version}/site-packages/nanobind/cmake";
  dontUseCmakeConfigure = true;
}

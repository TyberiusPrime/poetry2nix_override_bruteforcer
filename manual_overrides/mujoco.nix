{
  buildInputs = [pkgs.mujoco];
  dontUseCmakeConfigure = true;
  env.MUJOCO_PATH = "${pkgs.mujoco}";
  env.MUJOCO_PLUGIN_PATH = "${pkgs.mujoco}/lib";
  env.MUJOCO_CMAKE_ARGS = lib.concatStringsSep " " [
    "-DMUJOCO_SIMULATE_USE_SYSTEM_GLFW=ON"
    "-DMUJOCO_PYTHON_USE_SYSTEM_PYBIND11=ON"
  ];

  preConfigure =
    # Use non-system eigen3, lodepng, abseil: Remove mirror info and prefill
    # dependency directory. $build from setuptools.
    with pkgs;(
      let
        pname = old.pname;
        version = old.version;

        # E.g. 3.11.2 -> "311"
        pythonVersionMajorMinor = with lib.versions; "${major python.pythonVersion}${minor python.pythonVersion}";

        # E.g. "linux-aarch64"
        platform = with stdenv.hostPlatform.parsed; "${kernel.name}-${cpu.name}";
      in ''
        ${perl}/bin/perl -0777 -i -pe "s/GIT_REPO\n.*\n.*GIT_TAG\n.*\n//gm" mujoco/CMakeLists.txt
        ${perl}/bin/perl -0777 -i -pe "s/(FetchContent_Declare\(\n.*lodepng\n.*)(GIT_REPO.*\n.*GIT_TAG.*\n)(.*\))/\1\3/gm" mujoco/simulate/CMakeLists.txt

        build="/build/${pname}-${version}/build/temp.${platform}-cpython-${pythonVersionMajorMinor}/"
        mkdir -p $build/_deps
        ln -s ${mujoco.pin.lodepng} $build/_deps/lodepng-src
        ln -s ${mujoco.pin.eigen3} $build/_deps/eigen-src
        ln -s ${mujoco.pin.abseil-cpp} $build/_deps/abseil-cpp-src
      ''
    );
}

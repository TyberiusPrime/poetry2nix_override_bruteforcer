{
  preBuild = ''
    # go to the directory of setup.py
    # it get's lost in cmake.
    cd /build
    SETUP_PATH=`find . -name "setup.py" | sort | head -n 1`
    echo "SETUP_PATH: $SETUP_PATH"
    cd $(dirname $SETUP_PATH)
  '';
}

{
  postPatch = ''
    substituteInPlace progressbar/__init__.py \
      --replace-quiet "from compat import *" "from .compat import *" \
      --replace-quiet "from widgets import *" "from .widgets import *"
  '';
}

# Poetry2nix override brute forcer

A tool to somewhat automaticall generate overrides for poetry2nix.

Poetry2nix is limited to not use import-from-derivation.
That means it needs to presupply the build-sytems for python packages. 

Also, many python packages need some kind of minor overrides to actually build.

This project automates the process.


## Usage
1. Clone the repo, enter the nix devlop environment.
1. (remove input/py_info/*.json if you want the newest releases of everything to be considered)
1. run 01_assemble_package_list.py
1. run 02_build_packages.py (bring some time & ignore failing jobs for now)
1. run 03_stats.py to get an impression of how many newly working builds we have.
1. run 04_generate_overrides.py
1. Ignore the error messages and repeat the previous four steps -  
  02_build_packages autodetects packages to add to the the 'will never build list' ,
  and 04_generate_overrides.py will flag packages where we want to sweep all versions 
  to determine change points in build-systems and necessary overrides.
  Alternativly you can examine autodetected/needs_sweep, and run the individually
  with `./02_build_packages.py <pkg> [version]`
1. Look at the packages that still don't build. You can grep .ppg/errors/latest/* for that,
  or use 'random_failure.py' to find some. Try to get them to build (see below). 
  Check if they're building with `./02_build_packages.py <pkg> [version]`


## Getting packages to building 
 
- use `show_last_round.py <pkg> [version]` to view the nix log of the last build attempt
- if it's ultra specific, 
  add a manual_overide/<pkg>.nix file with the necessary overrides.
  Or a manual_overrides/<pkg>.json for the build-systems
- if it's more general, try to extend `guess_overrides(...)` in 02_build_packages.py
- if you can't make it work,  add it to input/known\_*\_errors.json

Good luck!


# TODO:

- figure out how to auto merge packages wit multiple overrides (currently commented out in the generated auto-overrides.nix
- figure out how to automatically write the necessary nix for packages that need different overrides per version (similar to teh build inputs)
- fix more packages
- extend to larger subset of pypi
- fix the auto-overrides.nix generation: must be an importable file exporting just (not just dumping our overrides.nix)  
- include the cargo.locks in poetry2nix-ready-files
- replace the versioneer replacements with a function
- fix the newlines in the substituteInPlace calls


# Building from Source
The core C++ library, `libcgillespy3d`, can be found in the `libcGillesPy3D/` directory. It is built using a custom [SCons](https://scons.org/documentation.html) build.

## Building the Core C++ Library
From the root-level directory, ensure that SCons is installed and run the following command:
```sh
scons -C libcGillesPy3D/
# to clean the environment:
scons -c -C libcGillesPy3D/
```

The build output is placed in the `libcGillesPy3D/lib` directory, which includes any static libraries required by dependencies, as well as a SWIG-generated `libcgillespy3d` package. Adding the `lib` directory to your `PATH`/`PYTHONPATH` will work as a manual way to add the `libcgillespy3d` library.

## Building the Python Extension
Before building the Python extension, you must first [build the core C++ library](#building-the-core-c-library).

From the root-level directory, install the library using `pip`:
```sh
pip install .
```

For development purposes, you may want to use an editable install to have changes to Python scripts reflect automatically in the environment:
```sh
pip install -e .
# when the C++ extension is modified, rerun the command to rebuild
# or, you can use the (technically deprecated) method of manually running the setup script:
python3 setup.py build_ext --inplace
# to clean the python build files:
python3 setup.py clean --all
```

However, most versions of `pip` cannot account for external extension packages and will break if attempting to do an editable install alone. There are two fixes for this to get extensions to load correctly using an editable install:
1. Treat the `libcgillespy3d` as an external package by manually configuring it onto your `PYTHONPATH`
```sh
# manual
export PYTHONPATH=$PYTHONPATH:$PWD/libcGillesPy3D/lib
# using conda
conda develop libcGillesPy3D/lib
```
2. Use the [PEP 517](https://peps.python.org/pep-0517/) install method (which will be standard in `pip` at some point in the future):
```sh
pip install -e . --use-pep517 # rerun to rebuild the extension
```
3. Add the extension build directory as a user site package:
```sh
mkdir -p $(python3 -m site --user-site) && echo "$PWD/libcGillesPy3D/lib" > "$(python3 -m site --user-site)/libcgillespy3d.pth"
```

Examples:

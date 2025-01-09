# Building from Source
The core C++ library, `libcgillespy3d`, can be found in the `libcGillesPy3D/` directory. It is built using a custom [SCons](https://scons.org/documentation.html) build.

## Building the Core C++ Library
From the root-level directory, ensure that SCons is installed and run the following command:

```sh
scons -C libcGillesPy3D/
```

If you have SCons installed, but it is not found you can use it as a python module with the following command: `python3 -m SCons -C libcGillesPy3D`

The build output is placed in the `libcGillesPy3D/lib` directory, which includes any static libraries required by dependencies, as well as a SWIG-generated `libcgillespy3d` package and a to-be-compiled C++ wrapper file, `libcGillesPy3D/obj/include/libcgillespy3d_wrap.cpp`.

## Configuring the SCons Build

The core C++ library's build exposes the following options:

| Flag        | Example                                                          | Description                                           |
| ----------- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| `CC`        | `scons -C libcGillesPy3D/ CC=clang`                              | Configures the chosen C compiler                      |
| `CFLAGS`    | `scons -C libcGillesPy3D/ CFLAGS='-g'`                           | Configures what C compiler flags to pass to `CC`      |
| `CXX`       | `scons -C libcGillesPy3D/ CXX=clang++`                           | Configures the chosen C++ compiler                    |
| `CXXFLAGS`  | `scons -C libcGillesPy3D/ CXXFLAGS='-g'`                         | Configures what C++ compiler flags to pass to `CXX`   |
| `LD`        | `scons -C libcGillesPy3D/ LD='lld'`                              | Configures the chosen linker                          |
| `PYTHONINC` | `scons -C libcGillesPy3D/ PYTHONINC=/usr/lib/include/python3.12/ | Configures the Python development header include path |

If not explicitly provided, all of these options will be inferred automatically by SCons.

## Building the Python Extension
Before building the Python extension, you must first [build the core C++ library](#building-the-core-c-library). The extension will be built as part of the Python build step.

A complete build command would be:

```sh
scons -C libcGillesPy3D/ && python3 -m build --wheel
```

You can install the library from source using `pip`:

```sh
scons -C libcGillesPy3D/ && pip install .
```

If you run into issues due to a Python version mismatch between SCons and `pip` (e.g. SCons is using Python 3.11 and `pip` is using Python 3.12), consider running both as a module of the same Python executable, for example:

```sh
python3 -m SCons -C libcGillesPy3D/ && python3 -m pip install .
```

If all else fails, use the [build configuration options](#configuring-the-scons-build) to manually specify failing options.

## Building for Development

For development purposes, you may want to use an editable install to have changes to Python scripts reflect automatically in the environment:

```sh
pip install -e .
```

This will install the Python scripts and allow changes to Python files to be reflected automatically. Our C++ extension needs to be configured separately.

### Adding the C++ Extension to Your Development Environment

There are a few options to safely add the C++ extension to your environment, so that rebuilding your extension and testing changes can be done easily.

1. Treat the `libcgillespy3d` as an external package by manually configuring it onto your `PYTHONPATH`, for example:
   ```sh
   # manual
   export PYTHONPATH=$PYTHONPATH:$PWD/libcGillesPy3D/lib
   # using conda
   conda develop libcGillesPy3D/lib
   ```
   Using this method, you won't need to rerun `pip install` again to see changes to your extension code.

2. Use the [PEP 517](https://peps.python.org/pep-0517/) install method (which will be standard in `pip` at some point in the future):
   ```sh
   pip install -e . --use-pep517 # rerun to rebuild the extension
   ```
   You'll need to rerun this command to see changes to your extension code.

3. Add the extension build directory as a user site package:
   ```sh
   mkdir -p $(python3 -m site --user-site) && echo "$PWD/libcGillesPy3D/lib" > "$(python3 -m site --user-site)/libcgillespy3d.pth"
   ```

### Developing Without Pip

If you're not using a `pip` editable install, you'll need to make sure that both the root-level project directory and the C++ build output directory at `libcGillesPy3D/lib` are on your `PYTHONPATH`. This ensures that `gillespy3d` and `libcgillespy3d` are both available:

```sh
export PYTHONPATH=$PYTHONPATH:$PWD:$PWD/libcGillesPy3D/lib
```

You can run the Python extension build without `pip` by invoking the setup script directly (technically it's discouraged by Python, but it's allowed):

```sh
python3 setup.py build_ext --inplace
```

This command compiles the Python extension and adds it to the `libcgillespy3d` package, in-place. As you make changes to your C++ extension, you can see those changes immediately by re-running SCons and `setup.py`:
```sh
scons -C libcGillesPy3D/ && python3 setup.py build_ext --inplace
```

You can test that the C++ extension is configured correctly by importing the C++ library from Python:

```python
from libcgillespy3d import libcgillespy3d
print(libcgillespy3d.__path__)
```

Examples:

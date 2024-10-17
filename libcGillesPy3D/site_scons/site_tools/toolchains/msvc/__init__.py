from SCons.Tool import msvc
from SCons.Util import CLVar

def exists(env):
    return "msvc" in env["TOOLS"] and msvc.exists(env)

def generate(env):
    env.Append(CXXFLAGS=CLVar(["$TOOLCHAIN_WIN32_CXXFLAGS", "/std:c++$TOOLCHAIN_CXX_STANDARD"]))

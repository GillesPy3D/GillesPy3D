from SCons.Tool import msvc
from SCons.Util import CLVar

def exists(env):
    return "msvc" in env["TOOLS"] and msvc.exists(env)

def generate(env):
    if "TOOLCHAIN_CXX_STANDARD" in env:
        env.Append(CXXFLAGS=CLVar("/std:c++17"))
    env.Append(CXXFLAGS=["$TOOLCHAIN_WIN32_CXXFLAGS"])

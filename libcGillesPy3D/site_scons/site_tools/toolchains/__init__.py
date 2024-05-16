from . import default, msvc
import os

def options(opts):
    opts.Add("CC")
    opts.Add("CFLAGS")
    opts.Add("CXX")
    opts.Add("CXXFLAGS")
    opts.Add("LD")

def exists(env):
    return default.exists(env) or msvc.exists(env)

def generate(env):
    if msvc.exists(env):
        msvc.generate(env)
        env.Append(TOOLCHAINDIR=os.path.dirname(msvc.__file__))
    else:
        default.generate(env)
        env.Append(TOOLCHAINDIR=os.path.dirname(default.__file__))

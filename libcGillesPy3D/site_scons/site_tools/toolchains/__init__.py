from . import default, msvc

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
    else:
        default.generate(env)

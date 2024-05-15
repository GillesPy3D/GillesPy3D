from . import default, msvc

def exists(env):
    return default.exists(env) or msvc.exists(env)

def generate(env):
    if msvc.exists(env):
        msvc.generate(env)
    else:
        default.generate(env)

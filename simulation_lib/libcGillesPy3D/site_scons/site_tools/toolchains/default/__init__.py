from SCons.Util import CLVar

def exists(env):
    return True

def generate(env):
    env.Append(CXXFLAGS=CLVar("-std=c++$TOOLCHAIN_CXX_STANDARD"))

from gillespy3d import *
from libcgillespy3d import CPropensityFunction, ModelContext, Simulation
import ctypes
import numba

model = Model()
kx, ky = Parameter("kx", 1.5), Parameter("ky", 2.1)
model.add_parameter(kx)
model.add_parameter(ky)
X, Y = Species("X", 100.0), Species("Y", 0.0)
model.add_species(X)
model.add_species(Y)
Rx, Ry = Reaction("Rx", reactants={X: 1}, products={Y: 1}, propensity_function="kx * X * Y"), \
         Reaction("Ry", reactants={Y: 1}, products={X: 1}, propensity_function="ky * X * Y")
model.add_reaction(Rx)
model.add_reaction(Ry)


# dynamically link propensities (not portable, due to POSIX and Windows both deviating from the C standard)
ctx = ModelContext(model)
Rx_id, Ry_id = ctx.reactions().get_reaction_id(Rx), ctx.reactions().get_reaction_id(Ry)

libpropensities = ctypes.cdll.LoadLibrary("./libpropensities.so")
propensity = ctypes.cast(getattr(libpropensities, "propensity"), ctypes.c_void_p)
pfn = CPropensityFunction(propensity.value)
ctx.reactions().set_propensity_function(Rx_id, pfn)
ctx.reactions().set_propensity_function(Ry_id, pfn)
Simulation(ctx)

# use Numba to JIT-compile propensity
jit_ctx = ModelContext(model)
Rx_id, Ry_id = jit_ctx.reactions().get_reaction_id(Rx), jit_ctx.reactions().get_reaction_id(Ry)

cdef = numba.types.double(
    numba.types.CPointer(numba.types.double),
    numba.types.CPointer(numba.types.double),
)

@numba.cfunc(cdef)
def jit_propensity(state, parameters):
    return (state[0] * state[1] * parameters[0]) + 1


jit_fn = ctypes.cast(jit_propensity.ctypes, ctypes.c_void_p)
jit_pfn = CPropensityFunction(jit_fn.value)
jit_ctx.reactions().set_propensity_function(Rx_id, jit_pfn)
jit_ctx.reactions().set_propensity_function(Ry_id, jit_pfn)
Simulation(jit_ctx)

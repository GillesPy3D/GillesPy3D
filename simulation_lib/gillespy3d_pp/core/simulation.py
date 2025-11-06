# GillesPy3D is a Python 3 package for simulation of
# spatial/non-spatial deterministic/stochastic reaction-diffusion-advection problems
# Copyright (C) 2023 GillesPy3D developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU GENERAL PUBLIC LICENSE Version 3 as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU GENERAL PUBLIC LICENSE Version 3 for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#from numba import jit
import inspect
from gillespy3d_pp.core.solvers.NumPySSASolver import NumPySSASolver

class Simulation():
    """
    A simulation in this class follows the stochastic simulation algorithim.


    :param  model: the model in which is invoked to run a simulation
    :type model: model

    :param mode: The compiler type, i.e jit is just in time, for compiling into machine code at runtime
    :type mode: str
    global vars: t : time... sum: sum of current simulation run
    """

    def __init__(self, model, solver):
        
        self.model = model
        self.solver = solver
        if isinstance(solver,str):
            print("str")
        elif inspect.isclass(solver):
            print("class")
        else:
            raise TypeError(f"Argument two must be either a valid string or a solver class")

    def testStuffs(self):
        print(self.model.parameters[1].__str__())

    def reset(self):
        #reset for each new run
        #grab sum and set to 0?
        #set .t to 0
        self.t =0 
        self.sum =0

    def run_until(self):
        if self.solver == NumPySSASolver():
            self.run_SSA();
        return None
    def run_SSA(self):




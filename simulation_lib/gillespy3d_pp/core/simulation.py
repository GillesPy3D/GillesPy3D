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

import inspect
from gillespy3d_pp.core.solvers.NumPySSASolver import NumPySSASolver
from gillespy3d_pp.core.error import SimulationError


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

    def run_until(self, time):
        if self.solver == NumPySSASolver():
            self.solver.NumPySSASolver.reset()
            self.solver.NumPySSASolver.run_until()

    def get_species(self,name):
        """
        Returns a species object by name.

        :param name: Name of the species object to be returned.
        :type name: str

        :returns: The specified species object.
        :rtype: gillespy2.Species

        :raises ModelError: If the species is not part of the model.
        """
        found = False
        index = 0
        for spec in self.model.species:
            if name in spec.name:
                found = True
                break
            index += 1
        if found == False:
            raise SimulationError(f"{self.model.name} does not contain a species named {name}.")
        return self.model.species[index]






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

from gillespy3d_pp.solvers.NumPySSASolver import NumPySSASolver
from gillespy3d_pp.core.error import SimulationError
import numpy as np


class Simulation():
    """
    A simulation in this class follows the stochastic simulation algorithim.


    :param  model: the model in which is invoked to run a simulation
    :type model: model

    :param mode: The compiler type, i.e jit is just in time, for compiling into machine code at runtime
    :type mode: str
    global vars: t : time... sum: sum of current simulation run
    """

    def __init__(self, model, solver, num_traj, dt=.1, end_t=10):

        self.model = model
        self.dt = dt
        self.end_t = end_t
        self.num_traj = num_traj
        self.solver = solver
        if solver == "SSA":
            self.solver = NumPySSASolver(self.model)
        # elif inspect.isclass(solver):
        #    print("class")
        # else:
         #   raise TypeError(f"Argument two must be either a valid string or a solver class")

    def reset(self):
        self.solver.reset()

    def get_time(self):
        return self.solver.get_time()

    def run(self):
        simulation_data = []
        timeline = np.linspace(0, self.end_t, int(
            round(self.end_t / self.dt + 1)))
        trajecties = np.zeros(
            (timeline.size, len(self.model.listOfSpecies) + 1))
        for traj in range(self.num_traj):
            self.reset()  # reset the simulation after each run
            while self.get_time() < self.end_t:
                # make f string
               # print('traj', traj, ' t:', self.get_time(),
               #       ' Substrate:', self.get_species('Substrate'))
                self.run_until(self.get_time()+self.dt,
                               simulation_data, timeline, trajecties)

    def run_until(self, end_t, simulation_data, timeline, trajecties):
        self.solver.run_until(end_t, simulation_data, timeline, trajecties)

    def get_species(self, species):
        """

        :param name: Name of the species object to be returned.
        :type name: str

        :returns: The specified species value
        :rtype: gillespy2.Species
        """
        return self.solver.get_species(species)

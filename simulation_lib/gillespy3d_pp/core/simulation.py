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
from gillespy3d_pp.core.result import Result, Trajectory
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

    def __init__(self,  model, number_of_trajectories, dt, end_t, solver=None):

        self.model = model
        self.dt = dt
        self.end_t = end_t
        self.number_of_trajectories = number_of_trajectories
        if not solver or solver == "SSA":
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
        # print("dt is ", self.dt)
        # print("end_t is ", self.end_t)

        # make if to check for timespan or use generator
        timeline = np.linspace(0, self.end_t, int(
            round(self.end_t / self.dt + 1)))
        species_names = list(self.model.listOfSpecies.keys())
        result = Result(simulation_data)
        for traj in range(self.number_of_trajectories):
            self.reset()  # reset the simulation after each run
            trajectory = Trajectory(
                len(species_names), len(timeline), species_names, timeline)
            # print(self.solver.get_curr_state())
            trajectory.record_state(self.solver.get_curr_state())
            # print("made it past the inital")
            for t in timeline[1:]:
                self.run_until(t)
                print("recording ", t)
                trajectory.record_state(self.solver.get_curr_state())
                print("state ", self.solver.get_curr_state())
            result.add_trajectory(trajectory)
        return result

    def run_until(self, end_t):
        self.solver.run_until(end_t)

    def get_species(self, species):
        """

        :param name: Name of the species object to be returned.
        :type name: str

        :returns: The specified species value
        :rtype: gillespy2.Species
        """
        return self.solver.get_species(species)

    def get_product(self, product):
        return self.solver.get_product(product)

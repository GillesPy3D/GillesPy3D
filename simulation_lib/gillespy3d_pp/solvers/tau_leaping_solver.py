# GillesPy3D is a Python 3 package for simulation of
# spatial/non-spatial deterministic/stochastic reaction-diffusion-advection problems
# Copyright (C) 2023-2024 GillesPy3D developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU GENERAL PUBLIC LICENSE Version 3 as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU GENERAL PUBLIC LICENSE Version 3 for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This module defines a model that simulates a discrete, stoachastic, mixed biochemical reaction network in python.

"""Class and methods for the Tau Leaping Solver"""
import copy
import random
import math
import numpy as np
from gillespy3d_pp.utils import Tau
from gillespy3d_pp.utils import solverutils as utils
from gillespy3d_pp.core.error import SimulationError


class TauLeapingSolver():
    """
    A Tau Leaping solver for GillesPy3D models.  This solver uses an algorithm that calculates
    multiple reactions in a single step over a given tau step size.  The change in propensities
    over this step are bounded by bounding the relative change in state, yielding greatly improved
    run-time performance with very little trade-off in accuracy.

    """

    name = "TauLeapingSolver"

    def __init__(self, model=None, debug=False, constant_tau_stepsize=None):
        if model is None:
            raise SimulationError("A model is required to run the simulation.")

        name = "TauLeapingSolver"
        if model is None:
            raise SimulationError(
                "A model is requied to run the simulation"
            )
        self.model = copy.deepcopy(model)
        self.debug = debug
        self.is_instantiated = True
        self.constant_tau_stepsize = constant_tau_stepsize

    def __get_reactions(self, step, curr_state, curr_time, save_time, propensities, reactions):
        """
        Helper Function to get reactions fired from t to t+tau.  
        :returns: Three values:
            rxn_count - dict with key=Reaction channel value=number of times fired
            curr_state - dict containing all state variables for system at current time
            curr_time - float representing current time
        """

        if curr_time + step > save_time:
            if self.debug:
                print("Step exceeds save_time, changing step size from ", step,
                      " to ", save_time - curr_time)
            step = save_time - curr_time

        if self.debug:
            print("Curr Time: ", curr_time, " Save time: ",
                  save_time, "step: ", step)

        rxn_count = {}

        for rxn in reactions:
            rxn_count[rxn] = np.random.poisson(propensities[rxn] * step)

        if self.debug:
            print("Reactions Fired: ", rxn_count)

        curr_time = curr_time+step

        return rxn_count, curr_state, curr_time

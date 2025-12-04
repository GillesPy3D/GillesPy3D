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

#This module defines a model that simulates a discrete, stoachastic, mixed biochemical reaction network in python.

import copy
import random
import math
import numpy as np
from gillespy3d_pp.core.error import NumPySSASolverError

class NumPySSASolver():
    name = "NumPySSASolver"
    result = None


    def reset(self):
        self.curr_time = 0
        self.curr_state = {}
        for spec in self.model.species:
            self.curr_state[spec] = spec.initial_value

    def get_species(self,species):
        """
         return population
        """
        return self.curr_state[species]

    def __init__(self,model=None):
        if model is None:
            raise NumPySSASolverError("A model is required to run the simulation.")
        self.model = copy.deepcopy(model)
        self.species = self.model.species
        self.reactions = list(self.model.reactions)
        self.number_reactions = len(self.reactions)
        self.dependent_rxns = {}
        self.is_instantiated = True
        self.number_species = len(self.model.species)
        self.species_changes = np.zeros((self.number_reactions,self.number_species))
        self.propensity_functions = {}
        self.volume = getattr(self.model, "volume", 1.0)
        self.parameters = {'V': self.volume}
        self.species_mappings  = self.model._sanitized_species_names()
        self.parameter_mappings = self.model._sanitized_parameter_names()
        for i, reaction in enumerate(self.reactions):
            for j, spec in enumerate(self.species):
                self.species_changes[i][j] = self.model.reactions[reaction].products.get(self.model.species[spec], 0) \
                                        - self.model.reactions[reaction].reactants.get(self.model.species[spec], 0)

            self.propensity_functions[reaction] = [eval('lambda S:' + self.model.listOfReactions[reaction].
                                                   sanitized_propensity_function(self.species_mappings, self.parameter_mappings),
                                                   self.parameters), i]

    def get_time(self):
        return self.curr_time

    def run_until(self,stop_time): 


        propensity_values = np.zeros(self.number_reactions)

        while self.curr_time < stop_time:
            #if past stop time, dont update
            species_states = list(self.curr_state.values())
            for i in range(self.number_reactions):
                propensity_values[i] = self.propensity_functions[self.reactions[i]][0](species_states)

            propensity_sum = np.sum(propensity_values)
            if propensity_sum <= 0:
                break
            cumulative_sum = random.uniform(0,propensity_sum)
            rand = random.random()

            tau = -math.log(rand) / propensity_sum
            if self.curr_time + tau > stop_time:
                self.curr_time = stop_time
                return
            else:
                self.curr_time += tau
            for potential_reaction in range(self.number_reactions):
                cumulative_sum -= propensity_sum[potential_reaction]
                if cumulative_sum <= 0:
                    for i, spec in enumerate(self.model.species):
                        self.curr_state[spec] += self.species_changes[potential_reaction][i]

                        reacName = self.reactions[potential_reaction]
                        species_states = list(self.curr_state.values())
                        for i in self.dependent_rxns[reacName]['dependencies']:
                            propensity_sum[self.propensity_functions[i][1]] = self.propensity_functions[i][0](species_states)

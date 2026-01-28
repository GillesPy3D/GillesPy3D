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
from gillespy3d_pp.utils import solverutils as nputils

class NumPySSASolver():
    name = "NumPySSASolver"
    result = None


    def reset(self):
        self.curr_time = 0
        self.curr_state = {}
        for s, spec in self.model.listOfSpecies.items():
            self.curr_state[s] = spec.initial_value

    def get_species(self,species):
        """
         return population
        """
        return self.curr_state[species]

    def __init__(self,model=None):
        if model is None:
            raise NumPySSASolverError("A model is required to run the simulation.")
        self.model = copy.deepcopy(model)
        self.species, self.species_mappings, self.number_species = nputils.numpy_initialization(self.model)
        self.reactions = list(self.model.listOfReactions.keys())
        self.number_reactions = len(self.reactions)
        self.dependent_rxns = nputils.dependency_grapher(self.model, self.reactions)
        self.is_instantiated = True
        self.number_species = len(self.model.listOfSpecies)
        self.species_changes = np.zeros((self.number_reactions,self.number_species))
        self.propensity_functions = {}
        self.volume = getattr(self.model, "volume", 1.0)
        self.parameter_values = {}
        for name, param in self.model.listOfParameters.items():
            self.parameter_values[name] = float(param.expression)
        self.parameter_values['vol'] = float(self.volume)
        self.propensity_func_name_map = {}
        self.species_mappings  = self.model._sanitized_species_names()#solver utils
        for i, r_name  in enumerate(self.reactions):
            for j,(s_name, _) in enumerate(self.species.items()):
                self.species_changes[i][j] = self.model.listOfReactions[r_name].products.get(self.model.listOfSpecies[s_name], 0) \
                                        - self.model.listOfReactions[r_name].reactants.get(self.model.listOfSpecies[s_name], 0)

            self.propensity_functions[r_name] = eval('lambda S:' + self.model.listOfReactions[r_name].
                                                 sanitized_propensity_function(self.species_mappings, self.parameter_values),
                                                     )
               # sanitized = self.model.listOfReactions[r_name].sanitized_propensity_function(
               #     self.species_mappings, self.parameter_values
               # )
               # print("FINAL LAMBDA:", sanitized)
               # raise


           # print(self.species_mappings," specs and params ",self.parameter_mappings)
           # print('lambda S:' + self.model.listOfReactions[r_name].
           #                                        sanitized_propensity_function(self.species_mappings, self.parameter_mappings))

           # print("after sant ",self.species_mappings," specs and params ",self.parameter_mappings)
           # print(self.parameters)
            #look at original, to find P0, S and V to update them to correct information
           # raise 
            self.propensity_func_name_map[r_name] = i
        #print("everything initalized")
        #print("props is ",self.propensity_functions)

    def get_time(self):
        return self.curr_time

    def run_until(self,stop_time): 


        propensity_values = np.zeros(self.number_reactions)

        while self.curr_time < stop_time:
            species_states = list(self.curr_state.values())
           # print("species state in full: ",list(self.curr_state.values()))
            # line below breaks due to no [0] exisiting, pending removal on curr_state finalization
            for i, r_name  in enumerate(self.reactions):
                propensity_values[i] = self.propensity_functions[r_name](species_states)
              #  print("propensity function of ",i," ",self.propensity_functions[r_name](species_states))
              #  print("and now for ", propensity_values)

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
              #  print("cumu sum ", cumulative_sum)
              #  print("prop sum ",propensity_sum)
                cumulative_sum -= propensity_values[potential_reaction]
                if cumulative_sum <= 0:
                   # print("species is ",self.species)
                    for i, spec in enumerate(self.species):
                        self.curr_state[spec] += self.species_changes[potential_reaction][i]

                        reacName = self.reactions[potential_reaction]
                        species_states = list(self.curr_state.values())
                        # what is i, is i r_name
                        # make propensity_index, dict, take 'r1' as name and ret 0, change name back to index
                        # make propensity_func_name_map to use here, 
                        for dep_rxn_name in self.dependent_rxns[reacName]['dependencies']:
                            #code is wrong, fix propensity functions[][]
                            propensity_values[self.propensity_func_name_map[dep_rxn_name]] = self.propensity_functions[dep_rxn_name](species_states)

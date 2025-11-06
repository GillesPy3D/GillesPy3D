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


    def __init__(self,model=None):
        if model is None:
            raise NumPySSASolverError("A model is required to run the simulation.")
        self.model = model.deepcopy(model)
        stop_event = None
        rc =0
        result = None
        pause_event = 0
        self.is_instantiated = True
    def trac_base (self,trac_base):
        for i, s in enumerate(self.model.species):
            trac_base[:, 0, i+1] = self.model.species[s].initial_value
        return trac_base
    def run_until(self, curr_state, total_time, t, number_of_trajectories=1, increment = None):
        timeStopped = 0 
        #resume parameter??
        #create time_line
        timeline = np.linspace(0, t, int(round(t / increment + 1)))
        reactions = list(self.model.reactions)
        number_reactions = len(reactions)
        species = self.model.species
        number_species = len(self.model.species)
        propensity_functions = {}
        species_changes = np.zeros((number_reactions,number_species))

        for i, reaction in enumerate(reactions):
            for j, spec in enumerate(species):
                species_changes[i][j] = self.model.reactions[reaction].products.get(self.model.species[spec], 0) \
                                        - self.model.reactions[reaction].reactants.get(self.model.species[spec], 0)

        trajectory_base = np.zeros((number_of_trajectories, timeline.size, len(species) + 1))
        tmpSpecies = {}
        trajectory_base = self.trac_base(trajectory_base)
        simulation_data = []
        for trajectory_num in range(number_of_trajectories):
            trajectory = trajectory_base
        # for futre possible threading? 
       # for trajectory in range(number_of_tracjectories):
       #     if self.stop_event.is_set():
       #         self.rc = 33
       #         break

            propensity_sums = np.zeros(number_reactions)
            curr_state[0] = {}
            curr_time = [0]
            total_time = [0]
            entry_count = 1
            for spec in self.model.species:
                curr_state[0][spec] = spec.initial_value


            while entry_count < timeline.size:
                #code for stop event and pause event can go here
                species_states = list(curr_state[0].values())
                for i in range(number_reactions):
                    propensity_sums[i] = propensity_functions[reactions[i]][0](species_states)

                propensity_sum = np.sum(propensity_sums)
                #no more reacition ? quit
                if propensity_sum <= 0:
                    break
                cumulative_sum = random.uniform(0,propensity_sum)
                rand = random.random()
                curr_time [0] += -math.log(rand) / propensity_sum
                total_time[0] += -math.log(rand) / propensity_sum
                #determine time passed in this reaction

                while entry_count < timeline.size and timeline[entry_count] <= curr_time[0]:
                    trajectory_base[entry_count, 1:] = species_states
                    entry_count +=1
            
                for potential_reaction in range(number_reactions):
                    cumulative_sum -= propensity_sums[potential_reaction]
                    if cumulative_sum <= 0:
                        for i, spec in enumerate(self.model.species):
                            curr_state[0][spec] += species_changes[potential_reaction][i]

                            reacName = reactions[potential_reaction]
                            species_states = list(curr_state[0].values())
                            #dependant_rxns could go here in future
            data = {
                'time': timeline
            }
            for i in range(number_species):
                data[species[i]] = trajectory[:, i +1]
            simulation_data.append(data)

        # if timeStopped != 0:
        # for when resume is implemented to allow pausing
        self.result = simulation_data
        return self.result #rc add here later







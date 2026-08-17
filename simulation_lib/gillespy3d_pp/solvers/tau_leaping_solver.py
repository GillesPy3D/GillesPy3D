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
from gillespy3d_pp.utils import solverutils as nputils
from gillespy3d_pp.core.error import SimulationError, SolverError


class TauLeapingSolver():
    """
    A Tau Leaping solver for GillesPy3D models.  This solver uses an algorithm that calculates
    multiple reactions in a single step over a given tau step size.  The change in propensities
    over this step are bounded by bounding the relative change in state, yielding greatly improved
    run-time performance with very little trade-off in accuracy.

    """

    name = "TauLeapingSolver"

    def __init__(self, model=None, debug=False, constant_tau_stepsize=None, epsilon=0.03, ssa_fallback=False):

        name = "TauLeapingSolver"
        if model is None:
            raise SimulationError(
                "A model is requied to run the simulation"
            )
        self.model = copy.deepcopy(model)
        self.debug = debug
        self.is_instantiated = True
        self.constant_tau_stepsize = constant_tau_stepsize
        self.epsilon = epsilon
        self.ssa_fallback = ssa_fallback
        self.last_rxn_count = {}
        self.species, self.species_mappings, self.number_species = nputils.numpy_initialization(
            self.model)
        self.reactions = list(self.model.listOfReactions.keys())
        self.number_reactions = len(self.reactions)
        self.dependent_rxns = nputils.dependency_grapher(
            self.model, self.reactions)
        self.is_instantiated = True
        self.number_species = len(self.model.listOfSpecies)
        self.species_changes = np.zeros(
            (self.number_reactions, self.number_species))
        self.propensity_functions = {}
        self.volume = getattr(self.model, "volume", 1.0)
        self.parameter_values = {}
        for name, param in self.model.listOfParameters.items():
            self.parameter_values[name] = float(param.expression)
        self.parameter_values['vol'] = float(self.volume)
        self._tau_samples = []
        self.propensity_func_name_map = {}
        self.species_mappings = self.model._sanitized_species_names()  # solver utils
        for i, r_name in enumerate(self.reactions):
            for j, (s_name, _) in enumerate(self.species.items()):
                self.species_changes[i][j] = self.model.listOfReactions[r_name].products.get(s_name, 0) \
                    - self.model.listOfReactions[r_name].reactants.get(s_name, 0)
            self.propensity_functions[r_name] = eval('lambda S:' + self.model.listOfReactions[r_name].
                                                     sanitized_propensity_function(
                                                         self.species_mappings, self.parameter_values),
                                                     )
            self.propensity_func_name_map[r_name] = i
        self.reset()

    def reset(self):
        self.curr_time = 0
        self.curr_state = {}
        for species_name, spec in self.model.listOfSpecies.items():
            self.curr_state[species_name] = spec.initial_value
        self.last_rxn_count = {}

    def get_time(self):
        return self.curr_time

    def get_curr_state(self):
        return self.curr_state

    def get_species(self, species_name):
        """
         return population
        """
        return self.curr_state[species_name]

    def get_product(self, product):
        return self.curr_state[product]

    def get_tau_stepsize(self):
        return self.constant_tau_stepsize

    def get_last_rxn_count(self):
        return self.last_rxn_count

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
        self.last_rxn_count = rxn_count

        return rxn_count, curr_state, curr_time

    def run_until(self, stop_time):
        propensity_values = np.zeros(self.number_reactions)
        propensities = {}

        while self.curr_time < stop_time:
            species_states = list(self.curr_state.values())
            for i, r_name in enumerate(self.reactions):
                propensity_values[i] = self.propensity_functions[r_name](
                    species_states)
                propensities[r_name] = propensity_values[i]

            if np.any(propensity_values < 0):
                raise SolverError("Negative propensity detected")

            propensity_sum = float(np.sum(propensity_values))
            if propensity_sum <= 0:
                self.curr_time = stop_time
                return

            if self.constant_tau_stepsize is not None:
                tau_step = self.constant_tau_stepsize
                if self.curr_time + tau_step > stop_time:
                    tau_step = stop_time - self.curr_time
            else:
                HOR, reactants, mu_i, sigma_i, g_i, epsilon_i, critical_threshold = \
                    Tau.initialize(self.model, self.epsilon)
                tau_step = Tau.select(
                    HOR, reactants, mu_i, sigma_i, g_i, epsilon_i,
                    self.epsilon, critical_threshold, self.model,
                    propensities, self.curr_state, self.curr_time, stop_time,
                )

            if tau_step <= 0:
                raise SolverError("Non-positive tau selected")

            if self.ssa_fallback and tau_step < 10.0 / propensity_sum:
                self._ssa_fallback(propensity_values, propensities, stop_time)
                continue

            attempt_tau = tau_step
            while True:
                rxn_count, _, _ = self.__get_reactions(
                    attempt_tau, self.curr_state, self.curr_time, stop_time,
                    propensities, self.reactions,
                )
                trial_state = dict(self.curr_state)
                negative = False
                for i, r_name in enumerate(self.reactions):
                    n_fires = rxn_count[r_name]
                    if n_fires == 0:
                        continue
                    for j, s_name in enumerate(self.species):
                        trial_state[s_name] += n_fires * \
                            self.species_changes[i][j]
                        if trial_state[s_name] < 0:
                            negative = True
                            break
                    if negative:
                        break

                if not negative:
                    break

                attempt_tau /= 2.0
                if attempt_tau < 1e-12:
                    raise SolverError(
                        "Tau halving failed to avoid negative populations")

            self._tau_samples.append(attempt_tau)
            self.curr_state = trial_state
            self.curr_time += attempt_tau
            self.last_rxn_count = rxn_count

            if self.curr_time >= stop_time:
                self.curr_time = stop_time
                return

    def _ssa_fallback(self, propensity_values, propensities, stop_time, n_steps=100):
        """Run a handful of exact SSA steps; used when adaptive tau is too small to leap efficiently."""
        for _ in range(n_steps):
            if self.curr_time >= stop_time:
                return
            propensity_sum = float(np.sum(propensity_values))
            if propensity_sum <= 0:
                self.curr_time = stop_time
                return

            rand = random.random()
            if rand <= 0.0:
                rand = 1e-300
            tau = -math.log(rand) / propensity_sum
            if self.curr_time + tau > stop_time:
                self.curr_time = stop_time
                return

            target = random.uniform(0, propensity_sum)
            cumulative = 0.0
            chosen = self.number_reactions - 1
            for i in range(self.number_reactions):
                cumulative += propensity_values[i]
                if cumulative >= target:
                    chosen = i
                    break

            for j, s_name in enumerate(self.species):
                self.curr_state[s_name] += self.species_changes[chosen][j]
                if self.curr_state[s_name] < 0:
                    raise SolverError(f"Negative species count for {s_name}")

            self.curr_time += tau
            self._tau_samples.append(tau)
            chosen_name = self.reactions[chosen]
            self.last_rxn_count = {chosen_name: 1}

            species_states = list(self.curr_state.values())
            for dep_rxn_name in self.dependent_rxns[chosen_name]['dependencies']:
                idx = self.propensity_func_name_map[dep_rxn_name]
                propensity_values[idx] = self.propensity_functions[dep_rxn_name](
                    species_states)
                propensities[dep_rxn_name] = propensity_values[idx]

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

import copy
from collections import OrderedDict
from scipy.integrate import ode
from gillespy3d_pp.core.error import SimulationError, SolverError


class ODESolver():
    """
    This solver produces the deterministic continuous solution via Ordinary Differential Equations.
    Uses integrators from scipy.integrate.ode to perform calculations used to produce solutions.

    ODE is deterministic, so a single integration is the definitive result. Under the hood the
    scipy integrator advances continuously; the per-timepoint ``get_curr_state`` interface simply
    samples that continuous solution onto the timeline, letting this solver be driven by
    :class:`~gillespy3d_pp.core.simulation.Simulation` just like the stochastic solvers.

    :param model: The model on which the solver will operate.
    :type model: gillespy2.Model
    """
    name = "ODESolver"

    def __init__(self, model=None, integrator='lsoda', integrator_options=None):
        if model is None:
            raise SimulationError("A model is required to run the simulation.")

        self.model = copy.deepcopy(model)
        self.integrator = integrator
        self.integrator_options = integrator_options or {}
        self.is_instantiated = True

        self.species_names = list(self.model.listOfSpecies.keys())
        self.c_prop = OrderedDict()
        for r_name, reaction in self.model.listOfReactions.items():
            self.c_prop[r_name] = compile(
                reaction.ode_propensity_function, '<string>', 'eval')

        # Constant portion of the eval namespace: parameters and volume.
        self.base_state = OrderedDict()
        for p_name, param in self.model.listOfParameters.items():
            self.base_state[p_name] = float(param.expression)
        if 'vol' not in self.base_state:
            self.base_state['vol'] = float(getattr(self.model, "volume", 1.0))

        self.reset()

    def reset(self):
        self.curr_time = 0.0
        self.curr_state = OrderedDict()
        y0 = [0.0] * len(self.species_names)
        for i, (s_name, spec) in enumerate(self.model.listOfSpecies.items()):
            self.curr_state[s_name] = spec.initial_value
            y0[i] = spec.initial_value

        self._integrator = ode(self._rhs).set_integrator(
            self.integrator, **self.integrator_options)
        self._integrator.set_initial_value(y0, self.curr_time)

    def _rhs(self, t, y):
        """
        The right hand side of the system of differential equations: the time
        derivative of each species population given the current state.

        :param t: current integration time
        :param y: species populations, ordered as ``self.species_names``
        :returns: list of dy/dt for each species
        """
        eval_state = dict(self.base_state)
        eval_state['t'] = t
        for i, s_name in enumerate(self.species_names):
            eval_state[s_name] = y[i]

        state_change = OrderedDict((s_name, 0.0)
                                   for s_name in self.species_names)
        for r_name, reaction in self.model.listOfReactions.items():
            propensity = eval(self.c_prop[r_name], eval_state)
            for react, stoich in reaction.reactants.items():
                state_change[react] -= propensity * stoich
            for prod, stoich in reaction.products.items():
                state_change[prod] += propensity * stoich
        return list(state_change.values())

    def run_until(self, stop_time):
        if stop_time <= self.curr_time:
            return

        y = self._integrator.integrate(stop_time)
        if not self._integrator.successful():
            raise SolverError("ODE integration failed to converge")

        self.curr_time = stop_time
        for i, s_name in enumerate(self.species_names):
            self.curr_state[s_name] = y[i]

    def get_time(self):
        return self.curr_time

    def get_curr_state(self):
        return self.curr_state

    def get_species(self, species_name):
        return self.curr_state[species_name]

    def get_product(self, product):
        return self.curr_state[product]

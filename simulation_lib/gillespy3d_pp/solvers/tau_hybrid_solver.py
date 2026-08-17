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
import random
import math
import sys
from collections import OrderedDict
from scipy.integrate import ode, LSODA
import heapq
import numpy as np
from gillespy3d_pp.utils import Tau
from gillespy3d_pp.core.raterule import RateRule
from gillespy3d_pp.core.assignmentrule import AssignmentRule
from gillespy3d_pp.core.functiondefinition import FunctionDefinition
from gillespy3d_pp.core.error import ModelError, SimulationError, SolverError

eval_globals = math.__dict__


def __piecewise(*args):
    # Eval entry for piecewise functions
    args = list(args)
    solution = None
    if len(args) % 2:
        args.append(True)
    for i, arg in enumerate(args):
        if not i % 2:
            continue
        if arg:
            solution = args[i - 1]
            break
    return solution


def __xor(*args):
    # Eval entry for MathML xor function
    from operator import ixor
    from functools import reduce
    args = list(args)
    return reduce(ixor, args)


eval_globals['false'] = False
eval_globals['true'] = True
eval_globals['piecewise'] = __piecewise
eval_globals['xor'] = __xor


class TauHybridSolver():
    """
    This solver uses a root-finding interpretation of the direct SSA method,
    along with ODE solvers to simulate ODE and Stochastic systems
    interchangeably or simultaneously.
    Uses integrators from scipy.integrate.ode to perform calculations used to produce solutions.

    :param model: The model on which the solver will operate.
    :type model: gillespy2.Model
    """
    name = "TauHybridSolver"

    def __init__(self, model=None, profile_reactions=False, constant_tau_stepsize=None):
        if model is None:
            raise SimulationError("A model is required to run the simulation.")

        name = 'TauHybridSolver'
        self.model = copy.deepcopy(model)
        self.is_instantiated = True
        self.profile_reactions = profile_reactions
        self.profile_data = {}
        if self.profile_reactions:
            self.profile_data['time'] = []
            for k in list(self.model.listOfSpecies)+list(self.model.listOfReactions):
                self.profile_data[k] = []
        self.non_negative_species = set()
        for reaction, _ in model.listOfReactions.items():
            for key, value in model.listOfReactions[reaction].reactants.items():
                self.non_negative_species.add(key)
            for key, value in model.listOfReactions[reaction].products.items():
                self.non_negative_species.add(key)
        self.constant_tau_stepsize = constant_tau_stepsize
        # check if model should skip ODE integration step
        self.pure_discrete = False
        if len(self.model.listOfRateRules) == 0:
            self.pure_discrete = True
            for species in self.model.listOfSpecies:
                if self.model.listOfSpecies[species].mode != 'discrete':
                    self.pure_discrete = False
                    break

    def reset(self):
        self.curr_time = 0.0
        self.curr_state = OrderedDict()
        self.__initialize_state(self.curr_state, debug=False)
        self.det_spec = {s: v.mode != 'discrete' for s,
                         v in self.model.listOfSpecies.items()}
        self.det_rxn = {r: False for r in self.model.listOfReactions}

    def __toggle_reactions(self, all_compiled, deterministic_reactions, dependencies,
                           curr_state, det_spec, rr_sets):
        """
        Helper method which is used to convert reaction channels into
        rate rules, and rate rules into reaction channels, as they are switched
        dynamically throughout the simulation based on user-supplied tolerance.
        """

        # initialize variables
        inactive_reactions = all_compiled['inactive_rxns']
        rate_rules = all_compiled['rules']
        rxns = all_compiled['rxns']

        # If the set has changed, reactivate non-determinsitic reactions
        reactivate = []
        for r in inactive_reactions:
            if not r in deterministic_reactions:
                reactivate.append(r)
        for r in reactivate:
            rxns[r] = inactive_reactions.pop(r, None)

        # Deactivate Determinsitic Reactions
        for r in deterministic_reactions:
            if not r in inactive_reactions:
                inactive_reactions[r] = rxns.pop(r, None)

        # floor non-det species
        for s, d in det_spec.items():
            if not d and isinstance(curr_state[s], float):
                curr_state[s] = round(curr_state[s])

        # Check if this reaction set is already compiled and in use:
        if deterministic_reactions in rr_sets.keys():
            return rr_sets[deterministic_reactions]
        else:
            # Otherwise, this is a new determinstic reaction set that must be compiled
            tmp = self.__create_diff_eqs(deterministic_reactions,
                                         dependencies, rr_sets, rate_rules)
            return tmp

    def __create_diff_eqs(self, comb, dependencies, rr_sets, rate_rules):
        """
        Helper method used to convert stochastic reaction descriptions into
        differential equations, used dynamically throught the simulation.
        """
        diff_eqs = OrderedDict()
        output_rules = copy.deepcopy(rate_rules)

        # Initialize sample dict
        rr_vars = {}
        for n, rr in self.model.listOfRateRules.items():
            rr_vars[rr.variable.name] = n
        for spec in self.model.listOfSpecies:
            if spec in rr_vars.keys():
                diff_eqs[self.model.listOfSpecies[spec]
                         ] = self.model.listOfRateRules[rr_vars[spec]].formula
            else:
                diff_eqs[self.model.listOfSpecies[spec]] = '0'

        # loop through each det reaction and concatenate it's diff eq for each species
        for reaction in comb:
            factor = {dep: 0 for dep in dependencies[reaction]}

            for key, value in self.model.listOfReactions[reaction].reactants.items():
                spec_obj = self.model.listOfSpecies[key]
                if not spec_obj.constant and not spec_obj.boundary_condition:
                    factor[key] -= value
            for key, value in self.model.listOfReactions[reaction].products.items():
                spec_obj = self.model.listOfSpecies[key]
                if not spec_obj.constant and not spec_obj.boundary_condition:
                    factor[key] += value

            for dep in dependencies[reaction]:
                if factor[dep] != 0:
                    if self.model.listOfSpecies[dep].mode == 'continuous':
                        diff_eqs[self.model.listOfSpecies[dep]] += ' + {0}*({1})'.format(factor[dep],
                                                                                         self.model.listOfReactions[reaction].ode_propensity_function)
                    else:
                        diff_eqs[self.model.listOfSpecies[dep]] += ' + {0}*({1})'.format(factor[dep],
                                                                                         self.model.listOfReactions[reaction].propensity_function)

        for spec in self.model.listOfSpecies:
            if diff_eqs[self.model.listOfSpecies[spec]] == '0':
                del diff_eqs[self.model.listOfSpecies[spec]]
        # create a dictionary of compiled gillespy2 rate rules
        for spec, rate in diff_eqs.items():
            output_rules[spec] = compile(gillespy2.RateRule(
                spec, rate).formula, '<string>', 'eval')
        rr_sets[comb] = rate_rules  # save values
        return output_rules

    def __flag_det_reactions(self, det_spec, det_rxn, dependencies):
        """
        Helper method used to flag reactions that can be processed
        deterministically without exceeding the user-supplied tolerance.
        """
        # Determine if each rxn would be deterministic apart from other reactions
        prev_state = det_rxn.copy()
        for rxn in self.model.listOfReactions:
            # assume it is deterministic
            det_rxn[rxn] = True
            # iterate through the dependent species of this reaction
            for species in dependencies[rxn]:
                # if any of the dependencies are discrete or (dynamic AND the
                # species itself has not been flagged as deterministic)
                # then allow it to be modelled discretely
                if self.model.listOfSpecies[species].mode == 'discrete':
                    det_rxn[rxn] = False
                    break
                if self.model.listOfSpecies[species].mode == 'dynamic' and det_spec[species] == False:
                    det_rxn[rxn] = False
                    break

        # Create a hashable frozenset of all determinstic reactions
        deterministic_reactions = set()
        for rxn in det_rxn:
            if det_rxn[rxn]:
                deterministic_reactions.add(rxn)
        deterministic_reactions = frozenset(deterministic_reactions)
        return deterministic_reactions

    def __calculate_statistics(self, curr_time, propensities, curr_state, tau_step, det_spec, cv_history={}):
        """
        Calculates Mean, Standard Deviation, and Coefficient of Variance for each
        dynamic species, then set if species can be represented determistically

        NOTE: the argument cv_history should not be passed in, this is modified by the function
        to keep a persistent data set.
        """
        # move configuration to solver init (issue #905)
        history_length = 12  # cite: "Statistical rules of thumb" G Van Belle

        if curr_time == 0.0:  # re-set cv_history
            for k in list(cv_history.keys()):
                del cv_history[k]

        CV = OrderedDict()
        # calculate CV by estimating the next step
        mn = {species: curr_state[species] for species, value in
              self.model.listOfSpecies.items() if value.mode == 'dynamic'}
        sd = {species: 0 for species, value in
              self.model.listOfSpecies.items() if value.mode == 'dynamic'}

        for r, rxn in self.model.listOfReactions.items():
            for reactant in rxn.reactants:
                if self.model.listOfSpecies[reactant].mode == 'dynamic':
                    mn[reactant] -= (propensities[r] * rxn.reactants[reactant])
                    sd[reactant] += (propensities[r] *
                                     (rxn.reactants[reactant] ** 2))
            for product in rxn.products:
                if self.model.listOfSpecies[product].mode == 'dynamic':
                    mn[product] += (propensities[r] * rxn.products[product])
                    sd[product] += (propensities[r] *
                                    (rxn.products[product] ** 2))
        # Calcuate the derivative based CV
        for species, value in self.model.listOfSpecies.items():
            if value.mode == 'dynamic':
                if mn[species] > 0 and sd[species] > 0:
                    CV[species] = math.sqrt(sd[species]) / mn[species]
                else:
                    # value chosen to guarantee species will be discrete
                    CV[species] = 1

        # Keep a history of the past CV values, calculate a time-averaged value
        CV_a = OrderedDict()  # time-averaged CV (forward derivative based)
        for species, value in self.model.listOfSpecies.items():
            if value.mode == 'dynamic':
                if species not in cv_history:
                    cv_history[species] = []
                cv_history[species].append(CV[species])
                if len(cv_history[species]) > history_length:
                    cv_history[species].pop(0)  # remove the first item
                CV_a[species] = sum(cv_history[species]) / \
                    len(cv_history[species])

        # Select DISCRETE or CONTINOUS mode for each species
        for species in mn:
            prev_det = det_spec[species]
            sref = self.model.listOfSpecies[species]
            if sref.switch_min == 0:
                # Set species to deterministic if CV is less than threshhold
                det_spec[species] = CV_a[species] < sref.switch_tol
            else:
                det_spec[species] = mn[species] > sref.switch_min

        return mn, sd, CV

    @staticmethod
    def __f(t, y, curr_state, species, reactions, rate_rules, propensities,
            y_map, compiled_reactions, active_rr, events, assignment_rules):
        """
        Evaluate the propensities for the reactions and the RHS of the Reactions and RateRules.
        Also evaluates boolean value of event triggers.
        """
        state_change = [0] * len(y_map)
        curr_state['t'] = t
        curr_state['time'] = t
        for item, index in y_map.items():
            if item in assignment_rules:
                curr_state[assignment_rules[item].variable] = eval(assignment_rules[item].formula,
                                                                   {**eval_globals, **curr_state})
            else:
                curr_state[item] = y[index]
        for s, rr in active_rr.items():
            try:
                state_change[y_map[s.name]
                             ] += eval(rr, {**eval_globals, **curr_state})
            except ValueError as e:
                pass
        for i, r in enumerate(compiled_reactions):
            propensities[r] = eval(compiled_reactions[r], {
                                   **eval_globals, **curr_state})
            state_change[y_map[r]] += propensities[r]
        for event in events:
            triggered = eval(event.trigger.expression, {
                             **eval_globals, **curr_state})
            if triggered:
                state_change[y_map[event]] = 1
        return state_change

    def __find_event_time(self, sol, start, end, index, depth):
        """
        Helper method providing binary search implementation for locating
        precise event times.
        """
        dense_range = np.linspace(start, end, 3)
        mid = dense_range[1]
        if start >= mid or mid >= end or depth == 20:
            return end
        solutions = np.diff(sol.sol(dense_range)
                            [-len(self.model.listOfEvents) + index])
        bool_res = [x > 0 for x in solutions]

        if bool_res[0]:  # event before mid
            depth += 1
            return self.__find_event_time(sol, dense_range[0],
                                          dense_range[1], index, depth)
        else:  # event after mid
            depth += 1
            return self.__find_event_time(sol, dense_range[1],
                                          dense_range[2], index, depth)

    def __detect_events(self, event_sensitivity, sol, delayed_events,
                        trigger_states, curr_time, curr_state):
        """
        Helper method to locate precise time of event firing.  This method
        first searches for any instance of an event using event_sensitivity to
        determine the granularity of the search.  If an event is detected, a
        binary search is then used to locate the precise time of that event.
        """
        event_times = {}
        dense_range = np.linspace(
            sol.t[0], sol.t[-1], len(sol.t) * event_sensitivity)
        solutions = np.diff(sol.sol(dense_range))
        for i, e in enumerate(self.model.listOfEvents.values()):
            bool_res = [x > 0 for x in solutions[i -
                                                 len(self.model.listOfEvents)]]
            curr_state[e.name] = bool_res[-1]
            # Search for changes from False to True in event, record first time
            for y in range(1, len(dense_range) - 1):
                # Check Persistent Delays.  If an event is not designated as
                # persistent, and the trigger expression fails to evaluate as
                # true before assignment is carried out, remove the event from
                # the queue.
                if e.name in trigger_states and not e.trigger.persistent:
                    if not bool_res[y]:
                        delayed_events[i] = delayed_events[-1]  # move to end
                        heapq.heappop(delayed_events)
                        del trigger_states[e.name]
                        curr_state[e.name] = False
                # IF triggered from false to true, refine search
                elif bool_res[y] and dense_range[y] != curr_time and bool_res[y - 1] == 0:
                    event_time = self.__find_event_time(sol, dense_range[y - 1],
                                                        dense_range[y + 1], i, 0)
                    if event_time in event_times:
                        event_times[event_time].append(e)
                    else:
                        event_times[event_time] = [e]
                    break
        return event_times

    def __get_next_step(self, event_times, reaction_times, delayed_events,
                        sim_end, next_tau):
        """
        Helper method to determine the next action to take during simulation,
        and returns that action along with the time that it occurs.
        """

        next_event_trigger = sim_end + 2
        next_delayed_event = sim_end + 3
        curr_time = sim_end

        # event triggers
        if len(event_times):
            next_event_trigger = min(event_times)

        # delayed events
        if len(delayed_events):
            next_delayed_event = delayed_events[0][0]

        # Execute rxns/events
        next_step = {sim_end: 'end', next_tau: 'tau',
                     next_event_trigger: 'trigger', next_delayed_event: 'delay'}

        # Set time to next action
        curr_time = min(sim_end, next_tau, next_event_trigger,
                        next_delayed_event)
        return next_step[curr_time], curr_time

    def __process_queued_events(self, event_queue, trigger_states,
                                curr_state, det_spec):
        """
        Helper method which processes the events queue. Method is primarily for
        evaluating assignments at the designated state (trigger time or event
        time).
        """
        # Process all queued events
        events_processed = []
        pre_assignment_state = curr_state.copy()
        while event_queue:
            # Get events in priority order
            fired_event = self.model.listOfEvents[heapq.heappop(event_queue)[
                1]]
            events_processed.append(fired_event)
            if fired_event.name in trigger_states:
                assignment_state = trigger_states[fired_event.name]
                del trigger_states[fired_event.name]
            else:
                assignment_state = pre_assignment_state
            for a in fired_event.assignments:
                # Get assignment value
                assign_value = eval(
                    a.expression, eval_globals, assignment_state)
                # Update state of assignment variable
                curr_state[a.variable.name] = assign_value

        return events_processed

    def __handle_event(self, event, curr_state, curr_time, event_queue,
                       trigger_states, delayed_events):
        """
        Helper method providing logic for updating states based on assignments.
        """
        # Fire trigger time events immediately
        if event.delay is None:
            heapq.heappush(event_queue, (eval(event.priority), event.name))
        # Queue delayed events
        else:
            curr_state['t'] = curr_time
            curr_state['time'] = curr_time
            execution_time = curr_time + \
                eval(event.delay, {**eval_globals, **curr_state})
            curr_state[event.name] = True
            heapq.heappush(delayed_events, (execution_time, event.name))
            if event.use_values_from_trigger_time:
                trigger_states[event.name] = curr_state.copy()
            else:
                trigger_states[event.name] = curr_state

    def __check_t0_events(self, initial_state):
        """
        Helper method for firing events who reach a trigger condition at start
        of simulation, time == 0.
        """
        # Check Event State at t==0
        species_modified_by_events = []
        t0_delayed_events = {}
        for e in self.model.listOfEvents.values():
            if not e.trigger.value:
                t0_firing = eval(e.trigger.expression, {
                                 **eval_globals, **initial_state})
                if t0_firing:
                    if e.delay is None:
                        for a in e.assignments:
                            initial_state[a.variable.name] = eval(
                                a.expression, {**eval_globals, **initial_state})
                            species_modified_by_events.append(a.variable.name)
                    else:
                        execution_time = eval(
                            e.delay, {**eval_globals, **initial_state})
                        t0_delayed_events[e.name] = execution_time
        return t0_delayed_events, species_modified_by_events

    def __update_stochastic_rxn_states(self, propensities, tau_step, compiled_reactions, curr_state, only_update=None):
        """
        Helper method for updating the state of stochastic reactions.

        if 'only_update' is set to a reaction name, it will only reset that reaction, and only one firing
        """

        rxn_count = OrderedDict()
        species_modified = OrderedDict()
        # Update stochastic reactions

        for rxn in compiled_reactions:
            rxn_count[rxn] = 0
            if only_update is not None:  # for a single SSA step
                if rxn == only_update:
                    # set this value, needs to be <0
                    curr_state[rxn] = math.log(np.random.uniform(0, 1))
                    rxn_count[rxn] = 1
            elif curr_state[rxn] > 0:
                rxn_count[rxn] = 1 + np.random.poisson(curr_state[rxn])
                curr_state[rxn] = math.log(np.random.uniform(0, 1))

            if rxn_count[rxn]:
                for reactant in self.model.listOfReactions[rxn].reactants:
                    species_modified[reactant] = True
                    curr_state[reactant] -= self.model.listOfReactions[rxn].reactants[reactant] * rxn_count[rxn]
                for product in self.model.listOfReactions[rxn].products:
                    species_modified[product] = True
                    curr_state[product] += self.model.listOfReactions[rxn].products[product] * rxn_count[rxn]
        return species_modified, rxn_count

    def __integrate_constant(self, integrator_options, curr_state, y0, curr_time,
                             propensities, y_map, compiled_reactions,
                             active_rr, event_queue,
                             delayed_events, trigger_states,
                             event_sensitivity, tau_step):
        """
        Integreate one step, skip ODE integrator as all species are 
        discrete.
        """
        tau_step = max(1e-6, tau_step)
        next_tau = curr_time + tau_step
        prev_time = curr_time
        curr_state['t'] = curr_time
        curr_state['time'] = curr_time

        event_times = {}
        reaction_times = []
        next_step, curr_time = self.__get_next_step(event_times, reaction_times,
                                                    delayed_events,
                                                    self.model.timespan[-1], next_tau)
        curr_state['t'] = curr_time

        tau_step2 = curr_time - prev_time

        for rxn in compiled_reactions:
            curr_state[rxn] = curr_state[rxn] + propensities[rxn]*tau_step2

        return curr_time, tau_step2

    def __integrate(self, integrator_options, curr_state, y0, curr_time,
                    propensities, y_map, compiled_reactions,
                    active_rr, event_queue,
                    delayed_events, trigger_states,
                    event_sensitivity, tau_step, det_rxn):
        """
        Helper function to perform the ODE integration of one step.  This
        method uses scipy.integrate.LSODA to get simulation data, and
        determines the next stopping point of the simulation. The state is
        updated and returned to __simulate along with curr_time and the
        solution object.
        """
        use_const = False
        if self.pure_discrete:
            use_const = True
        elif len(self.model.listOfRateRules) == 0:
            use_const = True
            for rxn in det_rxn:
                if det_rxn[rxn]:
                    use_const = False
                    break

        if use_const:
            return self.__integrate_constant(integrator_options, curr_state, y0, curr_time,
                                             propensities, y_map, compiled_reactions, active_rr, event_queue,
                                             delayed_events, trigger_states, event_sensitivity, tau_step)

        from functools import partial
        events = self.model.listOfEvents.values()
        dense_output = False
        int_args = [curr_state, self.model.listOfSpecies, self.model.listOfReactions,
                    self.model.listOfRateRules,
                    propensities, y_map,
                    compiled_reactions,
                    active_rr,
                    events,
                    self.model.listOfAssignmentRules]

        def rhs(t, y): return TauHybridSolver.__f(t, y, *int_args)
        if 'min_step' in integrator_options:
            tau_step = max(integrator_options['min_step'], tau_step)
        else:
            tau_step = max(1e-6, tau_step)
        # next_tau = curr_time + tau_step
        last_curr_time = curr_time

        # Set curr time to next time a change occurs in the system outside of
        # the standard ODE process.  Determine what kind of change this is,
        # and set the curr_time of simulation to restart simulation after
        # making the appropriate state changes.
        event_times = {}
        reaction_times = []
        next_step, curr_time = self.__get_next_step(event_times, reaction_times,
                                                    delayed_events,
                                                    self.model.timespan[-1], curr_time + tau_step)
        curr_state['t'] = curr_time
        curr_state['time'] = curr_time
        actual_tau_step = last_curr_time - curr_time

        # Integrate until end or tau is reached
        loop_count = 0
        sol = LSODA(rhs, last_curr_time, y0, curr_time)
        counter = 0
        while sol.t < curr_time:
            counter += 1
            sol.step()

        # Update states of all species based on changes made to species through
        # ODE processes.  This will update all species whose mode is set to
        # 'continuous', as well as 'dynamic' mode species which have been
        # flagged as deterministic.

        for spec_name, species in self.model.listOfSpecies.items():
            if not species.constant:
                curr_state[spec_name] = sol.y[y_map[spec_name]]

        # Search for precise event times
        '''
        if len(model.listOfEvents):
            event_times = self.__detect_events(event_sensitivity, sol, delayed_events,
                                               trigger_states, curr_time, curr_state)
        else:
            event_times = {}

        # Get next tau time
        reaction_times = []
        '''

        # Stochastic Reactions are also fired through a root-finding method
        # which mirrors the standard SSA probability.  Since we are using
        # Tau-Leaping, rather than firing reactions based on a direct poisson
        # distribution from the propensity, we use that same poisson
        # distribution to select a random negative offset for the reaction
        # state, then integrate forward along with any deterministic
        # reactions/species for a designated time (tau).  Root crossings
        # satisfy the SSA firing process, and because multiple reactions can be
        # fired in a single Tau step, a new random number will be generated and
        # added (representing a single-firing each time) until the state value
        # of the reaction is once again negative.
        for rxn in compiled_reactions:
            curr_state[rxn] = sol.y[y_map[rxn]]

        # In the case that a major change occurs to the system (outside of the
        # standard ODE process) is caused by an event trigger, we then examine
        # the event which was triggered.  if Event assignments are carried out
        # immediately, we add them to a heap in Event Priority order to be
        # immediately dealt with.  If an Event contains a delay, we can now set
        # the time of event assignment execution by evaluating the event delay
        # in the current state.
        if next_step == 'trigger':
            for event in event_times[curr_time]:
                self.__handle_event(event, curr_state, curr_time,
                                    event_queue, trigger_states, delayed_events)
        # In the case that a major change occurs to the system (outside of the
        # standard ODE process) is caused by a delayed event which has now
        # reached the designated time of execution, we add all currently
        # designated event assignments to a heap to be processed in Event
        # Priority order.
        elif next_step == 'delay':
            event = heapq.heappop(delayed_events)
            heapq.heappush(
                event_queue, (eval(self.model.listOfEvents[event[1]].priority), event[1]))

        return curr_time, actual_tau_step

    def __simulate_negative_state_check(self, curr_state):
        # check each species to see if they are negative
        for s in self.non_negative_species:
            if curr_state[s] < 0:
                raise SimulationError(f"Negative State detected at begining of step."
                                      " Species involved in reactions can not be negative.")

    def __simulate_invalid_state_check(self, species_modified, curr_state, compiled_reactions):
        invalid_state = False
        err_message = ""
        # check each species to see if they are negative
        for s in species_modified.keys():
            if curr_state[s] < 0:
                invalid_state = True
                err_message += f"'{s}' has negative state '{curr_state[s]}'"
        return (invalid_state, err_message)

    def __save_state_to_output(self, curr_time, save_index, curr_state, species,
                               trajectory, save_times):
        """
        Helper function to save the curr_state to the trajectory output
        """

        # Now update the step and trajectories for this step of the simulation.
        # Here we make our final assignments for this step, and begin
        # populating our results trajectory.

        num_saves = 0
        while len(save_times) > 0 and save_times[0] <= curr_time:
            # remove the value from the front of the list
            time = save_times.pop(0)
            # if a solution is given for it
            trajectory_index = save_index
            assignment_state = copy.deepcopy(curr_state)
            for s, sname in enumerate(species):
                # Get ODE Solutions
                trajectory[trajectory_index][s + 1] = curr_state[sname]
                # Update Assignment Rules for all processed time points
                if len(self.model.listOfAssignmentRules):
                    # Copy ODE state for assignments
                    assignment_state[sname] = curr_state[sname]
            assignment_state['t'] = time
            for ar in self.model.listOfAssignmentRules.values():
                var_name = ar.variable if isinstance(
                    ar.variable, str) else ar.variable.name
                assignment_value = eval(
                    ar.formula, {**eval_globals, **assignment_state})
                assignment_state[var_name] = assignment_value
                trajectory[trajectory_index][species.index(
                    var_name) + 1] = assignment_value
            num_saves += 1
            save_index += 1
        return save_index

    def get_time(self):
        return self.curr_time

    def get_species(self, species_name):
        return self.curr_state[species_name]

    def __simulate(self, integrator_options, curr_state, y0, curr_time,
                   propensities, species, parameters, compiled_reactions,
                   active_rr, y_map, trajectory, save_times, save_index,
                   delayed_events, trigger_states, event_sensitivity,
                   tau_step, debug, det_spec, det_rxn):
        """
        Function to process simulation until next step, which can be a
        stochastic reaction firing, an event trigger or assignment, or end of
        simulation.

        :param curr_state: Contains all state variables for system at current time
        :type curr_state: dict

        :param curr_time: Represents current time
        :type curr_time: float

        :param save_times: Currently unreached save points
        :type save_times: list

        :returns: curr_state, curr_time, save_times, sol
        """

        # first check if we have a valid state:
        self.__simulate_negative_state_check(curr_state)
        if curr_time == 0.0:
            # save state at beginning of simulation
            save_index = self.__save_state_to_output(
                curr_time, save_index, curr_state, species, trajectory, save_times
            )

        event_queue = []
        prev_y0 = copy.deepcopy(y0)
        prev_curr_state = copy.deepcopy(curr_state)
        prev_curr_time = curr_time
        loop_count = 0
        invalid_state = False

        starting_curr_state = copy.deepcopy(curr_state)
        starting_propensities = copy.deepcopy(propensities)
        starting_tau_step = tau_step
        species_modified = None
        rxn_count = None
        loop_err_message = ""
        if self.profile_reactions:
            self.profile_data['time'].append(curr_time)
            for k in list(self.model.listOfSpecies)+list(self.model.listOfReactions):
                self.profile_data[k].append(curr_state[k])

        # check each reaction to see if it is >=0. If we have taken a single SSA step, this could be >0 for the non-selected reactions, check if propensity is zero and reset if so
        for r in compiled_reactions.keys():
            if curr_state[r] >= 0 and propensities[r] == 0:
                curr_state[r] = math.log(np.random.uniform(0, 1))

        curr_time, actual_tau_step = self.__integrate(integrator_options, curr_state,
                                                      y0, curr_time, propensities, y_map,
                                                      compiled_reactions,
                                                      active_rr,
                                                      event_queue,
                                                      delayed_events,
                                                      trigger_states,
                                                      event_sensitivity,
                                                      tau_step, det_rxn
                                                      )

        species_modified, rxn_count = self.__update_stochastic_rxn_states(
            propensities, actual_tau_step, compiled_reactions, curr_state)

        # Occasionally, a tau step can result in an overly-aggressive
        # forward step and cause a species population to fall below 0,
        # which would result in an erroneous simulation.
        # We estimate the time to the first
        # stochatic reaction firing (assume constant propensities) and
        # simulate the ODE system until that time, fire that reaction
        # and continue the simulation.
        (invalid_state, invalid_err_message) = self.__simulate_invalid_state_check(
            species_modified, curr_state, compiled_reactions)

        if invalid_state:
            invalid_state = False
            # Redo this step, with a smaller Tau such that a single SSA reaction occurs
            y0 = copy.deepcopy(prev_y0)
            curr_state_after = copy.deepcopy(curr_state)
            curr_state = copy.deepcopy(prev_curr_state)
            floored_curr_state = copy.deepcopy(prev_curr_state)
            propensities_after = copy.deepcopy(propensities)
            propensities = copy.deepcopy(starting_propensities)
            floored_propensities = copy.deepcopy(starting_propensities)
            curr_time = prev_curr_time

            # floored propensites
            for i, s in enumerate(self.model.listOfSpecies):
                floored_curr_state[s] = math.floor(floored_curr_state[s])
            saved_curr_state = copy.deepcopy(curr_state)
            curr_state = floored_curr_state
            for i, r in enumerate(compiled_reactions):
                try:
                    floored_propensities[r] = eval(compiled_reactions[r], {
                                                   **eval_globals, **curr_state})
                except Exception as e:
                    raise SimulationError('Error calculation propensity for {0}.\nReason: {1}\nfloored_propensities={2}\ncompiled_reactions={3}'.format(
                        r, e, floored_propensities, compiled_reactions))
            curr_state = saved_curr_state

            rxn_times = OrderedDict()
            min_tau = None
            rxn_selected = None
            for rname, rcnt in rxn_count.items():
                if floored_propensities[rname] > 0.0:
                    # estimate the zero crossing time
                    rxn_times[rname] = -1 * \
                        curr_state[rname] / propensities[rname]
                    if min_tau is None or min_tau > rxn_times[rname]:
                        min_tau = rxn_times[rname]
                        rxn_selected = rname
            if rxn_selected is None:
                raise SimulationError(f"Negative State detected in step, and no reaction found to fire. error_message={
                                      invalid_err_message}")

            tau_step = min_tau  # estimated time to the first stochatic reaction

            curr_time, actual_tau_step = self.__integrate(integrator_options, curr_state,
                                                          y0, curr_time, propensities, y_map,
                                                          compiled_reactions,
                                                          active_rr,
                                                          event_queue,
                                                          delayed_events,
                                                          trigger_states,
                                                          event_sensitivity,
                                                          tau_step, det_rxn
                                                          )

            # only update the selected reaction
            first_rxn_count = copy.deepcopy(rxn_count)
            first_err_message = invalid_err_message
            species_modified, rxn_count = self.__update_stochastic_rxn_states(
                propensities, actual_tau_step, compiled_reactions, curr_state, only_update=rxn_selected)

            (invalid_state, invalid_err_message) = self.__simulate_invalid_state_check(
                species_modified, curr_state, compiled_reactions)
            if invalid_state:
                raise SimulationError(f"Negative State detected in step, after single SSA step. error_message={
                                      invalid_err_message}")

        save_index = self.__save_state_to_output(
            curr_time, save_index, curr_state, species, trajectory, save_times)

        events_processed = self.__process_queued_events(
            event_queue, trigger_states, curr_state, det_spec)

        # Finally, perform a final check on events after all non-ODE assignment
        # changes have been carried out on model.
        event_cycle = True
        while event_cycle:
            event_cycle = False
            for i, e in enumerate(self.model.listOfEvents.values()):
                triggered = eval(e.trigger.expression, {
                                 **eval_globals, **curr_state})
                if triggered and not curr_state[e.name]:
                    curr_state[e.name] = True
                    self.__handle_event(e, curr_state, curr_time,
                                        event_queue, trigger_states, delayed_events)
                    event_cycle = True
                elif not triggered:
                    curr_state[e.name] = False

        events_processed = self.__process_queued_events(
            event_queue, trigger_states, curr_state, det_spec)

        return curr_state, curr_time, save_times, save_index

    def __set_seed(self, seed):
        # Set seed if supplied
        if seed is not None:
            if not isinstance(seed, int):
                seed = int(seed)
            if seed > 0:
                np.random.seed(seed)
            else:
                raise ModelError('seed must be a positive integer')

    def __set_recommended_ode_defaults(self, integrator_options):
        """
        Set some ODE solver defaults.  These values are chosen based on the
        precision required to successfully complete the SBML Test suite.
        """

        if 'rtol' not in integrator_options:
            integrator_options['rtol'] = 1e-9
        if 'atol' not in integrator_options:
            integrator_options['atol'] = 1e-12
        if 'max_step' not in integrator_options:
            integrator_options['max_step'] = 0.25

    def __compile_all(self):
        """
        Compile all run-time evaluables to enhance performance.
        """
        compiled_reactions = OrderedDict()
        for i, r in enumerate(self.model.listOfReactions):
            compiled_reactions[r] = compile(self.model.listOfReactions[r].propensity_function, '<string>',
                                            'eval')

        compiled_rate_rules = OrderedDict()
        for i, rr in enumerate(self.model.listOfRateRules.values()):
            if isinstance(rr.variable, str):
                compiled_rate_rules[self.model.listOfSpecies[rr.variable]] = compile(
                    rr.formula, '<string>', 'eval')
            else:
                compiled_rate_rules[rr.variable] = compile(
                    rr.formula, '<string>', 'eval')
        compiled_inactive_reactions = OrderedDict()

        compiled_propensities = copy.deepcopy(compiled_reactions)

        return compiled_reactions, compiled_rate_rules, compiled_inactive_reactions, compiled_propensities

    def __initialize_state(self, curr_state, debug):
        """
        Initialize curr_state for each trajectory.
        """

        # intialize parameters to current state
        for p in self.model.listOfParameters:
            curr_state[p] = float(self.model.listOfParameters[p].expression)
        if 'vol' not in curr_state:
            curr_state['vol'] = float(getattr(self.model, "volume", 1.0))

        # initialize species population state
        for s in self.model.listOfSpecies:
            curr_state[s] = self.model.listOfSpecies[s].initial_value

        # Set reactions to uniform random number
        for i, r in enumerate(self.model.listOfReactions):
            curr_state[r] = math.log(np.random.uniform(0, 1))
            if debug:
                print("Setting Random number ",
                      curr_state[r], " for ", self.model.listOfReactions[r].name)

        # Initialize event last-fired times to 0
#        for e_name in self.model.listOfEvents:
#            curr_state[e_name] = 0

        sanitized_species = self.model._sanitized_species_names()
        sanitized_parameters = self.model._sanitized_parameter_names()
        for fd in self.model.listOfFunctionDefinitions.values():
            sanitized_function = fd.sanitized_function(
                sanitized_species, sanitized_parameters)
            curr_state[fd.name] = eval(f"lambda {', '.join(fd.args)}: {
                                       sanitized_function}", eval_globals)

        for ar in self.model.listOfAssignmentRules.values():
            if ar.variable in self.model.listOfSpecies:
                continue
            curr_state[ar.variable] = ar.formula

    def __map_state(self, species, parameters, compiled_reactions, events, curr_state):
        """
        Creates the start state vector for integration and provides a
        dictionary map to it's elements.
        """
        y_map = OrderedDict()
        # Build integration start state
        y0 = [0] * (len(species) + len(parameters) +
                    len(compiled_reactions) + len(events))
        for i, spec in enumerate(species):
            if isinstance(curr_state[spec], str):
                y0[i] = eval(curr_state[spec], {**eval_globals, **curr_state})
            else:
                y0[i] = curr_state[spec]
            y_map[spec] = i
        for i, param in enumerate(parameters):
            y0[i + len(species)] = curr_state[param]
            y_map[param] = i + len(species)
        for i, rxn in enumerate(compiled_reactions):
            y0[i + len(species) + len(parameters)] = curr_state[rxn]
            y_map[rxn] = i + len(species) + len(parameters)
        for i, event in enumerate(events.values()):
            y0[i + len(species) + len(parameters) +
               len(compiled_reactions)] = curr_state[event.name]
            y_map[event] = i + len(species) + \
                len(parameters) + len(compiled_reactions)
        return y0, y_map

    @classmethod
    def get_solver_settings(cls):
        """
        Returns a list of arguments supported by tau_hybrid_solver.run.
        :returns: Tuple of strings, denoting all keyword argument for this solvers run() method.
        :rtype: tuple
        """
        return ('model', 't', 'number_of_trajectories', 'increment', 'seed', 'debug', 'profile', 'tau_tol',
                'event_sensitivity', 'integrator_options')

    @classmethod
    def get_supported_features(cls):
        return {
            Event,
            RateRule,
            AssignmentRule,
            FunctionDefinition,
        }

    def __run(self, timeline, trajectory_base, initial_state, t=20,
              number_of_trajectories=1, increment=0.05, seed=None,
              debug=False, profile=False,
              tau_tol=0.03, event_sensitivity=100,
              integrator_options={}, **kwargs):

        # create mapping of species dictionary to array indices
        species_mappings = self.model._sanitized_species_names()
        species = list(self.model.listOfSpecies.keys())
        parameter_mappings = self.model._sanitized_parameter_names()
        parameters = list(self.model.listOfParameters.keys())
        number_species = len(species)

        t0_delayed_events, species_modified_by_events = self.__check_t0_events(
            initial_state)

        # Create deterministic tracking data structures
        det_spec = {species: value.mode != 'discrete' for (
            species, value) in self.model.listOfSpecies.items()}

        det_rxn = {rxn: False for (
            rxn, value) in self.model.listOfReactions.items()}

        # Determine if entire simulation is ODE or Stochastic, in order to
        # avoid unnecessary calculations during simulation
        simulation_data = []

        dependencies = OrderedDict()

        # If considering deterministic changes, create dependency data
        # structure for creating diff eqs later
        for reaction in self.model.listOfReactions:
            dependencies[reaction] = set()
            [dependencies[reaction].add(
                reactant) for reactant in self.model.listOfReactions[reaction].reactants]
            [dependencies[reaction].add(
                product) for product in self.model.listOfReactions[reaction].products]

        # Main trajectory loop
        for trajectory_num in range(number_of_trajectories):

            # NumPy array containing this simulation's results
            trajectory = trajectory_base[trajectory_num]
            propensities = OrderedDict()  # Propensities evaluated at current state

            curr_state = initial_state.copy()
            curr_time = 0  # Current Simulation Time

            for i, r in enumerate(self.model.listOfReactions):
                curr_state[r] = math.log(np.random.uniform(0, 1))
                if debug:
                    print("Setting Random number ",
                          curr_state[r], " for ", self.model.listOfReactions[r].name)

            end_time = self.model.timespan[-1]  # End of Simulation time
            entry_pos = 1
            data = OrderedDict()  # Dictionary for results
            data['time'] = timeline  # All time entries
            save_index = 0

            # Record Highest Order reactant for each reaction and set error tolerance
            HOR, reactants, mu_i, sigma_i, g_i, epsilon_i, critical_threshold = Tau.initialize(
                self.model, tau_tol)

            # One-time compilations to reduce time spent with eval
            compiled_reactions, compiled_rate_rules, compiled_inactive_reactions, compiled_propensities = \
                self.__compile_all()
            all_compiled = OrderedDict()
            all_compiled['rxns'] = compiled_reactions
            all_compiled['inactive_rxns'] = compiled_inactive_reactions
            all_compiled['rules'] = compiled_rate_rules

            save_times = list(np.copy(self.model.timespan.items))
            delayed_events = []
            trigger_states = {}

            # Handle delayed t0 events
            for state in trigger_states.values():
                if state is None:
                    state = curr_state
            for ename, etime in t0_delayed_events.items():
                curr_state[ename] = True
                heapq.heappush(delayed_events, (etime, ename))
                if self.model.listOfEvents[ename].use_values_from_trigger_time:
                    trigger_states[ename] = curr_state.copy()
                else:
                    trigger_states[ename] = curr_state

            # Each save step
            while curr_time < self.model.timespan[-1]:

                # Get current propensities
                for i, r in enumerate(self.model.listOfReactions):
                    try:
                        propensities[r] = eval(
                            compiled_propensities[r], eval_globals, curr_state)
                        if curr_state[r] > 0 and propensities[r] == 0:
                            # This is an edge case, that might happen after a single SSA step.
                            curr_state[r] = math.log(
                                np.random.uniform(0, 1))
                    except Exception as e:
                        raise SimulationError(
                            'Error calculation propensity for {0}.\nReason: {1}\ncurr_state={2}'.format(r, e, curr_state))

                # Calculate Tau statistics and select a good tau step
                if self.constant_tau_stepsize is None:
                    tau_step = Tau.select(HOR, reactants, mu_i, sigma_i, g_i, epsilon_i, tau_tol,
                                          critical_threshold, self.model, propensities, curr_state, curr_time, save_times[0])
                else:
                    tau_step = self.constant_tau_stepsize
                if debug:
                    X = ''
                    for k, v in curr_state.items():
                        X += f'{k}:{v:.2f} '
                    print(f"t={curr_time} tau={tau_step} curr_state={X}")

                # Process switching if used
                mn, sd, CV = self.__calculate_statistics(
                    curr_time, propensities, curr_state, tau_step, det_spec)

                # Calculate sd and CV for hybrid switching and flag deterministic reactions
                deterministic_reactions = self.__flag_det_reactions(
                    det_spec, det_rxn, dependencies)

                if debug:
                    print('mean: {0}'.format(mn))
                    print('standard deviation: {0}'.format(sd))
                    print('CV: {0}'.format(CV))
                    print('det_spec: {0}'.format(det_spec))
                    print('det_rxn: {0}'.format(det_rxn))

                # Set active reactions and rate rules for this integration step
                rr_sets = {frozenset(): compiled_rate_rules}  # base rr set
                active_rr = self.__toggle_reactions(all_compiled, deterministic_reactions,
                                                    dependencies, curr_state, det_spec, rr_sets)

                # Create integration initial state vector
                y0, y_map = self.__map_state(species, parameters,
                                             compiled_reactions, self.model.listOfEvents, curr_state)

                # Run simulation to next step
                curr_state, curr_time, save_times, save_index = self.__simulate(integrator_options,
                                                                                curr_state, y0, curr_time,
                                                                                propensities, species,
                                                                                parameters, compiled_reactions,
                                                                                active_rr, y_map,
                                                                                trajectory, save_times, save_index,
                                                                                delayed_events,
                                                                                trigger_states,
                                                                                event_sensitivity, tau_step,
                                                                                debug, det_spec, det_rxn)

            # End of trajectory, format results
            data = {'time': timeline}
            for i in range(number_species):
                data[species[i]] = trajectory[:, i + 1]
            simulation_data.append(data)

        return simulation_data

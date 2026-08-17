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

import numpy

# from gillespy3d.core.domain import Domain
from gillespy3d_pp.core.species import Species
# from gillespy3d.core.initialcondition import (
#    InitialCondition,
#   PlaceInitialCondition,
#  ScatterInitialCondition,
#    UniformInitialCondition
# )
from gillespy3d_pp.core.parameter import Parameter
from gillespy3d_pp.core.simulation import Simulation
from gillespy3d_pp.core.reaction import Reaction
# from gillespy3d.core.boundarycondition import BoundaryCondition
# from gillespy3d.core.datafunction import DataFunction
from gillespy3d_pp.core.timespan import TimeSpan
# from gillespy3d.solvers.build_expression import BuildExpression
from gillespy3d_pp.core.error import ModelError, ParameterError
from gillespy3d_pp.core.result import Result
from gillespy3d_pp.core.raterule import RateRule
from gillespy3d_pp.core.assignmentrule import AssignmentRule
from gillespy3d_pp.core.functiondefinition import FunctionDefinition
from random import randint
from collections import OrderedDict


class Model():
    """
    Representation of a spatial biochemical model.

    :param name: Name of the model
    :type name: str
    """

    def __init__(self, name="gillespy3d"):
        self.name = name
        self.listOfSpecies = OrderedDict()
        self.listOfParameters = OrderedDict()
        self.listOfReactions = OrderedDict()
        self.listOfRateRules = OrderedDict()
        self.listOfFunctionDefinitions = OrderedDict()
        self.listOfAssignmentRules = OrderedDict()
        self.initial_condition = []
        self.boundary_condition = []
        self.data_functions = []
        self.domain = None
        self.volume = 1.0

    def __str__(self):
        return f"Model(name={self.name}, species={self.listOfSpecies}, parameters={self.listOfParameters}, reactions={self.listOfReactions}, initial_condition={self.initial_condition}, boundary_condition={self.boundary_condition}, data_functions={self.data_functions}, domain={self.domain}, timespan={self.timespan})"

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        return False  # TODO

    def add(self, components):
        """
        Adds a component, or list of components to the model. If a list is provided,
        Species and Parameters are added before other components.  Lists may contain
        any combination of accepted types other than lists and do not need to be in
        any particular order.

        :param components: The component or list of components to be added to the
                           model.
        :type components: Species, Parameters, Reactions, Domain, Data Function, \
                          Initial Conditions, Boundary Conditions, and TimeSpan or
                          list

        :returns: The components that were added to the model.
        :rtype: Species, Parameters, Reactions, Domain, Data Function, \
                Initial Conditions, Boundary Conditions, TimeSpan, or list

        :raises ModelError: Component is invalid.
        """
        initialcondition_names = [
            PlaceInitialCondition.__name__,
            ScatterInitialCondition.__name__,
            UniformInitialCondition.__name__
        ]
        if isinstance(components, list):
            params = []
            others = []
            for component in components:
                if isinstance(component, Species) or \
                        type(component).__name__ in Species.__name__:
                    self.add_species(component)
                elif isinstance(component, Parameter) or \
                        type(component).__name__ in Parameter.__name__:
                    params.append(component)
                else:
                    others.append(component)

            for param in params:
                self.add_parameter(param)
            for component in others:
                self.add(component)
        elif isinstance(components, BoundaryCondition) or type(components).__name__ == BoundaryCondition.__name__:
            self.add_boundary_condition(components)
        elif isinstance(components, DataFunction) or type(components).__name__ == DataFunction.__name__:
            self.add_data_function(components)
        elif isinstance(components, Domain) or type(components).__name__ == Domain.__name__:
            self.add_domain(components)
        elif isinstance(components, InitialCondition) or type(components).__name__ in initialcondition_names:
            self.add_initial_condition(components)
        elif isinstance(components, Parameter) or type(components).__name__ == Parameter.__name__:
            self.add_parameter(components)
        elif isinstance(components, Reaction) or type(components).__name__ == Reaction.__name__:
            self.add_reaction(components)
        elif isinstance(components, Species) or type(components).__name__ == Species.__name__:
            self.add_species(components)
        elif isinstance(components, TimeSpan) or type(components).__name__ == TimeSpan.__name__:
            self.add_timespan(components)
        else:
            raise ModelError(f"Unsupported component: {
                             type(components)} is not a valid component.")
        return components

    def add_domain(self, domain, allow_all_types=False):
        """
        Add a spatial domain to the model

        :param domain: The Domain object to be added to the model
        :type domain: gillespy3d.core.domain.Domain

        :raises ModelError: Invalid Domain object
        """
        if not (isinstance(domain, Domain) or type(domain).__name__ == "Domain"):
            raise ModelError(
                Exception(f"Invalid Domain object, invalid input of type: {type(domain)}"))

        self.domain = domain

    def add_species(self, species):
        """
        Adds a species, or list of species to the model.

        :param species: The species or list of species to be added to the model object.
        :type species: gillespy3d.core.species.Species | list(gillespy3d.core.species.Species)

        :returns: The species or list of species that were added to the model.
        :rtype: gillespy3d.core.species.Species | list(gillespy3d.core.species.Species)

        :raises ModelError: If an invalid species is provided or if Species.validate fails.
        """
        if isinstance(species, list):
            for s in species:
                self.add_species(s)
        else:
            if not ((isinstance(species, Species) or type(species).__name__ == "Species")):
                raise ModelError(f"Invalid Species object, invalid input of type: {
                                 type(species).__name__}")
            if Species.validate(species):
                raise ModelError("Species.validate failed")
            self.listOfSpecies[species.name] = species
        return species

    def add_initial_condition(self, init_cond):
        """
        Add an initial condition object to the initialization of the model.

        :param init_cond: Initial condition to be added.
        :type init_cond: gillespy3d.core.initialcondition.InitialCondition

        :returns: The initial condition or list of initial conditions that were added to the model.
        :rtype: gillespy3d.core.initialcondition.InitialCondition | \
                list(gillespy3d.core.initialcondition.InitialCondition)

        :raises ModelError: If an invalid initial condition is provided.
        """
        names = [
            PlaceInitialCondition.__name__,
            ScatterInitialCondition.__name__,
            UniformInitialCondition.__name__
        ]
        if isinstance(init_cond, list):
            for initial_condition in init_cond:
                self.add_initial_condition(initial_condition)
        elif isinstance(init_cond, InitialCondition) or type(init_cond).__name__ in names:
            self.initial_condition.append(init_cond)
        else:
            errmsg = f"init_cond must be of type InitialCondition or list of InitialCondition not {
                type(init_cond)}"
            raise ModelError(errmsg)
        return init_cond

    def add_parameter(self, parameters):
        """
        Adds a parameter, or list of parameters to the model.

        :param parameters:  The parameter or list of parameters to be added to the model object.
        :type parameters: gillespy3d.core.parameter.Parameter | list(gillespy3d.core.parameter.Parameter)

        :returns: A parameter or list of Parameters that were added to the model.
        :rtype: gillespy3d.core.parameter.Parameter | list(gillespy3d.core.parameter.Parameter)

        :raises ModelError: If an invalid parameter is provided or if Parameter.validate fails.
        """
        if isinstance(parameters, list):
            for s in parameters:
                self.add_parameter(s)
        else:
            if not ((isinstance(parameters, Parameter)) or type(parameters).__name__ == "Parameter"):
                raise ModelError(f"Invalid Parameter object, invalid input of type: {
                                 type(parameters).__name__}")
            if Parameter.validate(parameters):
                raise ModelError("Species.validate failed")
            self.listOfParameters[parameters.name] = parameters
        return parameters

    def add_reaction(self, reactions):
        """
        Adds a reaction, or list of reactions to the model.

        :param reactions: The reaction or list of reactions to be added to the model object
        :type reactions: gillespy3d.core.reaction.Reaction | list(gillespy3d.core.reaction.Reaction)

        :returns: The reaction or list of reactions that were added to the model.
        :rtype: gillespy3d.core.reaction.Reaction | list(gillespy3d.core.reaction.Reaction)

        :raises ModelError: If an invalid reaction is provided or if Reaction.validate fails.
        """
        if isinstance(reactions, list):
            for s in reactions:
                self.add_reaction(s)
        else:
            if not ((isinstance(reactions, Reaction)) or type(reactions).__name__ == "Reaction"):
                raise ModelError(f"Invalid Reaction object, invalid input of type: {
                                 type(reactions).__name__}")
            if Reaction.validate(reactions):
                raise ModelError("Species.validate failed")
            self.listOfReactions[reactions.name] = reactions

        return reactions

    def add_boundary_condition(self, bound_cond):
        """
        Add an boundary condition object to the model.

        :param bound_cond: Boundary condition to be added
        :type bound_cond: gillespy3d.core.boundarycondition.BoundaryCondition

        :returns: The boundary condition or list of boundary conditions that were added to the model.
        :rtype: gillespy3d.core.boundarycondition.BoundaryCondition | \
                list(gillespy3d.core.boundarycondition.BoundaryCondition)

        :raises ModelError: If an invalid boundary conidition is provided.
        """
        if isinstance(bound_cond, list):
            for boundary_condition in bound_cond:
                self.add_boundary_condition(boundary_condition)
        elif isinstance(bound_cond, BoundaryCondition) or type(bound_cond).__name__ == "BoundaryCondition":
            self.boundary_condition.append(bound_cond)  # Actually add it
        else:
            errmsg = f"bound_cond must be of type BoundaryCondition or list of BoundaryCondition not {
                type(bound_cond)}"
            raise ModelError(errmsg)
        return bound_cond

    def add_data_function(self, data_function):
        """
        Add a scalar spatial function to the simulation. This is useful if you have a
        spatially varying input to your model. Argument is a instances of subclass of the
        gillespy3d.DataFunction class. It must implement a function 'map(point)' which takes a
        the spatial positon 'point' as an array, and it returns a float value.

        :param data_function: Data function to be added.
        :type data_function: gillespy3d.DataFunction

        :returns: DataFunction object(s) added tothe model.
        :rtype: gillespy3d.core.datafunction.DataFunction | list(gillespy3d.core.datafunction.DataFunction)

        :raises ModelError: Invalid DataFunction
        """
        if isinstance(data_function, list):
            for data_fn in data_function:
                self.add_data_function(data_fn)
        elif isinstance(data_function, DataFunction) or type(data_function).__name__ == 'DataFunction':
            self.data_functions.append(data_function)
        else:
            errmsg = f"data_function must be of type DataFunction or list of DataFunction not {
                type(data_function)}"
            raise ModelError(errmsg)
        return data_function

    def timespan(self, time_span, timestep_size=None):
        """
        alias of add_timespan()'
        """
        self.add_timespan(time_span, timestep_size)

    def add_timespan(self, time_span, timestep_size=None):
        """
        Set the time span of simulation.

        :param time_span: Evenly-spaced list of times at which to sample the species populations during the simulation.
        :type time_span: numpy.ndarray

        :param timestep_size: Size of each timestep in seconds
        :type timestep_size: float

        :raises ModelError: Invalid TimeSpan
        """
        if isinstance(time_span, TimeSpan) or type(time_span).__name__ == "TimeSpan":
            self.timespan = time_span
        elif isinstance(time_span, list):
            self.timespan = TimeSpan(time_span, timestep_size)
        else:
            raise ModelError(f"time_span must be of type TimeSpan or evenly space list of times not {
                             type(time_span)}")

    def _sanitized_species_names(self):
        """
        Generate a dictionary mapping user chosen species names to simplified formats which will be used
        later on by GillesPySolvers evaluating reaction propensity functions.

        :returns: the dictionary mapping user species names to their internal GillesPy notation.
        """
        species_name_mapping = OrderedDict([])
        for i, name in enumerate(self.listOfSpecies.keys()):
            species_name_mapping[name] = f'S[{i}]'
        return species_name_mapping

    def _sanitized_parameter_names(self):
        """
        Generate a dictionary mapping user chosen parameter names to simplified formats which will be used
        later on by GillesPySolvers evaluating reaction propensity functions.

        :returns: the dictionary mapping user parameter names to their internal GillesPy notation.
        """
        parameter_name_mapping = OrderedDict()
        parameter_name_mapping['vol'] = 'V'
        for i, name in enumerate(self.listOfParameters.keys()):
            if name not in parameter_name_mapping:
                parameter_name_mapping[name] = f'P{i}'
        return parameter_name_mapping

    def run(self, end_t=None, number_of_trajectories=10, *, dt):
        """
        Function calling simulation of the model. There are a number of
        parameters to be set here.

        :param solver: The solver by which to simulate the model. This solver object may
            be initialized separately to specify an algorithm. Optional, defaults to ssa solver.
        :type solver: gillespy.GillesPySolver

        :param timeout: Allows a time_out value in seconds to be sent to a signal handler,
            restricting simulation run-time
        :type timeout: int

        :param end_t: End time of simulation
        :type end_t: int

        :param sim_args: Simulation-specific arguments to be passed to sim.run_until()

        :param algorithm: Specify algorithm ('ODE', 'Tau-Leaping', or 'SSA') for GillesPy3D to automatically
            pick best solver using that algorithm.
        :type algorithm: str

        :returns:  Returns a Results object that inherits UserList and contains one or more Trajectory objects that
            inherit UserDict. Results object supports graphing.

        """
        # incorperate loop into
        from gillespy3d_pp import Simulation
        sim = Simulation(self, number_of_trajectories, dt, end_t, solver="SSA")
        return sim.run()


#    def run(self, number_of_trajectories=1, seed=None):
#        """
#        Simulate the model. Returns a result object containing simulation results.
#
#        :param number_of_trajectories: How many trajectories should be run.
#        :type number_of_trajectories: int
#
#        :param seed: The random seed given to the solver.
#        :type seed: int
#
#        :returns: A GillesPy3D Result object containing simulation data.
#        :rtype: gillespy3d.core.result.Result
#        """
#        if seed is None:
#            seed = randint(1, 100000000)
#
#        # For now, just return a single result
#        return Result(self, seed)
#

    def add_rate_rule(self, rate_rule):
        """
        Adds a rate rule, or list of rate rules to the model.

        :param rate_rule: The rate rule or list of rate rules to be added to the model object.
        :type rate_rule: gillespy2.RateRule | list of gillespy2.RateRules

        :returns: The rate rule or list of rate rules that were added to the model.
        :rtype: gillespy2.RateRule | list of gillespy2.RateRule

        :raises ModelError: If an invalid rate rule is provided or if rate rule validation fails.
        """
        if isinstance(rate_rule, list):
            for r_rule in sorted(rate_rule):
                self.add_rate_rule(r_rule)
        elif isinstance(rate_rule, RateRule) or type(rate_rule).__name__ == "RateRule":
            self._problem_with_name(rate_rule.name)
            ar_vars = [
                a_rule.variable for a_rule in self.listOfAssignmentRules.values()]
            rr_vars = [
                r_rule.variable for r_rule in self.listOfRateRules.values()]
            if rate_rule.variable in ar_vars:
                raise ModelError(
                    f"Duplicate variable in rate_rules AND assignment_rules: {
                        rate_rule.variable}."
                )
            if rate_rule.variable in rr_vars:
                raise ModelError(
                    f"Duplicate variable in rate_rules: {rate_rule.variable}.")
            self._resolve_rule(rate_rule)
            if rate_rule.variable.name in self.listOfSpecies:
                # check if the rate_rule's target's mode is continious
                if rate_rule.variable.mode == 'discrete':
                    raise ModelError(
                        "RateRules can not target discrete species")
                if rate_rule.variable.mode is None or rate_rule.variable.mode == 'dynamic':
                    # RateRules require a continuous target, so coerce the mode.
                    rate_rule.variable.mode = 'continuous'

            self.listOfRateRules[rate_rule.name] = rate_rule
            # Build the sanitized rate rule
            sanitized_rate_rule = RateRule(
                name=f'RR{len(self._listOfRateRules)}')
            sanitized_rate_rule.formula = rate_rule.sanitized_formula(
                self._listOfSpecies, self._listOfParameters
            )
            self._listOfRateRules[rate_rule.name] = sanitized_rate_rule
        else:
            errmsg = f"rate_rule must be of type RateRule or list of RateRules not {
                type(rate_rule)}."
            raise ModelError(errmsg)
        return rate_rule

    def delete_rate_rule(self, name):
        """
        Removes rate rule object by name.

        :param name: Name of the rate rule to be removed.
        :type name: str

        :raises ModelError: If the rate rule is not part of the model.
        """
        try:
            self.listOfRateRules.pop(name)
            if name in self._listOfRateRules:
                self._listOfRateRules.pop(name)
        except KeyError as err:
            raise ModelError(
                f"{self.name} does not contain a rate rule named {name}."
            ) from err

    def delete_all_rate_rules(self):
        """
        Removes all rate rules from the model object.
        """
        self.listOfRateRules.clear()
        self._listOfRateRules.clear()

    def get_rate_rule(self, name):
        """
        Returns a rate rule object by name.

        :param name: Name of the rate rule object to be returned.
        :type name: str

        :returns: The specified rate rule object.
        :rtype: gillespy2.RateRule

        :raises ModelError: If the rate rule is not part of the model.
        """
        if name not in self.listOfRateRules:
            raise ModelError(
                f"{self.name} does not contain a rate rule named {name}.")
        return self.listOfRateRules[name]

    def get_all_rate_rules(self):
        """
        Get all of the rate rules in the model object.

        :returns: A dict of all rate rules in the model, in the form: {name : rate rule object}.
        :rtype: OrderedDict
        """
        return self.listOfRateRules

    def _problem_with_name(self, name):
        if name in Model.reserved_names:
            names = Model.reserved_names
            raise ModelError(
                f'Name "{name}" is unavailable. It is reserved for internal '
                f'GillesPy use. Reserved Names: ({names}).'
            )
        if name in self.listOfSpecies:
            raise ModelError(
                f'Name "{name}" is unavailable. A species with that name exists.')
        if name in self.listOfParameters:
            raise ModelError(
                f'Name "{name}" is unavailable. A parameter with that name exists.')
        if name in self.listOfReactions:
            raise ModelError(
                f'Name "{name}" is unavailable. A reaction with that name exists.')
        if name in self.listOfEvents:
            raise ModelError(
                f'Name "{name}" is unavailable. An event with that name exists.')
        if name in self.listOfRateRules:
            raise ModelError(
                f'Name "{name}" is unavailable. A rate rule with that name exists.')
        if name in self.listOfAssignmentRules:
            raise ModelError(
                f'Name "{name}" is unavailable. An assignment rule with that name exists.')
        if name in self.listOfFunctionDefinitions:
            raise ModelError(
                f'Name "{name}" is unavailable. A function definition with that name exists.')
        if name.isdigit():
            raise ModelError(
                f'Name "{name}" is unavailable. Names must not be numeric strings.')
        for special_character in Model.special_characters:
            if special_character in name:
                chars = Model.special_characters
                raise ModelError(
                    f'Name "{name}" is unavailable. Names must not contain '
                    f'special characters: {chars}.'
                )

    def add_function_definition(self, function_definition):
        """
        Add function definition, or list of function definitions to the model

        :param function_definition: The function definition, or list of function definitions \
                to be added to the model object.
        :type function_definition: gillespy2.FunctionDefinition | list of gillespy2.FunctionDefinitions.

        :returns: The function defintion or list of function definitions that were added to the model.
        :rtype: gillespy2.FunctionDefinitions | list of gillespy2.FunctionDefinitions

        :raises ModelError: If an invalid function definition is provided.
        """
        if isinstance(function_definition, list):
            for func_def in function_definition:
                self.add_function_definition(func_def)
        elif isinstance(function_definition, FunctionDefinition) or \
                type(function_definition).__name__ == "FunctionDefinition":
            self._problem_with_name(function_definition.name)
            self.listOfFunctionDefinitions[function_definition.name] = function_definition
        else:
            errmsg = "function_definition must be of type FunctionDefinition or "
            errmsg += f"list of FunctionDefinitions not {
                type(function_definition)}."
            raise ModelError(errmsg)

    def delete_function_definition(self, name):
        """
        Removes a function definition object by name.

        :param name: Name of the function definition object to be removed.
        :type name: str
        """
        try:
            self.listOfFunctionDefinitions.pop(name)
            if name in self._listOfFunctionDefinitions:
                self._listOfFunctionDefinitions.pop(name)
        except KeyError as err:
            raise ModelError(
                f"{self.name} does not contain a function definition named {name}."
            ) from err

    def delete_all_function_definitions(self):
        """
        Removes all function definitions from the model object.
        """
        self.listOfFunctionDefinitions.clear()
        self._listOfFunctionDefinitions.clear()

    def get_function_definition(self, name):
        """
        Returns a function definition object by name.

        :param name: Name of the function definition object to be returned.
        :type name: str

        :returns: The specified function definition object.
        :rtype: gillespy2.FunctionDefinition
        """
        if name not in self.listOfFunctionDefinitions:
            raise ModelError(
                f"{self.name} does not contain a function definition named {name}.")
        return self.listOfFunctionDefinitions[name]

    def get_all_function_definitions(self):
        """
        Get all of the function definitions in the model object.

        :returns: A dict of all function definitions in the model, in the form {name : function definition object}.
        :rtype: OrderedDict
        """
        return self.listOfFunctionDefinitions


    def add_assignment_rule(self, assignment_rule):
        """
        Add an assignment rule, or list of assignment rules to the model.

        :param assignment_rules: The assignment rule or list of assignment rules to be added to the model object.
        :type assignment_rules: gillespy2.AssignmentRule or list of gillespy2.AssignmentRules

        :returns: The assignment rule or list of assignment rules that were added to the model.
        :rtype: gillespy2.AssignmentRule | list of gillespy2.AssignmentRule

        :raises ModelError: If an invalid assignment rule is provided or if assignment rule validation fails.
        """
        if isinstance(assignment_rule, list):
            for a_rule in assignment_rule:
                self.add_assignment_rule(a_rule)
        elif isinstance(assignment_rule, AssignmentRule) or type(assignment_rule).__name__ == "AssignmentRule":
            self._problem_with_name(assignment_rule.name)
            ar_vars = [a_rule.variable for a_rule in self.listOfAssignmentRules.values()]
            rr_vars = [r_rule.variable for r_rule in self.listOfRateRules.values()]
            if assignment_rule.variable in rr_vars:
                raise ModelError(
                    f"Duplicate variable in rate_rules AND assignment_rules: {assignment_rule.variable}."
                )
            if assignment_rule.variable in ar_vars:
                raise ModelError(f"Duplicate variable in assignments_rules: {assignment_rule.variable}.")
            self._resolve_rule(assignment_rule)
            self.listOfAssignmentRules[assignment_rule.name] = assignment_rule
            # Build the sanitized assignment rule
            sanitized_assignment_rule = AssignmentRule(name=f'AR{len(self._listOfAssignmentRules)}')
            sanitized_assignment_rule.formula = assignment_rule.sanitized_formula(
                self._listOfSpecies, self._listOfParameters
            )
            self._listOfAssignmentRules[assignment_rule.name] = sanitized_assignment_rule
        else:
            errmsg = "assignment_rule must be of type AssignmentRule or "
            errmsg += f"list of AssignmentRules not {type(assignment_rule)}."
            raise ModelError(errmsg)
        return assignment_rule

    def delete_assignment_rule(self, name):
        """
        Removes an assignment rule object by model.

        :param name: Name of the assignment rule object to be removed.
        :type name: str

        :raises ModelError: If the assignment rule is not part of the model.
        """
        try:
            self.listOfAssignmentRules.pop(name)
            if name in self._listOfAssignmentRules:
                self._listOfAssignmentRules.pop(name)
        except KeyError as err:
            raise ModelError(
                f"{self.name} does not contain an assignment rule named {name}."
            ) from err

    def delete_all_assignment_rules(self):
        """
        Removes all assignment rules from the model object.
        """
        self.listOfAssignmentRules.clear()
        self._listOfAssignmentRules.clear()

    def get_assignment_rule(self, name):
        """
        Returns an assignment rule object by name.

        :param name: Name of the assignment rule object to be returned.
        :type name: str

        :returns: The specified assignment rule object.
        :rtype: gillespy2.AssignmentRule

        :raises ModelError: If the assignment rule is not part of the model.
        """
        if name not in self.listOfAssignmentRules:
            raise ModelError(f"{self.name} does not contain an assignment rule named {name}.")
        return self.listOfAssignmentRules[name]

    def get_all_assignment_rules(self):
        """
        Get all of the assignment rules in the model object.

        :returns: A dict of all assignemt rules in the model, in the form: {name: reaction object}.
        """
        return self.listOfAssignmentRules

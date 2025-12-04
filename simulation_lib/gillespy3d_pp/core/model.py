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

import numpy

#from gillespy3d.core.domain import Domain
from gillespy3d_pp.core.species import Species
#from gillespy3d.core.initialcondition import (
#    InitialCondition,
#   PlaceInitialCondition,
#  ScatterInitialCondition,
#    UniformInitialCondition
#)
from gillespy3d_pp.core.parameter import Parameter
from gillespy3d_pp.core.simulation import Simulation
from gillespy3d_pp.core.reaction import Reaction
#from gillespy3d.core.boundarycondition import BoundaryCondition
#from gillespy3d.core.datafunction import DataFunction
from gillespy3d_pp.core.timespan import TimeSpan
#from gillespy3d.solvers.build_expression import BuildExpression
from gillespy3d_pp.core.error import ModelError, ParameterError
from gillespy3d_pp.core.result import Result
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
        self.species = []
        self.parameters = []
        self.reactions = []
        self.initial_condition = []
        self.boundary_condition = []
        self.data_functions = []
        self.domain = None
        #self.timespan = timespan


    def __str__(self):
        return f"Model(name={self.name}, species={self.species}, parameters={self.parameters}, reactions={self.reactions}, initial_condition={self.initial_condition}, boundary_condition={self.boundary_condition}, data_functions={self.data_functions}, domain={self.domain}, timespan={self.timespan})"

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        return False; #TODO

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
            raise ModelError(f"Unsupported component: {type(components)} is not a valid component.")
        return components


    def add_domain(self, domain, allow_all_types=False):
        """
        Add a spatial domain to the model

        :param domain: The Domain object to be added to the model
        :type domain: gillespy3d.core.domain.Domain

        :raises ModelError: Invalid Domain object
        """
        if not (isinstance(domain, Domain) or type(domain).__name__ == "Domain"):
            raise ModelError(Exception(f"Invalid Domain object, invalid input of type: {type(domain)}"))

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
                raise ModelError(f"Invalid Species object, invalid input of type: {type(species).__name__}")
            if Species.validate(species):
                raise ModelError("Species.validate failed")
            self.species.append(species)
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
            errmsg = f"init_cond must be of type InitialCondition or list of InitialCondition not {type(init_cond)}"
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
            if not ((isinstance(parameters,Parameter)) or type(parameters).__name__ == "Parameter"):
                raise ModelError(f"Invalid Parameter object, invalid input of type: {type(parameters).__name__}")
            if Parameter.validate(parameters):
                raise ModelError("Species.validate failed")
            self.parameters.append(parameters)
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
            if not ((isinstance(reactions,Reaction)) or type(reactions).__name__ == "Reaction"):
                raise ModelError(f"Invalid Reaction object, invalid input of type: {type(reactions).__name__}")
            if Reaction.validate(reactions):
                raise ModelError("Species.validate failed")
            self.reactions.append(reactions)
  
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
            errmsg = f"bound_cond must be of type BoundaryCondition or list of BoundaryCondition not {type(bound_cond)}"
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
            errmsg = f"data_function must be of type DataFunction or list of DataFunction not {type(data_function)}"
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
            raise ModelError(f"time_span must be of type TimeSpan or evenly space list of times not {type(time_span)}")

    def _sanitized_species_names(self):
        """
        Generate a dictionary mapping user chosen species names to simplified formats which will be used
        later on by GillesPySolvers evaluating reaction propensity functions.

        :returns: the dictionary mapping user species names to their internal GillesPy notation.
        """
        species_name_mapping = OrderedDict([])
        for i, name in enumerate(self.species):
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
        for i, name in enumerate(self.parameters):
            if name not in parameter_name_mapping:
                parameter_name_mapping[name] = f'P{i}'
        return parameter_name_mapping


    def run(self, number_of_trajectories=1, seed=None):
        """
        Simulate the model. Returns a result object containing simulation results.

        :param number_of_trajectories: How many trajectories should be run.
        :type number_of_trajectories: int

        :param seed: The random seed given to the solver.
        :type seed: int

        :returns: A GillesPy3D Result object containing simulation data.
        :rtype: gillespy3d.core.result.Result
        """
        if seed is None: 
            seed = randint(1, 100000000)

        # For now, just return a single result
        return Result(self, seed)


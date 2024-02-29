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

#This module defines a model that simulates a discrete, stoachastic, mixed biochemical reaction network in python.


from gillespy3d.core.domain import Domain
from gillespy3d.core.species import Species
from gillespy3d.core.initialcondition import (
    InitialCondition,
    PlaceInitialCondition,
    ScatterInitialCondition,
    UniformInitialCondition
)
from gillespy3d.core.parameter import Parameter
from gillespy3d.core.reaction import Reaction
from gillespy3d.core.boundarycondition import BoundaryCondition
from gillespy3d.core.datafunction import DataFunction
from gillespy3d.core.timespan import TimeSpan
from gillespy3d.solvers.build_expression import BuildExpression
from gillespy3d.core.error import ModelError

import libcgillespy3d


class Model(libcgillespy3d.Model):
    """
    Representation of a spatial biochemical model.

    :param name: Name of the model
    :type name: str
    """

    def __init__(self, name="gillespy3d"):
        super().__init__(name)

    def __str__(self):
        return ""

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        return False; #TODO

    def add(self, components):
        """
        Adds a component, or list of components to the model. If a list is provided, Species
        and Parameters are added before other components.  Lists may contain any combination
        of accepted types other than lists and do not need to be in any particular order.

        :param components: The component or list of components to be added the the model.
        :type components: Species, Parameters, Reactions, Domain, Data Function, \
                          Initial Conditions, Boundary Conditions, and TimeSpan or list

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
                if isinstance(component, Species) or type(component).__name__ in Species.__name__:
                    self.add_species(component)
                elif isinstance(component, Parameter) or type(component).__name__ in Parameter.__name__:
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
            self.timespan(components)
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
        if not isinstance(domain, Domain) and type(domain).__name__ != Domain.__name__:
            raise ModelError(
                "Unexpected parameter for add_domain. Parameter must be of type GillesPy3D.Domain."
            )

        super().add_domain(domain)
        return domain

    def add_species(self, species):
        """
        Adds a species, or list of species to the model.

        :param species: The species or list of species to be added to the model object.
        :type species: gillespy3d.core.species.Species | list(gillespy3d.core.species.Species

        :returns: The species or list of species that were added to the model.
        :rtype: gillespy3d.core.species.Species | list(gillespy3d.core.species.Species)

        :raises ModelError: If an invalid species is provided or if Species.validate fails.
        """

        if isinstance(species, list):
            for spec in species:
               self.add_species(spec)
        else:
            try:
                super().add_species(species)
            except TypeError as e:
                print(f"ERROR: {e}")
                errmsg = f"species must be of type Species or list of Species not {type(species)}"
                raise ModelError(errmsg) from e
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
                super().add_initial_condition(initial_condition)
        elif isinstance(init_cond, InitialCondition) or type(init_cond).__name__ in names:
            super().add_initial_condition(init_cond)
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
            for param in parameters:
                super().add_parameter(param)
        elif isinstance(parameters, Parameter) or type(parameters).__name__ == 'Parameter':
            super().add_parameter(parameters)
        else:
            errmsg = f"parameters must be of type Parameter or list of Parameter not {type(parameters)}"
            raise ModelError(errmsg)
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
            for reaction in reactions:
                super().add_reaction(reaction)
        elif isinstance(reactions, Reaction) or type(reactions).__name__ == "Reaction":
            super().add_reaction(reactions)
        else:
            errmsg = f"reactions must be of type Reaction or list of Reaction not {type(reactions)}"
            raise ModelError(errmsg)
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
                super().add_boundary_condition(boundary_condition)
        elif isinstance(bound_cond, BoundaryCondition) or type(bound_cond).__name__ in "BoundaryCondition":
            super().add_boundary_condition(bound_cond)
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
                super().add_data_function(data_fn)
        elif isinstance(data_function, DataFunction) or type(data_function).__name__ == 'DataFunction':
            super().add_data_function(data_function)
        else:
            errmsg = f"data_function must be of type DataFunction or list of DataFunction not {type(data_function)}"
            raise ModelError(errmsg)
        return data_function

    def timespan(self, time_span, timestep_size=None):
        self.add_timespan(time_span, timestep_size)

    def add_timespan(self, time_span, timestep_size=None):
        """
        Set the time span of simulation. The SSA-SDPD engine does not support
        non-uniform timespans.

        :param tspan: Evenly-spaced list of times at which to sample the species populations during the simulation.
        :type tspan: numpy.ndarray

        :param timestep_size: Size of each timestep in seconds
        :type timestep_size: float
        """
        if isinstance(time_span, TimeSpan) or type(time_span).__name__ == "TimeSpan":
            super().add_timespan(time_span)
        else:
            super().add_timespan(TimeSpan(time_span, timestep_size))

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


        return Result(super().run(number_of_trajectories,seed))
              

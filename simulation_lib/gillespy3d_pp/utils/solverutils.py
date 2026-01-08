# GillesPy2 is a modeling toolkit for biochemical simulation.
# Copyright (C) 2019-2024 GillesPy2 developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ast  # for dependency graphing
import numpy as np
from gillespy3d_pp.core.species import Species
from gillespy3d_pp.core.error import ModelError

"""
NUMPY SOLVER UTILITIES BELOW
"""

def numpy_initialization(model):
    species_mappings = model._sanitized_species_names()
    species = list(species_mappings.keys())
    parameter_mappings = model._sanitized_parameter_names()
    number_species = len(species)
    return species_mappings, species, parameter_mappings, number_species


def species_parse(model, custom_prop_fun):
    """
    This function uses Pythons AST module to parse custom propensity function, looking for Species in a model

    :param model: Model to be checked for species
    :param custom_prop_fun: The custom propensity function to be parsed

    :returns: List of species objects that are found in a custom propensity function
    """
    parsed_species = []

    class SpeciesParser(ast.NodeTransformer):
        def visit_Name(self, node):
            try:
                if isinstance(model.get_element(node.id), Species):
                    parsed_species.append(model.get_element(node.id))
            except ModelError:
                pass

    expr = custom_prop_fun
    expr = ast.parse(expr, mode='eval')
    expr = SpeciesParser().visit(expr)
    return parsed_species


def dependency_grapher(model, reactions):
    """
    This function returns a dependency graph for a models reactions in the form of a
    dictionary containing {species name: {'dependencies'}:[list of reaction names]}.

    :param model: Model to used to create a reaction dependency graph
    :param reactions: list[model.listOfReactions]

    :returns: Dependency graph dictionary
    """
    dependent_rxns = {}
    for i in reactions:
        cust_spec = []
        if model.listOfReactions[i].type == 'customized':
            cust_spec = (species_parse(model, model.listOfReactions[i].propensity_function))

        for j in reactions:

            if i not in dependent_rxns:
                dependent_rxns[i] = {'dependencies': []}
            if j not in dependent_rxns:
                dependent_rxns[j] = {'dependencies': []}
            if i == j:
                continue

            reactantsI = list(model.listOfReactions[i].reactants.keys())
            reactantsJ = list(model.listOfReactions[j].reactants.keys())

            if j not in dependent_rxns[i]['dependencies']:
                if any(elem in reactantsI for elem in reactantsJ):
                    if i not in dependent_rxns[j]['dependencies']:
                        dependent_rxns[j]['dependencies'].append(i)
                    dependent_rxns[i]['dependencies'].append(j)

            if i not in dependent_rxns[j]['dependencies']:
                if any(elem in list(model.listOfReactions[i].products.keys()) for elem in
                       list(model.listOfReactions[j].reactants.keys())):
                    dependent_rxns[j]['dependencies'].append(i)

            if cust_spec:
                if any(elem in cust_spec for elem in list(model.listOfReactions[j].reactants)) or any \
                            (elem in cust_spec for elem in list(model.listOfReactions[j].products)):
                    dependent_rxns[i]['dependencies'].append(j)

    return dependent_rxns

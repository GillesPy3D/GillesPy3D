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
import os
import numpy as np
from datetime import datetime
from collections import UserDict, UserList
import matplotlib.pyplot as plt  # pylint: disable=import-outside-toplevel


def common_rgb_values():
    '''
    List of 50 hex color values used for plotting graphs
    '''
    return [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
        '#bcbd22', '#17becf', '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#00ffff', '#ff00ff',
        '#800000', '#808000', '#008000', '#800080', '#008080', '#000080', '#ff9999', '#ffcc99',
        '#ccff99', '#cc99ff', '#ffccff', '#62666a', '#8896bb', '#77a096', '#9d5a6c', '#9d5a6c',
        '#eabc75', '#ff9600', '#885300', '#9172ad', '#a1b9c4', '#18749b', '#dadecf', '#c5b8a8',
        '#000117', '#13a8fe', '#cf0060', '#04354b', '#0297a0', '#037665', '#eed284', '#442244',
        '#ffddee', '#702afb'
    ]


def _plot_iterate(self, show_labels=True, included_species_list=[]):
    for i, species in enumerate(self.data):
        if species != 'time':

            if species not in included_species_list and included_species_list:
                continue

            line_color = common_rgb_values()[(
                i - 1) % len(common_rgb_values())]

            if show_labels:
                label = species
            else:
                label = ""

            plt.plot(self.data['time'], self.data[species],
                     label=label, color=line_color)


class Trajectory(UserDict):
    """ Trajectory Dict created by a gillespy3 solver containing single trajectory, extends the UserDict object.

    :param data: A dictionary of trajectory values created by a solver
    :type data: UserDict

    :param model: The name of the model used to create the trajectory
    :type model: str

    :param solver_name: The name of the solver used to create the trajectory
    :type solver_name: str

    :param rc: The solvers status return code.
    :type rc: int

    :param status: The solver status ('Success','Timed out')
    """

    def __init__(self, data, model=None, solver_name="Undefined solver name", rc=0):

        self.data = data
        self.model = model
        self.solver_name = solver_name
        self.rc = rc

        status_list = {0: 'Success', 33: 'Timed Out'}
        self.status = status_list[rc]

    def __getitem__(self, key):
        if isinstance(key, int):
            from gillespy3d_pp.core import log  # pylint: disable=import-outside-toplevel
            species = list(self.data.keys())[key]
            msg = "Trajectory is of type dictionary."
            msg += f"Use trajectory['[{species}]'] instead of trajectory[{
                key}]['{species}']"
            msg += f"Retrieving trajectory['[{species}]']"
            log.warning(msg)
            return self.data[species]
        if key in self.data:
            return self.data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)  # type: ignore
        raise KeyError(key)


class Result(UserList):
    """
    List of Trajectory objects created by a gillespy2 solver, extends the UserList object.

    :param data: A list of trajectory objects
    :type data: UserList
    """

    def __init__(self, data):
        self.data = data

    def __getattribute__(self, key):
        if key in ('model', 'solver_name', 'rc', 'status'):
            if len(self.data) > 1:
                from gillespy3d_pp.core import log  # pylint: disable=import-outside-toplevel
                msg = f"Results is of type list. Use results[i]['{
                    key}'] instead of results['{key}']"
                log.warning(msg)
            return getattr(Result.__getattribute__(self, key='data')[0], key)
        return UserList.__getattribute__(self, key)

    def __add__(self, other):
        combined_data = Result(data=(self.data + other.data))
        consistent_solver = combined_data._validate_solver()
        consistent_model = combined_data._validate_model()

        if not consistent_solver:
            from gillespy3d_pp.core import log  # pylint: disable=import-outside-toplevel
            log.warning(
                "Results objects contain Trajectory objects from multiple solvers.")

        if not consistent_model:
            raise ResultError(
                'Result objects contain Trajectory objects from multiple models.')

        return combined_data

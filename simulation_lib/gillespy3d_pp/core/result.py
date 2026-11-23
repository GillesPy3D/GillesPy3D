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
from gillespy3d_pp.core.error import ResultError
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
    """
    Helper class for plot method to make labels on first run
    """
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


class Trajectory():
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

    def __init__(self, num_species, num_timepoints, species_names, timeline):
        self.num_species = num_species
        self.num_timepoints = num_timepoints
        self.species_names = species_names
        self.timeline = timeline
        self.data = np.zeros((num_species, num_timepoints))
        self.nextRecordedDataIndex = 0

    def reset(self):
        self.data = np.zeros((self.num_species, self.num_timepoints))
        self.nextRecordedDataIndex = 0

    def record_state(self, curr_state):
        ind = 0
        tempData = []
        for i in curr_state.values():
            tempData.append(i)
            ind += 1

        self.data[:, self.nextRecordedDataIndex] = np.array(tempData)
        # print(tempData)

        self.nextRecordedDataIndex += 1

        # self.data[self.nextRecordedDataIndex,:] = curr_state.values()
        # self.nextRecordedDataIndex +=1

        # call record state in sim loop, then increment nextRecordedDataIndex

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

    def __getitem__(self, key):
        if key == 'data':
            return UserList.__getitem__(self, key)
        if isinstance(key, str):
            if len(self.data) > 1:
                from gillespy3d_pp.core import log  # pylint: disable=import-outside-toplevel
                msg = f"Results is of type list. Use results[i]['{
                    key}'] instead of results['{key}']"
                log.warning(msg)
            return self.data[0][key]
        return UserList.__getitem__(self, key)

    def __add__(self, other):
        combined_data = Result(data=(self.data + other.data))  # type:ignore
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

    def _validate_solver(self, reference=None):
        is_valid = True
        if reference is None:
            is_valid = False
        return is_valid

    def _validate_model(self, reference=None):
        is_valid = True
        if reference is None:
            is_valid = False
        return is_valid

    def add_trajectory(self, trajectory):
        self.data.append(trajectory)

    def to_ensemble(self):
        """
        Build an :class:`Ensemble` from this Result's trajectories.
        """
        return Ensemble(self.data)

    def plot(self, included_species=None, title=None, show_legend=True):
        """
        Plot all species populations over time for every trajectory in the result.

        :param included_species: If provided, only plot species whose names are in this list.
        :type included_species: list[str] | None

        :param title: Optional title for the plot.
        :type title: str | None

        :param show_legend: Whether to display the legend. Default True.
        :type show_legend: bool
        """
        if not self.data:
            return

        colors = common_rgb_values()
        fig, ax = plt.subplots()

        first_traj = self.data[0]
        species_names = first_traj.species_names
        timeline = first_traj.timeline
        multi = len(self.data) > 1

        for i, name in enumerate(species_names):
            if included_species and name not in included_species:
                continue
            color = colors[i % len(colors)]
            for traj_idx, traj in enumerate(self.data):
                ax.plot(
                    timeline,
                    traj.data[i],
                    label=name if traj_idx == 0 else None,
                    color=color,
                    alpha=0.9 if traj_idx == 0 else 0.2,
                )

        ax.set_xlabel("Time")
        ax.set_ylabel("Molecule Count")
        if title:
            ax.set_title(title)
        if show_legend:
            ax.legend()
        plt.tight_layout()
        plt.show()


class Ensemble():
    """
    Accumulator for trajectories collected across one or many simulations.

    The Ensemble stores trajectory data in a 3D array of shape
    ``(num_trajs, num_species, num_timepoints)`` and exposes a :meth:`mean`
    helper so callers can compute a mean ensemble after running an arbitrary
    number of simulations.

    :param trajectories: Initial trajectories (a :class:`Result`, a list of
        :class:`Trajectory`, or empty / ``None``). Subsequent batches can be
        added via :meth:`add_trajectory` or :meth:`add_trajectories`.
    :type trajectories: Result | list[Trajectory] | None
    """

    def __init__(self, trajectories=None):
        self.num_trajs = 0
        self.num_species = None
        self.num_timepoints = None
        self.species_names = None
        self.timeline = None
        self._data = []

        if trajectories:
            self.add_trajectories(trajectories)

    @property
    def data(self):
        """Stacked trajectory data, shape ``(num_trajs, num_species, num_timepoints)``."""
        if not self._data:
            return np.empty((0, 0, 0))
        return np.stack(self._data, axis=0)

    def _adopt_shape_from(self, trajectory):
        self.num_species = trajectory.num_species
        self.num_timepoints = trajectory.num_timepoints
        self.species_names = list(trajectory.species_names)
        self.timeline = np.asarray(trajectory.timeline)

    def _validate_shape(self, trajectory):
        if trajectory.num_species != self.num_species:
            raise ResultError(
                f"Trajectory has {trajectory.num_species} species, "
                f"ensemble expects {self.num_species}."
            )
        if trajectory.num_timepoints != self.num_timepoints:
            raise ResultError(
                f"Trajectory has {trajectory.num_timepoints} timepoints, "
                f"ensemble expects {self.num_timepoints}."
            )

    def add_trajectory(self, trajectory):
        """Append a single :class:`Trajectory` to the ensemble."""
        if self.num_species is None:
            self._adopt_shape_from(trajectory)
        else:
            self._validate_shape(trajectory)
        self._data.append(np.asarray(trajectory.data, dtype=float).copy())
        self.num_trajs += 1

    def add_trajectories(self, trajectories):
        """Append every trajectory in a :class:`Result` or iterable."""
        for traj in trajectories:
            self.add_trajectory(traj)

    def mean(self):
        """
        Mean across trajectories at each timepoint.

        :returns: array of shape ``(num_species, num_timepoints)``.
        """
        if self.num_trajs == 0:
            raise ResultError("Ensemble is empty; cannot compute mean.")
        return self.data.mean(axis=0)

    def std(self):
        """Standard deviation across trajectories, shape ``(num_species, num_timepoints)``."""
        if self.num_trajs == 0:
            raise ResultError("Ensemble is empty; cannot compute std.")
        return self.data.std(axis=0)

    def plot_mean(self, included_species=None, title=None, show_legend=True, show_band=False):
        """
        Plot the mean trajectory per species.

        :param included_species: Optional list of species names to include.
        :param show_band: If True, shade ±1 std around the mean.
        """
        if self.num_trajs == 0:
            return

        colors = common_rgb_values()
        fig, ax = plt.subplots()
        mean = self.mean()
        sd = self.std() if show_band else None

        for i, name in enumerate(self.species_names):
            if included_species and name not in included_species:
                continue
            color = colors[i % len(colors)]
            ax.plot(self.timeline, mean[i], label=name, color=color)
            if show_band:
                ax.fill_between(
                    self.timeline,
                    mean[i] - sd[i],
                    mean[i] + sd[i],
                    color=color,
                    alpha=0.2,
                )

        ax.set_xlabel("Time")
        ax.set_ylabel("Mean Molecule Count")
        if title:
            ax.set_title(title)
        if show_legend:
            ax.legend()
        plt.tight_layout()
        plt.show()


def build_ensemble(trajectories):
    """
    Build an :class:`Ensemble` from a :class:`Result` or list of trajectories.

    Convenience wrapper around ``Ensemble(trajectories)`` for use in scripts
    and notebooks where the call site reads better as a function.
    """
    return Ensemble(trajectories)

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

# Base Module Expections
class ModelError(Exception):
    """
    Class for exceptions in the model module.
    """

class SimulationError(Exception):
    """
    Class for exceptions in the simulation module.
    """

class ParameterError(ModelError):
    """
    Class for exceptions in parameter module.
    """

class ReactionError(ModelError):
    """
    Class for exceptions in reaction module.
    """

class SpeciesError(ModelError):
    """
    Class for exceptions in the species module.
    """

class TimespanError(ModelError):
    """
    Class for exceptions in the timespan module.
    """
class NumPySSASolverError(ModelError):
    """
    Class for exceptions in the NumPySSASolver module.
    """


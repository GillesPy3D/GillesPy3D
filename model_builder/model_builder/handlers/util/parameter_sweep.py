'''
GillesPy3D is a platform for simulating biochemical systems
Copyright (C) 2025 GillesPy3D developers.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import json
import numpy
import pickle
import logging
import traceback

import numpy

from gillespy2 import TimeSpan

from .model_builder_job import GillesPy3DJob
from .parameter_sweep_1d import ParameterSweep1D
from .parameter_sweep_2d import ParameterSweep2D
from .parameter_scan import ParameterScan
from .model_builder_errors import GillesPy3DJobResultsError, GillesPy3DJobError

log = logging.getLogger("gillespy3d")

class NumpyEncoder(json.JSONEncoder):
    '''
    ################################################################################################
    Custom json encoder for numpy ndarrays
    ################################################################################################
    '''
    def default(self, o):
        if isinstance(o, numpy.ndarray):
            return o.tolist()
        return json.JSONEncoder.default(self, o)


class ParameterSweep(GillesPy3DJob):
    '''
    ################################################################################################
    GillesPy3D parameter sweep job object
    ################################################################################################
    '''

    TYPE = "parameterSweep"

    def __init__(self, path):
        '''
        Intitialize an parameter sweep job object

        Attributes
        ----------
        path : str
            Path to the parameter sweep job
        '''
        super().__init__(path=path)
        self.g_model, self.s_model = self.load_models()
        self.settings = self.load_settings()


    def __get_run_settings(self):
        if self.settings['simulationSettings']['isAutomatic']:
            solver = self.g_model.get_best_solver()
            kwargs = {"number_of_trajectories":1 if "ODE" in solver.name else 20}
            if "CSolver" not in solver.name:
                return kwargs
            kwargs['solver'] = solver(model=self.g_model)
            return kwargs
        solver_map = {"ODE":self.g_model.get_best_solver_algo("ODE"),
                      "SSA":self.g_model.get_best_solver_algo("SSA"),
                      "CLE":self.g_model.get_best_solver_algo("CLE"),
                      "Tau-Leaping":self.g_model.get_best_solver_algo("Tau-Leaping"),
                      "Hybrid-Tau-Leaping":self.g_model.get_best_solver_algo("Tau-Leaping")}
        run_settings = self.get_run_settings(settings=self.settings, solver_map=solver_map)
        if "CSolver" in run_settings['solver'].name:
            run_settings['solver'] = run_settings['solver'](model=self.g_model)
        return run_settings


    @classmethod
    def __report_result_error(cls, trace):
        message = "An unexpected error occured with the result object"
        raise GillesPy3DJobResultsError(message, trace)


    @classmethod
    def __store_pickled_results(cls, job):
        try:
            with open('results/results.p', 'wb') as results_file:
                pickle.dump(job.ts_results, results_file)
        except Exception as err:
            message = f"Error storing pickled results: {err}\n{traceback.format_exc()}"
            log.error(message)
            return message
        return False


    def configure(self):
        '''
        Get the configuration arguments for 1D or 2D parameter sweep

        Attributes
        ----------
        '''
        run_settings = self.__get_run_settings()
        if "timespanSettings" in self.settings.keys():
            keys = self.settings['timespanSettings'].keys()
            if "endSim" in keys and "timeStep" in keys:
                end = self.settings['timespanSettings']['endSim']
                step_size = self.settings['timespanSettings']['timeStep']
                self.g_model.timespan(
                    TimeSpan.arange(step_size, t=end + step_size)
                )
        kwargs = {"model":self.g_model, "settings":run_settings}
        parameters = []
        for param in self.settings['parameterSweepSettings']['parameters']:
            p_range = numpy.linspace(param['min'], param['max'], param['steps'])
            parameters.append({"parameter":param['name'], "range":p_range})
        if len(parameters) > 1:
            kwargs['params'] = parameters
            return kwargs
        kwargs["param"] = parameters[0]
        return kwargs


    def run(self, verbose=True):
        '''
        Run a 1D or 2D parameter sweep job

        Attributes
        ----------
        verbose : bool
            Indicates whether or not to print debug statements
        '''
        kwargs = self.configure()
        if "param" in kwargs:
            job = ParameterSweep1D(**kwargs)
            sim_type = "1D parameter sweep"
        elif len(kwargs['params']) > 2:
            sim_type = "parameter scan"
            job = ParameterScan(**kwargs)
        else:
            sim_type = "2D parameter sweep"
            job = ParameterSweep2D(**kwargs)
        if verbose:
            log.info(f"Running the {sim_type}")
        job.run(job_id=self.get_file(), verbose=verbose)
        if not job.ts_results:
            message = "All simulations failed to complete."
            raise GillesPy3DJobError(message)
        if verbose:
            log.info(f"The {sim_type} has completed")
            log.info("Storing the results as pickle.")
        if not 'results' in os.listdir():
            os.mkdir('results')
        pkl_err = self.__store_pickled_results(job=job)
        if pkl_err:
            self.__report_result_error(trace=pkl_err)

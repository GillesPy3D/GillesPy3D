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
import copy
import pickle
import logging
import traceback

import gillespy2
from stochss_compute import RemoteSimulation

from .model_builder_job import GillesPy3DJob
from .model_builder_errors import GillesPy3DAPIError, GillesPy3DFileNotFoundError, GillesPy3DJobResultsError

log = logging.getLogger("gillespy3d")

class EnsembleSimulation(GillesPy3DJob):
    '''
    ################################################################################################
    GillesPy3D ensemble simulation job object
    ################################################################################################
    '''

    TYPE = "gillespy"

    def __init__(self, path, preview=False):
        '''
        Intitialize an ensemble simulation job object

        Attributes
        ----------
        path : str
            Path to the ensemble simulation job
        '''
        super().__init__(path=path)
        if not preview:
            try:
                self.settings = self.load_settings()
                self.g_model, self.s_model = self.load_models()
            except GillesPy3DAPIError as err:
                log.error(str(err))


    def __get_run_settings(self):
        solver_map = {"ODE":self.g_model.get_best_solver_algo("ODE"),
                      "SSA":self.g_model.get_best_solver_algo("SSA"),
                      "CLE":self.g_model.get_best_solver_algo("CLE"),
                      "Tau-Leaping":self.g_model.get_best_solver_algo("Tau-Leaping"),
                      "Hybrid-Tau-Leaping":self.g_model.get_best_solver_algo("Tau-Hybrid")}
        run_settings = self.get_run_settings(settings=self.settings, solver_map=solver_map)
        instance_solvers = ["ODECSolver", "SSACSolver", "TauLeapingCSolver", "TauHybridCSolver"]
        if run_settings['solver'].name in instance_solvers :
            run_settings['solver'] = run_settings['solver'](model=self.g_model)
        return run_settings


    @classmethod
    def __store_pickled_results(cls, results):
        try:
            with open('results/results.p', 'wb') as results_file:
                pickle.dump(results, results_file)
        except Exception as err:
            message = f"Error storing pickled results: {err}\n{traceback.format_exc()}"
            log.error(message)
            return message
        return False


    def __update_timespan(self):
        if "timespanSettings" in self.settings.keys():
            keys = self.settings['timespanSettings'].keys()
            if "endSim" in keys and "timeStep" in keys:
                end = self.settings['timespanSettings']['endSim']
                step_size = self.settings['timespanSettings']['timeStep']
                self.g_model.timespan(
                    gillespy2.TimeSpan.arange(step_size, t=end + step_size)
                )

    def __run(self, run_func, preview=False, verbose=True):
        if preview:
            if verbose:
                log.info(f"Running {self.g_model.name} preview simulation")
            live_file = f".{self.g_model.name}-preview.json"
            options = {"file_path": live_file}
            results = self.g_model.run(timeout=60, live_output="graph", live_output_options=options)
            if verbose:
                log.info(f"{self.g_model.name} preview simulation has completed")
                log.info(f"Generate result plot for {self.g_model.name} preview")
            plot = results.plotplotly(return_plotly_figure=True)
            plot["layout"]["autosize"] = True
            plot["config"] = {"responsive": True, "displayModeBar": True}
            return plot
        if self.settings['simulationSettings']['isAutomatic']:
            self.__update_timespan()
            is_ode = self.g_model.get_best_solver().name in ["ODESolver", "ODECSolver"]
            results = run_func(verbose=verbose, number_of_trajectories=1 if is_ode else 100)
        else:
            kwargs = self.__get_run_settings()
            self.__update_timespan()
            results = run_func(verbose=verbose, **kwargs)
        if verbose:
            log.info("The ensemble simulation has completed")
            log.info("Storing the results as pickle")
        if not 'results' in os.listdir():
            os.mkdir('results')
        pkl_err = self.__store_pickled_results(results=results)
        if verbose:
            log.info("Storing the polts of the results")
        if pkl_err:
            message = "An unexpected error occured with the result object"
            trace = str(pkl_err)
            raise GillesPy3DJobResultsError(message, trace)
        return None

    def __run_in_aws(self, verbose=False, **kwargs):
        aws_kwargs = copy.deepcopy(kwargs)
        if 'solver' in kwargs:
            aws_kwargs['solver'] = kwargs['solver'].__class__
        if verbose:
            log.info("Running the ensemble simulation in AWS")

        cluster = self.get_aws_cluster()
        # Run the simulation
        simulation = RemoteSimulation(self.g_model, server=cluster)
        aws_results = simulation.run(**aws_kwargs)
        return aws_results.get_gillespy2_results()

    def __run_local(self, verbose=False, **kwargs):
        if verbose:
            log.info("Running the ensemble simulation locally")
        return self.g_model.run(**kwargs)

    def run(self, preview=False, verbose=True):
        '''
        Run a GillesPy2 ensemble simulation job

        Attributes
        ----------
        preview : bool
            Indicates whether or not to run a 5 sec preivew
        verbose : bool
            Indicates whether or not to print debug statements
        '''
        try:
            compute_env = self.load_info()['compute_env']
        except GillesPy3DFileNotFoundError:
            compute_env = "local"
        if compute_env == 'AWS':
            results = self.__run(self.__run_in_aws, preview=preview, verbose=verbose)
            return results
        return self.__run(self.__run_local, preview=preview, verbose=verbose)

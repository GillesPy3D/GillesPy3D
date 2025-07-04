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
import csv
import json
import shutil
import pickle
import string
import hashlib
import tempfile

import datetime
import traceback

import numpy
import plotly

from escapism import escape

from .model_builder_base import GillesPy3DBase
from .model_builder_model import GillesPy3DModel
from .parameter_sweep_1d import ParameterSweep1D
from .parameter_sweep_2d import ParameterSweep2D
from .model_builder_spatial_model import GillesPy3DSpatialModel
from .model_builder_errors import GillesPy3DFileNotFoundError, GillesPy3DFileExistsError, \
                            FileNotJSONFormatError, PlotNotAvailableError, \
                            GillesPy3DPermissionsError, GillesPy3DJobResultsError

class GillesPy3DJob(GillesPy3DBase):
    '''
    ################################################################################################
    GillesPy3D job object
    ################################################################################################
    '''

    TYPES = {
        "gillespy":"_ES", "spatial":"_SES", "parameterSweep":"_PS", "inference":"_MI"
    }
    TITLES = {
        "gillespy":"Ensemble Simulation", "spatial":"Spatial Ensemble Simulation",
        "parameterSweep":"Parameter Sweep", "inference":"Model Inference"
    }

    def __init__(self, path, new=False, data=None):
        '''
        Intitialize a job object and if its new create it on the users file system

        Attributes
        ----------
        path : str
            Path to the job
        new : bool
            Indicates whether or not the job is new
        data : dict
            Load data needed for loading a job
        '''
        super().__init__(path=path)
        self.job = {}
        self.type = None
        self.time_stamp = None
        if new:
            self.type = data['type']
            self.__create_new_job(
                mdl_path=data['mdl_path'], settings=data['settings'], compute=data['compute_env']
            )


    def __create_new_job(self, mdl_path, settings=None, compute="Local"):
        path = self.get_path(full=True)
        try:
            os.mkdir(path)
            os.mkdir(self.__get_results_path(full=True))
            info = {
                "source_model": mdl_path, "wkfl_model": None, "type": self.type,
                "start_time": None, "compute_env": compute
            }
            self.update_info(new_info=info, new=True)
            with open(os.path.join(path, "logs.txt"), "w", encoding="utf-8") as log_file:
                log_file.close()
            shutil.copyfile(os.path.join(self.user_dir, mdl_path),
                            self.get_model_path(full=True))
            if settings is None:
                self.__create_settings()
            else:
                with open(self.__get_settings_path(full=True), "w",
                                                   encoding="utf-8") as settings_file:
                    json.dump(settings, settings_file)
        except FileExistsError as err:
            message = f"Could not create your job: {str(err)}"
            raise GillesPy3DFileExistsError(message, traceback.format_exc()) from err
        except FileNotFoundError as err:
            message = f"Could not find the file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err


    def __create_settings(self):
        if self.type == "parameterSweep":
            settings = self.get_settings_template()
            settings['simulationSettings']['realizations'] = 20
            with open(self.__get_settings_path(full=True), "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4, sort_keys=True)
        else:
            shutil.copyfile('/model_builder/model_builder_templates/workflowSettingsTemplate.json',
                            self.__get_settings_path(full=True))


    @classmethod
    def __get_csvzip(cls, dirname, name):
        shutil.make_archive(os.path.join(dirname, name), "zip", dirname, name)
        path = os.path.join(dirname, f"{name}.zip")
        with open(path, "rb") as zip_file:
            return zip_file.read()


    def __get_extract_dst_path(self, mdl_file):
        if ".proj" not in self.path:
            wkfl_dirname = os.path.dirname(self.path.replace(self.path.partition(".wkfl")[2], ""))
            return os.path.join(wkfl_dirname, mdl_file)
        proj_path = self.path.replace(self.path.partition(".proj")[2], "")
        if "WorkflowGroup1.wkgp" in self.path:
            return os.path.join(proj_path, mdl_file)
        wkgp_path = self.path.replace(self.path.partition(".wkgp")[2], "")
        has_mdl = len(list(filter(lambda file: file.endswith(".mdl"), os.listdir(wkgp_path)))) > 0
        if has_mdl:
            wkgp_file = f"{self.get_name(path=mdl_file)}.wkgp"
            path, changed = self.get_unique_path(name=wkgp_file, dirname=proj_path)
            if changed:
                mdl_file = f"{self.get_name(path=path)}.{mdl_file.split('.').pop()}"
            return os.path.join(path, mdl_file)
        wkgp_name = self.get_name(path=wkgp_path)
        if wkgp_name != self.get_name(path=mdl_file):
            mdl_file = f"{wkgp_name}.{mdl_file.split('.').pop()}"
        return os.path.join(wkgp_path, mdl_file)


    def __get_filtered_1d_results(self, f_keys):
        results = self.__get_pickled_results()
        f_results = []
        for key, result in results.items():
            if self.__is_result_valid(f_keys, key):
                f_results.append(result)
        return f_results


    def __get_filtered_2d_results(self, f_keys, param):
        results = self.__get_pickled_results()
        f_results = []
        for value in param['range']:
            p_key = f"{param['name']}:{value}"
            p_results = []
            for key, result in results.items():
                if p_key in key.split(',') and self.__is_result_valid(f_keys, key):
                    p_results.append(result)
            f_results.append(p_results)
        return f_results


    def __get_filtered_ensemble_results(self, data_keys):
        result = self.__get_pickled_results()
        if data_keys:
            key = [f"{name}:{value}" for name, value in data_keys.items()]
            key = ','.join(key)
            result = result[key]
        return result


    def __get_full_timeseries_csv(self, b_path, results, get_name, name):
        ts_path = os.path.join(b_path, "Time_Series")
        os.makedirs(ts_path)
        for i, (key, result) in enumerate(results.items()):
            data = [_data.split(':') for _data in key.split(',')]
            data_keys = {_data[0]: _data[1] for _data in data}
            nametag = get_name(name, i)
            self.log("info", f"\tGenerating CSV files for {nametag}...")
            result.to_csv(path=ts_path, nametag=nametag, stamp="")
            self.__write_parameters_csv(path=ts_path, name=nametag, data_keys=data_keys)


    @classmethod
    def __get_fixed_keys_and_dims(cls, settings, fixed):
        p_len = len(settings['parameterSweepSettings']['parameters'])
        dims = p_len - len(fixed.keys())
        if dims <= 0:
            message = "Too many fixed parameters were provided."
            message += "At least one variable parameter is required."
            raise GillesPy3DJobResultsError(message)
        if dims > 2:
            message = "Not enough fixed parameters were provided."
            message += "Variable parameters cannot exceed 2."
            raise GillesPy3DJobResultsError(message)
        f_keys = [f"{name}:{value}" for name, value in fixed.items()]
        return dims, f_keys


    def __get_info_path(self, full=False):
        return os.path.join(self.get_path(full=full), "info.json")


    def __get_pickled_results(self):
        path = os.path.join(self.__get_results_path(full=True), "results.p")
        with open(path, "rb") as results_file:
            return pickle.load(results_file)


    @classmethod
    def __get_presentation_links(cls, file):
        safe_chars = set(string.ascii_letters + string.digits)
        hostname = escape(os.environ.get('JUPYTERHUB_USER'), safe=safe_chars)
        query_str = f"?owner={hostname}&file={file}"
        present_link = f"/model_builder/present-job{query_str}"
        dl_base = "/model_builder/job/download_presentation"
        downloadlink = os.path.join(dl_base, hostname, file)
        open_link = f"https://open.stochss.org?open={downloadlink}"
        links = {"presentation": present_link, "download": downloadlink, "open": open_link}
        return links


    def __get_results_path(self, full=False):
        return os.path.join(self.get_path(full=full), "results")


    def __get_run_logs(self):
        path = os.path.join(self.get_path(full=True), "logs.txt")
        try:
            with open(path, "r", encoding="utf-8") as file:
                logs = file.read()
            self.log("debug", f"Contents of the log file: {logs}")
            if logs:
                return logs
            return "No logs were recoded for this job."
        except FileNotFoundError as err:
            message = f"Could not find the log file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err


    def __get_settings_path(self, full=False):
        return os.path.join(self.get_path(full=full), "settings.json")


    @classmethod
    def __is_result_valid(cls, f_keys, key):
        for f_key in f_keys:
            if f_key not in key.split(','):
                return False
        return True


    def __update_settings_to_current(self):
        settings = self.job['settings']
        if settings['template_version'] == self.SETTINGS_TEMPLATE_VERSION:
            return

        if "parameters" not in settings['parameterSweepSettings']:
            parameters = []
            if "paramID" in settings['parameterSweepSettings']['parameterOne']:
                p1_range = list(numpy.linspace(
                    settings['parameterSweepSettings']['p1Min'],
                    settings['parameterSweepSettings']['p1Max'],
                    settings['parameterSweepSettings']['p1Steps']
                ))
                parameters.append({
                    "paramID": settings['parameterSweepSettings']['parameterOne']['paramID'],
                    "min": settings['parameterSweepSettings']['p1Min'],
                    "max": settings['parameterSweepSettings']['p1Max'],
                    "name": settings['parameterSweepSettings']['parameterOne']['name'],
                    "range" : p1_range,
                    "steps": settings['parameterSweepSettings']['p1Steps'],
                    "hasChangedRanged": False
                })
            if "paramID" in settings['parameterSweepSettings']['parameterTwo']:
                p2_range = list(numpy.linspace(
                    settings['parameterSweepSettings']['p2Min'],
                    settings['parameterSweepSettings']['p2Max'],
                    settings['parameterSweepSettings']['p2Steps']
                ))
                parameters.append({
                    "paramID": settings['parameterSweepSettings']['parameterTwo']['paramID'],
                    "min": settings['parameterSweepSettings']['p2Min'],
                    "max": settings['parameterSweepSettings']['p2Max'],
                    "name": settings['parameterSweepSettings']['parameterTwo']['name'],
                    "range" : p2_range,
                    "steps": settings['parameterSweepSettings']['p2Steps'],
                    "hasChangedRanged": False
                })
            soi = settings['speciesOfInterest']
            settings['parameterSweepSettings'] = {
                "speciesOfInterest": soi, "parameters": parameters
            }

        settings['inferenceSettings'] = {
            "obsData": "", "parameters": [], "priorMethod": "Uniform Prior", "summaryStats": ""
        }
        settings['template_version'] = self.SETTINGS_TEMPLATE_VERSION


    @classmethod
    def __write_parameters_csv(cls, path, name, data_keys):
        csv_path = os.path.join(path, name, "parameters.csv")
        with open(csv_path, "w", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(list(data_keys.keys()))
            csv_writer.writerow(list(data_keys.values()))


    def duplicate_as_new(self, stamp):
        '''
        Get all data needed to create a new job that
        is a copy of this job in ready state.

        Attributes
        ----------
        '''
        wkfl = self.load()
        if wkfl['status'] != "ready":
            mdl_path = self.get_model_path(external=True)
        else:
            mdl_path = wkfl['mdlPath']
        if self.get_time_stamp():
            path = self.path.replace(self.get_time_stamp(), stamp)
        else:
            dirname = self.get_dir_name()
            mdl_name = self.get_name(path=mdl_path)
            path = os.path.join(dirname, f"{mdl_name}{self.TYPES[self.type]}{stamp}.wkfl")
        data = {"type":self.type, "mdl_path":self.get_model_path(), "settings":wkfl['settings']}
        kwargs = {"path": path, "new":True, "data":data}
        resp = {"message":f"A new job has been created from {self.path}",
                "mdlPath":mdl_path,
                "mdl_file":self.get_file(path=mdl_path)}
        return resp, kwargs


    def extract_model(self):
        '''
        Get all data needed to create a new model that is a copy of the jobs model

        Attributes
        ----------
        '''
        src_path = self.get_model_path()
        model = GillesPy3DModel(path=src_path).load()
        dst_path = self.__get_extract_dst_path(mdl_file=self.get_file(path=src_path))
        kwargs = {"path":dst_path, "new":True, "model":model}
        resp = {"message":f"A copy of the model in {self.path} has been created"}
        return resp, kwargs


    def get_csvzip_from_results(self, data_keys, proc_key, name):
        '''
        Get the csv files of the plot data for download.

        Attributes
        ----------
        data_keys : dict
            Dictionary of param names and values used to identify the correct data.
        proc_key : str
            Type post processing to preform.
        name : str
            Name of the csv directory
        '''
        try:
            self.log("info", "Getting job results...")
            result = self.__get_filtered_ensemble_results(data_keys)
            self.log("info", "Processing results...")
            if proc_key == "stddev":
                result = result.stddev_ensemble()
            elif proc_key == "avg":
                result = result.average_ensemble()
            self.log("info", "Generating CSV files...")
            with tempfile.TemporaryDirectory() as tmp_dir:
                if hasattr(result, "to_csv"):
                    result.to_csv(path=tmp_dir, nametag=name, stamp="")
                    if data_keys:
                        self.__write_parameters_csv(path=tmp_dir, name=name, data_keys=data_keys)
                else:
                    result.export_to_csv(folder_name=os.path.join(tmp_dir, name))
                self.log("info", "Generating zip archive...")
                return self.__get_csvzip(dirname=tmp_dir, name=name)
        except FileNotFoundError as err:
            message = f"Could not find the results pickle file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err
        except KeyError as err:
            message = f"The requested results are not available: {str(err)}"
            raise PlotNotAvailableError(message, traceback.format_exc()) from err


    def get_full_csvzip_from_results(self, name):
        '''
        Get the csv files for the full set of results data

        Attributes
        ----------
        name : str
            Name of the csv directory.
        '''
        self.log("info", "Getting job results...")
        results = self.__get_pickled_results()
        with tempfile.TemporaryDirectory() as tmp_dir:
            if not isinstance(results, dict):
                self.log("info", "Generating CSV files...")
                if hasattr(results, "to_csv"):
                    results.to_csv(path=tmp_dir, nametag=name, stamp="")
                else:
                    results.export_to_csv(folder_name=os.path.join(tmp_dir, name))
                self.log("info", "Generating zip archive...")
                return self.__get_csvzip(dirname=tmp_dir, name=name)
            def get_name(b_name, tag):
                return f"{b_name}_{tag}"
            b_path = os.path.join(tmp_dir, get_name(name, "full"))
            self.log("info", "Generating time series CSV files...")
            self.__get_full_timeseries_csv(b_path, results, get_name, name)
            return self.__get_csvzip(dirname=tmp_dir, name=get_name(name, "full"))


    def get_model_path(self, full=False, external=False):
        '''
        Return the path to the model file

        Attributes
        ----------
        full : bool
            Indicates whether or not to get the full path or local path
        external : bool
            Indicates whether or not to consider the path to the internal model
        '''
        info = self.load_info()
        self.log("debug", f"Job info: {info}")
        if external:
            if '.proj' not in self.path:
                return info['source_model']
            file = self.get_file(path=info['source_model'])
            proj_path = f"{self.path.split('.proj')[0]}.proj"
            if self.check_project_format(path=proj_path):
                return os.path.join(self.get_dir_name(), file)
            return os.path.join(proj_path, file)
        if info['wkfl_model'] is None:
            file = self.get_file(path=info['source_model'])
            return os.path.join(self.get_path(full=full), file)
        file = self.get_file(path=info['wkfl_model'])
        return os.path.join(self.get_path(full=full), file)


    def get_notebook_data(self):
        '''
        Get the needed data for converting to notebook

        Attributes
        ----------
        '''
        info = self.load_info()
        file = f"{self.get_name()}.ipynb"
        dirname = self.get_dir_name()
        if ".wkfl" in dirname:
            codes = {"gillespy": "_ES", "spatial": "_SES", "parameterSweep": "_PS", "inference": "_MI"}
            code = codes[info['type']]
            wkfl_name = self.get_name(path=dirname).replace(code, "_NB")
            file = f"{wkfl_name}_{file}"
            dirname = os.path.dirname(dirname)
        path = os.path.join(dirname, file)
        g_model, s_model = self.load_models()
        settings = self.load_settings()
        if info['type'] in ("gillespy", "spatial", "inference"):
            wkfl_type = info['type']
        elif info['type'] == "parameterSweep" and \
                    len(settings['parameterSweepSettings']['parameters']) == 1:
            wkfl_type = "1d_parameter_sweep"
        else:
            wkfl_type = "2d_parameter_sweep"
        kwargs = {"path":path, "new":True, "settings":settings,
                  "models":{"s_model":s_model, "model":g_model}}
        results_path = os.path.join(self.__get_results_path(), "results.p")
        return {
            "kwargs":kwargs, "type":wkfl_type, "results": results_path, "compute_env": info['compute_env']
        }


    def get_plot_from_results(self, data_keys, plt_key, add_config=False):
        '''
        Get the plotly figure for the results of a job

        Attributes
        ----------
        data_keys : dict
            Dictionary of param names and values used to identify the correct data.
        plt_key : str
            Type of plot to generate.
        '''
        self.log("debug", f"Key identifying the plot to generate: {plt_key}")
        try:
            self.log("info", "Loading the results...")
            result = self.__get_filtered_ensemble_results(data_keys)
            self.log("info", "Generating the plot...")
            if plt_key == "mltplplt":
                fig = result.plotplotly(return_plotly_figure=True, multiple_graphs=True)
            elif plt_key == "stddevran":
                fig = result.plotplotly_mean_stdev(return_plotly_figure=True)
            else:
                if plt_key == "stddev":
                    result = result.stddev_ensemble()
                elif plt_key == "avg":
                    result = result.average_ensemble()
                fig = result.plotplotly(return_plotly_figure=True)
            if add_config and plt_key != "mltplplt":
                fig["config"] = {"responsive":True}
            self.log("info", "Loading the plot...")
            return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
        except FileNotFoundError as err:
            message = f"Could not find the results pickle file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err
        except KeyError as err:
            message = f"The requested plot is not available: {str(err)}"
            raise PlotNotAvailableError(message, traceback.format_exc()) from err

    def get_plot_from_spatial_results(self, data_keys, add_config=False):
        '''
        Get the plotly figure for the results of a job

        Attributes
        ----------
        data_keys : dict
            Dictionary of param names and values used to identify the correct data.
        add_config : bool
            Whether or not to add plotly config settings.
        '''
        try:
            self.log("info", "Loading the results...")
            result = self.__get_filtered_ensemble_results(None)
            self.log("info", "Generating the plot...")
            if data_keys['target'] in ("type", "nu", "rho", "mass"):
                fig = result[data_keys['trajectory']].plot_property(
                    data_keys['target'], width="auto", height="auto", animated=True,
                    return_plotly_figure=True
                )
            elif data_keys['target'] == "v":
                fig = result[data_keys['trajectory']].plot_property(
                    data_keys['target'], p_ndx=data_keys['index'], width="auto", height="auto",
                    animated=True, return_plotly_figure=True
                )
            else:
                concentration = data_keys['mode'] == "discrete-concentration"
                deterministic = data_keys['mode'] == "continuous"
                fig = result[data_keys['trajectory']].plot_species(
                    data_keys['target'], concentration=concentration, deterministic=deterministic,
                    width="auto", height="auto", animated=True, return_plotly_figure=True
                )
            if add_config:
                fig['config'] = {"responsive": True}
            self.log("info", "Loading the plot...")
            return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
        except FileNotFoundError as err:
            message = f"Could not find the results pickle file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err
        except KeyError as err:
            message = f"The requested plot is not available: {str(err)}"
            raise PlotNotAvailableError(message, traceback.format_exc()) from err

    def get_psweep_csvzip_from_results(self, fixed, name):
        '''
        Get the csv file of the parameter sweep plot data for download

        Attributes
        ----------
        fixed : dict
            Dictionary for parameters that remain at a fixed value.
        '''
        settings = self.load_settings()
        try:
            self.log("info", "Loading job results...")
            dims, f_keys = self.__get_fixed_keys_and_dims(settings, fixed)
            params = list(filter(lambda param: param['name'] not in fixed.keys(),
                                 settings['parameterSweepSettings']['parameters']))
            with tempfile.TemporaryDirectory() as tmp_dir:
                if dims == 1:
                    kwargs = {"results": self.__get_filtered_1d_results(f_keys)}
                    kwargs["species"] = list(kwargs['results'][0][0].model.listOfSpecies.keys())
                    self.log("info", "Generating CSV files...")
                    ParameterSweep1D.to_csv(
                        param=params[0], kwargs=kwargs, path=tmp_dir, nametag=name
                    )
                else:
                    kwargs = {"results": self.__get_filtered_2d_results(f_keys, params[0])}
                    kwargs["species"] = list(kwargs['results'][0][0][0].model.listOfSpecies.keys())
                    self.log("info", "Generating CSV files...")
                    ParameterSweep2D.to_csv(
                        params=params, kwargs=kwargs, path=tmp_dir, nametag=name
                    )
                if fixed:
                    self.__write_parameters_csv(path=tmp_dir, name=name, data_keys=fixed)
                return self.__get_csvzip(dirname=tmp_dir, name=name)
        except FileNotFoundError as err:
            message = f"Could not find the results pickle file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err
        except KeyError as err:
            message = f"The requested results are not available: {str(err)}"
            raise PlotNotAvailableError(message, traceback.format_exc()) from err


    def get_psweep_plot_from_results(self, fixed, kwargs, add_config=False):
        '''
        Generate and return the parameter sweep plot form the time series results.

        Attributes
        ----------
        fixed : dict
            Dictionary for parameters that remain at a fixed value.
        kwarps : dict
            Dictionary of keys used for post proccessing the results.
        '''
        self.log("debug", f"Keys identifying the plot to generate: {kwargs}")
        settings = self.load_settings()
        try:
            self.log("info", "Loading the results...")
            dims, f_keys = self.__get_fixed_keys_and_dims(settings, fixed)
            params = list(filter(lambda param: param['name'] not in fixed.keys(),
                                 settings['parameterSweepSettings']['parameters']))
            if dims == 1:
                kwargs['param'] = params[0]
                kwargs['results'] = self.__get_filtered_1d_results(f_keys)
                self.log("info", "Generating the plot...")
                fig = ParameterSweep1D.plot(**kwargs)
            else:
                kwargs['params'] = params
                kwargs['results'] = self.__get_filtered_2d_results(f_keys, params[0])
                self.log("info", "Generating the plot...")
                fig = ParameterSweep2D.plot(**kwargs)
            if add_config:
                fig['config'] = {"responsive": True}
            self.log("info", "Loading the plot...")
            return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
        except FileNotFoundError as err:
            message = f"Could not find the results pickle file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err
        except KeyError as err:
            message = f"The requested plot is not available: {str(err)}"
            raise PlotNotAvailableError(message, traceback.format_exc()) from err


    @classmethod
    def get_run_settings(cls, settings, solver_map):
        '''
        Get the gillespy2 run settings for model.run()

        Attributes
        ----------
        settings : dict
            GillesPy3D simulation settings dict
        solver_map : dict
            Dictionary mapping algorithm to solver
        '''
        settings = settings['simulationSettings']
        kwargs = {} if solver_map is None else {"solver":solver_map[settings['algorithm']]}
        if settings['algorithm'] in ("ODE", "Hybrid-Tau-Leaping") and \
                                        "CSolver" not in kwargs['solver'].name:
            integrator_options = {"atol":settings['absoluteTol'], "rtol":settings['relativeTol']}
            kwargs["integrator_options"] = integrator_options
        if settings['algorithm'] == "ODE":
            return kwargs
        kwargs["number_of_trajectories"] = settings['realizations']
        if settings['seed'] != -1:
            kwargs['seed'] = settings['seed']
        if settings['algorithm'] == "SSA":
            return kwargs
        kwargs['tau_tol'] = settings['tauTol']
        return kwargs


    def get_time_stamp(self):
        '''
        Get the time stamp from the job name

        Attributes
        ----------
        '''
        name = self.get_name()
        time_stamp = "_"+"_".join(name.split('_')[-2:])
        if time_stamp.replace('_', '').isdigit():
            return time_stamp
        return None


    def load(self, new=False):
        '''
        Reads in all relavent data for a job and stores it in self.job.

        Attributes
        ----------
        '''
        error = None
        info = self.load_info()
        self.type = info['type']
        status = "new" if new else self.get_status()
        if status in ("new", "ready"):
            if ".proj" in self.path:
                mdl_dirname = self.get_dir_name()
                if "WorkflowGroup1" in self.path:
                    mdl_dirname = os.path.dirname(mdl_dirname)
                mdl_path = os.path.join(mdl_dirname, self.get_file(path=info['source_model']))
            else:
                mdl_path = info['source_model']
        else:
            mdl_path = self.get_model_path()
        try:
            model = GillesPy3DModel(path=mdl_path).load()
        except GillesPy3DFileNotFoundError as err:
            model = None
            error = {"Reason":err.reason, "Message":err.message, "traceback":err.traceback}
            self.log("error", f"Exception information: {error}")
        finally:
            settings = self.load_settings(model=model)
            info = self.load_info()
            logs = f"Compute Environment: {info['compute_env']}"
            if os.path.exists(os.path.join(self.path, "logs.txt")):
                logs = f"{logs}\n{self.__get_run_logs()}"
            self.job = {"mdlPath":mdl_path, "model":model, "settings":settings,
                        "startTime":info['start_time'], "status":status,
                        "timeStamp":self.time_stamp, "titleType":self.TITLES[info['type']],
                        "type":self.type, "directory":self.path, "logs":logs}
            if self.type == "inference":
                el_path = os.path.join(self.get_path(full=True), "export-links.json")
                try:
                    with open(el_path, "r", encoding="utf-8") as elfd:
                        self.job['exportLinks'] = json.load(elfd)
                except FileNotFoundError:
                    num_params = len(settings['inferenceSettings']['parameters'])
                    self.job['exportLinks'] = {i + 1: None for i in range(num_params)}

                for ndx, link in self.job['exportLinks'].items():
                    if link is not None:
                        epl_path = os.path.join(self.user_dir, link)
                        if not os.path.exists(epl_path):
                            self.job['exportLinks'][ndx] = None

            if "template_version" not in self.job['settings']:
                self.job['settings']['template_version'] = 0
            self.__update_settings_to_current()
            if error is not None:
                self.job['error'] = error
        return self.job


    def load_info(self):
        '''
        Reads the jobs load function

        Attributes
        ----------
        '''
        try:
            path = self.__get_info_path(full=True)
            self.log("debug", f"The path to the job's info file: {path}")
            with open(path, "r", encoding="utf-8") as info_file:
                info = json.load(info_file)
                if "annotation" not in info:
                    info['annotation'] = ""
                if "compute_env" not in info:
                    info['compute_env'] = "Local"
                return info
        except FileNotFoundError as err:
            message = f"Could not find the info file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err
        except json.decoder.JSONDecodeError as err:
            message = f"The info file is not JSON decobable: {str(err)}"
            raise FileNotJSONFormatError(message, traceback.format_exc()) from err


    def load_models(self):
        '''
        Load GillesPy2 and GillesPy3D models for running

        Atrributes
        ----------
        '''
        path = self.get_model_path()
        if path.endswith('.mdl'):
            model_obj = GillesPy3DModel(path=path)
            model = model_obj.convert_to_gillespy2()
        else:
            model_obj = GillesPy3DSpatialModel(path=path)
            model = model_obj.convert_to_spatialpy()
            model_obj.model['path'] = model_obj.get_file()
        return model, model_obj.model


    def load_settings(self, model=None):
        '''
        Load the job settings from the settings file

        Attributes
        ----------
        model : dict
            GillesPy3D model dict (used to backwards compatability)
        '''
        try:
            path = self.__get_settings_path(full=True)
            with open(path, "r", encoding="utf-8") as settings_file:
                return json.load(settings_file)
        except FileNotFoundError as err:
            if model is None:
                message = f"Could not find the settings file: {str(err)}"
                raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err
            settings = self.get_settings_template()
            if "simulationSettings" in model.keys():
                settings['simulationSettings'] = model['simulationSettings']
            elif self.type == "parameterSweep":
                settings['simulationSettings']['realizations'] = 20
            if "parameterSweepSettings" in model.keys():
                settings['parameterSweepSettings'] = model['parameterSweepSettings']
            return settings
        except json.decoder.JSONDecodeError as err:
            message = f"The settings file is not JSON decobable: {str(err)}"
            raise FileNotJSONFormatError(message, traceback.format_exc()) from err


    def publish_presentation(self, name=None):
        '''
        Publish a job, workflow, or project presentation.

        Attributes
        ----------
        name : str
            Name of the job presentation.
        '''
        present_dir = os.path.join(self.user_dir, ".presentations")
        if not os.path.exists(present_dir):
            os.mkdir(present_dir)
        try:
            self.load()
            job = json.dumps(self.job, sort_keys=True)
            file = f"{hashlib.md5(job.encode('utf-8')).hexdigest()}.job"
            dst = os.path.join(present_dir, file)
            if os.path.exists(dst):
                exists = True
            else:
                exists = False
                name = self.get_file() if name is None else name
                self.add_presentation_name(file, name)
                path = os.path.join(self.__get_results_path(), "results.p")
                with open(path, "rb") as results_file:
                    results = pickle.load(results_file)
                data = {"name": name, "job": self.job, "results": results}
                with open(dst, "wb") as presentation_file:
                    pickle.dump(data, presentation_file)
            links = self.__get_presentation_links(file)
            return links, exists
        except PermissionError as err:
            message = f"You do not have permission to publish this directory: {str(err)}"
            raise GillesPy3DPermissionsError(message, traceback.format_exc()) from err


    def save(self, mdl_path, settings, initialize=False):
        '''
        Save the data for a new or ready state job

        Attributes
        ----------
        '''
        path = self.get_model_path(full=True)
        new_info = {"source_model":mdl_path}
        if initialize:
            # If this format is not something Javascript's Date.parse() method
            # understands then the job status page will be unable to correctly create a
            # Date object from the datestring parsed from the job's info.json file
            new_info['start_time'] = datetime.datetime.now().strftime("%b %d, %Y  %I:%M %p UTC")
            new_info['wkfl_model'] = self.get_file(path=mdl_path)
            with open(os.path.join(self.path, 'RUNNING'), 'w', encoding="utf-8") as run_file:
                run_file.close()
        self.update_info(new_info=new_info)
        with open(self.__get_settings_path(full=True), "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=4, sort_keys=True)
        try:
            os.remove(path)
            shutil.copyfile(os.path.join(self.user_dir, mdl_path),
                            self.get_model_path(full=True))
            return f"Successfully saved the job: {self.path}"
        except FileNotFoundError as err:
            message = f"Could not find the model file: {str(err)}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc()) from err


    def save_plot(self, plot):
        '''
        Save a plot to the output settings (for projects only)

        Attributes
        ----------
        plot : dict
            plot data used needed to look up the plot
        '''
        settings = self.load_settings()
        self.log("debug", f"Original settings: {settings}")
        settings['resultsSettings']['outputs'].append(plot)
        self.log("debug", f"New settings: {settings}")
        with open(self.__get_settings_path(full=True), "w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, indent=4, sort_keys=True)
        return {"message":"The plot was successfully saved", "data":plot}


    def update_fig_layout(self, fig=None, plt_data=None):
        '''
        Update the figure layout.

        Attributes
        ----------
        fig : dict
            Plotly figure to be updated
        plt_data : dict
            Title and axes data for the plot
        '''
        self.log("debug", f"Title and axis data for the plot: {plt_data}")
        try:
            if plt_data is None:
                return fig
            for key in plt_data.keys():
                if key == "title":
                    fig['layout']['title']['text'] = plt_data[key]
                else:
                    fig['layout'][key]['title']['text'] = plt_data[key]
            return fig
        except KeyError as err:
            message = f"The requested plot is not available: {str(err)}"
            raise PlotNotAvailableError(message, traceback.format_exc()) from err


    def update_info(self, new_info, new=False):
        '''
        Updates the contents of the info file. If source model is updated,
        checks if the model exists at that path

        Attributes
        ----------
        new_info : dict
            Contains all data to be updated under the correct key
        new : bool
            Indicates whether or not an info file needs to be created
        '''
        if new:
            info = new_info
        else:
            info = self.load_info()
            if "source_model" in new_info:
                info['source_model'] = new_info['source_model']
            if "wkfl_model" in new_info:
                info['wkfl_model'] = new_info['wkfl_model']
            if "type" in new_info:
                info['type'] = new_info['type']
            if "start_time" in new_info:
                info['start_time'] = new_info['start_time']
            if "annotation" in new_info:
                info['annotation'] = new_info['annotation']
            if "compute_env" in new_info:
                info['compute_env'] = new_info['compute_env']
        self.log("debug", f"New info: {info}")
        with open(self.__get_info_path(full=True), "w", encoding="utf-8") as file:
            json.dump(info, file, indent=4, sort_keys=True)

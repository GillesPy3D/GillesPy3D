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
import logging
import subprocess
from tornado import web
from notebook.base.handlers import APIHandler
# APIHandler documentation:
# https://github.com/jupyter/notebook/blob/master/notebook/base/handlers.py#L583
# Note APIHandler.finish() sets Content-Type handler to 'application/json'
# Use finish() for json, write() for text

from .util import GillesPy3DFolder, GillesPy3DJob, GillesPy3DModel, GillesPy3DSpatialModel, GillesPy3DNotebook, \
                  GillesPy3DWorkflow, GillesPy3DParamSweepNotebook, GillesPy3DSciopeNotebook, \
                  GillesPy3DAPIError, report_error, report_critical_error, ModelInference

log = logging.getLogger('gillespy3d')


# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods
class NewWorkflowAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for creating a new workflow
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Creates a new workflow of the given type for the given model.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"The path to the workflow: {path}")
        mdl_path = self.get_query_argument(name="model")
        log.debug(f"The path to the model: {mdl_path}")
        wkfl_type = self.get_query_argument(name="type")
        log.debug(f"Type of the workflow: {wkfl_type}")
        try:
            log.info(f"Creating {path.split('/').pop()} workflow")
            wkfl = GillesPy3DWorkflow(path=path, new=True, mdl_path=mdl_path, wkfl_type=wkfl_type)
            resp = {"path": wkfl.path}
            log.info(f"Successfully created {wkfl.get_file()} workflow")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class LoadWorkflowAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for getting the Workflow's status, info, type, model for the Workflow manager page.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve workflow's status, info, and model from User's file system.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"The path to the workflow/model: {path}")
        try:
            log.info("Loading workflow data")
            resp = GillesPy3DWorkflow(path=path).load()
            log.debug(f"Response: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


    @web.authenticated
    async def post(self):
        '''
        Start saving the workflow.  Creates the workflow directory and workflow_info file if
        saving a new workflow.  Copys model into the workflow directory.

        Attributes
        ----------
        '''
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the workflow: {path}")
        data = json.loads(self.request.body.decode())
        log.debug(f"Workflow Data: {data}")
        log.debug(f"Path to the model: {data['model']}")
        try:
            wkfl = GillesPy3DWorkflow(path=path)
            log.info(f"Saving {wkfl.get_file()}")
            resp = wkfl.save(new_settings=data['settings'], mdl_path=data['model'])
            log.debug(f"Response: {resp}")
            log.info(f"Successfully saved {wkfl.get_file()}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class InitializeJobAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for initializing jobs.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Initialize a new job or an existing old format workflow.

        Attributes
        ----------
        '''
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the workflow: {path}")
        data = json.loads(self.get_query_argument(name="data"))
        log.debug(f"Handler query string: {data}")
        try:
            wkfl = GillesPy3DWorkflow(path=path)
            resp = wkfl.initialize_job(
                settings=data['settings'], mdl_path=data['mdl_path'], wkfl_type=data['type'],
                time_stamp=data['time_stamp'], compute=data['compute']
            )
            wkfl.print_logs(log)
            log.debug(f"Response message: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class RunWorkflowAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for running workflows.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Start running a workflow and record the time in UTC in the workflow_info file.
        Creates workflow directory and workflow_info file if running a new workflow.  Copys
        model into the workflow directory.

        Attributes
        ----------
        '''
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the workflow: {path}")
        wkfl_type = self.get_query_argument(name="type")
        log.debug(f"Type of workflow: {wkfl_type}")
        verbose = self.get_query_argument(name="verbose", default=False)
        try:
            script = "/model_builder/model_builder/handlers/util/scripts/start_job.py"
            exec_cmd = [f"{script}", f"{path}", f"{wkfl_type}", "-v"]
            if verbose:
                exec_cmd.append("-v")
            log.debug(f"Exec command sent to the subprocess: {exec_cmd}")
            log.debug('Sending the workflow run cmd')
            job = subprocess.Popen(exec_cmd)
            with open(os.path.join(path, "RUNNING"), "w", encoding="utf-8") as file:
                file.write(f"Subprocess id: {job.pid}")
            log.debug('The workflow has started')
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class WorkflowStatusAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for getting Workflow Status (checking for RUNNING and COMPLETE files.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve workflow status based on status files.

        Attributes
        ----------
        '''
        path = self.get_query_argument(name="path")
        log.debug(f'path to the workflow: {path}')
        log.debug('Getting the status of the workflow')
        try:
            wkfl = GillesPy3DJob(path=path)
            status = wkfl.get_status()
            log.debug(f'The status of the workflow is: {status}')
            self.write(status)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class PlotWorkflowResultsAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for getting result plots based on plot type.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve a plot figure of the job results based on the plot type in the request body.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"The path to the workflow: {path}")
        body = json.loads(self.get_query_argument(name='data'))
        log.debug(f"Plot args passed to the plot: {body}")
        try:
            if body['sim_type'] == "Inference":
                job = ModelInference(path=path)
                kwargs = {'add_config': True}
                kwargs.update(body['data_keys'])
                if "plt_data" in body.keys() and body['plt_data'] is not None:
                    kwargs.update(body['plt_data'])
                fig, fig2 = job.get_result_plot(**kwargs)
                log.debug(f"Histogram figure: {fig}, PDF figure: {fig2}")
                self.write({'histogram': fig, 'pdf': fig2})
            else:
                job = GillesPy3DJob(path=path)
                if body['sim_type'] in  ("GillesPy2", "GillesPy2_PS"):
                    fig = job.get_plot_from_results(data_keys=body['data_keys'],
                                                    plt_key=body['plt_key'], add_config=True)
                    job.print_logs(log)
                elif body['sim_type'] == "SpatialPy":
                    fig = job.get_plot_from_spatial_results(
                        data_keys=body['data_keys'], add_config=True
                    )
                else:
                    fig = job.get_psweep_plot_from_results(fixed=body['data_keys'],
                                                           kwargs=body['plt_key'], add_config=True)
                    job.print_logs(log)
                if "plt_data" in body.keys():
                    fig = job.update_fig_layout(fig=fig, plt_data=body['plt_data'])
                log.debug(f"Plot figure: {fig}")
                self.write(fig)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class WorkflowNotebookHandler(APIHandler):
    '''
    ################################################################################################
    Handler for handling conversions from model (.mdl) file or workflows (.wkfl)
    to Jupyter Notebook (.ipynb) file for notebook workflows.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Create a jupyter notebook workflow using a model_builder model.

        Attributes
        ----------
        '''
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the model/workflow: {path}")
        wkfl_type = self.get_query_argument(name="type")
        log.debug(f"Type of workflow: {wkfl_type}")
        compute = self.get_query_argument(name="compute", default=None)
        log.debug(f"Compute Environment: {compute}")
        try:
            if path.endswith(".mdl"):
                file_obj = GillesPy3DModel(path=path)
            elif path.endswith(".smdl"):
                file_obj = GillesPy3DSpatialModel(path=path)
            else:
                file_obj = GillesPy3DJob(path=path)
            log.info(f"Loading data for {file_obj.get_file()}")
            kwargs = file_obj.get_notebook_data()
            if "type" in kwargs:
                wkfl_type = kwargs['type']
                results = kwargs['results']
                compute = kwargs['compute_env']
                kwargs = kwargs['kwargs']
                log.info(f"Converting {file_obj.get_file()} to notebook")
            else:
                results = None
                log.info(f"Creating notebook workflow for {file_obj.get_file()}")
            log.debug(f"Type of workflow to be run: {wkfl_type}")
            if wkfl_type in ("1d_parameter_sweep", "2d_parameter_sweep"):
                notebook = GillesPy3DParamSweepNotebook(**kwargs)
                notebooks = {"1d_parameter_sweep":notebook.create_1d_notebook,
                             "2d_parameter_sweep":notebook.create_2d_notebook}
            elif wkfl_type in ("sciope_model_exploration", "model_inference", "inference"):
                notebook = GillesPy3DSciopeNotebook(**kwargs)
                notebooks = {"sciope_model_exploration":notebook.create_me_notebook,
                             "model_inference":notebook.create_mi_notebook,
                             "inference":notebook.create_mi_notebook}
            else:
                notebook = GillesPy3DNotebook(**kwargs)
                notebooks = {"gillespy":notebook.create_es_notebook,
                             "spatial":notebook.create_ses_notebook}
            resp = notebooks[wkfl_type](results=results, compute=compute)
            notebook.print_logs(log)
            log.debug(f"Response: {resp}")
            log.info(f"Successfully created the notebook for {file_obj.get_file()}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class SavePlotAPIHandler(APIHandler):
    '''
    ##############################################################################
    Handler for handling conversions from model (.mdl) file or workflows (.wkfl)
    to Jupyter Notebook (.ipynb) file for notebook workflows.
    ##############################################################################
    '''
    @web.authenticated
    async def post(self):
        '''
        Create a jupyter notebook workflow using a model_builder model.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"The path to the workflow setting file: {path}")
        plot = json.loads(self.request.body.decode())
        log.debug(f"The plot to be saved: {plot}")
        try:
            wkfl = GillesPy3DJob(path=path)
            resp = wkfl.save_plot(plot=plot)
            wkfl.print_logs(log)
            log.debug(f"Response message: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class SaveAnnotationAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for saving annotations for workflows.
    ################################################################################################
    '''
    @web.authenticated
    async def post(self):
        '''
        Adds/updates the workflows annotation in the info file.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"The path to the workflow info file: {path}")
        info = json.loads(self.request.body.decode())
        log.debug(f"The annotation to be saved: {info['annotation']}")
        try:
            log.info(f"Saving annotation for {path.split('/').pop()}")
            if GillesPy3DWorkflow.check_workflow_format(path=path):
                wkfl = GillesPy3DWorkflow(path=path)
                wkfl.save_annotation(info['annotation'])
            else:
                wkfl = GillesPy3DJob(path=path)
                wkfl.update_info(new_info=info)
                wkfl.print_logs(log)
            resp = {"message":"The annotation was successfully saved", "data":info['annotation']}
            log.info("Successfully saved the annotation")
            log.debug(f"Response message: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class UpadteWorkflowAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for updating workflow format.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Updates the workflow to the new format.

        Attributes
        ----------
        '''
        path = self.get_query_argument(name="path")
        log.debug(f"The path to the workflow: {path}")
        try:
            wkfl = GillesPy3DWorkflow(path=path)
            resp = wkfl.update_wkfl_format()
            log.debug(f"Response Message: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class JobPresentationAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for publishing job presentations.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Publish a job presentation.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"The path to the job: {path}")
        name = self.get_query_argument(name="name")
        log.debug(f"Name of the job presentation: {name}")
        try:
            job = GillesPy3DJob(path=path)
            log.info(f"Publishing the {job.get_name()} presentation")
            links, exists = job.publish_presentation(name=name)
            if exists:
                message = f"A presentation for {job.get_name()} already exists."
            else:
                message = f"Successfully published the {job.get_name()} presentation"
            resp = {"message": message, "links": links}
            log.info(resp['message'])
            log.debug(f"Response Message: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class DownloadCSVZipAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for downloading job csv results files.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Download a jobs results as CSV.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/zip')
        path = self.get_query_argument(name="path")
        csv_type = self.get_query_argument(name="type")
        data = self.get_query_argument(name="data", default=None)
        if data is not None:
            data = json.loads(data)
        try:
            if csv_type == "inference":
                job = ModelInference(path=path)
            else:
                job = GillesPy3DJob(path=path)
            name = job.get_name()
            self.set_header('Content-Disposition', f'attachment; filename="{name}.zip"')
            if csv_type == "time series":
                csv_data = job.get_csvzip_from_results(**data, name=name)
            elif csv_type == "psweep":
                csv_data = job.get_psweep_csvzip_from_results(fixed=data, name=name)
            elif csv_type == "inference":
                csv_data = job.get_csv_data(name=name)
            else:
                csv_data = job.get_full_csvzip_from_results(name=name)
            self.write(csv_data)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class ImportObsDataAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for importing observed data from remote file.
    ################################################################################################
    '''
    @web.authenticated
    async def post(self):
        '''
        Imports observed data from a file.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        dirname = os.path.dirname(self.request.body_arguments['path'][0].decode())
        if dirname == '.':
            dirname = ""
        elif ".wkgp" in dirname:
            dirname = os.path.dirname(dirname)
        data_file = self.request.files['datafile'][0]
        log.info(f"Importing observed data: {data_file['filename']}")
        try:
            folder = GillesPy3DFolder(path=dirname)
            if data_file['filename'].endswith(".zip"):
                new_name = data_file['filename'].replace(".zip", ".odf")
            else:
                new_name = None
            data_resp = folder.upload(
                'file', data_file['filename'], data_file['body'], new_name=new_name
            )
            resp = {'obsDataPath': data_resp['path'], 'obsDataFile': data_resp['file']}
            log.info("Successfully uploaded observed data")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class LoadObsDataFiles(APIHandler):
    '''
    ################################################################################################
    Handler for getting observed data files.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Get observed data files on disc for file selections.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        target_ext = self.get_query_argument(name="ext").split(',')
        try:
            folder = GillesPy3DFolder(path="")
            test = lambda ext, root, file: bool(
                "trash" in root.split("/") or file.startswith('.') or \
                'wkfl' in root or root.startswith('.') or root.endswith("obsd")
            )
            data_files = folder.get_file_list(ext=target_ext, test=test, inc_folders=True)
            resp = {'obsDataFiles': data_files}
            log.debug(f"Response: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()

class PreviewOBSDataAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for previewing observed data.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Preview the observed data files.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        try:
            wkfl = GillesPy3DWorkflow(path="")
            resp = {"figure": wkfl.preview_obs_data(path)}
            wkfl.print_logs(log)
            log.debug(f"Response: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()

class ExportInferredModelAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for exporting an inferred model.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Preview the observed data files.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        round = int(self.get_query_argument(name="round", default=-1))
        try:
            job = ModelInference(path=path)
            inf_model = job.export_inferred_model(round_ndx=round)

            end = -3 if '.wkgp' in path else -2
            dirname = '/'.join(path.split('/')[:end])
            if ".proj" in dirname:
                dst = os.path.join(dirname, f"{inf_model['name']}.wkgp", f"{inf_model['name']}.mdl")
            else:
                dst = os.path.join(dirname, f"{inf_model['name']}.mdl")
            model = GillesPy3DModel(path=dst, new=True, model=inf_model)

            resp = {"path": model.get_path()}
            log.debug(f"Response: {resp}")
            self.write(resp)
            job.update_export_links(round, dst)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()

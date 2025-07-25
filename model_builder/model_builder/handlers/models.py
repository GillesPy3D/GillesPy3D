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
import uuid
import logging
import subprocess
from tornado import web
from notebook.base.handlers import APIHandler
# APIHandler documentation:
# https://github.com/jupyter/notebook/blob/master/notebook/base/handlers.py#L583
# Note APIHandler.finish() sets Content-Type handler to 'application/json'
# Use finish() for json, write() for text

from .util import GillesPy3DFolder, GillesPy3DModel, GillesPy3DSpatialModel, GillesPy3DNotebook, \
                  GillesPy3DAPIError, report_error, report_critical_error


log = logging.getLogger('gillespy3d')

# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods
class JsonFileAPIHandler(APIHandler):
    '''
    ################################################################################################
    Base Handler for interacting with Model file Get/Post Requests and
    downloading json formatted files.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve model data from User's file system if it exists and
        create new models using a model template if they don't.  Also
        retrieves JSON files for download.

        Attributes
        ----------
        '''
        purpose = self.get_query_argument(name="for")
        log.debug(f"Purpose of the handler: {purpose}")
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the file: {path}")
        self.set_header('Content-Type', 'application/json')
        file_objs = {"ipynb":GillesPy3DNotebook, "mdl":GillesPy3DModel, "smdl":GillesPy3DSpatialModel}
        ext = path.split(".").pop()
        if ext == "ipynb":
            log.info("Getting notebook data for download")
        elif purpose == "None":
            log.info("Getting model data for download")
        else:
            log.info("Loading model data")
        try:
            file = file_objs[ext](path=path)
            data = file.load()
            log.debug(f"Contents of the json file: {data}")
            file.print_logs(log)
            self.write(data)
        except GillesPy3DAPIError as load_err:
            if purpose == "edit" and ext != "ipynb":
                try:
                    model = file_objs[ext](path=path, new=True)
                    data = model.load()
                    log.debug(f"Contents of the model template: {data}")
                    model.print_logs(log)
                    self.write(data)
                except GillesPy3DAPIError as new_model_err:
                    report_error(self, log, new_model_err)
            else:
                report_error(self, log, load_err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


    @web.authenticated
    async def post(self):
        '''
        Send/Save model data to user container.

        Attributes
        ----------
        '''
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the model: {path}")
        data = self.request.body.decode()
        log.debug(f"Model data to be saved: {data}")
        try:
            if path.endswith(".domn"):
                model = GillesPy3DSpatialModel(path=path)
                log.info(f"Saving {model.get_file(path=path)}")
                model.save_domain(domain=data)
            else:
                model = GillesPy3DModel(path=path)
                log.info(f"Saving {model.get_file(path=path)}")
                model.save(model=data)
                model.print_logs(log)
            log.info(f"Successfully saved {model.get_file(path=path)}")
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class LoadDomainEditorAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for loading the domain editor for spatial models.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Load and return the spatial model, domain, and domain plot.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path", default=None)
        log.debug(f"Path to the spatial model: {path}")
        d_path = self.get_query_argument(name="domain_path", default=None)
        if d_path is not None:
            log.debug(f"Path to the domain file: {d_path}")
        new = self.get_query_argument(name="new", default=False)
        log.debug(f"The domain is new: {new}")
        log.info("Loading the domain data")
        try:
            model = GillesPy3DSpatialModel(path=path)
            domain = model.get_domain(path=d_path, new=new)
            s_model = None if path is None else model.load()
            resp = {"model":s_model, "domain":domain}
            log.debug(f"Response: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class LoadDomainAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for loading the domain for the spatial model editor.
    ################################################################################################
    '''
    @web.authenticated
    async def post(self):
        '''
        Load and return the domain plot.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        domain = json.loads(self.request.body.decode())
        log.info("Generating the domain plot")
        try:
            model = GillesPy3DSpatialModel(path="")
            fig, limits = model.load_action_preview(domain)
            log.info("Loading the domain plot")
            if isinstance(fig, str):
                fig = json.loads(fig)
            resp = {"fig":fig, "particles": domain['particles'], "limits": limits}
            log.debug(f"Response: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class RunModelAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for running a model from the model editor.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Run the model with a 5 second timeout.  Results are sent to the
        client as a JSON object.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the model: {path}")
        run_cmd = self.get_query_argument(name="cmd")
        log.debug(f"Run command sent to the script: {run_cmd}")
        outfile = self.get_query_argument(name="outfile")
        # Create temporary results file it doesn't already exist
        if outfile == 'none':
            outfile = str(uuid.uuid4()).replace("-", "_")
        log.debug(f"Temporary outfile: {outfile}")
        target = self.get_query_argument(name="target", default=None)
        resp = {"Running":False, "Outfile":outfile, "Results":""}
        if run_cmd == "start":
            try:
                model = GillesPy3DModel(path=path)
                if os.path.exists(f".{model.get_name()}-preview.json"):
                    os.remove(f".{model.get_name()}-preview.json")
                exec_cmd = ['/model_builder/model_builder/handlers/util/scripts/run_preview.py',
                            f'{path}', f'{outfile}']
                if target is not None:
                    exec_cmd.insert(1, "--target")
                    exec_cmd.insert(2, f"{target}")
                log.debug(f"Script commands for running a preview: {exec_cmd}")
                subprocess.Popen(exec_cmd)
                resp['Running'] = True
                log.debug(f"Response to the start command: {resp}")
                self.write(resp)
            except Exception as err:
                report_critical_error(self, log, err)
        else:
            try:
                model = GillesPy3DModel(path=path)
                log.info("Check for preview results ...")
                results = model.get_preview_results(outfile=outfile)
                log.debug(f"Results for the model preview: {results}")
                if results is None:
                    resp['Running'] = True
                    resp['Results'] = model.get_live_results()
                    log.info("The preview is still running")
                else:
                    resp['Results'] = results
                    log.info("Loading the preview results")
                log.debug(f"Response to the read command: {resp}")
                self.write(resp)
            except Exception as err:
                report_critical_error(self, log, err)
        self.finish()


class ModelExistsAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for checking if a model already exists.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Check if the model already exists.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the file: {path}")
        try:
            model = GillesPy3DModel(path=path)
            resp = {"exists":os.path.exists(model.get_path(full=True))}
            log.debug(f"Response: {resp}")
            self.write(resp)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class ImportMeshAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for importing domain particles from remote file.
    ################################################################################################
    '''
    @web.authenticated
    async def post(self):
        '''
        Imports particles from a domain file to add to a domain.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        dirname = os.path.dirname(self.request.body_arguments['path'][0].decode())
        if dirname == '.':
            dirname = ""
        elif ".wkgp" in dirname:
            dirname = os.path.dirname(dirname)
        mesh_file = self.request.files['datafile'][0]
        log.info(f"Importing mesh: {mesh_file['filename']}")
        if "typefile" in self.request.files.keys():
            type_file = self.request.files['typefile'][0]
            log.info(f"Importing type descriptions: {type_file['filename']}")
        else:
            type_file = None
        try:
            folder = GillesPy3DFolder(path=dirname)
            mesh_resp = folder.upload('file', mesh_file['filename'], mesh_file['body'])
            resp = {'meshPath': mesh_resp['path'], 'meshFile': mesh_resp['file']}
            if type_file is not None:
                types_resp = folder.upload('file', type_file['filename'], type_file['body'])
                resp['typesPath'] = types_resp['path']
                resp['typesFile'] = types_resp['file']
            log.info("Successfully uploaded files")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class LoadExternalDomains(APIHandler):
    '''
    ################################################################################################
    Handler for getting external domain files.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Get all domain files on disc.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        try:
            folder = GillesPy3DFolder(path="")
            test = lambda ext, root, file: bool("trash" in root.split("/"))
            resp = folder.get_file_list(ext=".domn", test=test)
            log.debug(f"Response: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class LoadLatticeFiles(APIHandler):
    '''
    ################################################################################################
    Handler for getting mesh/domain and type description files.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Get mesh/domain and type description files on disc for file selections.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        target_ext = self.get_query_argument(name="ext")
        include_types = bool(self.get_query_argument(name="includeTypes", default=False))
        try:
            folder = GillesPy3DFolder(path="")
            test = lambda ext, root, file: bool(
                "trash" in root.split("/") or file.startswith('.') or \
                'wkfl' in root or root.startswith('.')
            )
            mesh_files = folder.get_file_list(ext=target_ext, test=test)
            resp = {'meshFiles': mesh_files}
            if include_types:
                type_files = folder.get_file_list(ext=".txt", test=test)
                resp['typeFiles'] = type_files
            log.debug(f"Response: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()

class ModelPresentationAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler publishing model presentations.
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Publish a model or spatial model presentation.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        path = self.get_query_argument(name="path")
        log.debug(f"Path to the file: {path}")
        file_objs = {"mdl":GillesPy3DModel, "smdl":GillesPy3DSpatialModel}
        ext = path.split(".").pop()
        try:
            model = file_objs[ext](path=path)
            log.info(f"Publishing the {model.get_name()} presentation")
            links, data = model.publish_presentation()
            if data is None:
                message = f"A presentation for {model.get_name()} already exists."
            else:
                message = f"Successfully published the {model.get_name()} presentation."
                if ext == "mdl":
                    file_objs[ext](**data)
            resp = {"message": message, "links": links}
            log.info(resp['message'])
            log.debug(f"Response Message: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()


class CreateNewBoundCondAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler creating new boundary conditions.
    ################################################################################################
    '''
    @web.authenticated
    async def post(self):
        '''
        Creates a new restricted boundary condition.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        data = json.loads(self.request.body.decode())
        path = data['model_path']
        kwargs = data['kwargs']
        log.debug(f"Args passed to the boundary condition constructor: {kwargs}")
        try:
            log.info("Creating the new boundary condition")
            model = GillesPy3DSpatialModel(path=path)
            resp = model.create_boundary_condition(kwargs)
            log.info("Successfully created the new boundary condition")
            log.debug(f"Response Message: {resp}")
            self.write(resp)
        except GillesPy3DAPIError as err:
            report_error(self, log, err)
        except Exception as err:
            report_critical_error(self, log, err)
        self.finish()

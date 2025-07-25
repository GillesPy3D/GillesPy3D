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
import time
import logging
import subprocess
from tornado import web
from notebook.base.handlers import IPythonHandler, APIHandler
# APIHandler documentation:
# https://github.com/jupyter/notebook/blob/master/notebook/base/handlers.py#L583
# Note APIHandler.finish() sets Content-Type handler to 'application/json'
# Use finish() for json, write() for text

from .util import GillesPy3DBase, report_error
from .util.model_builder_errors import AWSConfigurationError

log = logging.getLogger('gillespy3d')

# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods
class PageHandler(IPythonHandler):
    '''
    ################################################################################################
    Base handler for rendering model_builder pages.
    ################################################################################################
    '''
    def get_template_path(self):
        '''
        Retrieve the location of model_builder pages output by webpack.
        The html pages are located in the same directory as static assets.

        Attributes
        ----------
        '''
        return self.settings['config']['NotebookApp']['extra_static_paths'][0]

    @classmethod
    def get_server_path(cls):
        '''
        Retrieve the path to the server.

        Attributes
        ----------
        '''
        try:
            server_path = os.environ['JUPYTERHUB_SERVICE_PREFIX']
        except KeyError:
            server_path = '/'

        return server_path


class HomeHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Home Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D home page.

        Attributes
        ----------
        '''
        self.render("model_builder-home.html", server_path=self.get_server_path())


class UserHomeHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D User Home Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D user home page.

        Attributes
        ----------
        '''
        self.render("model_builder-user-home.html", server_path=self.get_server_path())


class QuickstartHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Tutorials Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D tutorials page.

        Attributes
        ----------
        '''
        self.render("model_builder-quickstart.html", server_path=self.get_server_path())


class ExampleLibraryHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Example Library Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D example library page.

        Attributes
        ----------
        '''
        self.render("model_builder-example-library.html", server_path=self.get_server_path())


class ModelBrowserHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D File Browser Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D file browser page.

        Attributes
        ----------
        '''
        self.render("model_builder-file-browser.html", server_path=self.get_server_path())


class ModelEditorHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Model Editor Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D model editor page.

        Attributes
        ----------
        '''
        self.render("model_builder-model-editor.html", server_path=self.get_server_path())


class DomainEditorHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Domain Editor Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D domain editor page.

        Attributes
        ----------
        '''
        self.render("model_builder-domain-editor.html", server_path=self.get_server_path())


class WorkflowSelectionHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Workflow Selection Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D workflow selection page.

        Attributes
        ----------
        '''
        self.render("model_builder-workflow-selection.html", server_path=self.get_server_path())


class WorkflowEditorHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Workflow Manager Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D workflow manager page.

        Attributes
        ----------
        '''
        self.render("model_builder-workflow-manager.html", server_path=self.get_server_path())


class ProjectManagerHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Project Manager Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D project manager page.

        Attributes
        ----------
        '''
        self.render("model_builder-project-manager.html", server_path=self.get_server_path())


class LoadingPageHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Loading Page Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D loading page.

        Attributes
        ----------
        '''
        self.render("model_builder-loading-page.html", server_path=self.get_server_path())


class MultiplePlotsHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D Multiple Plots Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D multiple plots page.

        Attributes
        ----------
        '''
        self.render("multiple-plots-page.html", server_path=self.get_server_path())


class UserSettingsHandler(PageHandler):
    '''
    ################################################################################################
    GillesPy3D User Settings Page Handler
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Render the GillesPy3D user settings page.

        Attributes
        ----------
        '''
        self.render("model_builder-user-settings.html", server_path=self.get_server_path())


class UserLogsAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for getting the user logs
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Return the contents of the user log file.

        Attributes
        ----------
        '''
        self.set_header('Content-Type', 'application/json')
        log_num = self.get_query_arguments(name="logNum")[0]
        path = os.path.join(os.path.expanduser("~"), ".user-logs.txt")
        try:
            if os.path.exists(f"{path}.bak"):
                with open(path, "r", encoding="utf-8") as log_file:
                    logs = log_file.read().strip().split("\n")
            else:
                logs = []
            with open(path, "r", encoding="utf-8") as log_file:
                logs.extend(log_file.read().strip().split("\n"))
                logs = logs[int(log_num):]
        except FileNotFoundError:
            open(path, "w", encoding="utf-8").close()
            logs = []
        self.write({"logs":logs})
        self.finish()


class ClearUserLogsAPIHandler(APIHandler):
    '''
    ################################################################################################
    Handler for clearing the user logs
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Clear contents of the user log file.

        Attributes
        ----------
        '''
        path = os.path.join(os.path.expanduser("~"), ".user-logs.txt")
        if os.path.exists(f'{path}.bak'):
            os.remove(f'{path}.bak')
        open(path, "w", encoding="utf-8").close()
        self.finish()


class LoadUserSettings(APIHandler):
    '''
    ################################################################################################
    GillesPy3D handler for loading user settings
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Load the existing user settings.

        Attributes
        ----------
        '''
        file = GillesPy3DBase(path='.user-settings.json')
        settings = file.load_user_settings()

        i_path = "/model_builder/model_builder_templates/instance_types.txt"
        with open(i_path, "r", encoding="utf-8") as itype_fd:
            instance_types = itype_fd.read().strip().split('|')
        instances = {}
        for instance_type in instance_types:
            (i_type, size) = instance_type.split('.')
            if i_type in instances:
                instances[i_type].append(size)
            else:
                instances[i_type] = [size]

        self.write({"settings": settings, "instances": instances})
        self.finish()

    @web.authenticated
    async def post(self):
        '''
        Save the user settings.

        Attributes
        ----------
        '''
        data = json.loads(self.request.body.decode())
        log.debug(f"Settings data to be saved: {data}")

        def check_env_data(data):
            if data['settings']['awsRegion'] == "":
                return False
            if data['settings']['awsAccessKeyID'] == "":
                return False
            if data['secret_key'] is None:
                return False
            return True

        if check_env_data(data):
            if not os.path.exists(".aws"):
                os.mkdir(".aws")
            with open(".aws/awsec2.env", "w", encoding="utf-8") as env_fd:
                contents = "\n".join([
                    f"AWS_DEFAULT_REGION={data['settings']['awsRegion']}",
                    f"AWS_ACCESS_KEY_ID={data['settings']['awsAccessKeyID']}",
                    f"AWS_SECRET_ACCESS_KEY={data['secret_key']}"
                ])
                env_fd.write(contents)

        with open(".user-settings.json", "w", encoding="utf-8") as usrs_fd:
            json.dump(data['settings'], usrs_fd, indent=4, sort_keys=True)
        self.finish()

class ConfirmAWSConfigHandler(APIHandler):
    '''
    ################################################################################################
    GillesPy3D handler for confirming AWS configuration
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Confirm that AWS is configured for running jobs..

        Attributes
        ----------
        '''
        file = GillesPy3DBase(path='.user-settings.json')
        settings = file.load_user_settings()
        if settings['awsHeadNodeStatus'] != "running":
            file.update_aws_status(settings['headNode'])
            err = AWSConfigurationError("AWS is not properly configured for running jobs.")
            report_error(self, log, err)

        self.write({"configured": True})
        self.finish()

class LaunchAWSClusterHandler(APIHandler):
    '''
    ################################################################################################
    GillesPy3D handler for launching the AWS cluster
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Launch the AWS cluster.

        Attributes
        ----------
        '''
        file = GillesPy3DBase(path='.user-settings.json')

        script = "/model_builder/model_builder/handlers/util/scripts/aws_compute.py"
        exec_cmd = [f"{script}", "-lv"]
        with subprocess.Popen(exec_cmd):
            print("Launching AWS")

        time.sleep(1)
        settings = file.load_user_settings()

        self.write({"settings": settings})
        self.finish()

class AWSClusterStatusHandler(APIHandler):
    '''
    ################################################################################################
    GillesPy3D handler for updating the AWS cluster status
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Update the AWS cluster status.

        Attributes
        ----------
        '''
        file = GillesPy3DBase(path='.user-settings.json')

        settings = file.load_user_settings()

        file.update_aws_status(settings['headNode'])

        self.write({"settings": settings})
        self.finish()

class TerminateAWSClusterHandler(APIHandler):
    '''
    ################################################################################################
    GillesPy3D handler for terminating the AWS cluster
    ################################################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Terminate the AWS cluster.

        Attributes
        ----------
        '''
        file = GillesPy3DBase(path='.user-settings.json')

        script = "/model_builder/model_builder/handlers/util/scripts/aws_compute.py"
        exec_cmd = [f"{script}", "-tv"]
        with subprocess.Popen(exec_cmd):
            print("Terminating AWS")

        time.sleep(1)
        settings = file.load_user_settings()

        self.write({"settings": settings})
        self.finish()

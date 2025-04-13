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

import logging
from notebook.utils import url_path_join

from .pages import *
from .file_browser import *
from .models import *
from .workflows import *
from .project import *
from .log import init_log

def get_page_handlers(route_start):
    '''
    Get the GillesPy3D page handlers

    Attributes
    ----------
    route_starts : str
        The base url for the web app
    '''
    handlers = [
        ##############################################################################
        # Page Handlers & API Handlers                                               #
        ##############################################################################
        (r'/model_builder/home\/?', UserHomeHandler),
        (r'/model_builder/quickstart\/?', QuickstartHandler),
        (r'/model_builder/example-library\/?', ExampleLibraryHandler),
        (r'/model_builder/files\/?$', ModelBrowserHandler),
        (r'/model_builder/models/edit\/?', ModelEditorHandler),
        (r'/model_builder/domain/edit\/?', DomainEditorHandler),
        (r'/model_builder/workflow/selection\/?', WorkflowSelectionHandler),
        (r'/model_builder/workflow/edit\/?', WorkflowEditorHandler),
        (r'/model_builder/project/manager\/?', ProjectManagerHandler),
        (r'/model_builder/loading-page\/?', LoadingPageHandler),
        (r'/model_builder/multiple-plots\/?', MultiplePlotsHandler),
        (r'/model_builder/settings\/?', UserSettingsHandler),
        (r'/model_builder/api/user-logs\/?', UserLogsAPIHandler),
        (r'/model_builder/api/clear-user-logs\/?', ClearUserLogsAPIHandler),
        (r'/model_builder/api/load-user-settings\/?', LoadUserSettings),
        (r'/model_builder/api/aws/job-config-check\/?', ConfirmAWSConfigHandler),
        (r'/model_builder/api/aws/launch-cluster\/?', LaunchAWSClusterHandler),
        (r'/model_builder/api/aws/cluster-status\/?', AWSClusterStatusHandler),
        (r'/model_builder/api/aws/terminate-cluster\/?', TerminateAWSClusterHandler),
        ##############################################################################
        # File Browser API Handlers                                                  #
        ##############################################################################
        (r"/model_builder/api/file/browser-list\/?", ModelBrowserFileList),
        (r"/model_builder/api/file/empty-trash\/?", EmptyTrashAPIHandler),
        (r"/model_builder/api/file/delete\/?", DeleteFileAPIHandler),
        (r"/model_builder/api/file/move\/?", MoveFileAPIHandler),
        (r"/model_builder/api/file/duplicate\/?", DuplicateModelHandler),
        (r"/model_builder/api/directory/duplicate\/?", DuplicateDirectoryHandler),
        (r"/model_builder/api/file/rename\/?", RenameAPIHandler),
        (r"/model_builder/api/model/to-spatial\/?", ConvertToSpatialAPIHandler),
        (r"/model_builder/api/spatial/to-model\/?", ConvertToModelAPIHandler),
        (r"/model_builder/api/model/to-sbml\/?", ModelToSBMLAPIHandler),
        (r"/model_builder/api/sbml/to-model\/?", SBMLToModelAPIHandler),
        (r"/model_builder/api/file/download\/?", DownloadAPIHandler),
        (r"/model_builder/api/file/download-zip\/?", DownloadZipFileAPIHandler),
        (r"/model_builder/api/directory/create\/?", CreateDirectoryHandler),
        (r"/model_builder/api/file/upload\/?", UploadFileAPIHandler),
        (r"/model_builder/api/workflow/duplicate\/?", DuplicateWorkflowAsNewHandler),
        (r"/model_builder/api/workflow/edit-model\/?", GetWorkflowModelPathAPIHandler),
        (r"/model_builder/api/file/upload-from-link\/?", UploadFileFromLinkAPIHandler),
        (r"/model_builder/api/file/unzip\/?", UnzipFileAPIHandler),
        (r"/model_builder/api/notebook/presentation\/?", NotebookPresentationAPIHandler),
        (r"/model_builder/api/file/presentations\/?", PresentationListAPIHandler),
        (r'/model_builder/api/example-library\/?', ImportFromLibrary),
        ##############################################################################
        # Model API Handlers                                                         #
        ##############################################################################
        (r"/model_builder/api/file/json-data\/?", JsonFileAPIHandler),
        (r"/model_builder/api/spatial-model/load-domain\/?", LoadDomainEditorAPIHandler),
        (r"/model_builder/api/spatial-model/domain-plot\/?", LoadDomainAPIHandler),
        (r"/model_builder/api/model/run\/?", RunModelAPIHandler),
        (r"/model_builder/api/model/exists\/?", ModelExistsAPIHandler),
        (r"/model_builder/api/spatial-model/import-mesh\/?", ImportMeshAPIHandler),
        (r"/model_builder/api/spatial-model/domain-list\/?", LoadExternalDomains),
        (r"/model_builder/api/model/new-bc\/?", CreateNewBoundCondAPIHandler),
        (r"/model_builder/api/model/presentation\/?", ModelPresentationAPIHandler),
        (r"/model_builder/api/spatial-model/lattice-files\/?", LoadLatticeFiles),
        (r"/model_builder/api/spatial-model/domain-plot\/?", LoadDomainAPIHandler),
        (r"/model_builder/api/spatial-model/load-domain\/?", LoadDomainEditorAPIHandler),
        (r"/model_builder/api/spatial-model/import-mesh\/?", ImportMeshAPIHandler),
        ##############################################################################
        # Project API Handlers                                                       #
        ##############################################################################
        (r"/model_builder/api/project/new-project\/?", NewProjectAPIHandler),
        (r"/model_builder/api/project/load-project\/?", LoadProjectAPIHandler),
        (r"/model_builder/api/project/load-browser\/?", LoadProjectBrowserAPIHandler),
        (r"/model_builder/api/project/load-project\/?", LoadProjectAPIHandler),
        (r"/model_builder/api/project/new-project\/?", NewProjectAPIHandler),
        (r"/model_builder/api/project/new-model\/?", NewModelAPIHandler),
        (r"/model_builder/api/project/add-existing-model\/?", AddExistingModelAPIHandler),
        (r"/model_builder/api/project/extract-model\/?", ExtractModelAPIHandler),
        (r"/model_builder/api/project/extract-workflow\/?", ExtractWorkflowAPIHandler),
        (r"/model_builder/api/project/meta-data\/?", ProjectMetaDataAPIHandler),
        (r"/model_builder/api/project/export-combine\/?", ExportAsCombineAPIHandler),
        (r"/model_builder/api/project/save-annotation\/?", UpdateAnnotationAPIHandler),
        (r"/model_builder/api/project/update-format\/?", UpadteProjectAPIHandler),
        ##############################################################################
        # Workflow API Handlers                                                      #
        ##############################################################################
        (r"/model_builder/api/workflow/new\/?", NewWorkflowAPIHandler),
        (r"/model_builder/api/workflow/load-workflow\/?", LoadWorkflowAPIHandler),
        (r"/model_builder/api/workflow/init-job\/?", InitializeJobAPIHandler),
        (r"/model_builder/api/workflow/run-job\/?", RunWorkflowAPIHandler),
        (r"/model_builder/api/workflow/workflow-status\/?", WorkflowStatusAPIHandler),
        (r"/model_builder/api/workflow/plot-results\/?", PlotWorkflowResultsAPIHandler),
        (r"/model_builder/api/workflow/notebook\/?", WorkflowNotebookHandler),
        (r"/model_builder/api/workflow/save-plot\/?", SavePlotAPIHandler),
        (r"/model_builder/api/workflow/save-annotation\/?", SaveAnnotationAPIHandler),
        (r"/model_builder/api/workflow/update-format\/?", UpadteWorkflowAPIHandler),
        (r"/model_builder/api/workflow/import-obs-data\/?", ImportObsDataAPIHandler),
        (r"/model_builder/api/workflow/obs-data-files\/?", LoadObsDataFiles),
        (r"/model_builder/api/workflow/preview-obs-data\/?", PreviewOBSDataAPIHandler),
        (r"/model_builder/api/job/presentation\/?", JobPresentationAPIHandler),
        (r"/model_builder/api/job/csv\/?", DownloadCSVZipAPIHandler),
        (r"/model_builder/api/job/export-inferred-model\/?", ExportInferredModelAPIHandler)
    ]
    full_handlers = list(map(lambda h: (url_path_join(route_start, h[0]), h[1]), handlers))
    return full_handlers


def load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    page_handlers = get_page_handlers(web_app.settings['base_url'])
    web_app.add_handlers(host_pattern, page_handlers)
    init_log()

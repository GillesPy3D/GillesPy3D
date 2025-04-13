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

import traceback

def report_error(handler, log, err):
    '''
    Report a model_builder error to the front end

    Attributes
    ----------
    handler : obj
        Jupyter Notebook API Handler
    log : obj
        GillesPy3D log
    '''
    handler.set_status(err.status_code)
    error = {"Reason":err.reason, "Message":err.message}
    if err.traceback is None:
        trace = traceback.format_exc()
    else:
        trace = err.traceback
    log.error("Exception information: %s\n%s", error, trace)
    error['Traceback'] = trace
    handler.write(error)

def report_critical_error(handler, log, err):
    '''
    Report a critical model_builder error to the front end.

    Attributes
    ----------
    handler : obj
        Jupyter Notebook API Handler
    log : obj
        GillesPy3D log
    '''
    handler.set_status(500)
    error = {"Reason":"Uncaught Critical Error", "Message":str(err)}
    trace = traceback.format_exc()
    log.error("Exception information: %s\n%s", error, trace)
    error['Traceback'] = trace
    handler.write(error)

class GillesPy3DAPIError(Exception):
    '''
    ################################################################################################
    GillesPy3D Base Api Handler Error
    ################################################################################################
    '''

    def __init__(self, status_code, reason, msg, trace):
        '''
        Base error for all model_builder api errors

        Attributes
        ----------
        status_code : int
            XML request status code
        reason : str
            Reason for the error
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__()
        self.status_code = status_code
        self.reason = reason
        self.message = msg
        self.traceback = trace


    def __str__(self):
        return f"{self.message}: \n{self.traceback}"



####################################################################################################
# File System Errors
####################################################################################################

class GillesPy3DFileExistsError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D File/Folder Exists API Handler Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the file/folder with the given path already exists

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "File Already Exists", msg, trace)


class GillesPy3DFileNotFoundError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D File/Folder Not Found API Handler Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the file/folder with the given path does not exist

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(404, "GillesPy3D File or Directory Not Found", msg, trace)


class GillesPy3DPermissionsError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D File/Folder Not Found API Handler Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the user does not have permission to modify the file/folder

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(403, "Permission Denied", msg, trace)


class GillesPy3DUnzipError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D Un-Zip Zip Archive API Handler Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that a problem occured during the extraction process for the zip archive

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(403, "Unable to Extract Contents", msg, trace)

####################################################################################################
# Model Errors
####################################################################################################

class FileNotJSONFormatError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D Model/Template Not In JSON Format
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the model or template file is not in proper JSON format

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "File Data Not JSON Format", msg, trace)


class GillesPy3DModelFormatError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D Model Not In Proper Format
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the model does not meet the current format requirements

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "GillesPy3D Model Not In Proper Format", msg, trace)


class DomainFormatError(GillesPy3DAPIError):
    '''
    ################################################################################################
    Domain File Not In Proper Format
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the domain file does not meet SpatialPy format requirements

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "Domain File Not In Proper Format", msg, trace)


class DomainUpdateError(GillesPy3DAPIError):
    '''
    ################################################################################################
    Domain File Can't Be Updated
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the domain file can't be updated as it may be a
        dependency of another doamin or a spatial model.

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(405, "Domain File Can't Be Updated.", msg, trace)


class DomainActionError(GillesPy3DAPIError):
    '''
    ################################################################################################
    Domain Action Failed to Initialize
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that an action for the a domain failed.

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "Domain Action Failed", msg, trace)


class DomainShapeError(GillesPy3DAPIError):
    '''
    ################################################################################################
    Domain Shape Failed to Initialize
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that a shape failed to initialize.

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "Domain Shape Failed", msg, trace)


class DomainTransformationError(GillesPy3DAPIError):
    '''
    ################################################################################################
    Domain Transformation Failed to Initialize
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that a transformation failed to initialize.

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "Domain Transformations Failed", msg, trace)

####################################################################################################
# Job Errors
####################################################################################################

class GillesPy3DJobError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D Job Errored During Run Time
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the job experienced an error during run

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(403, "Job Errored on Run", msg, trace)


class GillesPy3DJobNotCompleteError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D Job Has Not Completed
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the action requires a job to finish running before it can be executed

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(403, "Job Run Not Complete", msg, trace)


class PlotNotAvailableError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D Result Plot Not Found
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the requested plot was not found in the plots.json file

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(406, "Plot Figure Not Available", msg, trace)


class GillesPy3DJobResultsError(GillesPy3DAPIError):
    '''
    ################################################################################################
    GillesPy3D Job Results Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the job results object was corrupted

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(500, "Job Results Error", msg, trace)


####################################################################################################
# AWS Errors
####################################################################################################

class AWSConfigurationError(GillesPy3DAPIError):
    '''
    ################################################################################################
    AWS Configuration Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that GillesPy3D Compute configured to run jobs.

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(403, "AWS Configuration Error", msg, trace)

class AWSLauncherError(GillesPy3DAPIError):
    '''
    ################################################################################################
    AWS Launcher Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the GillesPy3D Compute launcher single node instance failed.

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(403, "AWS Launch Error", msg, trace)

class AWSTerminatorError(GillesPy3DAPIError):
    '''
    ################################################################################################
    AWS Terminator Error
    ################################################################################################
    '''

    def __init__(self, msg, trace=None):
        '''
        Indicates that the GillesPy3D Compute clean up failed.

        Attributes
        ----------
        msg : str
            Details on what caused the error
        trace : str
            Error traceback for the error
        '''
        super().__init__(403, "AWS Terminate Error", msg, trace)

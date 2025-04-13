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
import traceback

from gillespy2.sbml.SBMLimport import convert
from gillespy2.stochss.StochSSexport import export

from .model_builder_base import GillesPy3DBase
from .model_builder_errors import GillesPy3DFileNotFoundError

class GillesPy3DSBMLModel(GillesPy3DBase):
    '''
    ################################################################################################
    StochSS notebook object
    ################################################################################################
    '''

    def __init__(self, path, new=False, document=None):
        '''
        Intitialize a notebook object and if its new create it on the users file system

        Attributes
        ----------
        path : str
            Path to the sbml model file
        new : bool
            Indicates whether or not the file is new
        document : str
            Contents of the sbml model file
        '''
        super().__init__(path=path)
        if new:
            self.make_parent_dirs()
            sbml_path, changed = self.get_unique_path(name=self.get_file())
            if changed:
                self.path = sbml_path.replace(self.user_dir + '/', "")
            with open(sbml_path, "w") as sbml_file:
                sbml_file.write(document)


    def convert_to_gillespy(self):
        '''
        Convert the sbml model to a gillespy model and return it

        Attributes
        ----------
        '''
        path = self.get_path(full=True)
        if not os.path.exists(path):
            message = f"Could not find the sbml file: {path}"
            raise GillesPy3DFileNotFoundError(message, traceback.format_exc())

        g_model, errors = convert(path)
        errors = list(map(lambda error: error[0], errors))
        if g_model is None:
            errors.append("Error: could not convert the SBML Model to a GillesPy3D Model")
        return g_model, errors


    def convert_to_model(self, name=None, wkgp=False):
        '''
        Convert the sbml model to a model_builder model and return it with mdl path

        Attributes
        ----------
        '''
        g_model, errors = self.convert_to_gillespy() # GillesPy2 Model object
        if g_model is None:
            message = "ERROR! We were unable to convert the SBML Model into a GillesPy3D Model."
            return {"message":message, "errors":errors, "model":None}

        s_model = export(model=g_model, return_model_builder_model=True) # GillesPy3D Model in json format
        self.log("debug", f"Model: \n{json.dumps(s_model)}")

        s_file = f"{g_model.name}.mdl" if name is None else f"{name}.mdl"
        if wkgp:
            wkgp_path, changed = self.get_unique_path(name=f"{self.get_name(path=s_file)}.wkgp",
                                                      dirname=self.get_dir_name())
            if changed:
                s_file = s_file.replace(self.get_name(path=s_file), self.get_name(path=wkgp_path))
            s_path = os.path.join(wkgp_path, s_file)
        else:
            s_path = os.path.join(self.get_dir_name(), s_file)

        message = "The SBML Model was successfully converted to a GillesPy3D Model."
        return {"message":message, "errors":errors, "model":s_model, "path":s_path}

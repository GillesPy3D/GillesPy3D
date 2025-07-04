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
import ast
import json
import hashlib
import logging
import traceback

import numpy
import plotly

import spatialpy

from presentation_base import GillesPy3DBase, get_presentation_from_user
from presentation_error import GillesPy3DAPIError, DomainUpdateError, GillesPy3DModelFormatError, \
                               report_error

from jupyterhub.handlers.base import BaseHandler

log = logging.getLogger('gillespy3d')

# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods
class JsonFileAPIHandler(BaseHandler):
    '''
    ################################################################################################
    Base Handler for getting model presentations from user containers.
    ################################################################################################
    '''
    async def get(self):
        '''
        Load the model presentation from User's presentations directory.

        Attributes
        ----------
        '''
        owner = self.get_query_argument(name="owner")
        log.debug(f"Container id of the owner: {owner}")
        file = self.get_query_argument(name="file")
        log.debug(f"Name to the file: {file}")
        self.set_header('Content-Type', 'application/json')
        try:
            process_funcs = {
                "mdl": process_wmmodel_presentation, "smdl": process_smodel_presentation
            }
            ext = file.split(".").pop()
            model = get_presentation_from_user(
                owner=owner, file=file, kwargs={"file": file}, process_func=process_funcs[ext]
            )
            log.debug(f"Contents of the json file: {model['model']}")
            self.write(model)
        except GillesPy3DAPIError as load_err:
            report_error(self, log, load_err)
        self.finish()


class DownModelPresentationAPIHandler(BaseHandler):
    '''
    ################################################################################################
    Base Handler for downloading model presentations from user containers.
    ################################################################################################
    '''
    async def get(self, owner, file):
        '''
        Download the model presentation from User's presentations directory.

        Attributes
        ----------
        '''
        log.debug(f"Container id of the owner: {owner}")
        log.debug(f"Name to the file: {file}")
        self.set_header('Content-Type', 'application/json')
        try:
            process_funcs = {
                "mdl": process_wmmodel_presentation, "smdl": process_smodel_presentation
            }
            ext = file.split(".").pop()
            data = get_presentation_from_user(
                owner=owner, file=file, kwargs={"for_download": True},
                process_func=process_funcs[ext]
            )
            if "name" in data:
                filename = f"{data['name']}.{ext}"
            else:
                filename = f"{data['model']['name']}.{ext}"
            self.set_header('Content-Disposition', f'attachment; filename="{filename}"')
            log.debug(f"Contents of the json file: {data}")
            self.write(data)
        except GillesPy3DAPIError as load_err:
            report_error(self, log, load_err)
        self.finish()


def process_wmmodel_presentation(path, for_download=False, **kwargs):
    '''
    Get the model presentation data from the file.

    Attributes
    ----------
    path : str
        Path to the model presentation file.
    for_download : bool
        Whether or not the model presentation is being downloaded.
    '''
    with open(path, "r", encoding="utf-8") as mdl_file:
        model = json.load(mdl_file)
    if for_download:
        return model
    file_obj = GillesPy3DModel(model=model)
    model_pres = file_obj.load()
    file_obj.print_logs(log)
    return model_pres

def process_smodel_presentation(path, for_download=False, **kwargs):
    '''
    Get the model presentation data from the file.

    Attributes
    ----------
    path : str
        Path to the model presentation file.
    for_download : bool
        Whether or not the model presentation is being downloaded.
    '''
    with open(path, "r", encoding="utf-8") as mdl_file:
        body = json.load(mdl_file)
    if "files" not in body:
        body = GillesPy3DSpatialModel(model=body).load(v1_domain=True)
    if for_download:
        return GillesPy3DSpatialModel.get_presentation(**body)
    for entry in body['files'].values():
        if not os.path.exists(os.path.dirname(entry['pres_path'])):
            os.makedirs(os.path.dirname(entry['pres_path']))
        with open(entry['pres_path'], "w", encoding="utf-8") as entry_fd:
            entry_fd.write(entry['body'])
    file_obj = GillesPy3DSpatialModel(model=body['model'])
    model_pres = file_obj.load()
    file_obj.print_logs(log)
    return model_pres

template = {
    "is_spatial": False, "defaultID": 1, "defaultMode": "", "annotation": "", "volume": 1,
    "modelSettings": {"endSim": 20, "timeStep": 0.05, "timestepSize": 1e-5 },
    "domain": {
        "actions": [],
        "boundary_condition": {"reflect_x": True, "reflect_y": True, "reflect_z": True},
        "c_0": 10, "gravity": [0, 0, 0], "p_0": 100.0, "rho_0": 1.0, "shapes": [],
        "size": None, "static": True, "template_version": 2, "transformations": [],
        "types": [{
            "c":10, "fixed":False, "mass":1.0, "name":"Un-Assigned",
            "nu":0.0, "rho":1.0, "typeID":0, "volume":1.0
        }],
        "x_lim": [0, 0], "y_lim": [0, 0], "z_lim": [0, 0]
    },
    "species": [], "initialConditions": [], "parameters": [], "reactions": [], "rules": [],
    "eventsCollection": [], "functionDefinitions": [], "boundaryConditions": []
}

class GillesPy3DModel(GillesPy3DBase):
    '''
    ################################################################################################
    GillesPy3D model object
    ################################################################################################
    '''

    def __init__(self, model):
        '''
        Intitialize a model object

        Attributes
        ----------
        model : dict
            Existing model data
        '''
        super().__init__()
        self.model = model

    @classmethod
    def __update_event_assignments(cls, event, param_ids):
        if "eventAssignments" not in event.keys():
            return
        for assignment in event['eventAssignments']:
            try:
                if assignment['variable']['compID'] in param_ids:
                    expression = ast.literal_eval(assignment['variable']['expression'])
                    assignment['variable']['expression'] = expression
            except KeyError:
                pass
            except ValueError:
                pass

    def __update_events(self, param_ids):
        if "eventsCollection" not in self.model.keys() or not param_ids:
            return
        for event in self.model['eventsCollection']:
            self.__update_event_assignments(event=event, param_ids=param_ids)

    def __update_parameters(self):
        if "parameters" not in self.model.keys():
            return []
        param_ids = []
        for param in self.model['parameters']:
            try:
                param_ids.append(param['compID'])
                if isinstance(param['expression'], str):
                    param['expression'] = ast.literal_eval(param['expression'])
            except KeyError:
                pass
            except ValueError:
                pass
        return param_ids

    def __update_reactions(self):
        if "reactions" not in self.model.keys():
            return
        for reaction in self.model['reactions']:
            if "odePropensity" not in reaction.keys():
                reaction['odePropensity'] = reaction['propensity']
            try:
                if reaction['rate'].keys() and isinstance(reaction['rate']['expression'], str):
                    expression = ast.literal_eval(reaction['rate']['expression'])
                    reaction['rate']['expression'] = expression
            except KeyError:
                pass
            except ValueError:
                pass

    def __update_rules(self, param_ids):
        if "rules" not in self.model.keys() or not param_ids:
            return
        for rule in self.model['rules']:
            try:
                if rule['variable']['compID'] in param_ids:
                    expression = ast.literal_eval(rule['variable']['expression'])
                    rule['variable']['expression'] = expression
            except KeyError:
                pass
            except ValueError:
                pass

    def __update_model_to_current(self):
        if self.model['template_version'] == self.TEMPLATE_VERSION:
            return

        if "annotation" not in self.model.keys():
            self.model['annotation'] = ""
        if "volume" not in self.model.keys():
            if "volume" in self.model['modelSettings'].keys():
                self.model['volume'] = self.model['modelSettings']['volume']
            else:
                self.model['volume'] = 1

        param_ids = self.__update_parameters()
        self.__update_reactions()
        self.__update_events(param_ids=param_ids)
        self.__update_rules(param_ids=param_ids)

        if "refLinks" not in self.model.keys():
            self.model['refLinks'] = []

        self.model['template_version'] = self.TEMPLATE_VERSION

    def load(self):
        '''
        Reads the model file, updates the model to the current format, and stores it in self.model

        Attributes
        ----------
        '''
        if "template_version" not in self.model:
            self.model['template_version'] = 0
        self.__update_model_to_current()

        return {"model": self.model, "diff": self.diff}


class GillesPy3DSpatialModel(GillesPy3DBase):
    '''
    ################################################################################################
    GillesPy3D spatial model object
    ################################################################################################
    '''
    def __init__(self, model):
        '''
        Intitialize a spatial model object

        Attributes
        ----------
        model : dict
            Existing model data
        '''
        super().__init__()
        self.model = model

    @classmethod
    def __build_geometry(cls, geometry, name=None, formula=None):
        if formula is None:
            formula = geometry['formula']
        if name is None:
            name = geometry['name']

        class NewGeometry(spatialpy.Geometry): # pylint: disable=too-few-public-methods
            '''
            ########################################################################################
            Custom SpatialPy Geometry
            ########################################################################################
            '''
            __class__ = f"__main__.{name}"
            def __init__(self):
                pass

            def inside(self, point, on_boundary): # pylint: disable=no-self-use
                ''' Custom inside function for geometry. '''
                namespace = {'x': point[0], 'y': point[1], 'z': point[2], 'on_boundary': on_boundary}
                return eval(formula, {}, namespace)
        return NewGeometry()

    @classmethod
    def __build_model_builder_domain_particles(cls, domain):
        particles = []
        for i, vertex in enumerate(domain.vertices):
            viscosity = domain.nu[i]
            fixed = bool(domain.fixed[i])
            type_id = domain.typeNdxMapping[domain.type_id[i]]
            particle = {
                "particle_id": i + 1, "point": list(vertex), "type": type_id,
                "volume": domain.vol[i], "mass": domain.mass[i], "nu": viscosity,
                "rho": domain.rho[i], "c": domain.c[i], "fixed": fixed
            }
            particles.append(particle)
        return particles

    def __convert_actions(self, domain, s_domain, type_ids):
        geometries, lattices = self.__convert_shapes(s_domain)
        transformations = self.__convert_transformations(s_domain)
        try:
            actions = list(filter(lambda action: action['enable'], s_domain['actions']))
            actions = sorted(actions, key=lambda action: action['priority'])
            for i, action in enumerate(actions):
                # Build props arg
                if action['type'] in ('Fill Action', 'Set Action', 'XML Mesh', 'Mesh IO'):
                    kwargs = {
                        'mass': action['mass'], 'vol': action['vol'], 'rho': action['rho'],
                        'nu': action['nu'], 'c': action['c'], 'fixed': action['fixed']
                    }
                    if action['type'] in ('Fill Action', 'Set Action'):
                        kwargs['type_id'] = type_ids[action['typeID']].replace("-", "")
                else:
                    kwargs = {}
                # Apply actions
                if action['type'] == "Fill Action":
                    if action['scope'] == 'Multi Particle':
                        geometry = geometries[f"{action['shape']}_geom"]
                        if action['transformation'] == "":
                            lattice = lattices[f"{action['shape']}_latt"]
                        else:
                            lattice = transformations[action['transformation']]
                            lattice.lattice = lattices[f"{action['shape']}_latt"]
                        _ = domain.add_fill_action(
                            lattice=lattice, geometry=geometry, enable=action['enable'],
                            apply_action=action['enable'], **kwargs
                        )
                    else:
                        point = [action['point']['x'], action['point']['y'], action['point']['z']]
                        domain.add_point(point, **kwargs)
                elif action['type'] in ('XML Mesh', 'Mesh IO', 'GillesPy3D Domain'):
                    lattices = {
                        'XML Mesh': spatialpy.XMLMeshLattice, 'Mesh IO': spatialpy.MeshIOLattice,
                        'GillesPy3D Domain': spatialpy.StochSSLattice
                    }
                    filename = os.path.join(self.user_dir, action['filename'])
                    if action['type'] == "GillesPy3D Domain" or action['subdomainFile'] == "":
                        lattice = lattices[action['type']](filename)
                    else:
                        subdomain_file = os.path.join(self.user_dir, action['subdomainFile'])
                        lattice = lattices[action['type']](filename, subdomain_file=subdomain_file)
                    _ = domain.add_fill_action(
                        lattice=lattice, enable=action['enable'], apply_action=action['enable'], **kwargs
                    )
                else:
                    # Get proper geometry for scope
                    # 'Single Particle' scope creates a geometry using actions point.
                    if action['scope'] == 'Single Particle':
                        p_x = action['point']['x']
                        p_y = action['point']['y']
                        p_z = action['point']['z']
                        formula = f"x == {p_x} and y == {p_y} and z == {p_z}"
                        geometry = self.__build_geometry(
                            None, name=f"SPAGeometry{i + 1}", formula=formula
                        )
                    elif action['transformation'] == "":
                        geometry = geometries[f"{action['shape']}_geom"]
                    else:
                        geometry = transformations[action['transformation']]
                        geometry.geometry = geometries[f"{action['shape']}_geom"]
                    if action['type'] == "Set Action":
                        domain.add_set_action(
                            geometry=geometry, enable=action['enable'],
                            apply_action=action['enable'], **kwargs
                        )
                        if action['scope'] == "Single Particle":
                            curr_pnt = numpy.array([
                                action['point']['x'], action['point']['y'], action['point']['z']
                            ])
                            new_pnt = numpy.array([
                                action['newPoint']['x'], action['newPoint']['y'],
                                action['newPoint']['z']
                            ])
                            if numpy.count_nonzero(curr_pnt - new_pnt) > 0:
                                for j, vertex in enumerate(domain.vertices):
                                    if numpy.count_nonzero(curr_pnt - vertex) <= 0:
                                        domain.vertices[j] = new_pnt
                                        break
                    else:
                        domain.add_remove_action(
                            geometry=geometry, enable=action['enable'],
                            apply_action=action['enable']
                        )
        except KeyError as err:
            message = "Spatial actions are not properly formatted or "
            message += f"are referenced incorrectly: {str(err)}"
            raise GillesPy3DModelFormatError(message, traceback.format_exc()) from err

    def __convert_domain(self, type_ids, s_domain):
        try:
            xlim = tuple(s_domain['x_lim'])
            ylim = tuple(s_domain['y_lim'])
            zlim = tuple(s_domain['z_lim'])
            rho0 = s_domain['rho_0']
            c_0 = s_domain['c_0']
            p_0 = s_domain['p_0']
            gravity = s_domain['gravity']
            if gravity == [0, 0, 0]:
                gravity = None
            domain = spatialpy.Domain(0, xlim, ylim, zlim, rho0=rho0, c0=c_0, P0=p_0, gravity=gravity)
            self.__convert_actions(domain, s_domain, type_ids)
            self.__convert_types(domain, type_ids)
            return domain
        except KeyError as err:
            message = "Spatial model domain properties are not properly formatted or "
            message += f"are referenced incorrectly: {str(err)}"
            raise GillesPy3DModelFormatError(message, traceback.format_exc()) from err

    def __convert_shapes(self, s_domain):
        try:
            geometries = {}
            comb_geoms = []
            lattices = {}
            for s_shape in s_domain['shapes']:
                # Create geometry from shape
                geo_name = f"{s_shape['name']}_geom"
                if s_shape['type'] == "Standard":
                    if s_shape['formula'] in ("", "True"):
                        geometries[geo_name] = spatialpy.GeometryAll()
                    elif s_shape['formula'] == "on_boundary":
                        geometries[geo_name] = spatialpy.GeometryExterior()
                    elif s_shape['formula'] == "not on_boundary":
                        geometries[geo_name] = spatialpy.GeometryInterior()
                    else:
                        geometries[geo_name] = self.__build_geometry(None, name=geo_name, formula=s_shape['formula'])
                else:
                    geometry = spatialpy.CombinatoryGeometry("", {})
                    geometry.formula = s_shape['formula']
                    geometries[geo_name] = geometry
                    comb_geoms.append(geo_name)
                # Create lattice from shape if fillable
                if s_shape['fillable']:
                    lat_name = f"{s_shape['name']}_latt"
                    if s_shape['lattice'] == "Cartesian Lattice":
                        half_length = s_shape['length'] / 2
                        half_height = s_shape['height'] / 2
                        half_depth = s_shape['depth'] / 2
                        lattice = spatialpy.CartesianLattice(
                            -half_length, half_length, s_shape['deltax'],
                            ymin=-half_height, ymax=half_height, deltay=s_shape['deltay'],
                            zmin=-half_depth, zmax=half_depth, deltaz=s_shape['deltaz']
                        )
                    elif s_shape['lattice'] == "Spherical Lattice":
                        lattice = spatialpy.SphericalLattice(
                            s_shape['radius'], s_shape['deltas'], deltar=s_shape['deltar']
                        )
                    elif s_shape['lattice'] == "Cylindrical Lattice":
                        lattice = spatialpy.CylindricalLattice(
                            s_shape['radius'], s_shape['length'], s_shape['deltas'], deltar=s_shape['deltar']
                        )
                    lattices[lat_name] = lattice
            items = [' and ', ' or ', ' not ', '(', ')']
            for name in comb_geoms:
                formula = geometries[name].formula
                if formula.startswith("not "):
                    formula = formula.replace("not ", "")
                for item in items:
                    formula = formula.replace(item, " ")
                formula = formula.split(" ")
                geo_namespace = {}
                for key, geometry in geometries.items():
                    if key != name and key[:-5] in formula:
                        geo_namespace[key[:-5]] = geometry
                geometries[name].geo_namespace = geo_namespace
            return geometries, lattices
        except KeyError as err:
            message = "Spatial domain shapes are not properly formatted or "
            message += f"are referenced incorrectly: {str(err)}"
            raise GillesPy3DModelFormatError(message, traceback.format_exc()) from err

    @classmethod
    def __convert_types(cls, domain, type_ids):
        domain.typeNdxMapping = {"type_UnAssigned": 0}
        domain.typeNameMapping = {0: "type_UnAssigned"}
        domain.listOfTypeIDs = [0]
        for ndx, name in type_ids.items():
            if ndx not in domain.typeNameMapping:
                name = f"type_{name}"
                domain.typeNdxMapping[name] = ndx
                domain.typeNameMapping[ndx] = name
                domain.listOfTypeIDs.append(ndx)
        types = list(set(domain.type_id))
        for name in types:
            if name not in domain.typeNdxMapping:
                ndx = len(domain.typeNdxMapping)
                domain.typeNdxMapping[name] = ndx
                domain.typeNameMapping[ndx] = name
                domain.listOfTypeIDs.append(ndx)

    @classmethod
    def __convert_transformations(cls, s_domain):
        try:
            transformations = {}
            nested_trans = {}
            for s_transformation in s_domain['transformations']:
                name = s_transformation['name']
                if s_transformation['transformation'] != "":
                    nested_trans[name] = s_transformation['transformation']
                if s_transformation['type'] in ("Translate Transformation", "Rotate Transformation"):
                    vector = [
                        [
                            s_transformation['vector'][0]['x'],
                            s_transformation['vector'][0]['y'],
                            s_transformation['vector'][0]['z']
                        ],
                        [
                            s_transformation['vector'][1]['x'],
                            s_transformation['vector'][1]['y'],
                            s_transformation['vector'][1]['z']
                        ]
                    ]

                    if s_transformation['type'] == "Translate Transformation":
                        transformation = spatialpy.TranslationTransformation(vector)
                    else:
                        transformation = spatialpy.RotationTransformation(vector, s_transformation['angle'])
                elif s_transformation['type'] == "Reflect Transformation":
                    normal = numpy.array([
                        s_transformation['normal']['x'], s_transformation['normal']['y'],
                        s_transformation['normal']['z']
                    ])
                    point1 = numpy.array([
                        s_transformation['point1']['x'], s_transformation['point1']['y'],
                        s_transformation['point1']['z']
                    ])
                    point2 = numpy.array([
                        s_transformation['point2']['x'], s_transformation['point2']['y'],
                        s_transformation['point2']['z']
                    ])
                    point3 = numpy.array([
                        s_transformation['point3']['x'], s_transformation['point3']['y'],
                        s_transformation['point3']['z']
                    ])
                    if numpy.count_nonzero(point3 - point1) <= 0 or \
                                numpy.count_nonzero(point2 - point1) <= 0:
                        point2 = None
                        point3 = None
                    else:
                        normal = None
                    transformation = spatialpy.ReflectionTransformation(
                        point1, normal=normal, point2=point2, point3=point3
                    )
                else:
                    center = numpy.array([
                        s_transformation['center']['x'], s_transformation['center']['y'],
                        s_transformation['center']['z']
                    ])
                    transformation = spatialpy.ScalingTransformation(s_transformation['factor'], center=center)
                transformations[name] = transformation
            for trans, nested_tran in nested_trans.items():
                transformations[trans].transformation = transformations[nested_tran]
            return transformations
        except KeyError as err:
            message = "Spatial transformations are not properly formatted or "
            message += f"are referenced incorrectly: {str(err)}"
            raise GillesPy3DModelFormatError(message, traceback.format_exc()) from err

    @classmethod
    def __get_trace_data(cls, particles, name="", index=None, dimensions=3):
        common_rgb_values = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
            '#bcbd22', '#17becf', '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#00ffff', '#ff00ff',
            '#800000', '#808000', '#008000', '#800080', '#008080', '#000080', '#ff9999', '#ffcc99',
            '#ccff99', '#cc99ff', '#ffccff', '#62666a', '#8896bb', '#77a096', '#9d5a6c', '#9d5a6c',
            '#eabc75', '#ff9600', '#885300', '#9172ad', '#a1b9c4', '#18749b', '#dadecf', '#c5b8a8',
            '#000117', '#13a8fe', '#cf0060', '#04354b', '#0297a0', '#037665', '#eed284', '#442244',
            '#ffddee', '#702afb'
        ]
        ids = []
        x_data = []
        y_data = []
        z_data = []
        for particle in particles:
            ids.append(str(particle['particle_id']))
            x_data.append(particle['point'][0])
            y_data.append(particle['point'][1])
            z_data.append(particle['point'][2])
        marker = {"size":5}
        if index is not None:
            marker["color"] = common_rgb_values[(index) % len(common_rgb_values)]
        if dimensions == 2:
            return plotly.graph_objs.Scatter(
                ids=ids, x=x_data, y=y_data, name=name, mode="markers", marker=marker
            )
        return plotly.graph_objs.Scatter3d(
            ids=ids, x=x_data, y=y_data, z=z_data, name=name, mode="markers", marker=marker
        )

    def __update_domain_to_current(self, domain=None):
        domain = self.model['domain']

        if domain['template_version'] == self.DOMAIN_TEMPLATE_VERSION:
            return None

        self.__update_domain_to_v1(domain)
        # Create version 1 domain directory if needed.
        v1_dir = os.path.join('/tmp/presentation_cache', f"{self.model['name']}_domain_files")
        if not os.path.exists(v1_dir):
            os.mkdir(v1_dir)
        # Get the file name for the version 1 domain file
        v1_domain = None
        file = self.get_file().replace(".smdl", ".domn")
        filename = os.path.join(v1_dir, file)
        if self.path == filename:
            errmsg = f"{self.get_file()} may be a dependency of another doamin (.domn) "
            errmsg += "or a spatial model (.smdl) and can't be updated."
            raise DomainUpdateError(errmsg)
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as v1_domain_fd:
                v1_domain = json.dumps(json.load(v1_domain_fd), sort_keys=True, indent=4)
            curr_domain = json.dumps(domain, sort_keys=True, indent=4)
            if v1_domain != curr_domain:
                filename, _ = self.get_unique_path(
                    self.get_file().replace(".smdl", ".domn"), dirname=v1_dir
                )
                v1_domain = None
        entry = {
            'body': json.dumps(domain, sort_keys=True, indent=4), 'name': file,
            'dwn_path': os.path.join(f"{self.model['name']}_domain_files", file),
            'pres_path': filename
        }

        shapes = []
        for d_type in domain['types']:
            if 'geometry' in d_type and d_type['geometry']:
                shapes.append({
                    'deltar': 0, 'deltas': 0, 'deltax': 0, 'deltay': 0, 'deltaz': 0, 'depth': 0, 'fillable': False,
                    'formula': d_type['geometry'], 'height': 0, 'lattice': 'Cartesian Lattice',
                    'length': 0, 'name': f"shape{len(shapes) + 1}", 'radius': 0, 'type': 'Standard'
                })
        domain['actions'] = [{
            'type': 'GillesPy3D Domain', 'scope': 'Multi Particle', 'priority': 1, 'enable': True, 'shape': '',
            'transformation': '', 'filename': filename.replace(f'{self.user_dir}/', ''), 'subdomainFile': '',
            'point': {'x': 0, 'y': 0, 'z': 0}, 'newPoint': {'x': 0, 'y': 0, 'z': 0},
            'c': 10, 'fixed': False, 'mass': 1.0, 'nu': 0.0, 'rho': 1.0, 'typeID': 0, 'vol': 0.0
        }]
        domain['shapes'] = shapes
        domain['transformations'] = []
        domain['template_version'] = self.DOMAIN_TEMPLATE_VERSION

        return {'lattice1': entry}

    @classmethod
    def __update_domain_to_v1(cls, domain=None):
        if domain['template_version'] == 1:
            return

        if "static" not in domain.keys():
            domain['static'] = True
        type_changes = {}
        for i, d_type in enumerate(domain['types']):
            if d_type['typeID'] != i:
                type_changes[d_type['typeID']] = i
                d_type['typeID'] = i
            if "rho" not in d_type.keys():
                d_type['rho'] = d_type['mass'] / d_type['volume']
            if "c" not in d_type.keys():
                d_type['c'] = 10
            if "geometry" not in d_type.keys():
                d_type['geometry'] = ""
        if domain['particles']:
            for particle in domain['particles']:
                if particle['type'] in type_changes:
                    particle['type'] = type_changes[particle['type']]
                if "rho" not in particle.keys():
                    particle['rho'] = particle['mass'] / particle['volume']
                if "c" not in particle.keys():
                    particle['c'] = 10

    def __update_model_to_current(self):
        if self.model['template_version'] == self.TEMPLATE_VERSION:
            return

        if not self.model['defaultMode']:
            self.model['defaultMode'] = "discrete"
        elif self.model['defaultMode'] == "dynamic":
            self.model['defaultMode'] = "discrete-concentration"
        if "timestepSize" not in self.model['modelSettings'].keys():
            self.model['modelSettings']['timestepSize'] = 1e-5
        if "boundaryConditions" not in self.model.keys():
            self.model['boundaryConditions'] = []
        for species in self.model['species']:
            if "types" not in species.keys():
                species['types'] = list(range(1, len(self.model['domain']['types'])))
            if "diffusionConst" not in species.keys():
                if "diffusionCoeff" not in species.keys():
                    diff = 0.0
                else:
                    diff = species['diffusionCoeff']
                species['diffusionConst'] = diff
        for reaction in self.model['reactions']:
            if "odePropensity" not in reaction.keys():
                reaction['odePropensity'] = reaction['propensity']
            if "types" not in reaction.keys():
                reaction['types'] = list(range(1, len(self.model['domain']['types'])))

        self.model['template_version'] = self.TEMPLATE_VERSION

    @classmethod
    def get_presentation(cls, model=None, files=None):
        ''' Get the presentation for download. '''
        # Process file based lattices
        file_based_types = ('XML Mesh', 'Mesh IO', 'GillesPy3D Domain')
        for action in model['domain']['actions']:
            if action['type'] in file_based_types:
                action_id = hashlib.md5(json.dumps(action, sort_keys=True, indent=4).encode('utf-8')).hexdigest()
                action['filename'] = files[action_id]['dwn_path']
                if action['subdomainFile'] != "":
                    entry = files[f"{action_id}_sdf"]
                    action['subdomainFile'] = entry['dwn_path']
        return {'model': model, 'files': files}

    def get_domain_plot(self, domain, s_domain):
        '''
        Get a plotly plot of the models domain or a prospective domain

        Attributes
        ----------
        domain : spatialpy.Domain
            SpatialPy domain object used to generate plot data.
        s_domain : model_builder.Domain
            GillesPy3D domain object used to generate plot data.
        '''
        fig = domain.plot_types(return_plotly_figure=True)
        # Case #3: 1 or more particles and one type
        if len(s_domain['types']) == 1:
            fig['data'][0]['name'] = "Un-Assigned"
            ids = list(map(lambda particle: particle['particle_id'], s_domain['particles']))
            fig['data'][0]['ids'] = ids
        # Case #4: 1 or more particles and multiple types
        else:
            for index, d_type in enumerate(s_domain['types']):
                if d_type['name'] == "Un-Assigned":
                    t_test = lambda trace: trace['name'] in ("Un-Assigned", "UnAssigned")
                else:
                    t_test = lambda trace, name=d_type['name']: trace['name'] == name
                traces = list(filter(t_test, fig['data']))
                if len(traces) == 0:
                    fig['data'].insert(index, self.__get_trace_data(
                        particles=[], name=d_type['name'], index=index, dimensions=domain.dimensions
                    ))
                else:
                    particles = list(filter(
                        lambda particle, key=d_type['typeID']: particle['type'] == key,
                        s_domain['particles']
                    ))
                    ids = list(map(lambda particle: particle['particle_id'], particles))
                    trace = traces[0]
                    trace['name'] = d_type['name']
                    trace['ids'] = ids
        fig['layout']['width'] = None
        fig['layout']['height'] = None
        fig['layout']['autosize'] = True
        fig['config'] = {"responsive":True}
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def load(self, v1_domain=False):
        '''
        Reads the spatial model file, updates it to the current format, and stores it in self.model
        '''
        if "template_version" not in self.model:
            self.model['template_version'] = 0
        self.__update_model_to_current()

        if "template_version" not in self.model['domain']:
            self.model['domain']['template_version'] = 0
        files = self.__update_domain_to_current()

        if v1_domain:
            return {'model': self.model, 'files': files}
        plot, limits = self.load_action_preview()
        return {"model": self.model, "domainPlot": json.loads(plot), "domainLimits": limits}

    def load_action_preview(self):
        ''' Get a domain preview of all enabled actions. '''
        s_domain = self.model['domain']
        types = sorted(s_domain['types'], key=lambda d_type: d_type['typeID'])
        type_ids = {d_type['typeID']: d_type['name'] for d_type in types}
        domain = self.__convert_domain(type_ids, s_domain=s_domain)
        xlim, ylim, zlim = domain.get_bounding_box()
        limits = [list(xlim), list(ylim), list(zlim)]
        s_domain['particles'] = self.__build_model_builder_domain_particles(domain)
        plot = self.get_domain_plot(domain, s_domain)
        return plot, limits

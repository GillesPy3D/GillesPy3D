/*
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
*/

//models
let State = require('ampersand-state');
//collections
let Shapes = require('./shapes');
let Actions = require('./actions');
let Types = require('./domain-types');
let Transformations = require('./transformations');

module.exports = State.extend({
  props: {
    boundary_condition: 'object',
    c_0: 'number',
    gravity: 'object',
    p_0: 'number',
    rho_0: 'number',
    size: 'number',
    x_lim: 'object',
    y_lim: 'object',
    z_lim: 'object',
    static: 'boolean',
    template_version: 'number'
  },
  collections: {
    actions: Actions,
    shapes: Shapes,
    transformations: Transformations,
    types: Types
  },
  session: {
    def_particle_id: 'number',
    def_type_id: 'number',
    directory: 'string',
    dirname: 'string',
    particles: 'object',
    error: 'object'
  },
  initialize: function (attrs, options) {
    State.prototype.initialize.apply(this, arguments)
    this.def_type_id = this.types.length;
    this.types.forEach((type) => {
      if(type.typeID >= this.def_type_id) {
        this.def_type_id = type.typeID + 1;
      }
    });
  },
  getDefaultTypeID: function () {
    let id = this.def_type_id;
    this.def_type_id += 1;
    return id;
  },
  realignTypes: function (oldType) {
    this.def_type_id -= 1;
    this.types.forEach((type) => {
      if(type.typeID > oldType) {
        let id = type.typeID - 1;
        if(type.name === type.typeID.toString()) {
          type.name = id.toString();
        }
        type.typeID = id;
      }
    });
  },
  validateModel: function () {
    if(!this.types.validateCollection()) {
      this.error = {"type":"types"};
      return false;
    }
    if(!this.actions.validateCollection()) {
      this.error = {"type":"actions"};
      return false;
    }
    return true;
  },
  updateValid: function () {
    this.valid = this.validateModel()
  },
});
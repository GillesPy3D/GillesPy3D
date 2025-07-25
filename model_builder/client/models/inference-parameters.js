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
let InferenceParameter = require('./inference-parameter');
//collections
let Collection = require('ampersand-collection');

module.exports = Collection.extend({
  model: InferenceParameter,
  addInferenceParameter: function (paramID, name) {
    let variable = this.add({
      hasChangedRange: false,
      m: null,
      min: 0,
      max: 0,
      name: name,
      p: null,
      paramID: paramID,
      pm: null,
      s: null,
      u: null
    });
  },
  removeInferenceParameter: function (variable) {
    this.remove(variable);
  },
  updateVariables: function (parameters) {
    this.forEach((variable) => {
      let parameter = parameters.filter((parameter) => {
        return parameter.compID === variable.paramID;
      })[0];
      if(parameter === undefined) {
        this.removeVariable(variable);
      }else{
        variable.updateVariable(variable);
      }
    });
  }
});

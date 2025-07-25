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
var State = require('ampersand-state');

module.exports = State.extend({
  props: {
    compID: 'number',
    name: 'string',
    function: 'string',
    expression: 'string',
    variables: 'string',
    signature: 'string',
    annotation: 'string'
  },
  contains: function (attr, key) {
    if(key === null) { return true; }

    let checks = {
      'name': this.name.includes(key),
      'signature': this.name.includes(key),
      'expression': this.expression.includes(key)
    }

    if(attr !== null) {
      return checks[attr];
    }
    for(let attribute in checks) {
      if(checks[attribute]) { return true; }
    }
    return false;
  }
});
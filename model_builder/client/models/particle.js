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
    c: 'number',
    fixed: 'boolean',
    mass: 'number',
    nu: 'number',
    particle_id: 'number',
    point: 'object',
    rho: 'number',
    type: 'number',
    volume: 'number'
  },
  initialize: function (attrs, options) {
    State.prototype.initialize.apply(this, arguments)
  },
  comparePoint(point) {
    if(this.point.length !== point.length) { return false; }
    for(var i = 0; i < this.point.length; i++) {
      if(this.point[i] !== point[i]) { return false; }
    }
    return true;
  },
  validate: function () {
    return true;
  }
});

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

//views
let View = require('ampersand-view');
//templates
let template = require('../templates/includes/creatorListing.pug');

module.exports = View.extend({
  template: template,
  events: {
    'click [data-hook=remove-creator-btn]' : 'removeCreator'
  },
  initialize: function (attrs, options) {
    View.prototype.initialize.apply(this, arguments);
  },
  render: function (attrs, options) {
    View.prototype.render.apply(this, arguments);
  },
  removeCreator: function (e) {
    let index = this.parent.metadata.creators.indexOf(this.model.elementID);
    this.parent.metadata.creators.splice(index, 1);
    this.parent.renderCreatorListingView();
  }
});
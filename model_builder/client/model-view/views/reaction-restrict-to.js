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
let $ = require('jquery');
//views
let View = require('ampersand-view');
let DomainTypesView = require('./component-types');
//templates
let template = require('../templates/reactionRestrictTo.pug');

module.exports = View.extend({
  template: template,
  initialize: function (args) {
    View.prototype.initialize.apply(this, arguments);
    this.modelType = "reaction";
    this.baseModel = this.parent.parent.collection.parent;
  },
  render: function () {
    View.prototype.render.apply(this, arguments);
    this.renderDomainTypes();
    this.toggleRestrictToError();
    this.model.on('types-changed', this.toggleRestrictToError, this);
  },
  renderDomainTypes: function () {
    if(this.domainTypesView) {
      this.domainTypesView.remove();
    }
    this.domainTypesView = this.renderCollection(
      this.baseModel.domain.types,
      DomainTypesView,
      this.queryByHook("reaction-types-container"),
      {"filter": function (model) {
        return model.typeID != 0;
      }}
    );
  },
  toggleRestrictToError: function () {
    let errorMsg = $(this.queryByHook("restict-to-error"));
    if(this.model.types.length <= 0) {
      errorMsg.addClass('component-invalid');
      errorMsg.removeClass('component-valid');
    }else{
      errorMsg.addClass('component-valid');
      errorMsg.removeClass('component-invalid');
    }
  }
});
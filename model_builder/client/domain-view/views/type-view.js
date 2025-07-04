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
let path = require('path');
let _ = require('underscore');
//support files
let app = require('../../app');
let Tooltips = require('../../tooltips');
let tests = require('../../views/tests');
//views
let View = require('ampersand-view');
let InputView = require('../../views/input');
//templates
let editTemplate = require('../templates/editType.pug');
let viewTemplate = require('../templates/viewType.pug');

module.exports = View.extend({
  bindings: {
    'model.selected' : {
      type: function (el, value, previousValue) {
        el.checked = value;
      },
      hook: 'select'
    },
    'model.inUse': {
      hook: 'remove',
      type: 'booleanAttribute',
      name: 'disabled',
    }
  },
  events: {
    'change [data-hook=type-name]' : 'updateDepsOptions',
    'change [data-target=type-defaults]' : 'updateViewer',
    'change [data-hook=td-fixed]' : 'setTDFixed',
    'click [data-hook=select]' : 'selectType',
    'click [data-hook=remove]' : 'handleDeleteType',
  },
  initialize: function (attrs, options) {
    View.prototype.initialize.apply(this, arguments);
    this.viewMode = attrs.viewMode ? attrs.viewMode : false;
    this.tooltips = Tooltips.domainType;
  },
  render: function (attrs, options) {
    this.template = this.viewMode ? viewTemplate : editTemplate;
    View.prototype.render.apply(this, arguments);
    if(!this.viewMode) {
      if(this.model.selected) {
        setTimeout(_.bind(this.openTypeDetails, this), 1);
      }
    }
    $(this.queryByHook('view-td-fixed')).prop('checked', this.model.fixed)
    app.documentSetup();
  },
  handleDeleteType: function (e) {
    let typeID = this.model.typeID;
    let domain = this.model.collection.parent;
    let actions = domain.actions;
    this.model.collection.removeType(this.model);
    domain.trigger('update-particle-type-options', {currName: typeID});
    actions.trigger('update-type-options', {currName: typeID});
  },
  openTypeDetails: function () {
    $("#collapse-type-details" + this.model.typeID).collapse("show");
  },
  selectType: function () {
    this.model.selected = !this.model.selected;
  },
  setTDFixed: function (e) {
    this.model.fixed = e.target.checked;
    this.updateViewer();
  },
  update: function () {},
  updateDepsOptions: function (e) {
    let typeID = this.model.typeID;
    this.model.name = e.target.value;
    this.updateViewer();
    this.model.collection.parent.trigger(
      'update-particle-type-options', {currName: typeID, newName: this.model.typeID}
    );
    this.model.collection.parent.actions.trigger(
      'update-type-options', {currName: typeID, newName: this.model.typeID}
    );
  },
  updateValid: function () {},
  updateViewer: function () {
    this.parent.renderViewTypeView();
  },
  subviews: {
    inputName: {
      hook: "type-name",
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'name',
          tests: [tests.invalidChar],
          valueType: 'string',
          value: this.model.name
        });
      }
    },
    inputMass: {
      hook: "td-mass",
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'mass',
          modelKey: 'mass',
          valueType: 'number',
          tests: tests.valueTests,
          value: this.model.mass
        });
      }
    },
    inputVolume: {
      hook: 'td-vol',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'volume',
          modelKey: 'volume',
          valueType: 'number',
          tests: tests.valueTests,
          value: this.model.volume
        });
      }
    },
    inputDensity: {
      hook: 'td-rho',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'density',
          modelKey: 'rho',
          valueType: 'number',
          tests: tests.valueTests,
          value: this.model.rho
        });
      }
    },
    inputViscosity: {
      hook: 'td-nu',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'viscosity',
          modelKey: 'nu',
          valueType: 'number',
          tests: tests.valueTests,
          value: this.model.nu
        });
      }
    },
    inputSpeedOfSound: {
      hook: 'td-c',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'speed-of-sound',
          modelKey: 'c',
          valueType: 'number',
          tests: tests.valueTests,
          value: this.model.c
        });
      }
    }
  }
});
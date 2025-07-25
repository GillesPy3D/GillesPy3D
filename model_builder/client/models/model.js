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

let _ = require('underscore');
//support files
var app = require('../app');
var path = require('path');
//models
var Model = require('ampersand-model');
var TimespanSettings = require('./timespan-settings');
var Domain = require('./domain');
//collections
var Species = require('./species');
var InitialConditions = require('./initial-conditions');
var Parameters = require('./parameters');
var Reactions = require('./reactions');
var Rules = require('./rules');
var Events = require('./events');
var FunctionDefinitions = require('./function-definitions');
var BoundaryConditions = require('./boundary-conditions');

module.exports = Model.extend({
  url: function () {
    return path.join(app.getApiPath(), "file/json-data")+"?for="+this.for+"&path="+this.directory;
  },
  props: {
    annotation: 'string',
    defaultID: 'number',
    defaultMode: 'string',
    is_spatial: 'boolean',
    refLinks: 'object',
    volume: 'any',
    template_version: 'number'
  },
  collections: {
    species: Species,
    initialConditions: InitialConditions,
    parameters: Parameters,
    reactions: Reactions,
    rules: Rules,
    eventsCollection: Events,
    functionDefinitions: FunctionDefinitions,
    boundaryConditions: BoundaryConditions
  },
  children: {
    modelSettings: TimespanSettings,
    domain: Domain
  },
  session: {
    name: 'string',
    selectedReaction: 'object',
    directory: 'string',
    isPreview: 'boolean',
    for: 'string',
    valid: 'boolean',
    error: 'object'
  },
  derived: {
    elementID: {
      deps: ["collection"],
      fn: function () {
        if(this.collection) {
          return "M" + (this.collection.indexOf(this) + 1);
        }
        return "M-";
      }
    },
    open: {
      deps: ["directory"],
      fn: function () {
        let queryStr = "?path=" + this.directory;
        return path.join(app.getBasePath(), "model_builder/models/edit") + queryStr;
      }
    }
  },
  initialize: function (attrs, options){
    Model.prototype.initialize.apply(this, arguments);
    this.species.on('add change remove', this.updateValid, this);
    this.parameters.on('add change remove', this.updateValid, this);
    this.reactions.on('add change remove', this.updateValid, this);
    this.eventsCollection.on('add change remove', this.updateValid, this);
    this.rules.on('add change remove', this.updateValid, this);
  },
  validateModel: function () {
    if(this.is_spatial && this.domain.validateModel() === false) {
      this.error = {"type":"domain"};
      return false;
    };
    if(!this.species.validateCollection(this.is_spatial)) { return false; }
    if(this.is_spatial && !this.initialConditions.validateCollection()) { return false; }
    if(!this.parameters.validateCollection()) { return false; }
    if(!this.reactions.validateCollection(this.is_spatial)) { return false; }
    if(!this.eventsCollection.validateCollection()) { return false; }
    if(!this.rules.validateCollection()) { return false; }
    if(!this.is_spatial && this.reactions.length <= 0 && this.eventsCollection.length <= 0 && this.rules.length <= 0) {
      this.error = {"type":"process"};
      return false;
    }
    if(!this.volume === "" || isNaN(this.volume)) {
      this.error = {"type":"volume"};
      return false;
    };
    if(this.modelSettings.validate(this.is_spatial) === false) {
      this.error = {"type":"timespan"};
      return false;
    };
    return true;
  },
  updateValid: function () {
    this.error = {};
    this.valid = this.validateModel();
  },
  getDefaultID: function () {
    var id = this.defaultID;
    this.defaultID += 1;
    return id;
  },
  autoSave: function () {
    let self = this;
    setTimeout(function () {
      app.postXHR(self.url(), self.toJSON(), { success: _.bind(self.autoSave, self) });
    }, 120000);
  },
  //called when save button is clicked
  saveModel: function (cb=null) {
    var self = this;
    this.species.map(function (specie) {
      self.species.trigger('update-species', specie.compID, specie, false, false);
    });
    this.parameters.map(function (parameter) {
      self.parameters.trigger('update-parameters', parameter.compID, parameter);
    });
    if(cb) {
      app.postXHR(this.url(), this.toJSON(), { success: cb });
    }else{
      app.postXHR(this.url(), this.toJSON());
    }
  },
});

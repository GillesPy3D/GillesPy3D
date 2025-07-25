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

var $ = require('jquery');
//support files
let app = require('../../app');
var tests = require('../../views/tests');
var Tooltips = require('../../tooltips');
//views
var View = require('ampersand-view');
var InputView = require('../../views/input');
//templates
var template = require('../templates/timespanSettingsView.pug');

module.exports = View.extend({
  template: template,
  events: {
    'click [data-hook=collapse]' : 'changeCollapseButtonText',
    'input [data-hook=timestep-size-slider]' : 'viewTimestepValue',
    'change [data-hook=preview-time]' : 'updateViewer',
    'change [data-hook=time-units]' : 'updateTimeStep',
    'change [data-hook=timestep-size-slider]' : 'setTimestepSize'
  },
  initialize: function (attrs, options) {
    View.prototype.initialize.apply(this, arguments);
    this.readOnly = attrs.readOnly ? attrs.readOnly : false;
    this.tooltips = Tooltips.modelSettings
    this.isSpatial = attrs.isSpatial;
    let tssValues = {1e-5: 5, 1e-4: 4, 1e-3: 3, 1e-2: 2, 1e-1: 1, 1: 0}
    this.tssValue = tssValues[this.model.timestepSize]
  },
  render: function () {
    View.prototype.render.apply(this, arguments);
    if(this.readOnly) {
      $(this.queryByHook(this.model.elementID + '-timespan-edit-tab')).addClass("disabled");
      $(".nav .disabled>a").on("click", function(e) {
        e.preventDefault();
        return false;
      });
      $(this.queryByHook(this.model.elementID + '-timespan-view-tab')).tab('show');
      $(this.queryByHook(this.model.elementID + '-edit-timespan')).removeClass('active');
      $(this.queryByHook(this.model.elementID + '-view-timespan')).addClass('active');
    }else{
      this.toggleTimestepSizeError();
    }
    if(this.isSpatial) {
      $(this.queryByHook("timestep-size-container")).css("display", "inline-block");
      $(this.queryByHook("timestep-size-value")).html(this.model.timestepSize);
    }
  },
  changeCollapseButtonText: function (e) {
    app.changeCollapseButtonText(this, e);
  },
  setTimestepSize: function (e) {
    this.model.timestepSize = Number("1e-" + e.target.value);
    $(this.queryByHook("view-timestep-size")).html(this.model.timestepSize);
    this.toggleTimestepSizeError();
  },
  toggleTimestepSizeError: function () {
    let errorMsg = $(this.queryByHook("timestep-size-error"));
    if(this.isSpatial && this.model.timestepSize > this.model.timeStep) {
      errorMsg.addClass('component-invalid');
      errorMsg.removeClass('component-valid');
    }else{
      errorMsg.addClass('component-valid');
      errorMsg.removeClass('component-invalid');
    }
  },
  update: function (e) {},
  updateTimeStep: function () {
    this.updateViewer();
    this.toggleTimestepSizeError();
  },
  updateValid: function () {},
  updateViewer: function (e) {
    $(this.queryByHook("view-end-sim")).html("0 to " + this.model.endSim);
    $(this.queryByHook("view-time-step")).html(this.model.timeStep);
  },
  viewTimestepValue: function (e) {
    let value = Number("1e-" + e.target.value);
    $(this.queryByHook("timestep-size-value")).html(value);
  },
  subviews: {
    inputSimEnd: {
      hook: 'preview-time',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'end-sim',
          label: '0 to ',
          tests: tests.valueTests,
          modelKey: 'endSim',
          valueType: 'number',
          value: this.model.endSim
        });
      }
    },
    inputTimeUnit: {
      hook: 'time-units',
      prepareView: function (el) {
        return new InputView ({
          parent: this,
          required: true,
          name: 'time-units',
          tests: tests.valueTests,
          modelKey: 'timeStep',
          valueType: 'number',
          value: this.model.timeStep
        });
      }
    }
  }
});
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

//support files
let tests = require('../../views/tests');
//views
let InputView = require('../../views/input');
let View = require('ampersand-view');
//templates
let editTemplate = require('../templates/editCustomSummaryStatView.pug');
let viewTemplate = require('../templates/viewCustomSummaryStatView.pug');

module.exports = View.extend({
  events: {
    'change [data-target=custom-property]' : 'updateViewer',
    'change [data-hook=summary-stat-args]' : 'setCalculatorArgs',
    'click [data-hook=remove]' : 'removeSummaryStat'
  },
  initialize: function (attrs, options) {
    View.prototype.initialize.apply(this, arguments);
    this.viewMode = attrs.viewMode ? attrs.viewMode : false;
    this.customCalculators = attrs.customCalculators ? attrs.customCalculators : null;
  },
  render: function (attrs, options) {
    this.template = this.viewMode ? viewTemplate : editTemplate;
    View.prototype.render.apply(this, arguments);
  },
  removeSummaryStat: function () {
    this.model.collection.removeSummaryStat(this.model);
  },
  setCalculatorArgs: function (e) {
    this.model.setArgs(e.target.value);
    this.updateViewer();
  },
  update: function () {},
  updateValid: function () {},
  updateViewer: function () {
    try{
      this.parent.updateViewer();
    }catch(error){
      this.parent.parent.updateViewer();
    }
  },
  subviews: {
    nameInputView: {
      hook: "summary-stat-name",
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'observable-name',
          modelKey: 'name',
          tests: tests.nameTests,
          changeTests: [(text) => {
            if(!this.customCalculators.includes(text)) {
              return "This feature calculator is not currently supported."
            }
          }],
          valueType: 'string',
          value: this.model.name,
          placeholder: "-- i.e. autocorrelation --"
        });
      }
    },
    formulaInputView: {
      hook: "summary-stat-args",
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: false,
          name: 'summary-calculator-args',
          changeTests: [(text) => {
            try{
              this.model.setArgs(text, {dryRun: true});
            }catch(error) {
              return `Args must be in one of the following formats '{"lag": 1}' or '{"lag": 1},{"lag": 2}'.`
            }
          }],
          valueType: 'string',
          value: this.model.argsDisplay === "None" ? "" : this.model.argsDisplay,
          placeholder: '-- i.e. Requires arguments: {"lag":1} or leave blank if no arguments are required --'
        });
      }
    }
  }
});

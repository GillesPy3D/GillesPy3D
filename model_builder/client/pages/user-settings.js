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
// support files
let app = require('../app');
let tests = require('../views/tests');
// models
let Settings = require('../models/user-settings');
// views
let PageView = require('./base');
let InputView = require('../views/input');
let SelectView = require('ampersand-select-view');
// templates
let template = require('../templates/pages/userSettings.pug');

import initPage from './page.js';

let userSettings = PageView.extend({
  template: template,
  events: {
    'change [data-hook=user-logs]' : 'toggleUserLogs',
    'click [data-hook=apply-user-settings]' : 'handleApplyUserSettings'
  },
  initialize: function (attrs, options) {
    PageView.prototype.initialize.apply(this, arguments);
    let urlParams = new URLSearchParams(window.location.search);
    this.path = urlParams.has('continue') ? urlParams.get('continue') : null;
    this.model = new Settings();
    this.secretKey = null;
    app.getXHR(this.model.url(), {
      success: (err, response, body) => {
        this.model.set(body.settings);
        this.model.modelLoaded = true;
        this.instances = body.instances;
        $(this.queryByHook('user-logs')).prop('checked', this.model.userLogs);
      }
    });
  },
  render: function (attrs, options) {
    PageView.prototype.render.apply(this, arguments);
    if(this.path !== null) {
      $(this.queryByHook('aws-config-msg')).css('display', 'block');
    }
  },
  completeAction: function () {
    $(this.queryByHook("usa-in-progress")).css("display", "none");
    $(this.queryByHook("usa-complete")).css("display", "inline-block");
    setTimeout(() => {
      $(this.queryByHook("usa-complete")).css("display", "none");
    }, 5000);
  },
  disables: function (btnType, status) {
    let disables = {
      instance: !['not configured', 'not launched', 'terminated'].includes(status),
      launch: !['not launched', 'terminated'].includes(status),
      refresh: status === "not configured",
      terminate: ['not configured', 'not launched', 'terminated'].includes(status)
    }
    return disables[btnType];
  },
  errorAction: function (action) {
    $(this.queryByHook("usa-in-progress")).css("display", "none");
    $(this.queryByHook("usa-action-error")).text(action);
    $(this.queryByHook("usa-error")).css("display", "block");
  },
  handleApplyUserSettings: function ({cb=null}={}) {
    this.startAction();
    if(cb === null) {
      if(this.path === null) {
        cb = () => {
          this.completeAction();
          this.refreshAWSStatus(); // look into later, breaks entire webpage
        }
      }else{
        cb = () => {
          window.location.href = this.path;
        }
      }
    }
    let options = this.secretKey !== null ? {secretKey: this.secretKey} : {};
    this.model.applySettings(cb, options);
  },
  startAction: function () {
    $(this.queryByHook("usa-complete")).css("display", "none");
    $(this.queryByHook("usa-error")).css("display", "none");
    $(this.queryByHook("usa-in-progress")).css("display", "inline-block");
  },
  toggleUserLogs: function (e) {
    this.model.userLogs = e.target.checked;
  },
  update: function () {},
  updateValid: function () {},
});

initPage(userSettings);

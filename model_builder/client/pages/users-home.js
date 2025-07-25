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
//support files
let app = require('../app');
let modals = require('../modals');
//collections
let Collection = require('ampersand-collection');
//model
let Presentation = require('../models/presentation')
//views
let PageView = require('./base');
let PresentationView = require('../views/presentation-view');
//templates
let template = require('../templates/pages/usersHome.pug');

import initPage from './page.js';

let usersHomePage = PageView.extend({
  template: template,
  events: {
    'click [data-hook=new-project-btn]' : 'handleNewProjectClick',
    'click [data-hook=browse-projects-btn]' : 'handleBrowseProjectsClick',
    'click [data-hook=quickstart-btn]' : 'handleQuickstartClick'
  },
  initialize: function (attrs, options) {
    PageView.prototype.initialize.apply(this, arguments)
    let urlParams = new URLSearchParams(window.location.search)
    if(urlParams.has("open")){
      let queryString = "?path=" + urlParams.get("open") + "&action=open";
      let endpoint = path.join(app.getBasePath(), 'model_builder/loading-page') + queryString;
      window.location.href = endpoint;
    }
  },
  render: function (attrs, options) {
    PageView.prototype.render.apply(this, arguments);
    app.documentSetup();
  },
  handleNewProjectClick: function (e) {
    let self = this
    if(document.querySelector("#newProjectModal")) {
      document.querySelector("#newProjectModal").remove()
    }
    let modal = $(modals.createProjectHtml()).modal()
    let okBtn = document.querySelector("#newProjectModal .ok-model-btn")
    let input = document.querySelector("#newProjectModal #projectNameInput")
    input.focus()
    input.addEventListener("keyup", function (event) {
      if(event.keyCode === 13){
        event.preventDefault();
        okBtn.click();
      }
    });
    input.addEventListener("input", function (e) {
      var endErrMsg = document.querySelector('#newProjectModal #projectNameInputEndCharError')
      var charErrMsg = document.querySelector('#newProjectModal #projectNameInputSpecCharError')
      let error = app.validateName(input.value)
      okBtn.disabled = error !== "" || input.value.trim() === ""
      charErrMsg.style.display = error === "both" || error === "special" ? "block" : "none"
      endErrMsg.style.display = error === "both" || error === "forward" ? "block" : "none"
    });
    okBtn.addEventListener("click", function (e) {
      if(Boolean(input.value)) {
        modal.modal('hide')
        let projectPath = input.value + ".proj"
        let queryString = "?path="+projectPath
        let endpoint = path.join(app.getApiPath(), "project/new-project")+queryString
        app.getXHR(endpoint, {
          success: function (err, response, body) {
            let projectQS = "?path="+body.path;
            let projectEP = path.join(app.getBasePath(), "model_builder/project/manager")+projectQS;
            self.navToPage(projectEP);
          },
          error: function (err, response, body) {
            if(document.querySelector("#errorModal")) {
              document.querySelector("#errorModal").remove();
            }
            let errorModel = $(modals.errorHtml(body.Reason, body.Message)).modal();
          }
        });
      }
    });
  },
  handleBrowseProjectsClick: function (e) {
    let endpoint = path.join(app.getBasePath(), "model_builder/files#project-browser-section")
    this.navToPage(endpoint)
  },
  handleQuickstartClick: function (e) {
    let endpoint = path.join(app.getBasePath(), "model_builder/quickstart")
    this.navToPage(endpoint)
  },
  navToPage: function (endpoint) {
    window.location.href = endpoint
  }
});

initPage(usersHomePage);
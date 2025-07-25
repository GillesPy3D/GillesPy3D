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
let tests = require('../../views/tests');
//views
let View = require('ampersand-view');
let InputView = require('../../views/input');
let SelectView = require('ampersand-select-view');
//templates
let editTemplate = require('../templates/editAction.pug');
let viewTemplate = require('../templates/viewAction.pug');

module.exports = View.extend({
  bindings: {
    'model.selected' : {
      type: function (el, value, previousValue) {
        el.checked = value;
      },
      hook: 'select-action'
    },
    'model.enable' : {
      type: function (el, value, previousValue) {
        el.checked = value;
      },
      hook: 'enable-action'
    }
  },
  events: {
    'change [data-hook=select-type-container]' : 'selectActionType',
    'change [data-hook=select-scope-container]' : 'selectActionScope',
    'change [data-target=update-preview-plot]' : 'updatePreviewPlot',
    'change [data-hook=shape-container]' : 'selectShape',
    'change [data-hook=transformation-container]' : 'selectTransformation',
    'change [data-target=point]' : 'setPoint',
    'change [data-target=new-point]' : 'setNewPoint',
    'change [data-hook=particle-type]' : 'setParticleType',
    'change [data-target=particle-property-containers]' : 'updateViewers',
    'change [data-hook=particle-fixed]' : 'setParticleFixed',
    'change [data-hook=mesh-file]' : 'setMeshFile',
    'change [data-hook=type-file]' : 'setTypeFile',
    'change [data-hook=action-mesh-select]' : 'selectMeshFile',
    'change [data-hook=mesh-location-select]' : 'selectMeshLocation',
    'change [data-hook=action-type-select]' : 'selectTypeFile',
    'change [data-hook=type-location-select]' : 'selectFileLocation',
    'click [data-hook=select-action]' : 'selectAction',
    'click [data-hook=enable-action]' : 'enableAction',
    'click [data-hook=remove]' : 'removeAction',
    'click [data-hook=collapseImportFiles]' : 'toggleImportFiles',
    'click [data-hook=collapseUploadedFiles]' : 'toggleUploadedFiles',
    'click [data-hook=import-mesh-file]' : 'handleImportMesh'
  },
  initialize: function (attrs, options) {
    View.prototype.initialize.apply(this, arguments);
    this.viewMode = attrs.viewMode ? attrs.viewMode : false;
    this.chevrons = {
      hide: `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 512 512">
          <path d="M233.4 406.6c12.5 12.5 32.8 12.5 45.3 0l192-192c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L256 338.7 86.6 169.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l192 192z"/>
        </svg>
      `,
      show: `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 512 512">
          <path d="M233.4 105.4c12.5-12.5 32.8-12.5 45.3 0l192 192c12.5 12.5 12.5 32.8 0 45.3s-32.8 12.5-45.3 0L256 173.3 86.6 342.6c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3l192-192z"/>
        </svg>
      `
    }
    this.accepts = {"XML Mesh": ".xml", "Mesh IO": ".msh", "GillesPy3D Domain": ".domn"};
    this.accept = Object.keys(this.accepts).includes(this.model.type) ? this.accepts[this.model.type] : null;
    this.filetype = this.model.type === "GillesPy3D Domain" ? 'domain' : 'mesh';
    this.meshFile = null;
    this.typeFile = null;
  },
  render: function () {
    this.template = this.viewMode ? viewTemplate : editTemplate;
    View.prototype.render.apply(this, arguments);
    this.details = {
      'Multi Particle': {
        'Fill Action': [
          $(this.queryByHook('action-scope')),
          $(this.queryByHook('multi-particle-shape')),
          $(this.queryByHook('multi-particle-transformation')),
          $(this.queryByHook('particle-properties'))
        ],
        'Set Action': [
          $(this.queryByHook('action-scope')),
          $(this.queryByHook('multi-particle-shape')),
          $(this.queryByHook('multi-particle-transformation')),
          $(this.queryByHook('particle-properties'))
        ],
        'Remove Action': [
          $(this.queryByHook('action-scope')),
          $(this.queryByHook('multi-particle-shape')),
          $(this.queryByHook('multi-particle-transformation'))
        ]
      },
      'Single Particle': {
        'Fill Action': [
          $(this.queryByHook('action-scope')),
          $(this.queryByHook('single-particle-scope')),
          $(this.queryByHook('particle-properties'))
        ],
        'Set Action': [
          $(this.queryByHook('action-scope')),
          $(this.queryByHook('single-particle-scope')),
          $(this.queryByHook('new-location')),
          $(this.queryByHook('particle-properties'))
        ],
        'Remove Action': [
          $(this.queryByHook('action-scope')),
          $(this.queryByHook('single-particle-scope'))
        ]
      },
      'XML Mesh': [
        $(this.queryByHook('multi-particle-transformation')),
        $(this.queryByHook('import-properties')),
        $(this.queryByHook('type-descriptions-prop'))
      ],
      'Mesh IO': [
        $(this.queryByHook('multi-particle-transformation')),
        $(this.queryByHook('import-properties')),
        $(this.queryByHook('type-descriptions-prop'))
      ],
      'GillesPy3D Domain': [
        $(this.queryByHook('multi-particle-transformation')),
        $(this.queryByHook('import-properties'))
      ]
    }
    app.documentSetup();
    if(!this.viewMode){
      if(this.model.selected) {
        setTimeout(_.bind(this.openDetails, this), 1);
      }
      this.model.on('change', _.bind(this.updateViewer, this));
      this.renderShapeSelectView();
      this.renderTransformationSelectView();
      this.renderNewLocationViews();
      this.renderTypeSelectView();
      this.renderParticleProperties();
      if(Object.keys(this.accepts).includes(this.model.type)) {
        this.meshFiles = null;
        this.typeFiles = null;
        this.renderActionFileSelects();
      }
      this.toggleEnable();
    }
    this.displayDetails();
  },
  completeAction: function () {
    $(this.queryByHook("imf-in-progress")).css("display", "none");
    $(this.queryByHook("imf-complete")).css("display", "inline-block");
    setTimeout(() => {
      $(this.queryByHook("imf-complete")).css("display", "none");
    }, 5000);
  },
  displayDetails: function () {
    let importTypes = ['XML Mesh', 'Mesh IO', 'GillesPy3D Domain']
    let elements = importTypes.includes(this.model.type) ? 
                   this.details[this.model.type] : this.details[this.model.scope][this.model.type];
    elements.forEach((element) => {
      element.css('display', 'block');
    });
  },
  enableAction: function () {
    this.model.enable = !this.model.enable;
    this.collection.parent.trigger('update-plot-preview');
  },
  errorAction: function (action) {
    $(this.queryByHook("imf-in-progress")).css("display", "none");
    $(this.queryByHook("imf-action-error")).text(action);
    $(this.queryByHook("imf-error")).css("display", "block");
  },
  getShapeOptions: function () {
    let options = [];
    if(this.model.type === "Fill Action" && this.model.scope === "Multi Particle") {
      this.model.collection.parent.shapes.forEach((shape) => {
        if(shape.fillable) { options.push(shape.name); }
      });
    }else {
      this.model.collection.parent.shapes.forEach((shape) => {
        options.push(shape.name);
      });
    }
    return options;
  },
  getTransformationOptions: function () {
    return this.model.collection.parent.transformations.map((transformation) => {
      return transformation.name;
    });
  },
  handleImportMesh: function () {
    this.startAction();
    let formData = new FormData();
    var filePath = this.model.collection.parent.directory;
    if(filePath === null) {
      filePath = this.parent.parent.parent.model.directory;
    }
    formData.append("path", filePath);
    formData.append("datafile", this.meshFile);
    if(this.typeFile) {
      formData.append("typefile", this.typeFile);
    }
    let endpoint = path.join(app.getApiPath(), 'spatial-model/import-mesh');
    app.postXHR(endpoint, formData, {
      success: (err, response, body) => {
        body = JSON.parse(body);
        this.model.filename = path.join(body.meshPath, body.meshFile);
        if(Object.keys(body).includes("typesPath")) {
          this.model.subdomainFile = path.join(body.typesPath, body.typesFile);
          this.typeFiles = null;
        }
        this.completeAction();
        $(this.queryByHook('collapseUploadedFiles')).click();
        this.renderActionFileSelects();
      },
      error: (err, response, body) => {
        body = JSON.parse(body);
        this.errorAction(body.Message);
      }
    }, false);
  },
  hideDetails: function () {
    let importTypes = ['XML Mesh', 'Mesh IO', 'GillesPy3D Domain']
    let elements = importTypes.includes(this.model.type) ? 
                   this.details[this.model.type] : this.details[this.model.scope][this.model.type];
    elements.forEach((element) => {
      element.css('display', 'none');
    });
  },
  openDetails: function () {
    $("#collapse-action-details" + this.model.cid).collapse("show");
  },
  removeAction: function () {
    let actions = this.collection;
    let enabled = this.model.enable;
    actions.removeAction(this.model);
    actions.parent.trigger('update-shape-deps');
    if(enabled) {
      actions.parent.trigger('update-plot-preview');
    }
  },
  renderActionFileSelects: function () {
    var queryStr = `?ext=${this.accept}`;
    if(this.typeFiles === null) {
      queryStr += `${queryStr}&includeTypes=True`;
    }
    let endpoint = `${path.join(app.getApiPath(), 'spatial-model/lattice-files')}${queryStr}`;
    app.getXHR(endpoint, {success: (err, response, body) => {
      this.meshFiles = body.meshFiles;
      this.renderMeshSelectView();
      if(Object.keys(body).includes('typeFiles')) {
        this.typeFiles = body.typeFiles;
        this.renderTypeFileSelectView();
      }
    }});
  },
  renderDensityPropertyView: function () {
    if(this.densityPropertyView) {
      this.densityPropertyView.remove();
    }
    this.densityPropertyView = new InputView({
      parent: this,
      required: true,
      name: 'density',
      tests: tests.valueTests,
      valueType: 'number',
      modelKey: 'rho',
      value: this.model.rho
    });
    let hook = "particle-rho";
    app.registerRenderSubview(this, this.densityPropertyView, hook);
  },
  renderMassPropertyView: function () {
    if(this.massPropertyView) {
      this.massPropertyView.remove();
    }
    this.massPropertyView = new InputView({
      parent: this,
      required: true,
      name: 'mass',
      tests: tests.valueTests,
      valueType: 'number',
      modelKey: 'mass',
      value: this.model.mass
    });
    let hook = "particle-mass";
    app.registerRenderSubview(this, this.massPropertyView, hook);
  },
  renderMeshLocationSelectView: function (index) {
    if(this.meshLocationSelectView) {
      this.meshLocationSelectView.remove();
    }
    let value = Boolean(this.model.filename) ? this.model.filename : "";
    this.meshLocationSelectView = new SelectView({
      name: 'mesh-locations',
      required: false,
      idAttributes: 'cid',
      options: this.meshFiles.paths[index],
      value: value,
      unselectedText: "-- Select Mesh File Location --"
    });
    let hook = "mesh-location-select";
    app.registerRenderSubview(this, this.meshLocationSelectView, hook);
  },
  renderMeshSelectView: function () {
    if(this.meshSelectView) {
      this.meshSelectView.remove();
    }
    let files = this.meshFiles.files.filter((file) => {
      if(file[1] === this.model.filename.split('/').pop()) {
        return file;
      }
    });
    let value = files.length > 0 ? files[0] : "";
    this.meshSelectView = new SelectView({
      name: 'mesh-files',
      required: false,
      idAttributes: 'cid',
      options: this.meshFiles.files,
      value: value,
      unselectedText: "-- Select Mesh File --"
    });
    let hook = "action-mesh-select";
    app.registerRenderSubview(this, this.meshSelectView, hook);
    if(value !== "" && this.meshFiles.paths[value[0]].length > 1) {
      this.renderMeshLocationSelectView(value[0]);
      $(this.queryByHook("mesh-location-container")).css("display", "inline-block");
    }
  },
  renderNewLocationViews: function () {
    if(this.newLocationViews) {
      this.newLocationViews['x'].remove();
      this.newLocationViews['y'].remove();
      this.newLocationViews['z'].remove();
    }else{
      this.newLocationViews = {};
    }
    this.newLocationViews['x'] = new InputView({
      parent: this,
      required: true,
      name: 'new-point-x',
      tests: [tests.nanValue],
      valueType: 'number',
      value: this.model.newPoint.x
    });
    let hookX = "new-point-x-container";
    app.registerRenderSubview(this, this.newLocationViews['x'], hookX);
    this.newLocationViews['y'] = new InputView({
      parent: this,
      required: true,
      name: 'new-point-y',
      tests: [tests.nanValue],
      valueType: 'number',
      value: this.model.newPoint.y
    });
    let hookY = "new-point-y-container";
    app.registerRenderSubview(this, this.newLocationViews['y'], hookY);
    this.newLocationViews['z'] = new InputView({
      parent: this,
      required: true,
      name: 'new-point-z',
      tests: [tests.nanValue],
      valueType: 'number',
      value: this.model.newPoint.z
    });
    let hookZ = "new-point-z-container";
    app.registerRenderSubview(this, this.newLocationViews['z'], hookZ);
  },
  renderParticleProperties: function () {
    this.renderMassPropertyView();
    this.renderVolumePropertyView();
    this.renderDensityPropertyView();
    this.renderViscosityPropertyView();
    this.renderSOSPropertyView();
  },
  renderShapeSelectView: function () {
    if(this.shapeSelectView) {
      this.shapeSelectView.remove();
    }
    let options = this.getShapeOptions();
    this.shapeSelectView = new SelectView({
      name: 'shape',
      required: true,
      options: options,
      value: this.model.shape,
      unselectedText: "-- Select Shape --"
    });
    let hook = "shape-container";
    app.registerRenderSubview(this, this.shapeSelectView, hook);
  },
  renderSOSPropertyView: function () {
    if(this.sOSPropertyView) {
      this.sOSPropertyView.remove();
    }
    this.sOSPropertyView = new InputView({
      parent: this,
      required: true,
      name: 'speed-of-sound',
      tests: tests.valueTests,
      valueType: 'number',
      modelKey: 'c',
      value: this.model.c
    });
    let hook = "particle-c";
    app.registerRenderSubview(this, this.sOSPropertyView, hook);
  },
  renderTransformationSelectView: function () {
    if(this.transformationSelectView) {
      this.transformationSelectView.remove();
    }
    let options = this.getTransformationOptions();
    this.transformationSelectView = new SelectView({
      name: 'transformation',
      required: true,
      options: options,
      value: this.model.transformation,
      unselectedText: "-- Select Transformation --"
    });
    let hook = "transformation-container";
    app.registerRenderSubview(this, this.transformationSelectView, hook);
  },
  renderTypeLocationSelectView: function (index) {
    if(this.typeLocationSelectView) {
      this.typeLocationSelectView.remove();
    }
    let value = Boolean(this.model.subdomainFile) ? this.model.subdomainFile : "";
    this.typeLocationSelectView = new SelectView({
      name: 'type-locations',
      required: false,
      idAttributes: 'cid',
      options: this.typeFiles.paths[index],
      value: value,
      unselectedText: "-- Select Type File Location --"
    });
    let hook = "type-location-select";
    app.registerRenderSubview(this, this.typeLocationSelectView, hook);
  },
  renderTypeFileSelectView: function () {
    if(this.typeSelectView) {
      this.typeSelectView.remove();
    }
    var file = this.typeFiles.files.filter((file) => {
      if(file[1] === this.model.subdomainFile.split('/').pop()) {
        return file;
      }
    });
    let value = file.length > 0 ? file[0] : "";
    this.typeSelectView = new SelectView({
      name: 'type-files',
      required: false,
      idAttributes: 'cid',
      options: this.typeFiles.files,
      value: value,
      unselectedText: "-- Select Type File --"
    });
    let hook = "action-type-select";
    app.registerRenderSubview(this, this.typeSelectView, hook);
    if(value !== "" && this.typeFiles.paths[value[0]].length > 1) {
      this.renderTypeLocationSelectView(value[0]);
      $(this.queryByHook("types-location-container")).css("display", "inline-block");
    }
  },
  renderTypeSelectView: function () {
    if(this.typeSelectView) {
      this.typeSelectView.remove();
    }
    let options = this.model.collection.parent.types.map((type) => {
      return [type.typeID, type.name];
    });
    this.typeSelectView = new SelectView({
      name: 'type',
      required: true,
      options: options,
      value: this.model.typeID,
    });
    let hook = "particle-type";
    app.registerRenderSubview(this, this.typeSelectView, hook);
  },
  renderViscosityPropertyView: function () {
    if(this.viscosityPropertyView) {
      this.viscosityPropertyView.remove();
    }
    this.viscosityPropertyView = new InputView({
      parent: this,
      required: true,
      name: 'viscosity',
      tests: tests.valueTests,
      valueType: 'number',
      modelKey: 'nu',
      value: this.model.nu
    });
    let hook = "particle-nu";
    app.registerRenderSubview(this, this.viscosityPropertyView, hook);
  },
  renderVolumePropertyView: function () {
    if(this.volumePropertyView) {
      this.volumePropertyView.remove();
    }
    this.volumePropertyView = new InputView({
      parent: this,
      required: true,
      name: 'volume',
      tests: tests.valueTests,
      valueType: 'number',
      modelKey: 'vol',
      value: this.model.vol
    });
    let hook = "particle-vol";
    app.registerRenderSubview(this, this.volumePropertyView, hook);
  },
  selectAction: function () {
    this.model.selected = !this.model.selected;
  },
  selectActionScope: function (e) {
    this.hideDetails();
    this.model.scope = e.target.value;
    this.displayDetails();
    this.toggleEnable();
    this.updatePreviewPlot();
  },
  selectActionType: function (e) {
    this.hideDetails();
    this.model.type = e.target.value;
    this.displayDetails();
    let types = {
      'XML Mesh': '.xml', 'Mesh IO': '.msh', 'GillesPy3D Domain': '.domn'
    };
    if(Object.keys(types).includes(this.model.type)) {
      this.accept = types[this.model.type]
      $(this.queryByHook('mesh-file')).prop('accept', this.accept);
      this.filetype = this.model.type === "GillesPy3D Domain" ? 'domain' : 'mesh';
      $(this.queryByHook('meshfile-label')).text(`Please specify a ${this.filetype} to import: `);
      $(this.queryByHook('action-filename-label')).text(`Please specify a ${this.filetype} to import: `);
      $(this.queryByHook('mesh-location-message')).text(
        `There are multiple ${this.filetype} files with that name, please select a location`
      );
      this.renderActionFileSelects();
    }
    this.toggleEnable();
    this.updatePreviewPlot();
  },
  selectFileLocation: function (e) {
    this.model.subdomainFile = e.target.value ? e.target.value : "";
  },
  selectMeshFile: function (e) {
    let value = e.target.value;
    var msgDisplay = "none";
    var contDisplay = "none";
    if(value) {
      if(this.meshFiles.paths[value].length > 1) {
        msgDisplay = "block";
        contDisplay = "inline-block";
        this.renderMeshLocationSelectView(value);
        this.model.filename = "";
      }else{
        this.model.filename = this.meshFiles.paths[value][0];
      }
    }else{
      this.model.filename = "";
    }
    $(this.queryByHook("mesh-location-message")).css('display', msgDisplay);
    $(this.queryByHook("mesh-location-container")).css("display", contDisplay);
  },
  selectMeshLocation: function (e) {
    this.model.filename = e.target.value ? e.target.value : "";
  },
  selectShape: function (e) {
    this.model.shape = e.target.value;
    this.toggleEnable();
    this.model.collection.parent.trigger('update-shape-deps');
    this.updateViewer();
    this.updatePreviewPlot();
  },
  selectTypeFile: function (e) {
    let value = e.target.value;
    var msgDisplay = "none";
    var contDisplay = "none";
    if(value) {
      if(this.typeFiles.paths[value].length > 1) {
        msgDisplay = "block";
        contDisplay = "inline-block";
        this.renderTypeLocationSelectView(value);
        this.model.subdomainFile = "";
      }else{
        this.model.subdomainFile = this.typeFiles.paths[value][0];
      }
    }else{
      this.model.subdomainFile = "";
    }
    $(this.queryByHook("types-location-message")).css('display', msgDisplay);
    $(this.queryByHook("types-location-container")).css("display", contDisplay);
  },
  selectTransformation: function (e) {
    this.model.transformation = e.target.value;
    this.model.collection.parent.trigger('update-transformation-deps');
    this.updateViewer();
    this.updatePreviewPlot();
  },
  setMeshFile: function (e) {
    this.meshFile = e.target.files[0];
    this.updateViewer();
    $(this.queryByHook("import-mesh-file")).prop('disabled', !this.meshFile);
  },
  setNewPoint: function (e) {
    let key = e.target.parentElement.parentElement.dataset.name;
    let value = Number(e.target.value);
    this.model.newPoint[key] = value;
    this.updateViewer();
    this.updatePreviewPlot();
  },
  setParticleFixed: function (e) {
    this.model.fixed = !this.model.fixed;
    this.updateViewer();
    this.updatePreviewPlot();
  },
  setParticleType: function (e) {
    let value = Number(e.target.value);
    let currType = this.model.collection.parent.types.get(this.model.typeID, "typeID");
    let newType = this.model.collection.parent.types.get(value, "typeID");
    this.updatePropertyDefaults(currType, newType);
    this.model.typeID = value;
    this.model.collection.parent.trigger('update-type-deps');
    this.updateViewer();
    this.updatePreviewPlot();
  },
  setPoint: function (e) {
    let key = e.target.parentElement.parentElement.dataset.name;
    let value = Number(e.target.value);
    if(this.model.newPoint[key] === this.model.point[key]) {
      this.model.newPoint[key] = value;
      this.renderNewLocationViews();
    }
    this.model.point[key] = value;
    this.updateViewer();
    this.updatePreviewPlot();
  },
  setTypeFile: function (e) {
    this.typeFile = e.target.files[0];
    this.updateViewer();
  },
  startAction: function () {
    $(this.queryByHook("imf-complete")).css("display", "none");
    $(this.queryByHook("imf-error")).css("display", "none");
    $(this.queryByHook("imf-in-progress")).css("display", "inline-block");
  },
  toggleEnable: function () {
    let noShape = this.model.shape === "";
    let mltPart = this.model.scope === "Multi Particle";
    let noImprt = ["Fill Action", "Set Action", "Remove Action"].includes(this.model.type);
    let disable = noShape && mltPart && noImprt
    $(this.queryByHook("enable-action")).prop("disabled", disable);
  },
  toggleImportFiles: function (e) {
    let classes = $(this.queryByHook('collapseImportFiles')).attr("class").split(/\s+/);
    $(this.queryByHook('uploaded-chevron')).html(this.chevrons.hide);
    if(classes.includes('collapsed')) {
      $(this.queryByHook('import-chevron')).html(this.chevrons.show);
    }else{
      $(this.queryByHook('import-chevron')).html(this.chevrons.hide);
    }
  },
  toggleUploadedFiles: function (e) {
    let classes = $(this.queryByHook('collapseUploadedFiles')).attr("class").split(/\s+/);
    $(this.queryByHook('import-chevron')).html(this.chevrons.hide);
    if(classes.includes('collapsed')) {
      $(this.queryByHook('uploaded-chevron')).html(this.chevrons.show);
    }else{
      $(this.queryByHook('uploaded-chevron')).html(this.chevrons.hide);
    }
  },
  update: function () {},
  updatePreviewPlot: function () {
    if(!this.model.enable) { return }
    if(this.model.type === "Fill Action" && this.model.scope === "Multi Particle" && this.model.shape === "") {
      return
    }
    this.collection.parent.trigger('update-plot-preview');
  },
  updatePropertyDefaults: function (currType, newType) {
    if(this.model.mass === currType.mass) {
      this.model.mass = newType.mass;
    }
    if(this.model.vol === currType.volume) {
      this.model.vol = newType.volume;
    }
    if(this.model.rho === currType.rho) {
      this.model.rho = newType.rho;
    }
    if(this.model.nu === currType.nu) {
      this.model.nu = newType.nu;
    }
    if(this.model.c === currType.c) {
      this.model.c = newType.c;
    }
    if(this.model.fixed === currType.fixed) {
      this.model.fixed = newType.fixed;
    }
    this.renderParticleProperties();
    $(this.queryByHook('particle-fixed')).prop('checked', this.model.fixed);
  },
  updateValid: function () {},
  updateViewer: function () {
    this.parent.renderViewActionsView();
  },
  updateViewers: function () {
    this.updatePreviewPlot();
    this.updateViewer();
  },
  subviews: {
    inputPriority: {
      hook: 'input-priority-container',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'priority',
          tests: tests.valueTests,
          modelKey: 'priority',
          valueType: 'number',
          value: this.model.priority
        });
      }
    },
    selectType: {
      hook: 'select-type-container',
      prepareView: function (el) {
        let groupOptions = [
          {groupName: "Shape Actions", options: ['Fill Action', 'Set Action', 'Remove Action']},
          {groupName: "Import Actions", options: ['XML Mesh', 'Mesh IO', 'GillesPy3D Domain']}
        ]
        return new SelectView({
          name: 'type',
          required: true,
          idAttributes: 'cid',
          groupOptions: groupOptions,
          value: this.model.type
        });
      }
    },
    selectScope: {
      hook: 'select-scope-container',
      prepareView: function (el) {
        let options = [
          'Multi Particle',
          'Single Particle'
        ];
        return new SelectView({
          name: 'scope',
          required: true,
          idAttributes: 'cid',
          options: options,
          value: this.model.scope
        });
      }
    },
    inputPointX: {
      hook: 'point-x-container',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'point-x',
          tests: [tests.nanValue],
          valueType: 'number',
          value: this.model.point.x
        });
      }
    },
    inputPointY: {
      hook: 'point-y-container',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'point-y',
          tests: [tests.nanValue],
          valueType: 'number',
          value: this.model.point.y
        });
      }
    },
    inputPointZ: {
      hook: 'point-z-container',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: true,
          name: 'point-z',
          tests: [tests.nanValue],
          valueType: 'number',
          value: this.model.point.z
        });
      }
    }
  }
});
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
let modals = require('../../modals');
let Tooltips = require('../../tooltips');
let Plotly = require('plotly.js-dist');
//models
let Model = require('../../models/model');
//views
let InputView = require('../../views/input');
let View = require('ampersand-view');
let SelectView = require('ampersand-select-view');
let SweepParametersView = require('./sweep-parameter-range-view');
//templates
let spatialTemplate = require('../templates/spatialResultsView.pug');
let wellMixedTemplate = require('../templates/gillespyResultsView.pug');
let scanTemplate = require('../templates/parameterScanResultsView.pug');
let inferenceTemplate = require('../templates/inferenceResultsView.pug');
let sweepTemplate = require('../templates/parameterSweepResultsView.pug');
let ensembleTemplate = require('../templates/gillespyResultsEnsembleView.pug');

module.exports = View.extend({
  events: {
    'change [data-hook=title]' : 'setTitle',
    'change [data-hook=xaxis]' : 'setXAxis',
    'change [data-hook=yaxis]' : 'setYAxis',
    'change [data-hook=target-of-interest-list]' : 'getPlotForTarget',
    'change [data-hook=target-mode-list]' : 'getPlotForTargetMode',
    'change [data-hook=trajectory-index-slider]' : 'getPlotForTrajectory',
    'change [data-hook=round-index-slider]' : 'getPlotForRound',
    'change [data-hook=specie-of-interest-list]' : 'getPlotForSpecies',
    'change [data-hook=feature-extraction-list]' : 'getPlotForFeatureExtractor',
    'change [data-hook=ensemble-aggragator-list]' : 'getPlotForEnsembleAggragator',
    'change [data-hook=plot-type-select]' : 'getTSPlotForType',
    'click [data-hook=collapse-results-btn]' : 'changeCollapseButtonText',
    'click [data-hook=inference-histogram-tab]' : 'handleInferenceResize',
    'click [data-hook=inference-pdf-tab]' : 'handlePDFResize',
    'click [data-hook=round-histogram-tab]' : 'handleRoundResize',
    'click [data-hook=round-intersection-tab]' : 'handleIntersectionResize',
    'click [data-trigger=collapse-plot-container]' : 'handleCollapsePlotContainerClick',
    'click [data-target=model-export]' : 'handleExportInferredModel',
    'click [data-target=model-explore]' : 'handleExploreInferredModel',
    'click [data-target=edit-plot]' : 'openPlotArgsSection',
    'click [data-hook=multiple-plots]' : 'plotMultiplePlots',
    'click [data-target=download-png-custom]' : 'handleDownloadPNGClick',
    'click [data-target=download-json]' : 'handleDownloadJSONClick',
    'click [data-target=download-plot-csv]' : 'handlePlotCSVClick',
    'click [data-hook=convert-to-notebook]' : 'handleConvertToNotebookClick',
    'click [data-hook=download-results-csv]' : 'handleFullCSVClick',
    'click [data-hook=job-presentation]' : 'handlePresentationClick',
    'input [data-hook=trajectory-index-slider]' : 'viewTrajectoryIndex',
    'input [data-hook=round-index-slider]' : 'viewRoundIndex'
  },
  initialize: function (attrs, options) {
    View.prototype.initialize.apply(this, arguments);
    this.readOnly = Boolean(attrs.readOnly) ? attrs.readOnly : false;
    this.wkflName = attrs.wkflName;
    this.titleType = attrs.titleType;
    this.tooltips = Tooltips.jobResults;
    this.plots = {};
    this.plotArgs = {};
    this.activePlots = {};
    this.trajectoryIndex = 1;
    this.pdfResized = false;
    this.inferenceResized = false;
    this.roundHistoResized = false;
    this.intersectionResized = false;
  },
  render: function (attrs, options) {
    let isEnsemble = this.model.settings.simulationSettings.realizations > 1 && 
                     this.model.settings.simulationSettings.algorithm !== "ODE";
    let isParameterScan = this.model.settings.parameterSweepSettings.parameters.length > 2;
    let templates = {
      "Ensemble Simulation": isEnsemble ? ensembleTemplate : wellMixedTemplate,
      "Parameter Sweep": isParameterScan ? scanTemplate : sweepTemplate,
      "Spatial Ensemble Simulation": spatialTemplate,
      "Model Inference": inferenceTemplate
    }
    this.template = templates[this.titleType];
    View.prototype.render.apply(this, arguments);
    if(this.readOnly) {
      $(this.queryByHook("job-presentation")).css("display", "none");
      if(!isParameterScan){
        $(this.queryByHook("convert-to-notebook")).css("display", "none");
      }
    }else if(app.getBasePath() === "/") {
      $(this.queryByHook("job-presentation")).css("display", "none");
    }else if(!this.parent.newFormat) {
      $(this.queryByHook("job-presentation")).prop("disabled", true);
      $(this.queryByHook("update-format-message")).css("display", "block");
    }
    if(this.titleType === "Ensemble Simulation") {
      var type = isEnsemble ? "stddevran" : "trajectories";
    }else if(this.titleType === "Parameter Sweep") {
      this.tsPlotData = {"parameters":{}};
      this.fixedParameters = {};
      var type = "ts-psweep";
      this.renderSpeciesOfInterestView();
      this.renderFeatureExtractionView();
      if(isEnsemble) {
        this.renderEnsembleAggragatorView();
        this.renderPlotTypeSelectView();
        this.tsPlotData["type"] = "stddevran"
      }else{
        $(this.queryByHook('ensemble-aggragator-container')).css("display", "none");
        $(this.queryByHook('plot-type-header')).css("display", "none");
        this.tsPlotData["type"] = "trajectories"
      }
      this.getPlot("psweep");
      this.renderSweepParameterView();
    }else if(this.titleType === "Spatial Ensemble Simulation") {
      var type = "spatial";
      this.spatialTarget = "type";
      this.targetIndex = null;
      this.targetMode = "discrete";
      this.renderTargetOfInterestView();
      if(this.model.settings.simulationSettings.realizations > 1) {
        $(this.queryByHook("spatial-trajectory-header")).css("display", "inline-block");
        $(this.queryByHook("spatial-trajectory-container")).css("display", "inline-block");
      }
      $(this.queryByHook("spatial-plot-csv")).css('display', 'none');
    }else{
      var type = "inference";
      this.roundIndex = this.model.settings.inferenceSettings.numRounds === 0 ? 1 : this.model.settings.inferenceSettings.numRounds;
      let parameters = this.model.settings.inferenceSettings.parameters;
      this.intersectionNames = [parameters.at(0).name, parameters.at(1).name];
      if(this.model.exportLinks[this.roundIndex] !== null) {
        $(this.queryByHook("inference-model-export")).text("Open Model");
        $(this.queryByHook("inference-model-explore")).text("Explore Model");
      }
      if(this.roundIndex > 1) {
        $(this.queryByHook("round-index-value")).text(this.roundIndex);
        $(this.queryByHook("round-index-slider")).prop("value", this.roundIndex);
      }else{
        $(this.queryByHook("round-slider-container")).css('display', 'none');
      }
      // TODO: Enable inference presentations when implemented
      $(this.queryByHook("job-presentation")).prop("disabled", true);
    }
    this.getPlot(type);
  },
  changeCollapseButtonText: function (e) {
    app.changeCollapseButtonText(this, e);
  },
  endAction: function () {
    $(this.queryByHook("job-action-start")).css("display", "none");
    let saved = $(this.queryByHook("job-action-end"));
    saved.css("display", "inline-block");
    setTimeout(function () {
      saved.css("display", "none");
    }, 5000);
  },
  errorAction: function () {
    $(this.queryByHook("job-action-start")).css("display", "none");
    let error = $(this.queryByHook("job-action-err"));
    error.css("display", "inline-block");
    setTimeout(function () {
      error.css("display", "none");
    }, 5000);
  },
  cleanupPlotContainer: function (type, {pdfOnly=false}={}) {
    if(["inference", "round"].includes(type)) {
      let histoEL = this.queryByHook(`${type}-histogram-plot`);
      if(!pdfOnly) {
        Plotly.purge(histoEL);
        $(this.queryByHook(`${type}-histogram-plot`)).empty();
        $(this.queryByHook(`${type}-histogram-plot-spinner`)).css("display", "block");
      }
      if(type === "inference") {
        let pdfEL = this.queryByHook('inference-pdf-plot');
        Plotly.purge(pdfEL);
        $(this.queryByHook('inference-pdf-plot')).empty();
        $(this.queryByHook('inference-pdf-plot-spinner')).css("display", "block");
      }else {
        let interEL = this.queryByHook('round-intersection-plot');
        Plotly.purge(interEL);
        $(this.queryByHook('round-intersection-plot')).empty();
        $(this.queryByHook('round-intersection-plot-spinner')).css("display", "block");
        if(!pdfOnly) {
          $(this.queryByHook("round-model-export")).prop("disabled", true);
          $(this.queryByHook("round-model-explore")).prop("disabled", true);
          $(this.queryByHook("round-download")).prop("disabled", true);
          $(this.queryByHook("round-edit-plot")).prop("disabled", true);
          try {
            histoEL.removeListener('plotly_click', _.bind(this.selectIntersection, this));
          }catch (err) {
            //pass
          }
        }
      }
    }else {
      let el = this.queryByHook(`${type}-plot`);
      Plotly.purge(el);
      $(this.queryByHook(type + "-plot")).empty();
      if(["ts-psweep", "psweep"].includes(type)) {
        $(this.queryByHook(`${type}-download`)).prop("disabled", true);
        $(this.queryByHook(`${type}-edit-plot`)).prop("disabled", true);
        $(this.queryByHook("multiple-plots")).prop("disabled", true);
      }else if(type === "spatial") {
        $(this.queryByHook("spatial-plot-loading-msg")).css("display", "block");
      }
      $(this.queryByHook(`${type}-plot-spinner`)).css("display", "block");
    }
  },
  downloadCSV: function (csvType, data) {
    var queryStr = `?path=${this.model.directory}&type=${csvType}`;
    if(data) {
      queryStr += `&data=${JSON.stringify(data)}`;
    }
    let endpoint = `${path.join(app.getApiPath(), "job/csv")}${queryStr}`;
    window.open(endpoint);
  },
  exportInferredModel: function (type, {cb=null}={}) {
    let round = type === "round" ? this.roundIndex : this.model.settings.inferenceSettings.numRounds
    if(this.model.exportLinks[round] === null) {
      var queryStr = `?path=${this.model.directory}`;
      if(type === "round") {
        queryStr += `&round=${this.roundIndex}`;
      }
      let endpoint = `${path.join(app.getApiPath(), "job/export-inferred-model")}${queryStr}`;
      app.getXHR(endpoint, {
        success: (err, response, body) => {
          if(cb === null) {
            let editEP = `${path.join(app.getBasePath(), "model_builder/models/edit")}?path=${body.path}`;
            window.location.href = editEP;
          }else {
            cb(err, response, body);
          }
        }
      });
    }else if(cb === null){
      let mdPath = this.model.exportLinks[round];
      let editEP = `${path.join(app.getBasePath(), "model_builder/models/edit")}?path=${mdPath}`;
      window.location.href = editEP;
    }else {
      cb();
    }
  },
  fixPlotSize: function (type, plotID) {
    let figID = plotID === "histogram" ? plotID : "pdf"
    let plotEL = this.queryByHook(`${type}-${plotID}-plot`);
    // Clear plot
    Plotly.purge(plotEL);
    $(plotEL).empty();
    // Re-render the plot
    if(Object.keys(this.plots).includes(this.activePlots[type])) {
      let figure = this.plots[this.activePlots[type]]
      Plotly.newPlot(plotEL, figure[figID]);
      if(type === "round" && plotID === "histogram") {
        plotEL.on('plotly_click', _.bind(this.selectIntersection, this));
      }
      return true;
    }
    return false;
  },
  getPlot: function (type, {pdfOnly=false}={}) {
    this.cleanupPlotContainer(type, {pdfOnly: pdfOnly});
    let data = this.getPlotData(type);
    if(data === null) { return };
    let storageKey = JSON.stringify(data);
    data['plt_data'] = this.getPlotLayoutData();
    if(Boolean(this.plots[storageKey])) {
      let renderTypes = ['psweep', 'ts-psweep', 'ts-psweep-mp', 'mltplplt', 'spatial', 'round'];
      if(renderTypes.includes(type)) {
        this.activePlots[type] = storageKey;
        this.plotFigure(this.plots[storageKey], type, {pdfOnly: pdfOnly});
      }
    }else{
      let queryStr = `?path=${this.model.directory}&data=${JSON.stringify(data)}`;
      let endpoint = `${path.join(app.getApiPath(), "workflow/plot-results")}${queryStr}`;
      app.getXHR(endpoint, {
        success: (err, response, body) => {
          if(type === "round") {
            let xLabel = {
              font: {size: 16}, showarrow: false, text: "", x: 0.5, xanchor: "center", xref: "paper",
              y: 0, yanchor: "top", yref: "paper", yshift: -30
            }
            let yLabel = {
              font: {size: 16}, showarrow: false, text: "", textangle: -90, x: 0, xanchor: "right",
              xref: "paper", xshift: -40, y: 0.5, yanchor: "middle", yref: "paper"
            }
            body.histogram.layout.annotations.push(xLabel);
            body.histogram.layout.annotations.push(yLabel);
            body.pdf.layout.annotations.push(xLabel);
            body.pdf.layout.annotations.push(yLabel);
          }
          this.activePlots[type] = storageKey;
          this.plots[storageKey] = body;
          this.plotFigure(body, type, {pdfOnly: pdfOnly});
        },
        error: (err, response, body) => {
          if(type === "spatial") {
            $(this.queryByHook("spatial-plot-loading-msg")).css("display", "none");
          }
          $(this.queryByHook(`${type}-plot-spinner`)).css("display", "none");
          let message = `<p>${body.Message}</p><p><b>Please re-run this job to get this plot</b></p>`;
          $(this.queryByHook(`${type}-plot`)).html(message);
        }
      });
    }
  },
  getPlotData: function (type) {
    let data = {};
    if(type === 'psweep'){
      data['sim_type'] = "ParameterSweep";
      if(this.model.settings.parameterSweepSettings.parameters.length <= 2) {
        data['data_keys'] = {}
      }else {
        let dataKeys = this.getDataKeys(false);
        let paramDiff = this.model.settings.parameterSweepSettings.parameters.length - Object.keys(dataKeys).length
        if(paramDiff <= 0) {
          $(this.queryByHook(type + "-plot-spinner")).css("display", "none");
          $(this.queryByHook("too-many-params")).css("display", "block");
          return null;
        }
        if(paramDiff > 2) {
          $(this.queryByHook(type + "-plot-spinner")).css("display", "none");
          $(this.queryByHook("too-few-params")).css("display", "block");
          return null;
        }
        $(this.queryByHook("too-few-params")).css("display", "none");
        $(this.queryByHook("too-many-params")).css("display", "none");
        data['data_keys'] = dataKeys;
      }
      data['plt_key'] = this.getPlotKey(type);
    }else if(type === "ts-psweep" || type === "ts-psweep-mp") {
      data['sim_type'] = "GillesPy2_PS";
      data['data_keys'] = this.getDataKeys(true);
      data['plt_key'] = type === "ts-psweep-mp" ? "mltplplt" : this.tsPlotData.type;
    }else if(type === "spatial") {
      data['sim_type'] = "SpatialPy";
      data['data_keys'] = {
        target: this.spatialTarget, index: this.targetIndex, mode: this.targetMode, trajectory: this.trajectoryIndex - 1
      };
      data['plt_key'] = type;
    }else if(["inference", "round"].includes(type)) {
      data['sim_type'] = "Inference";
      data['data_keys'] = {
        "epoch": type === "inference" ? null : this.roundIndex - 1,
        "names": type === "inference" ? null : this.intersectionNames
      }
      data['plt_key'] = "inference";
    }else {
      data['sim_type'] = "GillesPy2";
      data['data_keys'] = {};
      data['plt_key'] = type;
    }
    return data
  },
  getPlotLayoutData: function () {
    if(Object.keys(this.plotArgs).length){
      return this.plotArgs;
    }
    return null
  },
  getPlotForEnsembleAggragator: function (e) {
    this.model.settings.resultsSettings.reducer = e.target.value;
    this.getPlot('psweep')
  },
  getPlotForRound: function (e) {
    this.roundIndex = Number(e.target.value);
    this.roundHistoResized = false;
    this.intersectionResized = false;
    this.getPlot('round');
  },
  getPlotForFeatureExtractor: function (e) {
    this.model.settings.resultsSettings.mapper = e.target.value;
    this.getPlot('psweep')
  },
  getPlotForSpecies: function (e) {
    let species = this.model.model.species.filter(function (spec) {
      return spec.name === e.target.value;
    })[0];
    this.model.settings.parameterSweepSettings.speciesOfInterest = species;
    this.getPlot('psweep')
  },
  getPlotForTarget: function (e) {
    let value = e.target.value;
    if(["0", "1", "2"].includes(value)) {
      this.spatialTarget = "v";
      this.targetIndex = number(value);
    }else{
      this.spatialTarget = value;
      this.targetIndex = null;
    }
    if(!["type", "v", "nu", "rho", "mass"].includes(this.spatialTarget)) {
      $(this.queryByHook('job-results-mode-header')).css('display', 'inline-block');
      $(this.queryByHook('job-results-mode-container')).css('display', 'inline-block');
      this.renderTargetModeView();
    }else{
      $(this.queryByHook('job-results-mode-header')).css('display', 'none');
      $(this.queryByHook('job-results-mode-container')).css('display', 'none');
    }
    this.getPlot("spatial");
  },
  getPlotForTargetMode: function (e) {
    this.targetMode = e.target.value;
    this.getPlot("spatial");
  },
  getPlotForTrajectory: function (e) {
    this.trajectoryIndex = Number(e.target.value);
    this.getPlot('spatial');
  },
  getPlotKey: function (type) {
    if(type === "psweep") {
      let realizations = this.model.settings.simulationSettings.realizations;
      let algorithm = this.model.settings.simulationSettings.algorithm;
      let plt_key = {
        species: this.model.settings.parameterSweepSettings.speciesOfInterest.name,
        mapper: this.model.settings.resultsSettings.mapper,
        reducer: algorithm !== "ODE" && realizations > 1 ? this.model.settings.resultsSettings.reducer : null
      }
      return plt_key;
    }
  },
  getTSPlotForType: function (e) {
    this.tsPlotData.type = e.target.value;
    let display = this.tsPlotData.type === "trajectories" ? "inline-block" : "none";
    $(this.queryByHook("multiple-plots")).css("display", display);
    this.getPlot("ts-psweep");
  },
  getDataKeys: function (full) {
    if(full) { return this.tsPlotData.parameters; }
    let self = this;
    let parameters = {};
    this.model.settings.parameterSweepSettings.parameters.forEach(function (param) {
      if(param.fixed){
        parameters[param.name] = self.fixedParameters[param.name];
      }
    });
    return parameters;
  },
  getType: function (storageKey) {
    let plotData = JSON.parse(storageKey)
    if(plotData.sim_type === "GillesPy2") { return plotData.plt_key; }
    if(plotData.sim_type === "GillesPy2_PS") { return "ts-psweep"; }
    if(plotData.sim_type === "Inference") {
      if(plotData.data_keys.round === null) { return "inference"; }
      return "round"
    }
    return "psweep"
  },
  handleCollapsePlotContainerClick: function (e) {
    app.changeCollapseButtonText(this, e);
    let type = e.target.dataset.type;
    if(['psweep', 'ts-psweep'].includes(type)) { return }
    for (var storageKey in this.plots) {
      let data = JSON.parse(storageKey)
      if(data.plt_key === type) { return }
    }
    this.getPlot(type);
  },
  handleConvertToNotebookClick: function (e) {
    let is2D = this.model.settings.parameterSweepSettings.parameters.length > 1;
    let types = {
      "Ensemble Simulation": "gillespy",
      "Spatial Ensemble Simulation": "spatialpy",
      "Parameter Sweep": is2D ? "2d_parameter_sweep" : "1d_parameter-sweep"
    }
    let type = types[this.titleType];
    let queryStr = `?path=${this.model.directory}&type=${type}`;
    let endpoint = `${path.join(app.getApiPath(), "workflow/notebook")}${queryStr}`;
    app.getXHR(endpoint, {
      success: (err, response, body) => {
        window.open(path.join(app.getBasePath(), "notebooks", body.FilePath));
      }
    });
  },
  handleDownloadJSONClick: function (e) {
    let type = e.target.dataset.type;
    let storageKey = JSON.stringify(this.getPlotData(type));
    if(["inference", "round"].includes(type)) {
      if(type === "inference") {
        let classList = this.queryByHook("inference-histogram-tab").classList.value.split(" ");
        var key = classList.includes("active") ? "histogram" : "pdf";
        var nameBase = `${type}-${key}`;
      }else{
        let classList = this.queryByHook("round-histogram-tab").classList.value.split(" ");
        var key = classList.includes("active") ? "histogram" : "pdf";
        let pltKey = key === "pdf" ? `${this.intersectionNames.join("-X-")}-intersection` : key;
        var nameBase = `${type}${this.roundIndex}-${pltKey}`;
      }
      var jsonData = this.plots[storageKey][key];
    }else if(type === "spatial") {
      var nameBase = `${type}${this.trajectoryIndex}`
    }else{
      var jsonData = this.plots[storageKey];
      var nameBase = type
    }
    let dataStr = JSON.stringify(jsonData);
    let dataURI = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    let exportFileDefaultName = `${nameBase}-plot.json`;

    let linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataURI);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  },
  handleDownloadPNGClick: function (e) {
    let type = e.target.dataset.type;
    if(["inference", "round"].includes(type)) {
      if(type === "inference") {
        let classList = this.queryByHook("inference-histogram-tab").classList.value.split(" ");
        var key = classList.includes("active") ? "histogram" : "pdf";
      }else{
        let classList = this.queryByHook("round-histogram-tab").classList.value.split(" ");
        var key = classList.includes("active") ? "histogram" : "intersection";
      }
      var divEL = `div[data-hook=${type}-${key}-plot]`;
    }else{
      var divEL = `div[data-hook=${type}-plot]`;
    }
    let pngButton = $(`${divEL} a[data-title*="Download plot as a png"]`)[0];
    pngButton.click();
  },
  handleExploreInferredModel: function (e) {
    let type = e.target.dataset.hook.split('-')[0];
    this.exportInferredModel(type, {cb: _.bind(this.newWorkflow, this)});
  },
  handleExportInferredModel: function (e) {
    let type = e.target.dataset.hook.split('-')[0];
    this.exportInferredModel(type);
  },
  handleFullCSVClick: function (e) {
    if(this.titleType === "Model Inference") {
      this.downloadCSV("inference", null);
    }else {
      this.downloadCSV("full", null);
    }
  },
  handleInferenceResize: function (e) {
    if(!this.inferenceResized) {
      setTimeout(() => {
        this.inferenceResized = this.fixPlotSize("inference", "histogram");
      }, 0)
    }
  },
  handleIntersectionResize: function (e) {
    if(!this.intersectionResized) {
      setTimeout(() => {
        this.intersectionResized = this.fixPlotSize("round", "intersection");
      }, 0)
    }
  },
  handlePDFResize: function (e) {
    if(!this.pdfResized) {
      setTimeout(() => {
        this.pdfResized = this.fixPlotSize("inference", "pdf");
      }, 0)
    }
  },
  handleRoundResize: function (e) {
    if(!this.roundHistoResized) {
      setTimeout(() => {
        this.roundHistoResized = this.fixPlotSize("round", "histogram");
      }, 0)
    }
  },
  handlePlotCSVClick: function (e) {
    let type = e.target.dataset.type;
    if(type !== "psweep") {
      var data = {
        data_keys: type === "ts-psweep" ? this.getDataKeys(true) : {},
        proc_key: type === "ts-psweep" ? this.tsPlotData.type : type
      }
      var csvType = "time series"
    }else{
      var data = this.getDataKeys(false)
      var csvType = "psweep"
    }
    this.downloadCSV(csvType, data);
  },
  handlePresentationClick: function (e) {
    let self = this;
    this.startAction();
    let name = this.wkflName + "_" + this.model.name;
    let queryStr = "?path=" + this.model.directory + "&name=" + name;
    let endpoint = path.join(app.getApiPath(), "job/presentation") + queryStr;
    app.getXHR(endpoint, {
      success: function (err, response, body) {
        self.endAction("publish");
        let title = body.message;
        let linkHeaders = "Shareable Presentation Link";
        let links = body.links;
        $(modals.presentationLinks(title, linkHeaders, links)).modal();
        let copyBtn = document.querySelector('#presentationLinksModal #copy-to-clipboard');
        copyBtn.addEventListener('click', function (e) {
          let onFulfilled = (value) => {
            $("#copy-link-success").css("display", "inline-block");
          } 
          let onReject = (reason) => {
            let msg = $("#copy-link-failed");
            msg.html(reason);
            msg.css("display", "inline-block");
          }
          app.copyToClipboard(links.presentation, onFulfilled, onReject);
        });
      },
      error: function (err, response, body) {
        if(document.querySelector("#errorModal")) {
          document.querySelector("#errorModal").remove();
        }
        self.errorAction();
        $(modals.errorHtml(body.Reason, body.Message)).modal();
      }
    });
  },
  newWorkflow: function (err, response, body) {
    let type = "Parameter Sweep"
    if([undefined, null].includes(body)) {
      body = { path: this.model.exportLinks[this.roundIndex] };
    }
    let model = new Model({ directory: body.path });
    app.getXHR(model.url(), {
      success: (err, response, body) => {
        model.set(body);
        model.updateValid();
        if(model.valid){
          app.newWorkflow(this, model.directory, model.is_spatial, type);
        }else{
          if(document.querySelector("#errorModal")) {
            document.querySelector("#errorModal").remove();
          }
          let title = "Model Errors Detected";
          let endpoint = `${path.join(app.getBasePath(), "model_builder/models/edit")}?path=${model.directory}&validate`;
          let message = `Errors were detected in you model <a href="${endpoint}">click here to fix your model<a/>`;
          $(modals.errorHtml(title, message)).modal();
        }
      }
    });
  },
  openPlotArgsSection: function (e) {
    $(this.queryByHook("edit-plot-args")).collapse("show");
    $(document).ready(function () {
      $("html, body").animate({ 
          scrollTop: $("#edit-plot-args").offset().top - 50
      }, false);
    });
  },
  plotFigure: function (figure, type, {pdfOnly=false}={}) {
    if(["inference", "round"].includes(type)) {
      let histoHook = `${type}-histogram-plot`;
      let histoEL = this.queryByHook(histoHook);
      if(!pdfOnly) {
        // Display histogram plot
        Plotly.newPlot(histoEL, figure.histogram);
        $(this.queryByHook(`${type}-histogram-plot-spinner`)).css("display", "none");
        $(this.queryByHook(`${type}-model-export`)).prop("disabled", false);
        $(this.queryByHook(`${type}-model-explore`)).prop("disabled", false);
      }
      // Display pdf plot
      if(type === "inference") {
        let pdfHook = 'inference-pdf-plot';
        let pdfEL = this.queryByHook(pdfHook);
        Plotly.newPlot(pdfEL, figure.pdf);
        $(this.queryByHook('inference-pdf-plot-spinner')).css("display", "none");
      }else {
        let interHook = 'round-intersection-plot';
        let interEL = this.queryByHook(interHook);
        Plotly.newPlot(interEL, figure.pdf);
        $(this.queryByHook('round-intersection-plot-spinner')).css("display", "none");
        if(!pdfOnly) {
          histoEL.on('plotly_click', _.bind(this.selectIntersection, this));
          if(this.model.exportLinks[this.roundIndex] !== null) {
            $(this.queryByHook("round-model-export")).text("Open Model");
            $(this.queryByHook("round-model-explore")).text("Explore Model");
          }else {
            $(this.queryByHook("round-model-export")).text("Export Model");
            $(this.queryByHook("round-model-explore")).text("Export & Explore Model");
          }
        }
      }
    }else {
      let hook = `${type}-plot`;
      let el = this.queryByHook(hook);
      Plotly.newPlot(el, figure);
      if(type === "spatial") {
        $(this.queryByHook("spatial-plot-loading-msg")).css("display", "none");
      }
      $(this.queryByHook(`${type}-plot-spinner`)).css("display", "none");
      if(type === "trajectories" || (this.tsPlotData && this.tsPlotData.type === "trajectories")) {
        $(this.queryByHook("multiple-plots")).prop("disabled", false);
      }      
    }
    if(!pdfOnly) {
      $(this.queryByHook(`${type}-edit-plot`)).prop("disabled", false);
      $(this.queryByHook(`${type}-download`)).prop("disabled", false);
    }
  },
  plotMultiplePlots: function (e) {
    let type = e.target.dataset.type;
    let data = this.getPlotData(type);
    var queryStr = "?path=" + this.model.directory + "&wkfl=" + this.wkflName;
    queryStr += "&job=" + this.model.name + "&data=" + JSON.stringify(data);
    let endpoint = path.join(app.getBasePath(), "model_builder/multiple-plots") + queryStr;
    window.open(endpoint);
  },
  renderEnsembleAggragatorView: function () {
    let ensembleAggragators = [
      ["min", "Minimum of ensemble"],
      ["max", "Maximum of ensemble"],
      ["avg", "Average of ensemble"],
      ["var", "Variance of ensemble"]
    ];
    let ensembleAggragatorView = new SelectView({
      name: 'ensemble-aggragator',
      requires: true,
      idAttribute: 'cid',
      options: ensembleAggragators,
      value: this.model.settings.resultsSettings.reducer
    });
    app.registerRenderSubview(this, ensembleAggragatorView, 'ensemble-aggragator-list');
  },
  renderFeatureExtractionView: function () {
    let featureExtractors = [
      ["min", "Minimum of population"],
      ["max", "Maximum of population"], 
      ["avg", "Average of population"], 
      ["var", "Variance of population"], 
      ["final", "Population at last time point"]
    ];
    let featureExtractionView = new SelectView({
      name: 'feature-extractor',
      requires: true,
      idAttribute: 'cid',
      options: featureExtractors,
      value: this.model.settings.resultsSettings.mapper
    });
    app.registerRenderSubview(this, featureExtractionView, 'feature-extraction-list');
  },
  renderPlotTypeSelectView: function () {
    let options = [
      ["stddevran", "Mean and Standard Deviation"],
      ["trajectories", "Trajectories"],
      ["stddev", "Standard Deviation"],
      ["avg", "Trajectory Mean"]
    ];
    let plotTypeSelectView = new SelectView({
      name: 'plot-type',
      required: true,
      idAttribute: 'cid',
      options: options,
      value: "stddevran"
    });
    app.registerRenderSubview(this, plotTypeSelectView, "plot-type-select");
  },
  renderSpeciesOfInterestView: function () {
    let speciesNames = this.model.model.species.map(function (specie) { return specie.name});
    let speciesOfInterestView = new SelectView({
      name: 'species-of-interest',
      required: true,
      idAttribute: 'cid',
      options: speciesNames,
      value: this.model.settings.parameterSweepSettings.speciesOfInterest.name
    });
    app.registerRenderSubview(this, speciesOfInterestView, "specie-of-interest-list");
  },
  renderSweepParameterView: function () {
    let tsSweepParameterView = this.renderCollection(
      this.model.settings.parameterSweepSettings.parameters,
      SweepParametersView,
      this.queryByHook("ts-parameter-ranges")
    );
    if(this.model.settings.parameterSweepSettings.parameters.length > 2) {
      let options = {viewOptions: {showFixed: true, parent: this}};
      let psSweepParameterView = this.renderCollection(
        this.model.settings.parameterSweepSettings.parameters,
        SweepParametersView,
        this.queryByHook("ps-parameter-ranges"),
        options
      );
    }
  },
  renderTargetOfInterestView: function () {
    let species = this.model.model.species.map((specie) => {
      return [specie.name, specie.name];
    });
    let header = Boolean(species) ? "Variables" : "Variables (empty)";
    let properties = [
      ["type", "Type"], ["0", "X Velocity"], ["1", "Y Velocity"], ["2", "Z Velocity"],
      ["rho", "Density"], ["mass", "Mass"], ["nu", "Viscosity"]
    ];
    let options = [
      {groupName: "Properties", options: properties},
      {groupName: header, options: species}
    ];
    let targetOfInterestView = new SelectView({
      name: 'target',
      required: true,
      eagerValidate: true,
      groupOptions: options,
      value: this.spatialTarget
    });
    app.registerRenderSubview(this, targetOfInterestView, "target-of-interest-list");
  },
  renderTargetModeView: function () {
    if(this.targetModeView) { return; }
    let options = [
      ["discrete", "Population (outputs: absolute value)"],
      ["discrete-concentration", "Population (outputs: scaled by volume)"],
      ["continuous", "Concentration"]
    ];
    this.targetModeView = new SelectView({
      name: 'target-mode',
      required: true,
      eagerValidate: true,
      options: options,
      value: this.targetMode
    });
    app.registerRenderSubview(this, this.targetModeView, "target-mode-list");
  },
  selectIntersection: function (data) {
    let subplot = data.event.target.dataset.subplot;
    let subplotID = subplot === "xy" ? 0 : Number(subplot.split('x').pop().split('y')[0]) - 1;
    let parameters = this.model.settings.inferenceSettings.parameters
    let col = subplotID % parameters.length;
    let row = (subplotID - col) / parameters.length;
    if(row < col) {
      this.intersectionNames = [parameters.at(row).name, parameters.at(col).name];
      this.queryByHook('round-intersection-tab').click();
      setTimeout(() => {
        this.getPlot("round", {pdfOnly: true});
        this.intersectionResized = false;
      }, 0);
    }
  },
  setTitle: function (e) {
    this.plotArgs['title'] = e.target.value
    for (var storageKey in this.plots) {
      let type = this.getType(storageKey);
      let fig = this.plots[storageKey]
      if(Object.keys(fig.layout).includes('title')) {
        fig.layout.title.text = e.target.value
      }else{
        fig.layout.title = {'text': e.target.value, 'x': 0.5, 'xanchor': 'center'}
      }
    }
    for (var [type, storageKey] of Object.entries(this.activePlots)) {
      this.plotFigure(this.plots[storageKey], type);
    }
  },
  setXAxis: function (e) {
    this.plotArgs['xaxis'] = e.target.value
    for (var storageKey in this.plots) {
      let type = this.getType(storageKey);
      let fig = this.plots[storageKey]
      if(['inference', 'round'].includes(type)) {
        fig.layout.annotations.at(-2).text = e.target.value
      }else {
        fig.layout.xaxis.title.text = e.target.value
      }
    }
    for (var [type, storageKey] of Object.entries(this.activePlots)) {
      this.plotFigure(this.plots[storageKey], type);
    }
  },
  setYAxis: function (e) {
    this.plotArgs['yaxis'] = e.target.value
    for (var storageKey in this.plots) {
      let type = this.getType(storageKey);
      let fig = this.plots[storageKey]
      if(['inference', 'round'].includes(type)) {
        fig.layout.annotations.at(-1).text = e.target.value
      }else {
        fig.layout.xaxis.title.text = e.target.value
      }
    }
    for (var [type, storageKey] of Object.entries(this.activePlots)) {
      this.plotFigure(this.plots[storageKey], type);
    }
  },
  startAction: function () {
    $(this.queryByHook("job-action-start")).css("display", "inline-block");
    $(this.queryByHook("job-action-end")).css("display", "none");
    $(this.queryByHook("job-action-err")).css("display", "none");
  },
  update: function () {},
  updateValid: function () {},
  viewRoundIndex: function (e) {
    $(this.queryByHook("round-index-value")).html(e.target.value);
  },
  viewTrajectoryIndex: function (e) {
    $(this.queryByHook("trajectory-index-value")).html(e.target.value);
  },
  subviews: {
    inputTitle: {
      hook: 'title',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: false,
          name: 'title',
          valueType: 'string',
          value: this.plotArgs.title || ""
        });
      }
    },
    inputXAxis: {
      hook: 'xaxis',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: false,
          name: 'xaxis',
          valueType: 'string',
          value: this.plotArgs.xaxis || ""
        });
      }
    },
    inputYAxis: {
      hook: 'yaxis',
      prepareView: function (el) {
        return new InputView({
          parent: this,
          required: false,
          name: 'yaxis',
          valueType: 'string',
          value: this.plotArgs.yaxis || ""
        });
      }
    }
  }
});

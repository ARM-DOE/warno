// Contains, creates and removes different widgets.
function WidgetManager(containerDiv, controllerUrl, logViewerURL, statusPlotURL, genGraphURL) {
    this.containerDiv = containerDiv;
    this.controllerUrl = controllerUrl;
    this.logViewerURL = logViewerURL;
    this.statusPlotURL = statusPlotURL;
    this.genGraphURL = genGraphURL;
    this.newWidgetId = 0;
    this.widgets = [];
    this.hasTightBorders = false;

    this.timer = setInterval(this.tick.bind(this), 60000)
};

WidgetManager.prototype.tick = function(){
    this.removeInactive();
    for (i = 0; i < this.widgets.length; i++){
        this.widgets[i].tick()
    }
};

WidgetManager.prototype.saveDashboard = function() {
    this.removeInactive();

    var payload = [];
    for (i = 0; i < this.widgets.length; i++) {
        payload.push(this.widgets[i].saveDashboard());
    }
    return JSON.stringify(payload);
};

WidgetManager.prototype.loadDashboard = function(dashboardSchematic) {
    this.removeWidgets();
    this.removeInactive();

    this.buildFromSchematic(dashboardSchematic);
};

WidgetManager.prototype.buildFromSchematic = function(dashboardSchematic) {
    // Build objects from the returned dashboard configuration
    for (var i = 0; i < dashboardSchematic.length; i ++) {
        if (dashboardSchematic[i]["type"] == "LogViewer") {
            this.addLogViewer();
            var newLogViewer = this.widgets[this.widgets.length - 1];
            newLogViewer.loadDashboard(dashboardSchematic[i]["data"]);
        }
        if (dashboardSchematic[i]["type"] == "StatusPlot") {
            this.addStatusPlot();
            var newStatusPlot = this.widgets[this.widgets.length - 1];
            newStatusPlot.loadDashboard(dashboardSchematic[i]["data"]);
        }
        if (dashboardSchematic[i]["type"] == "Histogram") {
            this.addHistogram(dashboardSchematic[i]["data"]);
        }
        if (dashboardSchematic[i]["type"] == "DualHistogram") {
            this.addDualHistogram(dashboardSchematic[i]["data"]);
        }
        if (dashboardSchematic[i]["type"] == "InstrumentGraph") {
            this.addInstrumentGraph(dashboardSchematic[i]["data"]);
        }
        if (dashboardSchematic[i]["type"] == "RealTimeGauge") {
            this.addRealTimeGauge(dashboardSchematic[i]["data"]);
        }
    }
}

WidgetManager.prototype.copyWidget = function(widgetId) {
    for (i = 0; i < this.widgets.length; i++) {
        if (this.widgets[i].id == widgetId) {
            // Quick solution. Appends a schematic entry then builds the objects from it.
            var schematic = [];
            schematic.push(this.widgets[i].saveDashboard());
            this.buildFromSchematic(schematic);
        }
    }
}

WidgetManager.prototype.removeInactive = function() {
    for (i = 0; i < this.widgets.length; i++){
        if(!this.widgets[i].active){
            this.widgets.splice(i, 1);
            i--;  // This ensures that the index doesn't get messed up by the removal of an element.
        }
    }
}

WidgetManager.prototype.addLogViewer = function() {
    newLogViewer = new LogViewer(this, this.newWidgetId, this.containerDiv, this.controllerUrl, this.logViewerURL);
    this.widgets.push(newLogViewer);
    this.newWidgetId += 1;
    if (this.hasTightBorders) {
        newLogViewer.tightBorders();
    }
};

WidgetManager.prototype.addStatusPlot = function() {
    newStatusPlot = new StatusPlot(this, this.newWidgetId, this.containerDiv, this.controllerUrl, this.statusPlotURL);
    this.widgets.push(newStatusPlot);
    this.newWidgetId +=1;
    if (this.hasTightBorders) {
        newStatusPlot.tightBorders();
    }
};

WidgetManager.prototype.addHistogram = function(schematic) {
    newHistogram = new Histogram(this, this.newWidgetId, this.containerDiv, this.controllerUrl, schematic);
    this.widgets.push(newHistogram);
    this.newWidgetId +=1;
    if (this.hasTightBorders) {
        newHistogram.tightBorders();
    }
};

WidgetManager.prototype.addDualHistogram = function(schematic) {
    newDualHistogram = new DualHistogram(this, this.newWidgetId, this.containerDiv, this.controllerUrl, schematic);
    this.widgets.push(newDualHistogram);
    this.newWidgetId +=1;
    if (this.hasTightBorders) {
        newDualHistogram.tightBorders();
    }
};

WidgetManager.prototype.addInstrumentGraph = function(schematic) {
    newInstrumentGraph = new InstrumentGraph(this, this.newWidgetId, this.containerDiv, this.controllerUrl,
                                             this.genGraphURL, schematic);
    this.widgets.push(newInstrumentGraph);
    this.newWidgetId += 1;
    if (this.hasTightBorders) {
        newInstrumentGraph.tightBorders();
    }
};

WidgetManager.prototype.addRealTimeGauge = function(schematic) {
    newRealTimeGauge = new RealTimeGauge(this, this.newWidgetId, this.containerDiv, this.controllerUrl, schematic);
    this.widgets.push(newRealTimeGauge);
    this.newWidgetId += 1;
    if (this.hasTightBorders) {
        newRealTimeGauge.tightBorders();
    }
}

WidgetManager.prototype.removeWidgets = function() {
    for (var i = this.widgets.length; i > 0; i--){
        this.widgets[i - 1].remove();
        this.widgets.splice(i - 1, 1);
    }
}

WidgetManager.prototype.tightBorders = function() {
    this.hasTightBorders = true;
    for (var i = 0; i < this.widgets.length; i ++) {
        this.widgets[i].tightBorders();
    }
}

WidgetManager.prototype.wideBorders = function() {
    this.hasTightBorders = false;
    for (var i = 0; i < this.widgets.length; i ++) {
        this.widgets[i].wideBorders();
    }
}



// Log Display Section
function LogViewer(manager, id, containerDiv, controllerUrl, logViewerURL) {
    this.manager = manager;
    this.finishedLoading = true;
    this.id = id;
    this.active = true;                       // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Log Viewer";
    this.div.id = "log-viewer-" + this.id;
    this.logViewerURL = logViewerURL;         // URL for updating the status plot.
    this.updateFrequency = 1;                 // How often in minutes this object will update.
    this.updateCounter = 0;
    this.instrumentId = -1;                   // -1 Translates to 'All' logs
    this.maxLogs = 5;
    this.activeCounter = false;
    this.quickDisplay = false;


    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=log_viewer&widget_id=" + this.id;
    this.ajaxLoadUrl(this.div, parameterizedUrl);
};

LogViewer.prototype.tick = function() {
    if (this.activeCounter === true) {
        this.updateCounter += 1;
        if (this.updateCounter >= this.updateFrequency){
            this.updateCounter = 0;
            this.generateLogViewer();
        }
    }
};

LogViewer.prototype.saveDashboard = function() {
    var data = {"instrumentId": this.instrumentId, "maxLogs": this.maxLogs};
    return {"type": "LogViewer", "data": data};
}

LogViewer.prototype.loadDashboard = function(schematic) {
    this.finishedLoading = false;
    this.quickDisplay = true;  // Forces the full view generation in the ajaxLoadUrl from the LogViewer Creation
    this.instrumentId = schematic["instrumentId"];
    this.maxLogs = schematic["maxLogs"];
    var instrumentIdSelect = document.getElementById("log-viewer-instrument-selector-" + this.id);
    if (instrumentIdSelect) {  // If the element exists, update and generate, if not, should be taken care of by setting quickDisplay above.
        var maxLogsInput = document.getElementById("log-viewer-max-logs-" + this.id);
        instrumentIdSelect.value = this.instrumentId;
        maxLogsInput.value = this.maxLogs;
        this.generateLogViewer();
    }

}

LogViewer.prototype.remove = function() {
    element = document.getElementById('log-viewer-' + this.id);
    element.parentNode.removeChild(element);
    this.active = false;
};

LogViewer.prototype.ajaxLoadUrl = function(element, url) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
            // To get JSON and HTML parts, need to do custom extraction.
            element.innerHTML = xmlHttp.responseText;

            var addButton = document.getElementById("add-log-viewer-button-" + that.id);
            addButton.onclick = function () { that.generateLogViewer(); };
            var copyButton = document.getElementById("copy-log-viewer-button-" + that.id);
            copyButton.onclick = function () { that.manager.copyWidget(that.id); };
            var removeButton = document.getElementById("remove-log-viewer-button-" + that.id);
            removeButton.onclick = function () { that.remove(); };

            var instrumentIdSelect = document.getElementById("log-viewer-instrument-selector-" + that.id);
            var maxLogsInput = document.getElementById("log-viewer-max-logs-" + that.id);
            instrumentIdSelect.value = that.instrumentId;
            maxLogsInput.value = that.maxLogs;

            if (that.quickDisplay === true) {  // If quick display was set, will immediately display with current setup.
                that.generateLogViewer()       // It's an ugly workaround for ajax behaviour for dashboard loading
            }
        }
    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

LogViewer.prototype.generateLogViewer = function() {
    this.activeCounter = true;

    var fillElement = document.getElementById("log-viewer-container-" + this.id);
    this.instrumentId = document.getElementById("log-viewer-instrument-selector-" + this.id).value;
    this.maxLogs = document.getElementById("log-viewer-max-logs-" + this.id).value;
    var url = this.logViewerURL + '?instrument_id=' + this.instrumentId + '&max_logs=' + this.maxLogs;

    ajaxLoadUrl(fillElement, url)
};

LogViewer.prototype.tightBorders = function() {
    this.div.className = "wd_tight";
}

LogViewer.prototype.wideBorders = function() {
    this.div.className = "wd";
}





// Status Plot Section
function StatusPlot(manager, id, containerDiv, controllerUrl, statusPlotURL) {
    this.manager = manager;
    this.id = id;
    this.active = true;                       // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Status Plot";
    this.div.id = "status-plot-" + this.id;
    this.statusPlotURL = statusPlotURL;       // URL for updating the status plot.
    this.updateFrequency = 1;                 // How often in minutes this object will update.
    this.updateCounter = 0;
    this.siteId = -1;                         // Defaults to -1, meaning all sites
    this.activeCounter = false;
    this.quickDisplay = false;                // quickDisplay allows for ajax friendly loading of the dashboard

    this.currentId = 0;

    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=status_plot&widget_id=" + this.id;
    this.ajaxLoadUrl(this.div, parameterizedUrl);
};

StatusPlot.prototype.tick = function() {
    if (this.activeCounter === true) {
        this.updateCounter += 1;
        if (this.updateCounter >= this.updateFrequency){
            this.updateCounter = 0;
            this.generateStatusPlot();
        }
    }
};

StatusPlot.prototype.saveDashboard = function() {
    var data = {"siteId": this.siteId};
    return {"type": "StatusPlot", "data": data};
}

StatusPlot.prototype.loadDashboard = function(schematic) {
    this.quickDisplay = true;  // Forces the full view generation in the ajaxLoadUrl from the StatusPlot Creation
    this.siteId = schematic["siteId"];
    var siteIdSelect = document.getElementById("status-plot-site-selector-" + this.id);
    if (siteIdSelect) {  // If the element exists, update and generate, if not, should be taken care of by setting quickDisplay above.
        siteIdSelect.value = this.siteId;
        this.generateStatusPlot();
    }

}

StatusPlot.prototype.remove = function() {
    element = document.getElementById('status-plot-' + this.id);
    element.parentNode.removeChild(element);
    this.active = false;
};

StatusPlot.prototype.ajaxLoadUrl = function(element, url) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
            // To get JSON and HTML parts, need to do custom extraction.
            element.innerHTML = xmlHttp.responseText;

            var addButton = document.getElementById("add-status-plot-button-" + that.id);
            addButton.onclick = function () { that.generateStatusPlot(); };
            var copyButton = document.getElementById("copy-status-plot-button-" + that.id);
            copyButton.onclick = function () { that.manager.copyWidget(that.id); };
            var removeButton = document.getElementById("remove-status-plot-button-" + that.id);
            removeButton.onclick = function () { that.remove(); };

            var siteIdSelect = document.getElementById("status-plot-site-selector-" + that.id);
            siteIdSelect.value = that.siteId;

            if (that.quickDisplay === true) {  // If quick display was set, will immediately display with current setup.
                that.generateStatusPlot()       // It's an ugly workaround for ajax behaviour for dashboard loading
            }
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

StatusPlot.prototype.generateStatusPlot = function() {
    this.activeCounter = true;

    var fillElement = document.getElementById("status-plot-container-" + this.id);
    this.siteId = document.getElementById("status-plot-site-selector-" + this.id).value;
    var url = this.statusPlotURL + '?site_id=' + this.siteId;

    ajaxLoadUrl(fillElement, url)
};

StatusPlot.prototype.tightBorders = function() {
    this.div.className = "wd_tight";
}

StatusPlot.prototype.wideBorders = function() {
    this.div.className = "wd";
}



// Real Time Gauge section
function RealTimeGauge(manager, id, containerDiv, controllerUrl, schematic) {
    this.manager = manager;
    this.id = id;
    this.active = true;            // When no longer active, should be removed from the parent manager
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Histogram";
    this.div.id = "real-time-gauge-" + this.id;

    this.instrument_list = [];
    this.column_list = [];

    var validSchematic = false;
    if (schematic) {
        validSchematic = true;
        this.instrumentId = schematic["instrumentId"];
        this.attribute = schematic["attribute"];
        this.controllerHidden = schematic["controllerHidden"];
        this.graphSize = schematic["graphSize"];
    } else {
        this.instrumentId = null;
        this.attribute = null;
        this.controllerHidden = false;
        this.graphSize = "medium";
    }

    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=real_time_gauge&widget_id=" + this.id;
    // If there was a valid schematic, ajaxLoadUrl will load from the schematic rather than set defaults.
    this.ajaxLoadUrl(this.div, parameterizedUrl, validSchematic);
}

RealTimeGauge.prototype.tick = function() {
    this.updateGauge();
};

RealTimeGauge.prototype.saveDashboard = function() {
    data = {
        "controllerHidden": this.controllerHidden,
        "graphSize": this.graphSize,
        "instrumentId": this.instrumentId,
        "attribute": this.attribute
    }

    return {"type": "RealTimeGauge", "data": data};
}

RealTimeGauge.prototype.remove = function () {
    element = document.getElementById('real-time-gauge-' + this.id);
    element.parentNode.removeChild(element);
    this.active = false;
};

RealTimeGauge.prototype.ajaxLoadUrl = function(element, url, loadDashboard) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
                        // To get JSON and HTML parts, need to do custom extraction.
            var responseDict = JSON.parse(xmlHttp.responseText);
            element.innerHTML = responseDict["html"];
            // Updates the instrument and column lists for the update function to populate properly.
            that.instrumentList = responseDict["json"]["instrument_list"];
            that.columnList = responseDict["json"]["column_list"];

            that.initializeElements(loadDashboard);
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

RealTimeGauge.prototype.initializeElements = function (loadDashboard) {
    var that = this;

    if (loadDashboard) {


        // TODO set graph size?
        document.getElementById("real-time-gauge-size-button-" + that.graphSize + "-" + that.id).checked = true;

        if (that.controllerHidden) {
            that.hideController();
        }
        if (that.constraintStyle == "auto") {
            that.showConstraintAuto();
        } else {
            that.showConstraintCustom();
        }
    } else {

    }

    // Selector for which instrument the attributes are for
    // When changed should update all options for attribute selector
    var selector = document.getElementById("instrument-select-" + that.id);
    selector.onchange = function () { that.updateSelect(false); };

    // Button to copy Histogram widget. Disabled until data is graphed (or data will not properly copy)
    var copyButton = document.getElementById("real-time-gauge-copy-button-" + that.id);
    copyButton.onclick = function () { that.manager.copyWidget(that.id); };
    copyButton.disabled = true;
    copyButton.title = "Cannot Copy Until Gauge Displayed";

    // Button to remove Histogram widget
    var removeButton = document.getElementById("real-time-gauge-remove-button-" + that.id);
    removeButton.onclick = function () { that.remove(); };

    // Button to generate Histogram from data parameter controls
    var addButton = document.getElementById("real-time-gauge-add-button-" + that.id);
    addButton.onclick = function () { that.generateRealTimeGauge(); };

    // Data parameter controls: Hide and Reveal
    var hideButton = document.getElementById("real-time-gauge-hide-button-" + that.id);
    hideButton.onclick = function () { that.hideController(); };
    var revealButton = document.getElementById("real-time-gauge-reveal-button-" + that.id);
    revealButton.onclick = function () { that.revealController(); };

    // Update attribute selector with options
    that.updateSelect(loadDashboard);
}

RealTimeGauge.prototype.updateSelect = function(loadDashboard) {
    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var attributeSelect = document.getElementById("attribute-select-" + this.id);
    var attributeInput = document.getElementById("attribute-input-" + this.id);

    if (loadDashboard){
        if (this.instrumentId) {
            instrumentSelect.value = this.instrumentId;
        }
    }

    removeOptions(attributeSelect);
    instrumentId = instrumentSelect.value;
    var instrumentValidColumns = this.columnList[instrumentId];
    instrumentValidColumns.sort()

    for (var i =0; i< instrumentValidColumns.length; i++){
        newOption = document.createElement("option");
        newOption.value = instrumentValidColumns[i];
        newOption.text = instrumentValidColumns[i];
        attributeSelect.appendChild(newOption);
    }

    if (loadDashboard){
        if (this.attribute) {
            attributeInput.value = this.attribute;
        }
    }

}

RealTimeGauge.prototype.generateRealTimeGauge = function () {
    console.log("Generated");
}

RealTimeGauge.prototype.updateRealTimeGauge = function () {
    console.log("Trigger");
}

RealTimeGauge.prototype.hideController = function () {
    element = document.getElementById("real-time-gauge-controller-" + this.id);
    element.style.display = "none";
    this.controllerHidden = true;
};

RealTimeGauge.prototype.revealController = function () {
    element = document.getElementById("real-time-gauge-controller-" + this.id);
    element.style.display = "";
    this.controllerHidden = false;
};

RealTimeGauge.prototype.tightBorders = function() {
    this.div.className = "wd_tight";
}

RealTimeGauge.prototype.wideBorders = function() {
    this.div.className = "wd";
}
















// Histogram Section
// If schematic is null, loads up with defaults.  If schematic exists, loads the schematic and displays the histogram
function Histogram(manager, id, containerDiv, controllerUrl, schematic) {
    this.manager = manager;
    this.id = id;
    this.active = true;       // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Histogram";
    this.div.id = "histogram-" + this.id;
    this.instrumentList = []; // Filled by ajax request
    this.columnList = [];     // Filled by ajax request
    this.lastReceived = null;      // The timestamp for the last data received

    this.updateCounter = 0;
    this.activeCounter = false;

    var validSchematic = false;
    if (schematic) {
        validSchematic = true;
        this.controllerHidden = schematic["controllerHidden"];
        this.updateFrequency = schematic["updateFrequency"]; // How often in minutes this object will update.

        this.binNumber = schematic["binNumber"];
        this.colorRed = schematic["colorRed"];
        this.colorGreen = schematic["colorGreen"];
        this.colorBlue = schematic["colorBlue"];

        this.startUTC = schematic["startUTC"];
        this.endUTC = schematic["endUTC"];
        this.lowerLimit = schematic["lowerLimit"];
        this.upperLimit = schematic["upperLimit"];
        this.graphSize = schematic["graphSize"];

        this.instrumentId = schematic["instrumentId"];
        this.attribute = schematic["attribute"];

        // Need to perform checks now, because some previously saved dashboards will not have these new fields.
        if (schematic["constraintStyle"]) {
            this.constraintStyle = schematic["constraintStyle"];
        } else {
            this.constraintStyle = "custom";
        }
        if (schematic["constraintRange"]) {
            this.constraintRange = schematic["constraintRange"];
        } else {
            this.constraintRange = "sixhour"
        }
        if (schematic["convertToDB"]) {
            this.convertToDB = schematic["convertToDB"];
        } else {
            this.convertToDB = false;
        }
    } else {
        this.controllerHidden = false;
        this.updateFrequency = 5; // How often in minutes this object will update.

        this.binNumber = 0;
        this.colorRed = 0;
        this.colorGreen = 50;
        this.colorBlue = 226;

        this.startUTC = "01/01/2000 00:00";
        this.endUTC = "01/01/2170 00:00:00";
        this.lowerLimit = "";
        this.upperLimit = "";
        this.graphSize = "medium";

        this.instrumentId = null;
        this.attribute = null;
        this.constraintStyle = "custom";   // The data constraint controls available
        this.constraintRange = "sixhour";  // If constraintStyle is 'auto', the range for the data displayed
        this.convertToDB = false;          // Whether or not the data is converted to dB scale before graphing.
    }

    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=histogram&widget_id=" + this.id;
    // If there was a valid schematic, ajaxLoadUrl will load from the schematic rather than set defaults.
    this.ajaxLoadUrl(this.div, parameterizedUrl, validSchematic);
};

Histogram.prototype.tick = function() {
    if (this.activeCounter === true) {
        this.updateCounter += 1;
        if (this.updateCounter >= this.updateFrequency){
            this.updateCounter = 0;
            this.generateHistogram();
        }
    }
};

Histogram.prototype.saveDashboard = function() {
    data = {
        "controllerHidden": this.controllerHidden,
        "binNumber": this.binNumber,
        "colorRed": this.colorRed,
        "colorGreen": this.colorGreen,
        "colorBlue": this.colorBlue,
        "startUTC": this.startUTC,
        "endUTC": this.endUTC,
        "lowerLimit": this.lowerLimit,
        "upperLimit": this.upperLimit,
        "graphSize": this.graphSize,
        "instrumentId": this.instrumentId,
        "attribute": this.attribute,
        "updateFrequency": this.updateFrequency,
        "constraintStyle": this.constraintStyle,
        "constraintRange": this.constraintRange,
        "convertToDB": this.convertToDB
    }

    return {"type": "Histogram", "data": data};
}

Histogram.prototype.ajaxLoadUrl = function(element, url, loadDashboard) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
            // To get JSON and HTML parts, need to do custom extraction.
            var responseDict = JSON.parse(xmlHttp.responseText);
            element.innerHTML = responseDict["html"];
            // Updates the instrument and column lists for the update function to populate properly.
            that.instrumentList = responseDict["json"]["instrument_list"];
            that.columnList = responseDict["json"]["column_list"];

            that.initializeElements(loadDashboard);
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

Histogram.prototype.initializeElements = function (loadDashboard) {
    var that = this;  // Substitution allows inline function assignments to reference 'this' rather than themselves


    if (loadDashboard) {
        document.getElementById("datetime-input-start-" + that.id).value = that.startUTC;
        document.getElementById("datetime-input-end-" + that.id).value = that.endUTC;

        document.getElementById("histogram-upper-limit-" + that.id).value = parseFloat(that.upperLimit);
        document.getElementById("histogram-lower-limit-" + that.id).value = parseFloat(that.lowerLimit);

        document.getElementById("histogram-size-button-" + that.graphSize + "-" + that.id).checked = true;

        document.getElementById("time-range-" + that.constraintRange + "-" + that.id).checked = true;

        document.getElementById("convert-to-dB-" + that.id).checked = that.convertToDB;

        if (that.controllerHidden) {
            that.hideController();
        }
        if (that.constraintStyle == "auto") {
            that.showConstraintAuto();
        } else {
            that.showConstraintCustom();
        }
    } else {
        // Defaults the graph beginning time to 7 days ago
        updateStartTime(that.id, 7);
        document.getElementById("datetime-input-end-" + that.id).value = that.endUTC;
        that.showConstraintCustom();
    }

    // Selector for which instrument the attributes are for
    // When changed should update all options for attribute selector
    var selector = document.getElementById("instrument-select-" + that.id);
    selector.onchange = function () { that.updateSelect(false); };

    // Button to copy Histogram widget. Disabled until data is graphed (or data will not properly copy)
    var copyButton = document.getElementById("histogram-copy-button-" + that.id);
    copyButton.onclick = function () { that.manager.copyWidget(that.id); };
    copyButton.disabled = true;
    copyButton.title = "Cannot Copy Until Graph Displayed";

    // Button to remove Histogram widget
    var removeButton = document.getElementById("histogram-remove-button-" + that.id);
    removeButton.onclick = function () { that.remove(); };

    // Button to generate Histogram from data parameter controls
    var addButton = document.getElementById("histogram-add-button-" + that.id);
    addButton.onclick = function () { that.generateHistogram(); };

    // Secondary generate Histogram button inside the controller
    var controllerAddButton = document.getElementById("controller-histogram-add-" + that.id);
    controllerAddButton.onclick = function () { that.generateHistogram(); };

    // Data parameter controls: Hide and Reveal
    var hideButton = document.getElementById("histogram-hide-button-" + that.id);
    hideButton.onclick = function () { that.hideController(); };
    var revealButton = document.getElementById("histogram-reveal-button-" + that.id);
    revealButton.onclick = function () { that.revealController(); };

    // Config control bindings: Hide, Reveal, Apply
    var configOpenButton = document.getElementById("histogram-config-open-button-" + that.id);
    configOpenButton.onclick = function () { that.openConfig(); };
    var configCloseButton = document.getElementById("histogram-config-close-button-" + that.id);
    configCloseButton.onclick = function () { that.closeConfig(); };
    var configApplyButton = document.getElementById("histogram-config-apply-button-" + that.id);
    configApplyButton.onclick = function () { that.applyConfig(); };

    // Update attribute selector with options
    that.updateSelect(loadDashboard);

    if (loadDashboard) {
        that.generateHistogram()
    }
}

Histogram.prototype.updateSelect = function(loadDashboard) {
    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var attributeSelect = document.getElementById("attribute-select-" + this.id);
    var attributeInput = document.getElementById("attribute-input-" + this.id);

    if (loadDashboard){
        if (this.instrumentId) {
            instrumentSelect.value = this.instrumentId;
        }
    }

    removeOptions(attributeSelect);
    instrumentId = instrumentSelect.value;
    var instrumentValidColumns = this.columnList[instrumentId];
    instrumentValidColumns.sort()

    for (var i =0; i< instrumentValidColumns.length; i++){
        newOption = document.createElement("option");
        newOption.value = instrumentValidColumns[i];
        newOption.text = instrumentValidColumns[i];
        attributeSelect.appendChild(newOption);
    }

    if (loadDashboard){
        if (this.attribute) {
            attributeInput.value = this.attribute;
        }
    }

}

Histogram.prototype.remove = function () {
    element = document.getElementById('histogram-' + this.id);
    element.parentNode.removeChild(element);
    this.active = false;
};

Histogram.prototype.generateHistogram = function() {
    this.activeCounter = true;  // Activates the periodic update checks

    var xmlhttp = new XMLHttpRequest();
    this.lastReceived = null;

    var div = document.getElementById('histogram-container-' + this.id)

    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var attributeInput = document.getElementById("attribute-input-" + this.id);
    this.instrumentId = instrumentSelect.value;
    var instrumentName = instrumentSelect.options[instrumentSelect.selectedIndex].text;
    this.attribute = attributeInput.value;
    this.startUTC = document.getElementById("datetime-input-start-" + this.id).value;
    this.endUTC = document.getElementById("datetime-input-end-" + this.id).value;
    this.upperLimit = parseFloat(document.getElementById("histogram-upper-limit-" + this.id).value);
    this.lowerLimit = parseFloat(document.getElementById("histogram-lower-limit-" + this.id).value);

    // Enable copy button and change title to reflect functionality
    var copyButton = document.getElementById("histogram-copy-button-" + this.id);
    copyButton.disabled = false;
    copyButton.title = "Copy This Widget";

    this.convertToDB = document.getElementById("convert-to-dB-" + this.id).checked;

    // Size from radio set
    var graphWidth = 500;
    var graphHeight = 400;
    var graphSizeElement = document.querySelector('input[name="histogram-size-' + this.id + '"]:checked');
    if (graphSizeElement) {
        this.graphSize = graphSizeElement.value;
    }

    var constraintRange = document.querySelector('input[name="time-range-' + this.id + '"]:checked');

    if (constraintRange) {
        this.constraintRange = constraintRange.value;
    }

    // Set sizes according to selection
    if (this.graphSize == "small") {
        graphWidth = 350;
        graphHeight = 280;
    } else if (this.graphSize == "medium") {
        graphWidth = 500;
        graphHeight = 400;
    } else if (this.graphSize == "large") {
        graphWidth = 750;
        graphHeight = 600;
    }

//    var key_elems = document.getElementById('attribute-input-' + this.id);
//    var keys = [];
//    for (var i = 0; i < key_elems.length; i++) {
//        keys.push(key_elems[i].value);
//    }

    start = new Date(this.startUTC + " UTC");
    end = new Date(this.endUTC + " UTC");

    var that = this; // Allows 'this' object to be accessed correctly within the xmlhttp function.
                     // Inside the function 'this' references the function rather than the Histogram object we want.

    // Setup AJAX message and send.
    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var response = JSON.parse(xmlhttp.responseText);

            delete that.lastReceived;

            if (response == "[]") {
                // There was an error.  This is probably a very foolish way to indicate errors from server->client
                var masterDiv = document.getElementById('histogram-container-' + that.id)
                while (masterDiv.hasChildNodes()) {
                    masterDiv.removeChild(masterDiv.firstChild);
                }
                var errorDiv = document.createElement("div");
                errorDiv.style.color = "red";
                errorDiv.innerHTML = "Could not retrieve Data.  Verify attribute is valid.";
                masterDiv.appendChild(errorDiv);
            }

            if (response.data) {
                if (response.data.length > 0) {
                    // Only works because received data is sorted by time with newest at the end.
                    // Timestamp from most recent data.  Adding Z tells Date it is UTC
                    that.lastReceived = new Date(response.data[response.data.length - 1][0] + "Z")
                } else {
                    that.lastReceived = null;
                }

                var field1 = response.data.map(function(i){ return i[1] });

                field1 = field1.filter(isNotSentinel);
                if (that.convertToDB) {
                    field1 = field1.map(toDB);
                }

                var useAutorange = true;
                var histogramRange = [0,1];

                var lowerBin = Math.min(...field1);
                var upperBin = Math.max(...field1);
                if (upperBin == lowerBin) { // Kind of cheap way to prevent 0 bin sizes due to all data being same value
                    upperBin += 0.0000001;
                    lowerBin -= 0.0000001;
                }
                var binSize = 0.25;
                var xbinDict = {};

                if (that.binNumber > 0) {
                    nbins = that.binNumber;
                } else {
                    nbins = Math.sqrt(field1.length);
                }

                // If upper and lower limits are set and valid, set the bin and range limits to them
                if (!isNaN(that.lowerLimit)
                    && that.lowerLimit != ""
                    && !isNaN(that.upperLimit)
                    && that.upperLimit != "")
                {
                    histogramRange = [that.lowerLimit, that.upperLimit];
                    useAutorange = false;
                    lowerBin = that.lowerLimit;
                    upperBin = that.upperLimit;
                }

                // Calculate bin size from either the default limits or the custom limits
                binSize = (upperBin - lowerBin) / nbins;

                var data = [
                    {
                        x: field1,
                        type: 'histogram',
                        marker: {
                            color: 'rgba(' + that.colorRed + ', ' + that.colorGreen + ', ' + that.colorBlue + ', 0.7)',
                        },

                        autobinx: false,
                        xbins: {
                            start: lowerBin,
                            end: upperBin,
                            size: binSize
                        }
                    }]

                var layout = {
                    showlegend: false,
                    autosize: false,
                    width: graphWidth,
                    height: graphHeight,
                    margin: {t: 50, r: 50, b: 50, l: 50, pad:10},
                    hovermode: 'closest',
                    bargap: 0,
                    title: instrumentName + ":" + that.attribute,
                    xaxis: {
                        //domain: [-20, 30],
                        autorange: useAutorange,
                        range: histogramRange,
                        showgrid: true,
                        zeroline: false,
                        title: "Value",
                    },
                    yaxis: {
                        //domain: [0, 0.85],
                        showgrid: true,
                        zeroline: true,
                        title: "Occurences",
                        gridwidth: 3,
                        gridcolor: "#rgb(200,200,200,0.7)"
                    },
                };

                Plotly.newPlot(div, data, layout);
                that.updateLastReceived();

            } else {
                that.lastReceived = null;
            }
        }
    };

    if (this.constraintStyle == "auto") {
        var startTime = this.getAutomaticBeginning();
        var endTime = new Date();
        var startUTCArg = startTime.toUTCString();
        var endUTCArg = endTime.toUTCString();
    } else {
        var startUTCArg = this.startUTC;
        var endUTCArg = this.endUTC;
    }

    var url = "/generate_instrument_graph" +
              "?keys=" + this.attribute +
              "&instrument_id=" + this.instrumentId +
              "&start=" + startUTCArg +
              "&end=" + endUTCArg;
    xmlhttp.open("POST", url, true);

    //Send out the request
    xmlhttp.send();

};

Histogram.prototype.applyConfig = function () {
    var errorElement = document.getElementById("histogram-config-error-" + this.id);
    var successElement = document.getElementById("histogram-config-success-" + this.id);
    errorElement.innerHTML = "";
    successElement.innerHTML = "";

    var errorOccurred = false;
    var errorMessage = ""

    // Validate Update Frequency
    // Cast value to an integer if possible.  If it fails, get NaN
    var inputUpdateFrequency = +(document.getElementById("histogram-update-frequency-" + this.id).value);
    if (!isNaN(inputUpdateFrequency) && isNormalInteger(String(inputUpdateFrequency))){
        if (inputUpdateFrequency <= 0){
            errorMessage += "Update Frequency must be positive integer.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Update Frequency must be positive integer.<br>";
        errorOccurred = true;
    }

    // Validate Bin Number
    var inputBinNumber = +(document.getElementById("histogram-bin-number-" + this.id).value);
    if (isNaN(inputBinNumber) || !isNormalInteger(String(inputBinNumber))){
        errorMessage += "Number of Bins must be positive integer or 0.<br>";
        errorOccurred = true;
    }

    // Validate Colors
    var inputColorRed = +(document.getElementById("histogram-color-red-" + this.id).value);
    if (!isNaN(inputColorRed) && isNormalInteger(String(inputColorRed))){
        if (inputColorRed > 255) {
            errorMessage += "Graph Color Red must be an integer from 0 to 255.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Graph Color Red must be an integer from 0 to 255.<br>";
        errorOccurred = true;
    }

    var inputColorGreen = +(document.getElementById("histogram-color-green-" + this.id).value);
    if (!isNaN(inputColorGreen) && isNormalInteger(String(inputColorGreen))){
        if (inputColorGreen > 255) {
            errorMessage += "Graph Color Green must be an integer from 0 to 255.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Graph Color Green must be an integer from 0 to 255.<br>";
        errorOccurred = true;
    }

    var inputColorBlue = +(document.getElementById("histogram-color-blue-" + this.id).value);
    if (!isNaN(inputColorBlue) && isNormalInteger(String(inputColorBlue))){
        if (inputColorBlue > 255) {
            errorMessage += "Graph Color Blue must be an integer from 0 to 255.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Graph Color Blue must be an integer from 0 to 255.<br>";
        errorOccurred = true;
    }

    if (errorOccurred) {
        errorElement.innerHTML = errorMessage;
    } else {
        this.updateFrequency = inputUpdateFrequency;
        this.binNumber = inputBinNumber;
        this.colorRed = inputColorRed;
        this.colorGreen = inputColorGreen;
        this.colorBlue = inputColorBlue;

        successElement.innerHTML = "Configuration Updated.";
        this.generateHistogram();
    }
};


Histogram.prototype.updateLastReceived = function() {
    var statusBubble = document.getElementById("receive-status-" + this.id);
    if (this.lastReceived == null) {
        statusBubble.className = "db_receive_status";
        document.getElementById("last-received-" + this.id).innerHTML = "No Data";
        return;
    }

    // If lastReceived exists, display the time the last data was received and update status bubble depending on age.
    var day = this.lastReceived.getUTCDate();
    var month = this.lastReceived.getUTCMonth() + 1;
    var year = this.lastReceived.getUTCFullYear();
    var hours = this.lastReceived.getUTCHours();
    var minutes = this.lastReceived.getUTCMinutes();
    var seconds = this.lastReceived.getUTCSeconds();
    var lastReceivedUTC = month + "/" + day + "/" + year + " " + hours + ":" + minutes + ":" + seconds;
    document.getElementById("last-received-" + this.id).innerHTML = lastReceivedUTC;

    var currentTime = new Date();
    var differenceMinutes = (currentTime - this.lastReceived) / (60000); // Difference starts in milliseconds

    if ((0 <= differenceMinutes) && (differenceMinutes < 5)) {
        statusBubble.className = "db_receive_status db_status_good";
    } else if ((5 <= differenceMinutes) && (differenceMinutes <= 15)) {
        statusBubble.className = "db_receive_status db_status_weak";
    } else {
        statusBubble.className = "db_receive_status db_status_dead";
    }

}


Histogram.prototype.getAutomaticBeginning = function () {
    var now = new Date();
    if (this.constraintRange == "tenminute") {
        return new Date(now.setMinutes(now.getMinutes() - 10));
    } if (this.constraintRange == "hour") {
        return new Date(now.setHours(now.getHours() - 1));
    } else if (this.constraintRange == "sixhour") {
        return new Date(now.setHours(now.getHours() - 6));
    } else if (this.constraintRange == "day") {
        return new Date(now.setDate(now.getDate() - 1));
    } else if (this.constraintRange == "week") {
        return new Date(now.setDate(now.getDate() - 7));
    } else if (this.constraintRange == "fortnight") {
        return new Date(now.setDate(now.getDate() - 14));
    } else if (this.constraintRange == "month") {
        return new Date(now.setMonth(now.getMonth() - 1));
    } else {
        // Default to six hours
        return new Date(now.setHours(now.getHours() - 6));
    }

}

Histogram.prototype.hideController = function () {
    element = document.getElementById("histogram-controller-" + this.id);
    element.style.display = "none";
    this.controllerHidden = true;
};

Histogram.prototype.revealController = function () {
    element = document.getElementById("histogram-controller-" + this.id);
    element.style.display = "";
    this.controllerHidden = false;
};

Histogram.prototype.openConfig = function () {
    var contentElement = document.getElementById("histogram-content-" + this.id);
    var configElement = document.getElementById("histogram-config-" + this.id);
    contentElement.style.display = "none";
    configElement.style.display = "block";

    // Clear and reset input values and messages
    var frequencyInput = document.getElementById("histogram-update-frequency-" + this.id);
    frequencyInput.value = this.updateFrequency;

    var binNumberInput = document.getElementById("histogram-bin-number-" + this.id);
    binNumberInput.value = this.binNumber;

    var colorRedInput = document.getElementById("histogram-color-red-" + this.id);
    colorRedInput.value = this.colorRed;
    var colorGreenInput = document.getElementById("histogram-color-green-" + this.id);
    colorGreenInput.value = this.colorGreen;
    var colorBlueInput = document.getElementById("histogram-color-blue-" + this.id);
    colorBlueInput.value = this.colorBlue;

    var errorElement = document.getElementById("histogram-config-error-" + this.id);
    var successElement = document.getElementById("histogram-config-success-" + this.id);
    errorElement.innerHTML = "";
    successElement.innerHTML = "";
};

Histogram.prototype.closeConfig = function () {
    var contentElement = document.getElementById("histogram-content-" + this.id);
    var configElement = document.getElementById("histogram-config-" + this.id);
    configElement.style.display = "";
    contentElement.style.display = "";
};

Histogram.prototype.showConstraintAuto = function () {
    var autoElement = document.getElementById("auto-times-" + this.id);
    var customElement = document.getElementById("custom-times-" + this.id);
    var constraintButton = document.getElementById("time-constraint-switch-" + this.id);
    autoElement.style.display = "block";
    customElement.style.display = "none";
    var that = this;
    constraintButton.onclick = function () { that.showConstraintCustom(); };
    constraintButton.innerHTML = "Switch to Custom Range";
    this.constraintStyle = "auto"
}

Histogram.prototype.showConstraintCustom = function () {
    var autoElement = document.getElementById("auto-times-" + this.id);
    var customElement = document.getElementById("custom-times-" + this.id);
    var constraintButton = document.getElementById("time-constraint-switch-" + this.id);
    autoElement.style.display = "none";
    customElement.style.display = "block";
    var that = this;
    constraintButton.onclick = function () { that.showConstraintAuto(); };
    constraintButton.innerHTML = "Switch to Sliding Window";
    this.constraintStyle = "custom";
}

Histogram.prototype.tightBorders = function() {
    this.div.className = "wd_tight";
}

Histogram.prototype.wideBorders = function() {
    this.div.className = "wd";
}



// DualHistogram Section
// If schematic is null, loads up with defaults.  If schematic exists, loads the schematic and displays the histogram
function DualHistogram(manager, id, containerDiv, controllerUrl, schematic) {
    this.manager = manager;
    this.id = id;
    this.active = true;       // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Dual Histogram";
    this.div.id = "histogram-" + this.id;
    this.instrumentList = []; // Filled by ajax request
    this.columnList = [];     // Filled by ajax request
    this.lastReceived = null;      // The timestamp for the last data received

    this.updateCounter = 0;
    this.activeCounter = false;

    var validSchematic = false;
    if (schematic) {
        validSchematic = true;
        this.controllerHidden = schematic["controllerHidden"];
        this.updateFrequency = schematic["updateFrequency"]; // How often in minutes this object will update.

        this.colorRed = schematic["colorRed"];
        this.colorGreen = schematic["colorGreen"];
        this.colorBlue = schematic["colorBlue"];

        this.startUTC = schematic["startUTC"];
        this.endUTC = schematic["endUTC"];
        this.xLowerLimit = schematic["xLowerLimit"];
        this.xUpperLimit = schematic["xUpperLimit"];
        this.yLowerLimit = schematic["yLowerLimit"];
        this.yUpperLimit = schematic["yUpperLimit"];
        this.graphSize = schematic["graphSize"];

        this.instrumentId = schematic["instrumentId"];
        this.attribute1 = schematic["attribute1"];
        this.attribute2 = schematic["attribute2"];

        this.constraintStyle = schematic["constraintStyle"];
        this.constraintRange = schematic["constraintRange"];
        this.convertToDB = schematic["convertToDB"];

        this.colorScale = schematic["colorScale"];  // Color scale for histogram heat map
    } else {
        this.controllerHidden = false;
        this.updateFrequency = 5; // How often in minutes this object will update.

        this.colorRed = 0;
        this.colorGreen = 50;
        this.colorBlue = 226;

        this.startUTC = "01/01/2000 00:00";
        this.endUTC = "01/01/2170 00:00:00";
        this.xLowerLimit = "";
        this.xUpperLimit = "";
        this.yLowerLimit = "";
        this.yUpperLimit = "";
        this.graphSize = "medium";

        this.instrumentId = null;
        this.attribute1 = null;
        this.attribute2 = null;
        this.constraintStyle = "custom";   // The data constraint controls available
        this.constraintRange = "sixhour";  // If constraintStyle is 'auto', the range for the data displayed
        this.convertToDB = false;          // Whether or not the data is converted to dB scale before graphing.

        this.colorScale = "Hot";           // Color scale for histogram heat map
    }

    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=dual_histogram&widget_id=" + this.id;
    // If there was a valid schematic, ajaxLoadUrl will load from the schematic rather than set defaults.
    this.ajaxLoadUrl(this.div, parameterizedUrl, validSchematic);
};

DualHistogram.prototype.tick = function() {
    if (this.activeCounter === true) {
        this.updateCounter += 1;
        if (this.updateCounter >= this.updateFrequency){
            this.updateCounter = 0;
            this.generateDualHistogram();
        }
    }
};

DualHistogram.prototype.saveDashboard = function() {
    data = {
        "controllerHidden": this.controllerHidden,
        "colorRed": this.colorRed,
        "colorGreen": this.colorGreen,
        "colorBlue": this.colorBlue,
        "startUTC": this.startUTC,
        "endUTC": this.endUTC,
        "xLowerLimit": this.xLowerLimit,
        "xUpperLimit": this.xUpperLimit,
        "yLowerLimit": this.yLowerLimit,
        "yUpperLimit": this.yUpperLimit,
        "graphSize": this.graphSize,
        "instrumentId": this.instrumentId,
        "attribute1": this.attribute1,
        "attribute2": this.attribute2,
        "updateFrequency": this.updateFrequency,
        "constraintStyle": this.constraintStyle,
        "constraintRange": this.constraintRange,
        "convertToDB": this.convertToDB,
        "colorScale": this.colorScale
    }

    return {"type": "DualHistogram", "data": data};
}

DualHistogram.prototype.ajaxLoadUrl = function(element, url, loadDashboard) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
            // To get JSON and HTML parts, need to do custom extraction.
            var responseDict = JSON.parse(xmlHttp.responseText);
            element.innerHTML = responseDict["html"];
            // Updates the instrument and column lists for the update function to populate properly.
            that.instrumentList = responseDict["json"]["instrument_list"];
            that.columnList = responseDict["json"]["column_list"];

            that.initializeElements(loadDashboard);
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

DualHistogram.prototype.initializeElements = function (loadDashboard) {
    var that = this;  // Substitution allows inline function assignments to reference 'this' rather than themselves


    if (loadDashboard) {
        document.getElementById("datetime-input-start-" + that.id).value = that.startUTC;
        document.getElementById("datetime-input-end-" + that.id).value = that.endUTC;

        document.getElementById("histogram-x-upper-limit-" + that.id).value = parseFloat(that.xUpperLimit);
        document.getElementById("histogram-x-lower-limit-" + that.id).value = parseFloat(that.xLowerLimit);
        document.getElementById("histogram-y-upper-limit-" + that.id).value = parseFloat(that.yUpperLimit);
        document.getElementById("histogram-y-lower-limit-" + that.id).value = parseFloat(that.yLowerLimit);

        document.getElementById("histogram-size-button-" + that.graphSize + "-" + that.id).checked = true;

        document.getElementById("time-range-" + that.constraintRange + "-" + that.id).checked = true;

        document.getElementById("convert-to-dB-" + that.id).checked = that.convertToDB;

        if (that.controllerHidden) {
            that.hideController();
        }
        if (that.constraintStyle == "auto") {
            that.showConstraintAuto();
        } else {
            that.showConstraintCustom();
        }
    } else {
        // Defaults the graph beginning time to 7 days ago
        updateStartTime(that.id, 7);
        document.getElementById("datetime-input-end-" + that.id).value = that.endUTC;
        that.showConstraintCustom();
    }

    document.getElementById("color-scale-" + that.id).value = that.colorScale;

    // Selector for which instrument the attributes are for
    // When changed should update all options for attribute selector
    var selector = document.getElementById("instrument-select-" + that.id);
    selector.onchange = function () { that.updateSelect(false); };

    // Button to copy Histogram widget. Disabled until data is graphed (or data will not properly copy)
    var copyButton = document.getElementById("histogram-copy-button-" + that.id);
    copyButton.onclick = function () { that.manager.copyWidget(that.id); };
    copyButton.disabled = true;
    copyButton.title = "Cannot Copy Until Graph Displayed";

    // Button to remove Histogram widget
    var removeButton = document.getElementById("histogram-remove-button-" + that.id);
    removeButton.onclick = function () { that.remove(); };

    // Button to generate Histogram from data parameter controls
    var addButton = document.getElementById("histogram-add-button-" + that.id);
    addButton.onclick = function () { that.generateDualHistogram(); };

    // Secondary generate Histogram button inside the controller
    var controllerAddButton = document.getElementById("controller-histogram-add-" + that.id);
    controllerAddButton.onclick = function () { that.generateDualHistogram(); };

    // Data parameter controls: Hide and Reveal
    var hideButton = document.getElementById("histogram-hide-button-" + that.id);
    hideButton.onclick = function () { that.hideController(); };
    var revealButton = document.getElementById("histogram-reveal-button-" + that.id);
    revealButton.onclick = function () { that.revealController(); };

    // Config control bindings: Hide, Reveal, Apply
    var configOpenButton = document.getElementById("histogram-config-open-button-" + that.id);
    configOpenButton.onclick = function () { that.openConfig(); };
    var configCloseButton = document.getElementById("histogram-config-close-button-" + that.id);
    configCloseButton.onclick = function () { that.closeConfig(); };
    var configApplyButton = document.getElementById("histogram-config-apply-button-" + that.id);
    configApplyButton.onclick = function () { that.applyConfig(); };

    // Update attribute selector with options
    that.updateSelect(loadDashboard);

    if (loadDashboard) {
        that.generateDualHistogram()
    }
}

DualHistogram.prototype.updateSelect = function(loadDashboard) {
    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var attributeSelect1 = document.getElementById("attribute-select-1-" + this.id);
    var attributeInput1 = document.getElementById("attribute-input-1-" + this.id);

    var attributeSelect2 = document.getElementById("attribute-select-2-" + this.id);
    var attributeInput2 = document.getElementById("attribute-input-2-" + this.id);

    if (loadDashboard){
        if (this.instrumentId) {
            instrumentSelect.value = this.instrumentId;
        }
    }

    removeOptions(attributeSelect1);
    removeOptions(attributeSelect2)
    instrumentId = instrumentSelect.value;
    var instrumentValidColumns = this.columnList[instrumentId];
    instrumentValidColumns.sort()

    for (var i =0; i< instrumentValidColumns.length; i++){
        // Attribute 1
        newOption = document.createElement("option");
        newOption.value = instrumentValidColumns[i];
        newOption.text = instrumentValidColumns[i];
        attributeSelect1.appendChild(newOption);
        // Attribute 2
        newOption = document.createElement("option");
        newOption.value = instrumentValidColumns[i];
        newOption.text = instrumentValidColumns[i];
        attributeSelect2.appendChild(newOption);
    }

    if (loadDashboard){
        if (this.attribute1) {
            attributeInput1.value = this.attribute1;
        }
        if (this.attribute2) {
            attributeInput2.value = this.attribute2;
        }
    }

}

DualHistogram.prototype.remove = function () {
    element = document.getElementById('histogram-' + this.id);
    element.parentNode.removeChild(element);
    this.active = false;
};

DualHistogram.prototype.generateDualHistogram = function() {
    this.activeCounter = true;  // Activates the periodic update checks

    var xmlhttp = new XMLHttpRequest();
    this.lastReceived = null;

    var div = document.getElementById('histogram-container-' + this.id)

    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var attributeInput1 = document.getElementById("attribute-input-1-" + this.id);
    var attributeInput2 = document.getElementById("attribute-input-2-" + this.id);
    this.instrumentId = instrumentSelect.value;
    this.instrumentId = instrumentSelect.value;
    var instrumentName = instrumentSelect.options[instrumentSelect.selectedIndex].text;
    this.attribute1 = attributeInput1.value;
    this.attribute2 = attributeInput2.value;
    this.startUTC = document.getElementById("datetime-input-start-" + this.id).value;
    this.endUTC = document.getElementById("datetime-input-end-" + this.id).value;
    this.xUpperLimit = parseFloat(document.getElementById("histogram-x-upper-limit-" + this.id).value);
    this.xLowerLimit = parseFloat(document.getElementById("histogram-x-lower-limit-" + this.id).value);
    this.yUpperLimit = parseFloat(document.getElementById("histogram-y-upper-limit-" + this.id).value);
    this.yLowerLimit = parseFloat(document.getElementById("histogram-y-lower-limit-" + this.id).value);

    // Enable copy button and change title to reflect functionality
    var copyButton = document.getElementById("histogram-copy-button-" + this.id);
    copyButton.disabled = false;
    copyButton.title = "Copy This Widget";

    this.convertToDB = document.getElementById("convert-to-dB-" + this.id).checked;

    // Size from radio set
    var graphWidth = 500;
    var graphHeight = 400;
    var graphSizeElement = document.querySelector('input[name="histogram-size-' + this.id + '"]:checked');
    if (graphSizeElement) {
        this.graphSize = graphSizeElement.value;
    }

    var constraintRange = document.querySelector('input[name="time-range-' + this.id + '"]:checked');

    if (constraintRange) {
        this.constraintRange = constraintRange.value;
    }

    // Set sizes according to selection
    if (this.graphSize == "small") {
        graphWidth = 350;
        graphHeight = 280;
    } else if (this.graphSize == "medium") {
        graphWidth = 500;
        graphHeight = 400;
    } else if (this.graphSize == "large") {
        graphWidth = 750;
        graphHeight = 600;
    }

    start = new Date(this.startUTC + " UTC");
    end = new Date(this.endUTC + " UTC");

    var that = this; // Allows 'this' object to be accessed correctly within the xmlhttp function.
                     // Inside the function 'this' references the function rather than the Histogram object we want.

    // Setup AJAX message and send.
    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var response = JSON.parse(xmlhttp.responseText);

            delete that.lastReceived;

            if (response == "[]") {
                // There was an error.  This is probably a very foolish way to indicate errors from server->client
                var masterDiv = document.getElementById('histogram-container-' + that.id)
                while (masterDiv.hasChildNodes()) {
                    masterDiv.removeChild(masterDiv.firstChild);
                }
                var errorDiv = document.createElement("div");
                errorDiv.style.color = "red";
                errorDiv.innerHTML = "Could not retrieve Data.  Verify attributes are valid.";
                masterDiv.appendChild(errorDiv);
            }

            if (response.data) {
                if (response.data.length > 0) {
                    // Only works because received data is sorted by time with newest at the end.
                    // Timestamp from most recent data.  Adding Z tells Date it is UTC
                    that.lastReceived = new Date(response.data[response.data.length - 1][0] + "Z")
                } else {
                    that.lastReceived = null;
                }
                var t = response.data.map(function(i){ return i[0] });
                var x = response.data.map(function(i){ return i[1] });
                var y = response.data.map(function(i){ return i[2] })

                if (that.convertToDB) {
                    x = x.map(toDB);
                    y = y.map(toDB);
                }

                // If upper and lower limits are set and valid, set the bin and range limits to them
                // For X
                var xUseAutorange = true;
                var xRange = [0, 1]

                if (!isNaN(that.xLowerLimit)
                    && that.xLowerLimit != ""
                    && !isNaN(that.xUpperLimit)
                    && that.xUpperLimit != "")
                {
                    xRange = [that.xLowerLimit, that.xUpperLimit];
                    xUseAutorange = false;
                    lowerBin = that.xLowerLimit;
                    upperBin = that.xUpperLimit;
                }

                // For Y
                var yUseAutorange = true;
                var yRange = [0, 1]

                if (!isNaN(that.yLowerLimit)
                    && that.yLowerLimit != ""
                    && !isNaN(that.yUpperLimit)
                    && that.yUpperLimit != "")
                {
                    yRange = [that.yLowerLimit, that.yUpperLimit];
                    yUseAutorange = false;
                    lowerBin = that.yLowerLimit;
                    upperBin = that.yUpperLimit;
                }
                var trace1 = {
                    x: x,
                    y: y,
                    mode: 'markers',
                    name: 'points',
                    marker: {
                        color: 'rgb(' + that.colorRed + ', ' + that.colorGreen + ', ' + that.colorBlue + ')',
                        size: 2,
                        opacity: 0.4
                    },
                    type: 'scatter'
                };
                var trace2 = {
                    x: x,
                    y: y,
                    name: 'density',
                    ncontours: 20,
                    colorscale: that.colorScale,
                    reversescale: true,
                    showscale: false,
                    type: 'histogram2dcontour'
                };
                var trace3 = {
                    x: x,
                    name: 'x density',
                    marker: {color: 'rgb(' + that.colorRed + ', ' + that.colorGreen + ', ' + that.colorBlue + ')'},
                    yaxis: 'y2',
                    type: 'histogram'
                };
                var trace4 = {
                    y: y,
                    name: 'ydensity',
                    marker: {color: 'rgb(' + that.colorRed + ', ' + that.colorGreen + ', ' + that.colorBlue + ')'},
                    xaxis: 'x2',
                    type: 'histogram'
                };
                var data = [trace1, trace2, trace3, trace4];
                var layout = {
                    showlegend: false,
                    autosize: false,
                    width: graphWidth,
                    height: graphHeight,
                    margin: {t: 50},
                    hovermode: 'closest',
                    bargap: 0,
                    xaxis: {
                        title: that.attribute1,
                        domain: [0, 0.85],
                        autorange: xUseAutorange,
                        range: xRange,
                        showgrid: false,
                        zeroline: false
                    },
                    yaxis: {
                        title: that.attribute2,
                        domain: [0, 0.85],
                        autorange: yUseAutorange,
                        range: yRange,
                        showgrid: false,
                        zeroline: false
                    },
                    xaxis2: {
                        domain: [0.85, 1],
                        showgrid: false,
                        zeroline: false
                    },
                    yaxis2: {
                        domain: [0.85, 1],
                        showgrid: false,
                        zeroline: false
                    }
                };

                Plotly.newPlot(div, data, layout);
                that.updateLastReceived();

            } else {
                that.lastReceived = null;
            }
        }
    };

    if (this.constraintStyle == "auto") {
        var startTime = this.getAutomaticBeginning();
        var endTime = new Date();
        var startUTCArg = startTime.toUTCString();
        var endUTCArg = endTime.toUTCString();
    } else {
        var startUTCArg = this.startUTC;
        var endUTCArg = this.endUTC;
    }

    var url = "/generate_instrument_graph" +
              "?keys=" + this.attribute1 + "," + this.attribute2 +
              "&instrument_id=" + this.instrumentId +
              "&start=" + startUTCArg +
              "&end=" + endUTCArg;
    xmlhttp.open("POST", url, true);

    //Send out the request
    xmlhttp.send();

};

DualHistogram.prototype.applyConfig = function () {
    var errorElement = document.getElementById("histogram-config-error-" + this.id);
    var successElement = document.getElementById("histogram-config-success-" + this.id);
    errorElement.innerHTML = "";
    successElement.innerHTML = "";

    var errorOccurred = false;
    var errorMessage = ""

    var colorScale = document.getElementById("color-scale-" + this.id).value;

    // Validate Update Frequency
    // Cast value to an integer if possible.  If it fails, get NaN
    var inputUpdateFrequency = +(document.getElementById("histogram-update-frequency-" + this.id).value);
    if (!isNaN(inputUpdateFrequency) && isNormalInteger(String(inputUpdateFrequency))){
        if (inputUpdateFrequency <= 0){
            errorMessage += "Update Frequency must be positive integer.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Update Frequency must be positive integer.<br>";
        errorOccurred = true;
    }

    // Validate Colors
    var inputColorRed = +(document.getElementById("histogram-color-red-" + this.id).value);
    if (!isNaN(inputColorRed) && isNormalInteger(String(inputColorRed))){
        if (inputColorRed > 255) {
            errorMessage += "Graph Color Red must be an integer from 0 to 255.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Graph Color Red must be an integer from 0 to 255.<br>";
        errorOccurred = true;
    }

    var inputColorGreen = +(document.getElementById("histogram-color-green-" + this.id).value);
    if (!isNaN(inputColorGreen) && isNormalInteger(String(inputColorGreen))){
        if (inputColorGreen > 255) {
            errorMessage += "Graph Color Green must be an integer from 0 to 255.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Graph Color Green must be an integer from 0 to 255.<br>";
        errorOccurred = true;
    }

    var inputColorBlue = +(document.getElementById("histogram-color-blue-" + this.id).value);
    if (!isNaN(inputColorBlue) && isNormalInteger(String(inputColorBlue))){
        if (inputColorBlue > 255) {
            errorMessage += "Graph Color Blue must be an integer from 0 to 255.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Graph Color Blue must be an integer from 0 to 255.<br>";
        errorOccurred = true;
    }

    if (errorOccurred) {
        errorElement.innerHTML = errorMessage;
    } else {
        this.updateFrequency = inputUpdateFrequency;
        this.colorRed = inputColorRed;
        this.colorGreen = inputColorGreen;
        this.colorBlue = inputColorBlue;
        this.colorScale = colorScale;

        successElement.innerHTML = "Configuration Updated.";
        this.generateDualHistogram();
    }
};


DualHistogram.prototype.updateLastReceived = function() {
    var statusBubble = document.getElementById("receive-status-" + this.id);
    if (this.lastReceived == null) {
        statusBubble.className = "db_receive_status";
        document.getElementById("last-received-" + this.id).innerHTML = "No Data";
        return;
    }

    // If lastReceived exists, display the time the last data was received and update status bubble depending on age.
    var day = this.lastReceived.getUTCDate();
    var month = this.lastReceived.getUTCMonth() + 1;
    var year = this.lastReceived.getUTCFullYear();
    var hours = this.lastReceived.getUTCHours();
    var minutes = this.lastReceived.getUTCMinutes();
    var seconds = this.lastReceived.getUTCSeconds();
    var lastReceivedUTC = month + "/" + day + "/" + year + " " + hours + ":" + minutes + ":" + seconds;
    document.getElementById("last-received-" + this.id).innerHTML = lastReceivedUTC;

    var currentTime = new Date();
    var differenceMinutes = (currentTime - this.lastReceived) / (60000); // Difference starts in milliseconds

    if ((0 <= differenceMinutes) && (differenceMinutes < 5)) {
        statusBubble.className = "db_receive_status db_status_good";
    } else if ((5 <= differenceMinutes) && (differenceMinutes <= 15)) {
        statusBubble.className = "db_receive_status db_status_weak";
    } else {
        statusBubble.className = "db_receive_status db_status_dead";
    }

}


DualHistogram.prototype.getAutomaticBeginning = function () {
    var now = new Date();
    if (this.constraintRange == "tenminute") {
        return new Date(now.setMinutes(now.getMinutes() - 10));
    } if (this.constraintRange == "hour") {
        return new Date(now.setHours(now.getHours() - 1));
    } else if (this.constraintRange == "sixhour") {
        return new Date(now.setHours(now.getHours() - 6));
    } else if (this.constraintRange == "day") {
        return new Date(now.setDate(now.getDate() - 1));
    } else if (this.constraintRange == "week") {
        return new Date(now.setDate(now.getDate() - 7));
    } else if (this.constraintRange == "fortnight") {
        return new Date(now.setDate(now.getDate() - 14));
    } else if (this.constraintRange == "month") {
        return new Date(now.setMonth(now.getMonth() - 1));
    } else {
        // Default to six hours
        return new Date(now.setHours(now.getHours() - 6));
    }

}

DualHistogram.prototype.hideController = function () {
    element = document.getElementById("histogram-controller-" + this.id);
    element.style.display = "none";
    this.controllerHidden = true;
};

DualHistogram.prototype.revealController = function () {
    element = document.getElementById("histogram-controller-" + this.id);
    element.style.display = "";
    this.controllerHidden = false;
};

DualHistogram.prototype.openConfig = function () {
    var contentElement = document.getElementById("histogram-content-" + this.id);
    var configElement = document.getElementById("histogram-config-" + this.id);
    contentElement.style.display = "none";
    configElement.style.display = "block";

    // Clear and reset input values and messages
    var frequencyInput = document.getElementById("histogram-update-frequency-" + this.id);
    frequencyInput.value = this.updateFrequency;

    var colorRedInput = document.getElementById("histogram-color-red-" + this.id);
    colorRedInput.value = this.colorRed;
    var colorGreenInput = document.getElementById("histogram-color-green-" + this.id);
    colorGreenInput.value = this.colorGreen;
    var colorBlueInput = document.getElementById("histogram-color-blue-" + this.id);
    colorBlueInput.value = this.colorBlue;

    var errorElement = document.getElementById("histogram-config-error-" + this.id);
    var successElement = document.getElementById("histogram-config-success-" + this.id);
    errorElement.innerHTML = "";
    successElement.innerHTML = "";
};

DualHistogram.prototype.closeConfig = function () {
    var contentElement = document.getElementById("histogram-content-" + this.id);
    var configElement = document.getElementById("histogram-config-" + this.id);
    configElement.style.display = "";
    contentElement.style.display = "";
};

DualHistogram.prototype.showConstraintAuto = function () {
    var autoElement = document.getElementById("auto-times-" + this.id);
    var customElement = document.getElementById("custom-times-" + this.id);
    var constraintButton = document.getElementById("time-constraint-switch-" + this.id);
    autoElement.style.display = "block";
    customElement.style.display = "none";
    var that = this;
    constraintButton.onclick = function () { that.showConstraintCustom(); };
    constraintButton.innerHTML = "Switch to Custom Range";
    this.constraintStyle = "auto"
}

DualHistogram.prototype.showConstraintCustom = function () {
    var autoElement = document.getElementById("auto-times-" + this.id);
    var customElement = document.getElementById("custom-times-" + this.id);
    var constraintButton = document.getElementById("time-constraint-switch-" + this.id);
    autoElement.style.display = "none";
    customElement.style.display = "block";
    var that = this;
    constraintButton.onclick = function () { that.showConstraintAuto(); };
    constraintButton.innerHTML = "Switch to Sliding Window";
    this.constraintStyle = "custom";
}

DualHistogram.prototype.tightBorders = function() {
    this.div.className = "wd_tight";
}

DualHistogram.prototype.wideBorders = function() {
    this.div.className = "wd";
}



// Instrument Graph Section
function InstrumentGraph(manager, id, containerDiv, controllerUrl, genGraphURL, schematic) {
    this.manager = manager;
    this.id = id;
    this.active = true;            // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Instrument Graph";
    this.div.id = "instrument-graph-" + this.id;
    this.instrumentList = [];      // Filled by ajax request
    this.columnList = [];          // Filled by ajax request
    this.genGraphURL = genGraphURL;
    this.updateCounter = 0;
    this.nextAttributeId = 1;      // 0 is already taken by the template html.
    this.graphData = [];
    this.graphTitle = null;
    this.dygraph = "";
    this.lastReceived = null;      // The timestamp for the last data received
    this.statsHidden = true;

    var validSchematic = false;
    if (schematic) {
        validSchematic = true;
        this.controllerHidden = schematic["controllerHidden"];
        this.statFrequency = schematic["statFrequency"];
        this.instrumentId = schematic["instrumentId"];
        this.updateFrequency = schematic["updateFrequency"];
        this.graphSize = schematic["graphSize"];
        this.keys = schematic["attributes"];
        this.beginningTime = new Date(schematic["beginningUTC"] + " UTC");
        this.endTime = new Date(schematic["endUTC"] + " UTC");
        this.originTime = this.beginningTime;
        this.rollPeriod = schematic["rollPeriod"];
        // Need to perform checks now, because some previously saved dashboards will not have these new fields.
        if (schematic["convertToDB"]) {
            this.convertToDB = schematic["convertToDB"];
        } else {
            this.convertToDB = false;
        }
        if (schematic["constraintStyle"]) {
            this.constraintStyle = schematic["constraintStyle"];
        } else {
            this.constraintStyle = "custom";
        }
        if (schematic["constraintRange"]) {
            this.constraintRange = schematic["constraintRange"];
        } else {
            this.constraintRange = "sixhour"
        }
        if (schematic["lowerLimit"]) {
            this.lowerLimit = schematic["lowerLimit"];  // Lower y-value range bound
        } else {
            this.lowerLimit = null;                     // Null means automatic lower range
        }
        if (schematic["upperLimit"]) {
            this.upperLimit = schematic["upperLimit"]   // Upper y-value range bound
        } else {
            this.upperLimit = null;                     // Null means automatic upper range
        }

    } else {
        this.controllerHidden = false;
        this.statFrequency = 10;       // How often the stats will be generated. Every X requests for data, update stats
        this.instrumentId = null;      //
        this.updateFrequency = 1;      // How often in minutes this object will update.
        this.graphSize = "medium";     //
        this.keys = [];                // Given attribute keys to graph
        this.beginningTime = null;     // Start time for the next data request. Updates each request to avoid duplicates
        this.endTime = null;           // End time for the next data request
        this.originTime = null;        // Origin time is the beginning time at graph creation, for aggregate stats
        this.rollPeriod = 3;           // Roll period for the Dygraph
        this.convertToDB = false;      // Whether or not the data is converted to dB scale before graphing.
        this.constraintStyle = "custom";   // The data constraint controls available
        this.constraintRange = "sixhour";  // If constraintStyle is 'auto', the range for the data displayed
        this.lowerLimit = null;            // Lower y-value range bound.  Null means automatic lower range
        this.upperLimit = null;            // Upper y-value range bound.  Null means automatic upper range
    }

    // Statistic fields, only handled if stats_enabled is true
    this.statsEnabled = false;
    this.selLowerDeviation = 0;
    this.selUpperDeviation = 0;
    this.minimum = 0;
    this.maximum = 0;
    this.median = 0;
    this.average = 0;
    this.stdDeviation = 0;
    this.forceRedraw = false; // When set to true, redraws the whole Dygraph.  Used to update stat lines
    this.statCount = this.statFrequency - 1; // Counter for requests without stat generation.
                                             // Setting this way guarantees the first request generates stats

    this.selectPairList = []; // Holds the id, instrument selector element, and attribute selector element for each
                              // attribute row.  Allows for updating multiple attribute selectors.

    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=instrument_graph&widget_id=" + this.id;
    this.ajaxLoadUrl(this.div, parameterizedUrl, validSchematic);
};

InstrumentGraph.prototype.tick = function() {
    if (this.dygraph != "") {
        this.updateCounter += 1;
        if (this.updateCounter >= this.updateFrequency){
            this.updateCounter = 0;
            this.updateInstrumentGraph();
        }
    }

};

InstrumentGraph.prototype.saveDashboard = function() {

    var day = this.originTime.getUTCDate();
    var month = this.originTime.getUTCMonth() + 1;
    var year = this.originTime.getUTCFullYear();
    var hours = this.originTime.getUTCHours();
    var minutes = this.originTime.getUTCMinutes();
    var seconds = this.originTime.getUTCSeconds();
    var beginningUTC = month + "/" + day + "/" + year + " " + hours + ":" + minutes + ":" + seconds;

    var day = this.endTime.getUTCDate();
    var month = this.endTime.getUTCMonth() + 1;
    var year = this.endTime.getUTCFullYear();
    var hours = this.endTime.getUTCHours();
    var minutes = this.endTime.getUTCMinutes();
    var seconds = this.endTime.getUTCSeconds();
    var endUTC = month + "/" + day + "/" + year + " " + hours + ":" + minutes + ":" + seconds;
    data = {
        "controllerHidden": this.controllerHidden,
        "instrumentId": this.instrumentId,
        "attributes": this.keys,
        "updateFrequency": this.updateFrequency,
        "statFrequency": this.statFrequency,
        "beginningUTC": beginningUTC,
        "endUTC": endUTC,
        "graphSize": this.graphSize,
        "rollPeriod": this.rollPeriod,
        "convertToDB": this.convertToDB,
        "constraintStyle": this.constraintStyle,
        "constraintRange": this.constraintRange,
        "lowerLimit": this.lowerLimit,
        "upperLimit": this.upperLimit
    }
    return {"type": "InstrumentGraph", "data": data}
}

InstrumentGraph.prototype.ajaxLoadUrl = function(element, url, loadDashboard) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
            // To get JSON and HTML parts, need to do custom extraction.
            var responseDict = JSON.parse(xmlHttp.responseText);
            element.innerHTML = responseDict["html"];
            // Updates the instrument and column lists for the update function to populate properly.
            that.instrumentList = responseDict["json"]["instrument_list"];
            that.columnList = responseDict["json"]["column_list"];

            that.initializeElements(loadDashboard);
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

InstrumentGraph.prototype.initializeElements = function (loadDashboard) {
    var that = this;  // Substitution allows inline function assignments to reference 'this' rather than themselves

    if (loadDashboard) {
        var day = this.beginningTime.getUTCDate();  // No good way to easily format datetime string
        var month = this.beginningTime.getUTCMonth() + 1;
        var year = this.beginningTime.getUTCFullYear();
        var hours = this.beginningTime.getUTCHours();
        var minutes = this.beginningTime.getUTCMinutes();
        var seconds = this.beginningTime.getUTCSeconds();
        var beginningUTC = month + "/" + day + "/" + year + " " + hours + ":" + minutes + ":" + seconds;
        document.getElementById("datetime-input-start-" + that.id).value = beginningUTC;

        var day = this.endTime.getUTCDate();       // No good way to easily format datetime string
        var month = this.endTime.getUTCMonth() + 1;
        var year = this.endTime.getUTCFullYear();
        var hours = this.endTime.getUTCHours();
        var minutes = this.endTime.getUTCMinutes();
        var seconds = this.endTime.getUTCSeconds();
        var endUTC = month + "/" + day + "/" + year + " " + hours + ":" + minutes + ":" + seconds;
        document.getElementById("datetime-input-end-" + that.id).value = endUTC;
        document.getElementById("instrument-select-" + that.id).value = that.instrumentId;

        document.getElementById("instrument-size-button-" + that.graphSize + "-" + that.id).checked = true;

        document.getElementById("inst-graph-upper-limit-" + that.id).value = parseFloat(that.upperLimit);
        document.getElementById("inst-graph-lower-limit-" + that.id).value = parseFloat(that.lowerLimit);

        document.getElementById("convert-to-dB-" + that.id).checked = that.convertToDB;

        document.getElementById("time-range-" + that.constraintRange + "-" + that.id).checked = true;

        if (that.controllerHidden) {
            that.hideController();
        }
        if (that.constraintStyle == "auto") {
            that.showConstraintAuto();
        } else {
            that.showConstraintCustom();
        }
    } else {
        // Defaults the graph beginning time to 7 days ago
        updateStartTime(that.id, 7);
        that.showConstraintCustom();
    }

    this.statsHidden = true;

    // Button to copy Instrument widget.  Disabled until data is graphed (or data will not properly copy)
    var copyButton = document.getElementById("inst-graph-copy-button-" + that.id);
    copyButton.onclick = function () { that.manager.copyWidget(that.id); };
    copyButton.disabled = true;
    copyButton.title = "Cannot Copy Until Graph Displayed";

    //Button to remove this widget
    var removeButton = document.getElementById("inst-graph-remove-button-" + that.id);
    removeButton.onclick = function () { that.remove(); };

    // Button to generate graph from data parameter controls
    var addButton = document.getElementById("inst-graph-add-button-" + that.id);
    addButton.onclick = function () { that.generateInstrumentGraph(); };

    // Secondary graph button inside the controller
    var controllerAddButton = document.getElementById("controller-graph-add-" + that.id);
    controllerAddButton.onclick = function () { that.generateInstrumentGraph(); };

    // Selector for which instrument the attributes are for
    // When changed should update all options for attribute selectors
    var instrumentSelect = document.getElementById("instrument-select-" + that.id);
    instrumentSelect.onchange = function () { that.updateSelect(false); };
    that.instrumentId = instrumentSelect.value;

    // Button to add another attribute to graph
    var attributeButton = document.getElementById("inst-add-attribute-button-" + that.id);
    attributeButton.onclick = function () { that.addAttribute(); };

    // Each added attribute has a set that is tracked: a selector for the attribute, an input, and a button to remove it
    var removeButton = document.getElementById("inst-remove-attribute-button-" + that.id + "-0");
    removeButton.onclick = function () { that.removeAttribute(0) };
    var attributeSelect = document.getElementById("attribute-select-" + that.id + "-0");
    var attributeInput = document.getElementById("attribute-input-" + that.id + "-0");
    that.selectPairList = [{ "id": 0, "attributeSelect": attributeSelect, "attributeInput": attributeInput,
                             "removeButton": removeButton }];

    // Data parameter controls: Hide and Reveal
    var hideButton = document.getElementById("inst-hide-button-" + that.id);
    hideButton.onclick = function () { that.hideController(); };
    var revealButton = document.getElementById("inst-reveal-button-" + that.id);
    revealButton.onclick = function () { that.revealController(); };

    // Config control bindings: Hide, Reveal, Apply
    var configOpenButton = document.getElementById("inst-graph-config-open-button-" + that.id);
    configOpenButton.onclick = function () { that.openConfig(); };
    var configCloseButton = document.getElementById("inst-graph-config-close-button-" + that.id);
    configCloseButton.onclick = function () { that.closeConfig(); };
    var configApplyButton = document.getElementById("inst-graph-config-apply-button-" + that.id);
    configApplyButton.onclick = function () { that.applyConfig(); };

    that.updateSelect(loadDashboard);

    if (loadDashboard) {
        that.generateInstrumentGraph();
    }
}

InstrumentGraph.prototype.updateSelect = function(loadDashboard) {
    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    if (loadDashboard) {
        if (this.instrumentId) {
            instrumentSelect.value = this.instrumentId;
        }
    }

    var instrumentValidColumns = this.columnList[instrumentSelect.value];
    instrumentValidColumns.sort();

    for (var j = 0; j < this.selectPairList.length; j++){
        var attributeSelect = this.selectPairList[j]["attributeSelect"];
        removeOptions(attributeSelect);

        for (var i = 0; i < instrumentValidColumns.length; i++){
            newOption = document.createElement("option");
            newOption.value = instrumentValidColumns[i];
            newOption.text = instrumentValidColumns[i];
            attributeSelect.appendChild(newOption);
        }
    }

    if (loadDashboard) {
        if (this.keys) {
            while (this.keys.length > this.selectPairList.length) {
                this.addAttribute();
            }
            for (var i = 0; i < this.keys.length; i ++) {
                this.selectPairList[i]["attributeInput"].value = this.keys[i];
            }
        } else {
            this.selectPairList = [];
        }
    }
}

InstrumentGraph.prototype.remove = function() {
    var element = document.getElementById('instrument-graph-' + this.id);
    element.parentNode.removeChild(element);
    this.active = false;
};

InstrumentGraph.prototype.generateInstrumentGraph = function(){

    // Clear out old data.
    this.keys = [];            // Given attribute keys to graph
    this.beginningTime = null; // Start time for the next data request. Updates each request to avoid duplicates
    this.endTime = null;       // End time for the next data request
    this.originTime = null;    // Origin time is the beginning time at graph creation, for aggregate stats
    this.graphData = [];
    this.graphTitle = null;
    this.dygraph = "";
    this.nextAttributeId = 1;  // 0 is already taken by the template html.
    this.lastReceived = null;

    // Statistic fields, only handled if stats_enabled is true
    this.statsEnabled = false;
    this.selLowerDeviation = 0;
    this.selUpperDeviation = 0;
    this.minimum = 0;
    this.maximum = 0;
    this.median = 0;
    this.average = 0;
    this.stdDeviation = 0;
    this.forceRedraw = false;  // When set to true, redraws the whole Dygraph.  Used to update stat lines
    this.statCount = this.statFrequency - 1; // Counter for requests without stat generation.
                                               // Setting this way guarantees the first request generates stats


    var masterDiv = document.getElementById('instrument-graph-container-' + this.id)

    var constraintRange = document.querySelector('input[name="time-range-' + this.id + '"]:checked');

    if (constraintRange) {
        this.constraintRange = constraintRange.value;
    }

    // Size from radio set
    this.graphSize = "medium";
    var graphWidth = 500;
    var graphHeight = 400;
    var graphSizeElement = document.querySelector('input[name="inst-graph-size-' + this.id + '"]:checked');

    if (graphSizeElement) {
        this.graphSize = graphSizeElement.value;
    }

    // Set sizes according to selection
    if (this.graphSize == "small") {
        graphWidth = 350;
        graphHeight = 280;
    } else if (this.graphSize == "medium") {
        graphWidth = 500;
        graphHeight = 400;
    } else if (this.graphSize == "large") {
        graphWidth = 750;
        graphHeight = 600;
    }

    // Enable copy button and change title to reflect functionality
    var copyButton = document.getElementById("inst-graph-copy-button-" + this.id);
    copyButton.disabled = false;
    copyButton.title = "Copy This Widget";

    var keyElems = document.getElementsByName("attribute-input-" + this.id);
    this.keys = [];
    for (var i = 0; i < keyElems.length; i++) {
        this.keys.push(keyElems[i].value);
    }

    startStr = document.getElementById("datetime-input-start-" + this.id).value;
    if (this.constraintStyle == "auto") {
        this.originTime = this.getAutomaticBeginning();
        this.beginningTime = this.getAutomaticBeginning();
    } else {
        this.originTime = new Date(startStr + " UTC");
        this.beginningTime = new Date(startStr + " UTC");
    }

    endStr = document.getElementById("datetime-input-end-" + this.id).value;
    if (this.constraintStyle == "auto") {
        delete this.endTime;
        this.endTime = new Date();
    } else {
        this.endTime = new Date(endStr + " UTC");
    }

    this.convertToDB = document.getElementById("convert-to-dB-" + this.id).checked;

    // Get y-axis range limits
    this.upperLimit = parseFloat(document.getElementById("inst-graph-upper-limit-" + this.id).value);
    this.lowerLimit = parseFloat(document.getElementById("inst-graph-lower-limit-" + this.id).value);

    // Clear Master Div
    while (masterDiv.firstChild) {
        masterDiv.removeChild(masterDiv.lastChild)
    }

    // Partition out divs.
    this.graphDivId = "graphdiv-" + this.id;
    this.graphDiv = document.createElement('div');
    this.graphDiv.className = "dashboard_instrument_dygraph";
    this.graphDiv.innerHTML += '<div id = "' + this.graphDivId + '-parent">' +
                         '<div id="' + this.graphDivId +
                         '" style="width: ' + graphWidth + 'px; height: ' + graphHeight +
                         'px; display: inline-block;"></div></div>'

    this.dataDivId = "datadiv-" + this.id;
    this.dataDiv = document.createElement('div');
    this.dataDiv.className = "dashboard_graph_stats";

    var instrumentSelect = document.getElementById("instrument-select-" + this.id)
    this.instrumentId = instrumentSelect.value;

    // If there is only one attribute graphed, generate a button that allows the user to get stats for the attribute
    if (String(this.keys).split(",").length ==1){
        this.graphTitle = instrumentSelect.options[instrumentSelect.selectedIndex].text
                          + ":" + String(this.keys);

        // Clear anything that might be in there already
        while (this.dataDiv.hasChildNodes()){
            this.dataDiv.removeChild(this.dataDiv.firstChild);
        }

        var customButton=document.createElement('button');
        var that = this;
        customButton.innerHTML = "Get Dataset Statistics";
        customButton.title = "Get Detailed Statistics for This Attribute"
        // Passes the Graph into the function so that the button with reference the Graph that created it
        customButton.onclick = function () { that.enableStats(); } ;

        this.dataDiv.appendChild(customButton);

    }
    else {
        this.graphTitle = instrumentSelect.options[instrumentSelect.selectedIndex].text;
        // If there is more than one attribute graphed, display a list of the attributes being graphed
        htmlConstruct = "<b>Attributes: </b>";
        attributeList = String(this.keys).split(",");
        for (i = 0; i < attributeList.length; i ++ ) {
            htmlConstruct += "<br>" + attributeList[i];
        }
        this.dataDiv.innerHTML = htmlConstruct;
    }

    masterDiv.insertBefore(this.graphDiv, masterDiv.firstChild);
    //Appending dataDiv onto this div assures that it will be removed with the Graph if the Graph is removed
    // Add button to hide or display stats
    var statsHiddenButton = document.createElement('button');
    statsHiddenButton.id = "stats-hidden-button-" + this.id;
    var that = this;
    statsHiddenButton.onclick = function () { that.toggleStatsHidden(); };
    statsHiddenButton.innerHTML = "Stats";
    this.dataDiv.style.display = "none";

    var linebreak = document.createElement("br");

    // Container div to hold all stats controls
    var statsDiv = document.createElement("div");
    statsDiv.style.display = "inline-block";
    statsDiv.appendChild(statsHiddenButton);
    statsDiv.appendChild(linebreak);
    statsDiv.appendChild(this.dataDiv);

    // Append container div
    this.graphDiv.firstChild.appendChild(statsDiv);
    this.innerDiv = document.getElementById(this.graphDivId);
    this.innerDiv.innerHTML = "<p><br><i>Loading Graph...</i></p>"

    this.dygraph = "";
    this.updateInstrumentGraph();
}

InstrumentGraph.prototype.enableStats = function() {
    // Even though this is a Graph's 'enable stats' function, it was necessary to pass the graph to allow it
    // to be dynamically called by a button generated by the Graph.

    this.statsEnabled = true; // Graph will now display and track stats
    this.forceRedraw = true;  // Graph will be redrawn on next update to show std deviation lines

    this.dataDiv.innerHTML = '<b>Selection 95th Percentile:</b><br>' +
                               'Loading...' +
                               '<br><b>Entire Database:</b><br>' +
                               '<div class="graph_stats_half">Current: Loading...' +
                               '<br>Average: Loading...' +
                               '<br>Std. Dev.: Loading...' + '</div>' +
                               '<div class="graph_stats_half">Minimum: Loading...' +
                               '<br>Maximum: Loading...' +
                               '<br>Median: Loading...' + '</div>';

    this.updateInstrumentGraph()
};

InstrumentGraph.prototype.addAttribute = function () {
    var masterDiv = document.getElementById("inst-graph-controller-" + this.id);

    var attributeDiv = document.createElement('div');
    attributeDiv.id = "attr-div-" + this.id + "-" + this.nextAttributeId

    var removeButton = document.createElement('button');
    var attributeSpan = document.createElement('span');
    var attributeInput = document.createElement('input');
    var attributeSelect = document.createElement('datalist');

    // Pieces from updateSelect to update only the new attribute
    instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var instrumentValidColumns = this.columnList[instrumentSelect.value];
    instrumentValidColumns.sort();
    removeOptions(attributeSelect);


    removeButton.id = "inst-remove-attribute-button-" + this.id + "-" + this.nextAttributeId;
    var that = this;
    var functionParameter = that.nextAttributeId;
    removeButton.onclick = function () { that.removeAttribute(functionParameter); };
    removeButton.innerHTML = "X";
    removeButton.title = "Remove This Attribute"

    attributeSelect.className = "attribute_select";
    attributeSelect.id = "attribute-select-" + this.id + "-" + this.nextAttributeId;
    attributeSelect.name = "attribute-select-" + this.id;

    attributeInput.id = "attribute-input-" + this.id + "-" + this.nextAttributeId;
    attributeInput.name = "attribute-input-" + this.id;
    attributeInput.setAttribute("list", attributeSelect.id);  // Have to set list attribute this way for some reason.

    // Options must be added after the list is tied to the input
    for (var i = 0; i < instrumentValidColumns.length; i++){
        newOption = document.createElement("option");
        newOption.value = instrumentValidColumns[i];
        //newOption.text = instrumentValidColumns[i];
        attributeSelect.appendChild(newOption);
    }

    var placeholderOption = document.createElement("option");
    placeholderOption.value = "Select an Instrument";
    attributeSelect.appendChild(placeholderOption);

    attributeDiv.appendChild(removeButton);
    attributeDiv.appendChild(attributeSpan);
    attributeSpan.appendChild(attributeInput);
    attributeSpan.appendChild(attributeSelect);

    masterDiv.appendChild(attributeDiv);

    this.selectPairList.push({ "id": this.nextAttributeId, "attributeSelect": attributeSelect,
                               "attributeInput": attributeInput, "removeButton": removeButton });

    this.nextAttributeId += 1;
}

InstrumentGraph.prototype.removeAttribute = function (id) {
    if (this.selectPairList.length > 1) {  // Never remove all attributes. Graphing without attributes causes error
        for (var i = 0; i < this.selectPairList.length; i++) {
            if (this.selectPairList[i]["id"] == id) {
                attributeDiv = document.getElementById("attr-div-" + this.id + "-" + id);
                masterDiv = document.getElementById("inst-graph-controller-" + this.id);
                masterDiv.removeChild(attributeDiv);
                this.selectPairList.splice(i, 1);
                break;
            }
        }
    }
}

InstrumentGraph.prototype.updateWithValues = function(values) {
    // Read in the various statistics for the Graph
    var upper = this.selUpperDeviation.toPrecision(4);
    var lower = this.selLowerDeviation.toPrecision(4);
    var minimum = this.minimum.toPrecision(4);
    var maximum = this.maximum.toPrecision(4);
    var median = this.median.toPrecision(4);
    var average = this.average.toPrecision(4);
    var stdDeviation = this.stdDeviation.toPrecision(4);


    if (this.statsEnabled === true) {
        //Add extra information if stats are enabled

        //Get the current value (either the most recent incoming value, or if there are no incoming values,
        //the most recent value currently stored.

        var current = 0
        if (values.length > 0) {
            current = values[values.length - 1][1].toPrecision(4);
        }
        else if (this.graphData.length > 0) {
            current = this.graphData[this.graphData.length - 1][1].toPrecision(4);
        }

        this.dataDiv.innerHTML = '<b>Selection 95th Percentile:</b><br>' +
                                   lower + ', ' + upper +
                                   '<br><b>Entire Database:</b><br>' +
                                   '<div class="graph_stats_half">Current: <br> ' + current +
                                   '<br>Average: <br> ' + average +
                                   '<br>Std. Dev.: <br> ' + stdDeviation + "</div>" +
                                   '<div class="graph_stats_half">Minimum: <br> ' + minimum +
                                   '<br>Maximum: <br> ' + maximum +
                                   '<br>Median: <br> ' + median + "<div>";


        //Callback handles drawing the deviation lines on the Dygraph.
        deviationCallback = function(canvas, area, g) {
                  var LowCoords = g.toDomCoords(0, lower);
                  var HighCoords = g.toDomCoords(0, upper);

                  var high = HighCoords[1];
                  var low = LowCoords[1];

                  canvas.fillStyle = 'red';
                  canvas.fillRect(area.x, low, area.w, 2);
                  canvas.fillStyle = 'blue';
                  canvas.fillRect(area.x, high, area.w, 2);
                  }
    }
    else {
        deviationCallback = null;
    }
    if (this.graphData.length <= 0 || this.forceRedraw === true) {
        if (this.convertToDB) {
            this.graphData = this.graphData.concat(values.filter(dataToDB));
        } else {
            this.graphData = this.graphData.concat(values);
        }
        this.forceRedraw = false;

        if (this.graphData.length > 0){
            delete this.lastReceived
            this.lastReceived = new Date(this.graphData[this.graphData.length - 1][0]) // Timestamp from most recent data

            yRange = [null, null];   // Deafault is automatic ranging

            // If the upper and lower limits are somewhat reasonable, use them instead for the y-axis range
            if (!isNaN(this.lowerLimit)
                && this.lowerLimit != ""
                && !isNaN(this.upperLimit)
                && this.upperLimit != "")
            {
                yRange = [this.lowerLimit, this.upperLimit];
            }

            this.dygraph = new Dygraph(
            this.innerDiv,
            this.graphData,
            {
                title: this.graphTitle,
                rollPeriod: this.rollPeriod,
                showRoller: true,
                showRangeSelector: true,
                rangeSelectorHeight: 20,
                rangeSelectorPlotStrokeColor: 'darkred',
                rangeSelectorPlotFillColor: 'lightgreen',
                valueRange: yRange,

                labelsUTC: true,
                labels: ["Time"].concat(this.keys),
                axes: {
                    ticker: function (a, b, pixels, opts, dygraph, vals) {
                                return Dygraph.getDateAxis(a, b, Dygraph.ANNUAL, opts, dygraph);
                    }
                },
                underlayCallback: deviationCallback
            });

        }
        else {
            this.innerDiv.innerHTML = "<p>No Data Available<br>" +
                                       "Verify that the start and end times are valid and formatted correctly.</p>";
        }
    }
    else
    {
        if (values.length > 0) {
            delete this.lastReceived
            this.lastReceived = new Date(values[values.length - 1][0]) // Timestamp from most recent data

            if (this.convertToDB) {
                this.graphData = this.graphData.concat(values.filter(dataToDB));
            } else {
                this.graphData = this.graphData.concat(values);
            }
            if (this.constraintStyle == "auto") {
                this.trimOldGraphData();
            }
            this.dygraph.updateOptions({ 'file': this.graphData });
        }
    }
    //Set the beginning time for this graph to now.  This means updating the graph will only add new values.
    //Need to use the last entry from the database, since local clock may be off
    if (this.graphData.length > 0) {
        delete this.beginningTime;
        this.beginningTime = new Date(this.graphData[this.graphData.length - 1][0]);
        //Tiny increment so it doesnt pull the same data repeatedly
        this.beginningTime.setUTCSeconds(this.beginningTime.getUTCSeconds() + 1);
    }
}

InstrumentGraph.prototype.updateLastReceived = function() {
    var statusBubble = document.getElementById("receive-status-" + this.id);
    if (this.lastReceived == null) {
        statusBubble.className = "db_receive_status";
        document.getElementById("last-received-" + this.id).innerHTML = "No Data";
        return;
    }

    // If lastReceived exists, display the time the last data was received and update status bubble depending on age.
    var day = this.lastReceived.getUTCDate();
    var month = this.lastReceived.getUTCMonth() + 1;
    var year = this.lastReceived.getUTCFullYear();
    var hours = this.lastReceived.getUTCHours();
    var minutes = this.lastReceived.getUTCMinutes();
    var seconds = this.lastReceived.getUTCSeconds();
    var lastReceivedUTC = month + "/" + day + "/" + year + " " + hours + ":" + minutes + ":" + seconds;
    document.getElementById("last-received-" + this.id).innerHTML = lastReceivedUTC;

    var currentTime = new Date();
    var differenceMinutes = (currentTime - this.lastReceived) / (60000); // Difference starts in milliseconds

    if ((0 <= differenceMinutes) && (differenceMinutes < 5)) {
        statusBubble.className = "db_receive_status db_status_good";
    } else if ((5 <= differenceMinutes) && (differenceMinutes <= 15)) {
        statusBubble.className = "db_receive_status db_status_weak";
    } else {
        statusBubble.className = "db_receive_status db_status_dead";
    }

}

InstrumentGraph.prototype.updateInstrumentGraph = function() {
// keys, beginning_time, end_time, origin_time
    //Gets the next set of data values
    graphData = "";
    var thisGraph = this;
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        //After the asynchronous request successfully returns
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
        {
            //Pull out the response text from the request
            var recMessage = JSON.parse(xmlhttp.responseText);

            if (recMessage == "[]") {
                // There was an error.  This is probably a very foolish way to indicate errors from server->client
                var masterDiv = document.getElementById('instrument-graph-container-' + thisGraph.id)
                while (masterDiv.hasChildNodes()) {
                    masterDiv.removeChild(masterDiv.firstChild);
                }
                var errorDiv = document.createElement("div");
                errorDiv.style.color = "red";
                errorDiv.innerHTML = "Could not retrieve Data.  Verify all attributes are valid.";
                masterDiv.appendChild(errorDiv);
            } else {
                // Process the data
                for (i = 0; i < recMessage['data'].length; i ++)
                {
                    // Have add a Z to the given UTC time to convert in JavaScript
                    recMessage['data'][i][0] = new Date(recMessage['data'][i][0] + "Z");
                }

                thisGraph.selUpperDeviation = recMessage['upper_deviation'];
                thisGraph.selLowerDeviation = recMessage['lower_deviation'];
                if (recMessage['min']){
                    thisGraph.minimum = recMessage['min'];}
                if (recMessage['max']){
                    thisGraph.maximum = recMessage['max'];}
                if (recMessage['median']){
                    thisGraph.median = recMessage['median'];}
                if (recMessage['average']){
                    thisGraph.average = recMessage['average'];}
                if (recMessage['std_deviation']){
                    thisGraph.stdDeviation = recMessage['std_deviation'];}

                thisGraph.updateWithValues(recMessage['data']);

                thisGraph.updateLastReceived();
            }

        }
    };
    //Send JSON POST XMLHTTPRequest to generator controller.
    //Include keys for the generated graph, and convert start and end datetimes to a valid argument format
    //Assume input is in UTC
    var originUTC = this.originTime.toUTCString();
    var startUTC = this.beginningTime.toUTCString();
    if (this.constraintStyle == "auto") {
        delete this.endTime;
        this.endTime = new Date();
    }
    var endUTC = this.endTime.toUTCString();

    var doStats = 0;
    //If stats are enabled, set 'doStats' every 'this.statFrequency' times
    if(this.statsEnabled) {
            this.statCount += 1;
            if (this.statCount >= this.statFrequency) {
                this.statCount = 0;
                doStats = 1;
            }
        }

    var url = this.genGraphURL +
              "?keys=" + this.keys +
              "&instrument_id=" + this.instrumentId +
              "&start=" + startUTC +
              "&end=" + endUTC +
              "&origin=" + originUTC +
              "&do_stats=" + doStats;
    xmlhttp.open("POST", url, true);
    //Send out the  request
    xmlhttp.send();
};

InstrumentGraph.prototype.trimOldGraphData = function () {
    // This function assumes the data is ordered from oldest to newest data
    // Removes all entries older than the automatic range's beginning.
    var beginning = this.getAutomaticBeginning();
    var countToRemove = 0;
    for (var i = 0; i < this.graphData.length; i ++) {
        if (beginning > this.graphData[i][0]) {
            countToRemove += 1;
        } else {
            this.graphData.splice(0, countToRemove);
            break;
        }
    }
}

InstrumentGraph.prototype.getAutomaticBeginning = function () {
    var now = new Date();
    if (this.constraintRange == "tenminute") {
        return new Date(now.setMinutes(now.getMinutes() - 10));
    } if (this.constraintRange == "hour") {
        return new Date(now.setHours(now.getHours() - 1));
    } else if (this.constraintRange == "sixhour") {
        return new Date(now.setHours(now.getHours() - 6));
    } else if (this.constraintRange == "day") {
        return new Date(now.setDate(now.getDate() - 1));
    } else if (this.constraintRange == "week") {
        return new Date(now.setDate(now.getDate() - 7));
    } else if (this.constraintRange == "fortnight") {
        return new Date(now.setDate(now.getDate() - 14));
    } else if (this.constraintRange == "month") {
        return new Date(now.setMonth(now.getMonth() - 1));
    } else {
        // Default to six hours
        return new Date(now.setHours(now.getHours() - 6));
    }

}

InstrumentGraph.prototype.applyConfig = function () {
    var errorElement = document.getElementById("inst-graph-config-error-" + this.id);
    var successElement = document.getElementById("inst-graph-config-success-" + this.id);
    errorElement.innerHTML = "";
    successElement.innerHTML = "";

    var errorOccurred = false;
    var errorMessage = ""

    // Validate Update Frequency
    // Cast value to an integer if possible.  If it fails, get NaN
    var inputUpdateFrequency = +(document.getElementById("inst-graph-update-frequency-" + this.id).value);
    if (!isNaN(inputUpdateFrequency) && isNormalInteger(String(inputUpdateFrequency))){
        if (inputUpdateFrequency <= 0){
            errorMessage += "Update Frequency must be positive integer.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Update Frequency must be positive integer.<br>";
        errorOccurred = true;
    }

    // Validate Stat Frequency
    var inputStatFrequency = +(document.getElementById("inst-graph-stat-frequency-" + this.id).value);
    if (!isNaN(inputStatFrequency) && isNormalInteger(String(inputStatFrequency))){
        if (inputStatFrequency <= 0){
            errorMessage += "Stat Frequency must be positive integer.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Stat Frequency must be positive integer.<br>";
        errorOccurred = true;
    }

    // Validate Roll Period
    var inputRollPeriod = +(document.getElementById("inst-graph-roll-period-" + this.id).value);
    if (!isNaN(inputRollPeriod) && isNormalInteger(String(inputRollPeriod))){
        if (inputRollPeriod <= 0){
            errorMessage += "Roll Period must be positive integer.<br>";
            errorOccurred = true;
        }
    } else {
        errorMessage += "Roll Period must be positive integer.<br>";
        errorOccurred = true;
    }

    if (errorOccurred) {
        errorElement.innerHTML = errorMessage;
    } else {
        this.updateFrequency = inputUpdateFrequency;
        this.statFrequency = inputStatFrequency;
        this.rollPeriod = inputRollPeriod;

        successElement.innerHTML = "Configuration Updated.  You may need to regenerate the graph.";
    }
};

// Hide/Show Functions
InstrumentGraph.prototype.hideController = function () {
    var element = document.getElementById("inst-graph-controller-" + this.id);
    element.style.display = "none";
    this.controllerHidden = true;
};

InstrumentGraph.prototype.revealController = function () {
    var element = document.getElementById("inst-graph-controller-" + this.id);
    element.style.display = "";
    this.controllerHidden = false;
};

InstrumentGraph.prototype.openConfig = function () {
    var contentElement = document.getElementById("inst-graph-content-" + this.id);
    var configElement = document.getElementById("inst-graph-config-" + this.id);
    contentElement.style.display = "none";
    configElement.style.display = "block";

    // Clear and reset input values and messages
    var frequencyInput = document.getElementById("inst-graph-update-frequency-" + this.id);
    frequencyInput.value = this.updateFrequency;

    var rollPeriodInput = document.getElementById("inst-graph-roll-period-" + this.id);
    rollPeriodInput.value = this.rollPeriod;

    var statFrequencyInput = document.getElementById("inst-graph-stat-frequency-" + this.id);
    statFrequencyInput.value = this.statFrequency;

    var errorElement = document.getElementById("inst-graph-config-error-" + this.id);
    var successElement = document.getElementById("inst-graph-config-success-" + this.id);
    errorElement.innerHTML = "";
    successElement.innerHTML = "";
};

InstrumentGraph.prototype.closeConfig = function () {
    var contentElement = document.getElementById("inst-graph-content-" + this.id);
    var configElement = document.getElementById("inst-graph-config-" + this.id);
    configElement.style.display = "";
    contentElement.style.display = "";
};

InstrumentGraph.prototype.toggleStatsHidden = function () {
    var statsHiddenButton = document.getElementById("stats-hidden-button-" + this.id);
    if (this.dataDiv.style.display == "none") {
        this.dataDiv.style.display = "";
        statsHiddenButton.innerHTML = "Hide"
    } else {
        this.dataDiv.style.display = "none";
        statsHiddenButton.innerHTML = "Stats";
    }
}

InstrumentGraph.prototype.showConstraintAuto = function () {
    var autoElement = document.getElementById("auto-times-" + this.id);
    var customElement = document.getElementById("custom-times-" + this.id);
    var constraintButton = document.getElementById("time-constraint-switch-" + this.id);
    autoElement.style.display = "block";
    customElement.style.display = "none";
    var that = this;
    constraintButton.onclick = function () { that.showConstraintCustom(); };
    constraintButton.innerHTML = "Switch to Custom Range";
    this.constraintStyle = "auto"
}

InstrumentGraph.prototype.showConstraintCustom = function () {
    var autoElement = document.getElementById("auto-times-" + this.id);
    var customElement = document.getElementById("custom-times-" + this.id);
    var constraintButton = document.getElementById("time-constraint-switch-" + this.id);
    autoElement.style.display = "none";
    customElement.style.display = "block";
    var that = this;
    constraintButton.onclick = function () { that.showConstraintAuto(); };
    constraintButton.innerHTML = "Switch to Sliding Window";
    this.constraintStyle = "custom";
}

InstrumentGraph.prototype.tightBorders = function() {
    this.div.className = "wd_tight";
}

InstrumentGraph.prototype.wideBorders = function() {
    this.div.className = "wd";
}


// Helper functions
function ajaxLoadUrl(element, url) {
    var xmlHttp = new XMLHttpRequest();

    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
           element.innerHTML = xmlHttp.responseText;
        }
    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

function removeOptions(selectBox) {
    for(var i = selectBox.options.length - 1 ; i >= 0 ; i--)
    {
        selectBox.remove(i);
    }
};

function isNotSentinel(value){
 if (value == -999){
     return false;
 } else {
     return true;
 }
};

function dataToDB(inputData) {
    for (var i = 1; i < inputData.length; i++)
        inputData[i] = 10 * (Math.log(inputData[i]) / Math.LN10);
    return inputData;
}

function toDB(inputData) {
    return 10 * (Math.log(inputData) / Math.LN10);
}

function updateStartTime(id, days) {
    temp = new Date()
    temp.setDate(temp.getDate() - days)
    updatedTime = (temp.getUTCMonth() + 1) + '/' + temp.getUTCDate() + '/' + temp.getUTCFullYear() + " " +
                   temp.getUTCHours() + ":" + temp.getUTCMinutes();
    document.getElementById("datetime-input-start-" + id).value = updatedTime;
};

// http://stackoverflow.com/questions/10834796/validate-that-a-string-is-a-positive-integer
function isNormalInteger(str) {
    var n = ~~Number(str);
    return String(n) === str && n >= 0;
};
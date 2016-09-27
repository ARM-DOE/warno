// Contains, creates and removes different widgets.
function WidgetManager(containerDiv, controllerUrl) {
    this.containerDiv = containerDiv;
    this.controllerUrl = controllerUrl;
    this.newWidgetId = 0;
    this.widgets = [];

    this.timer = setInterval(this.tick.bind(this), 60000)
};

WidgetManager.prototype.tick = function(){
    this.removeInactive();
    for (i = 0; i < this.widgets.length; i++){
        this.widgets[i].tick()
    }
};

WidgetManager.prototype.removeInactive = function() {
    for (i = 0; i < this.widgets.length; i++){
        if(!this.widgets[i].active){
            this.widgets.splice(i, 1);
            i--;  // This ensures that the index doesn't get messed up by the removal of an element.
        }
    }
}

WidgetManager.prototype.addLogViewer = function(logViewerURL) {
    newLogViewer = new LogViewer(this.newWidgetId, this.containerDiv, this.controllerUrl, logViewerURL);
    this.widgets.push(newLogViewer);
    this.newWidgetId += 1;
};

WidgetManager.prototype.addStatusPlot = function(statusPlotURL) {
    newStatusPlot = new StatusPlot(this.newWidgetId, this.containerDiv, this.controllerUrl, statusPlotURL);
    this.widgets.push(newStatusPlot);
    this.newWidgetId +=1;
};

WidgetManager.prototype.addHistogram = function() {
    newHistogram = new Histogram(this.newWidgetId, this.containerDiv, this.controllerUrl);
    this.widgets.push(newHistogram);
    this.newWidgetId +=1;
};

WidgetManager.prototype.addInstrumentGraph = function(genGraphURL) {
    newInstrumentGraph = new InstrumentGraph(this.newWidgetId, this.containerDiv, this.controllerUrl, genGraphURL);
    this.widgets.push(newInstrumentGraph);
    this.newWidgetId += 1;
};





// Log Display Section
function LogViewer(id, containerDiv, controllerUrl, logViewerURL) {
    this.id = id;
    this.active = true; // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Log Viewer";
    this.div.id = "log-viewer-" + this.id;
    this.logViewerURL = logViewerURL; // URL for updating the status plot.
    this.updateFrequency = 1; // How often in minutes this object will update.
    this.updateCounter = 0;
    this.activeCounter = false;


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

LogViewer.prototype.removeLogViewer = function() {
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
            var removeButton = document.getElementById("remove-log-viewer-button-" + that.id);
            removeButton.onclick = function () { that.removeLogViewer(); };
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

LogViewer.prototype.generateLogViewer = function() {
    this.activeCounter = true;

    var fillElement = document.getElementById("log-viewer-container-" + this.id);
    var instrumentId = document.getElementById("log-viewer-instrument-selector-" + this.id).value;
    var maxLogs = document.getElementById("log-viewer-max-logs-" + this.id).value;
    var url = this.logViewerURL + '?instrument_id=' + instrumentId + '&max_logs=' + maxLogs;

    ajaxLoadUrl(fillElement, url)
};





// Status Plot Section
function StatusPlot(id, containerDiv, controllerUrl, statusPlotURL) {
    this.id = id;
    this.active = true; // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Status Plot";
    this.div.id = "status-plot-" + this.id;
    this.statusPlotURL = statusPlotURL; // URL for updating the status plot.
    this.updateFrequency = 1; // How often in minutes this object will update.
    this.updateCounter = 0;
    this.activeCounter = false;

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

StatusPlot.prototype.removeStatusPlot = function() {
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
            var removeButton = document.getElementById("remove-status-plot-button-" + that.id);
            removeButton.onclick = function () { that.removeStatusPlot(); };
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

StatusPlot.prototype.generateStatusPlot = function() {
    this.activeCounter = true;

    var fillElement = document.getElementById("status-plot-container-" + this.id);
    var siteId = document.getElementById("status-plot-site-selector-" + this.id).value;
    var url = this.statusPlotURL + '?site_id=' + siteId;

    ajaxLoadUrl(fillElement, url)
};




// Histogram Section
function Histogram(id, containerDiv, controllerUrl) {
    this.id = id;
    this.active = true;       // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Histogram";
    this.div.id = "histogram-" + this.id;
    this.instrumentList = []; // Filled by ajax request
    this.columnList = [];     // Filled by ajax request
    this.updateFrequency = 5; // How often in minutes this object will update.
    this.updateCounter = 0;
    this.activeCounter = false;
    this.binNumber = 0;
    this.colorRed = 0;
    this.colorGreen = 50;
    this.colorBlue = 226;

    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=histogram&widget_id=" + this.id;
    this.ajaxLoadUrl(this.div, parameterizedUrl);
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

Histogram.prototype.ajaxLoadUrl = function(element, url) {
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

            that.initializeElements();
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

Histogram.prototype.initializeElements = function () {
    var that = this;  // Substitution allows inline function assignments to reference 'this' rather than themselves

    // Defaults the graph beginning time to 7 days ago
    updateStartTime(that.id, 7);

    // Selector for which instrument the attributes are for
    // When changed should update all options for attribute selector
    var selector = document.getElementById("instrument-select-" + that.id);
    selector.onchange = function () { that.updateSelect(); };

    // Button to remove Histogram widget
    var removeButton = document.getElementById("histogram-remove-button-" + that.id);
    removeButton.onclick = function () { that.removeHistogram(); };

    // Button to generate Histogram from data parameter controls
    var addButton = document.getElementById("histogram-add-button-" + that.id);
    addButton.onclick = function () { that.generateHistogram(); };

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
    that.updateSelect();
}

Histogram.prototype.updateSelect = function() {
    instrumentSelect = document.getElementById("instrument-select-" + this.id);
    attributeSelect = document.getElementById("attribute-select-" + this.id);

    removeOptions(attributeSelect);
    instrumentId = instrumentSelect.value;
    var instrumentValidColumns = this.columnList[instrumentId];
    instrumentValidColumns.sort()

    for (var i =0; i< instrumentValidColumns.length; i++){
        newOption = document.createElement("option");
        newOption.value = instrumentValidColumns[i];
        newOption.text = instrumentValidColumns[i];
        attributeSelect.add(newOption);
    }
}

Histogram.prototype.removeHistogram = function () {
    element = document.getElementById('histogram-' + this.id);
    element.parentNode.removeChild(element);
    this.active = false;
};

Histogram.prototype.generateHistogram = function() {
    this.activeCounter = true;  // Activates the periodic update checks

    var xmlhttp = new XMLHttpRequest();

    var div = document.getElementById('histogram-container-' + this.id)

    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var attributeSelect = document.getElementById("attribute-select-" + this.id);
    var instrumentId = instrumentSelect.value;
    var instrumentName = instrumentSelect.options[instrumentSelect.selectedIndex].text;
    var attribute = attributeSelect.value;
    var startUTC = document.getElementById("datetime-input-start-" + this.id).value;
    var endUTC = document.getElementById("datetime-input-end-" + this.id).value;
    var upperLimit = parseFloat(document.getElementById("histogram-upper-limit-" + this.id).value);
    var lowerLimit = parseFloat(document.getElementById("histogram-lower-limit-" + this.id).value);

    // Size from radio set
    var graphSize = "medium";
    var graphWidth = 500;
    var graphHeight = 400;
    var graphSizeElement = document.querySelector('input[name="histogram-size-' + this.id + '"]:checked');
    if (graphSizeElement) {
        graphSize = graphSizeElement.value;
    }

    // Set sizes according to selection
    if (graphSize == "small") {
        graphWidth = 350;
        graphHeight = 280;
    } else if (graphSize == "medium") {
        graphWidth = 500;
        graphHeight = 400;
    } else if (graphSize == "large") {
        graphWidth = 750;
        graphHeight = 600;
    }

    var key_elems = document.getElementById('attribute-select-' + this.id);
    var keys = [];
    for (var i = 0; i < key_elems.length; i++) {
        keys.push(key_elems[i].value);
    }

    startStr = document.getElementById("datetime-input-start-" + this.id).value;
    start = new Date(startStr + " UTC");

    endStr = document.getElementById("datetime-input-end-" + this.id).value;
    end = new Date(endStr + " UTC");

    var that = this; // Allows 'this' object to be accessed correctly within the xmlhttp function.
                     // Inside the function 'this' references the function rather than the Histogram object we want.

    // Setup AJAX message and send.
    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var response = JSON.parse(xmlhttp.responseText);
            var field1 = response.data.map(function(i){ return i[1] });

            field1 = field1.filter(isNotSentinel)

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
            if (!isNaN(lowerLimit)
                && lowerLimit != ""
                && !isNaN(upperLimit)
                && upperLimit != "")
            {
                histogramRange = [lowerLimit, upperLimit];
                useAutorange = false;
                lowerBin = lowerLimit;
                upperBin = upperLimit;


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

                    //nbinsx : nbins,
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
            title: instrumentName + ":" + attribute,
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
    }};


    var url = "/generate_instrument_graph" +
              "?keys=" + attribute +
              "&instrument_id=" + instrumentId +
              "&start=" + startUTC +
              "&end=" + endUTC;
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

Histogram.prototype.hideController = function () {
    element = document.getElementById("histogram-controller-" + this.id);
    element.style.display = "none";
};

Histogram.prototype.revealController = function () {
    element = document.getElementById("histogram-controller-" + this.id);
    element.style.display = "";
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




// Instrument Graph Section
function InstrumentGraph(id, containerDiv, controllerUrl, genGraphURL) {
    this.id = id;
    this.active = true;            // When no longer active, should be removed from the parent manager.
    this.div = document.createElement('div');
    this.div.className = 'wd';
    this.div.innerHTML = "Instrument Graph";
    this.div.id = "instrument-graph-" + this.id;
    this.instrumentList = [];      // Filled by ajax request
    this.columnList = [];          // Filled by ajax request
    this.graphSize = "medium";
    this.graphWidth = 500;
    this.graphHeight = 400;
    this.genGraphURL = genGraphURL;
    this.updateFrequency = 1;      // How often in minutes this object will update.
    this.updateCounter = 0;
    this.nextAttributeId = 1;      // 0 is already taken by the template html.
    this.instrumentSelect = null; //

    this.keys = [];                // Given attribute keys to graph
    this.beginningTime = null;     // Start time for the next data request. Updates each request to avoid duplicates
    this.endTime = null;           // End time for the next data request
    this.originTime = null;        // Origin time is the beginning time at graph creation, for aggregate stats
    this.graphData = [];
    this.graphTitle = null;
    this.dygraph = ""
    this.rollPeriod = 3;           // Roll period for the Dygraph

    // Statistic fields, only handled if stats_enabled is true
    this.statsEnabled = false;
    this.selLowerDeviation = 0;
    this.selUpperDeviation = 0;
    this.minimum = 0;
    this.maximum = 0;
    this.median = 0;
    this.average = 0;
    this.stdDeviation = 0;
    this.statFrequency = 10;  // How often the stats will be generated. Every X requests for data, update stats
    this.forceRedraw = false; // When set to true, redraws the whole Dygraph.  Used to update stat lines
    this.statCount = this.statFrequency - 1; // Counter for requests without stat generation.
                                             // Setting this way guarantees the first request generates stats

    this.selectPairList = []; // Holds the id, instrument selector element, and attribute selector element for each
                              // attribute row.  Allows for updating multiple attribute selectors.

    containerDiv.appendChild(this.div);
    var parameterizedUrl = controllerUrl + "?widget_name=instrument_graph&widget_id=" + this.id;
    this.ajaxLoadUrl(this.div, parameterizedUrl);
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

InstrumentGraph.prototype.ajaxLoadUrl = function(element, url) {
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

            that.initializeElements();

            that.updateSelect();
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();

    //
};

InstrumentGraph.prototype.initializeElements = function () {
    var that = this;  // Substitution allows inline function assignments to reference 'this' rather than themselves

    // Defaults the graph beginning time to 7 days ago
    updateStartTime(that.id, 7);

    //Button to remove this widget
    var removeButton = document.getElementById("inst-graph-remove-button-" + that.id);
    removeButton.onclick = function () { that.removeInstrumentGraph(); };

    // Button to generate graph from data parameter controls
    var addButton = document.getElementById("inst-graph-add-button-" + that.id);
    addButton.onclick = function () { that.generateInstrumentGraph(); };

    // Selector for which instrument the attributes are for
    // When changed should update all options for attribute selectors
    that.instrumentSelect = document.getElementById("instrument-select-" + that.id);
    that.instrumentSelect.onchange = function () { that.updateSelect(); };

    // Button to add another attribute to graph
    var attributeButton = document.getElementById("inst-add-attribute-button-" + that.id);
    attributeButton.onclick = function () { that.addAttribute(); };

    // Each added attribute has a pair that is tracked: a selector for the attribute and a button to remove it
    var removeButton = document.getElementById("inst-remove-attribute-button-" + that.id + "-0");
    removeButton.onclick = function () { that.removeAttribute(0) };
    var attributeSelect = document.getElementById("attribute-select-" + that.id + "-0");
    that.selectPairList = [{ "id": 0, "attributeSelect": attributeSelect , "removeButton": removeButton }];

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
}

InstrumentGraph.prototype.updateSelect = function() {
    var instrumentId = this.instrumentSelect.value;
    var instrumentValidColumns = this.columnList[instrumentId];
    instrumentValidColumns.sort();

    for (var j = 0; j < this.selectPairList.length; j++){
        var attributeSelect = this.selectPairList[j]["attributeSelect"];
        removeOptions(attributeSelect);

        for (var i = 0; i < instrumentValidColumns.length; i++){
            newOption = document.createElement("option");
            newOption.value = instrumentValidColumns[i];
            newOption.text = instrumentValidColumns[i];
            attributeSelect.add(newOption);
        }
    }
}

InstrumentGraph.prototype.removeInstrumentGraph = function() {
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

    // Statistic fields, only handled if stats_enabled is true
    this.statsEnabled = false;
    this.selLowerDeviation = 0;
    this.selUpperDeviation = 0;
    this.minimum = 0;
    this.maximum = 0;
    this.median = 0;
    this.average = 0;
    this.stdDeviation = 0;
    this.statFrequency = 10;   // How often the stats will be generated. Every X requests for data, update stats
    this.forceRedraw = false;  // When set to true, redraws the whole Dygraph.  Used to update stat lines
    this.statCount = this.statFrequency - 1; // Counter for requests without stat generation.
                                               // Setting this way guarantees the first request generates stats


    var masterDiv = document.getElementById('instrument-graph-container-' + this.id)

    // Size from radio set
    this.graphSize = "medium";
    this.graphWidth = 500;
    this.graphHeight = 400;
    var graphSizeElement = document.querySelector('input[name="inst-graph-size-' + this.id + '"]:checked');

    if (graphSizeElement) {
        this.graphSize = graphSizeElement.value;
    }

    // Set sizes according to selection
    if (this.graphSize == "small") {
        this.graphWidth = 350;
        this.graphHeight = 280;
    } else if (this.graphSize == "medium") {
        this.graphWidth = 500;
        this.graphHeight = 400;
    } else if (this.graphSize == "large") {
        this.graphWidth = 750;
        this.graphHeight = 600;
    }

    var keyElems = document.getElementsByName("attribute-select-" + this.id);
    this.keys = [];
    for (var i = 0; i < keyElems.length; i++) {
        this.keys.push(keyElems[i].value);
    }

    startStr = document.getElementById("datetime-input-start-" + this.id).value;
    this.originTime = new Date(startStr + " UTC");
    this.beginningTime = new Date(startStr + " UTC");

    endStr = document.getElementById("datetime-input-end-" + this.id).value;
    this.endTime = new Date(endStr + " UTC");

    // Clear Master Div
    while (masterDiv.firstChild) {
        masterDiv.removeChild(masterDiv.lastChild)
    }

    // Partition out divs.
    this.graphDivId = "graphdiv-" + this.id;
    this.graphDiv = document.createElement('div');
    this.graphDiv.className = "dashboard_instrument_dygraph";
    this.graphDiv.innerHTML = '<div id = "' + this.graphDivId + '-parent">' +
                         '<div id="' + this.graphDivId +
                         '" style="width: ' + this.graphWidth + 'px; height: ' + this.graphHeight +
                         'px; display: inline-block;"></div></div>'

    this.dataDivId = "datadiv-" + this.id;
    this.dataDiv = document.createElement('div');
    this.dataDiv.className = "dashboard_graph_stats"

    // If there is only one attribute graphed, generate a button that allows the user to get stats for the attribute
    if (String(this.keys).split(",").length ==1){
        this.graphTitle = this.instrumentSelect.options[this.instrumentSelect.selectedIndex].text
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
    this.graphDiv.firstChild.appendChild(this.dataDiv)
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
    var attributeSelect = document.createElement('select');
    attributeDiv.appendChild(removeButton);
    attributeDiv.appendChild(attributeSpan);
    attributeSpan.appendChild(attributeSelect);

    removeButton.id = "inst-remove-attribute-button-" + this.id + "-" + this.nextAttributeId;
    var that = this;
    var functionParameter = that.nextAttributeId;
    removeButton.onclick = function () { that.removeAttribute(functionParameter); };
    removeButton.innerHTML = "X";
    removeButton.title = "Remove This Attribute"

    attributeSelect.className = "attribute_select";
    attributeSelect.id = "attribute-select-" + this.id + "-" + this.nextAttributeId;
    attributeSelect.name = "attribute-select-" + this.id;

    var placeholderOption = document.createElement("option");
    placeholderOption.text = "Select an Instrument";
    attributeSelect.add(placeholderOption);

    masterDiv.appendChild(attributeDiv);

    this.selectPairList.push({ "id": this.nextAttributeId, "attributeSelect": attributeSelect,
                               "removeButton": removeButton });
    this.updateSelect();

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
        this.graphData = this.graphData.concat(values);
        this.forceRedraw = false;

        if (this.graphData.length > 0){
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
            this.graphData = this.graphData.concat(values);
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

InstrumentGraph.prototype.updateInstrumentGraph = function() {
// keys, beginning_time, end_time, origin_time
    //Gets the next set of data values
    graphData = "";
    var thisGraph = this;
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        //After the asyncronous request successfully returns
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
        {
            //Pull out the response text from the request
            var recMessage = JSON.parse(xmlhttp.responseText);
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
        }
    };
    //Send JSON POST XMLHTTPRequest to generator controller.
    //Include keys for the generated graph, and convert start and end datetimes to a valid argument format
    //Assume input is in UTC

    var originUTC = this.originTime.toUTCString();
    var startUTC = this.beginningTime.toUTCString();
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
              "&instrument_id=" + this.instrumentSelect.value +
              "&start=" + startUTC +
              "&end=" + endUTC +
              "&origin=" + originUTC +
              "&do_stats=" + doStats;
    xmlhttp.open("POST", url, true);
    //Send out the  request
    xmlhttp.send();
};

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
};

InstrumentGraph.prototype.revealController = function () {
    var element = document.getElementById("inst-graph-controller-" + this.id);
    element.style.display = "";
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
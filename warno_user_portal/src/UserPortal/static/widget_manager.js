// Contains, creates and removes different widgets.
function WidgetManager(containerDiv, controllerUrl, logViewerURL, statusPlotURL, genGraphURL) {
    this.containerDiv = containerDiv;    // Div widgets will be added to
    this.controllerUrl = controllerUrl;  // URL for the backend widget controller
    this.logViewerURL = logViewerURL;    // URL to access log viewer --Feels clunky
    this.statusPlotURL = statusPlotURL;  // URL to access status plot --Feels clunky
    this.genGraphURL = genGraphURL;      // URL of hook that returns graph data for given attributes
    this.newWidgetId = 0;                // ID of the next widget that is created.  Should be incremented to stay unique
    this.widgets = [];                   // Array of active widget objects
    this.hasTightBorders = false;        // Whether automatic borders for widgets are enabled or disabled

    this.timer = setInterval(this.tick.bind(this), 60000)  // Timer set to trigger once a minute
};

WidgetManager.prototype.tick = function(){
    // Regularly removes any widgets that are no longer active and 'ticks' for each widget that is still active
    this.removeInactive();
    for (i = 0; i < this.widgets.length; i++){
        this.widgets[i].tick()
    }
};

WidgetManager.prototype.saveDashboard = function() {
    //First removes any inactive widgets
    this.removeInactive();

    // Gathers for each widget a representation that can be used to recreate the widget, returning all as a JSON object
    var payload = [];
    for (i = 0; i < this.widgets.length; i++) {
        payload.push(this.widgets[i].saveDashboard());
    }

    // Now push any information relevant to the WidgetManager itself
    var widgetManagerInfo = {
        "type": "WidgetManager",
        "data": {
            "tightBorders": this.hasTightBorders
        }
    }

    payload.push(widgetManagerInfo)

    return JSON.stringify(payload);
};

WidgetManager.prototype.loadDashboard = function(dashboardSchematic) {
    // First, clear out all widgets on the dashboard
    this.removeWidgets();
    this.removeInactive();

    // Build new dashboard from the given schematic
    this.buildFromSchematic(dashboardSchematic);
};

WidgetManager.prototype.buildFromSchematic = function(dashboardSchematic) {
    // Build objects from a given dashboard configuration
    // Each representation of a widget is expected to have a 'type' field, which indicates which object to create, and a
    // 'data' field, which is passed to the widget to accurately recreate it.
    for (var i = 0; i < dashboardSchematic.length; i ++) {
        if (dashboardSchematic[i]["type"] == "LogViewer") {
            this.addLogViewer(dashboardSchematic[i]["data"]);
        }
        if (dashboardSchematic[i]["type"] == "StatusPlot") {
            this.addStatusPlot(dashboardSchematic[i]["data"]);
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
        if (dashboardSchematic[i]["type"] == "CurrentTime") {
            this.addCurrentTime(dashboardSchematic[i]["data"]);
        }
        if (dashboardSchematic[i]["type"] == "WidgetManager") {
            // One assumption here is that because the WidgetManager schematic is added at the end of the saveDashboard
            // function, this should always be the last schematic to load if it exits, making it safe to
            // update the borders of the widgets here.
            this.hasTightBorders = dashboardSchematic[i]["data"]["tightBorders"];
            this.updateBorders();
        }
    }
}

WidgetManager.prototype.copyWidget = function(widgetId) {
    // Find the widget that matches the given ID
    for (i = 0; i < this.widgets.length; i++) {
        if (this.widgets[i].id == widgetId) {
            // When found, retrieve the representation of the widget and build a new widget from the representation
            var schematic = [];
            schematic.push(this.widgets[i].saveDashboard());
            this.buildFromSchematic(schematic);
        }
    }
};

WidgetManager.prototype.removeInactive = function() {
    // Cycles through the list of widgets, removing any widgets that have been marked as no longer 'active'
    for (i = 0; i < this.widgets.length; i++){
        if(!this.widgets[i].active){
            this.widgets.splice(i, 1);
            i--;  // This ensures that the index doesn't get messed up by the removal of an element.
        }
    }
};

WidgetManager.prototype.addCurrentTime = function(schematic) {
    var newCurrentTime = new CurrentTime(this, this.newWidgetId, this.containerDiv, schematic);
    this.widgets.push(newCurrentTime);
    this.newWidgetId += 1;
    if (this.hasTightBorders) {
        newCurrentTime.tightBorders();
    }
};

WidgetManager.prototype.addLogViewer = function(schematic) {
    var newLogViewer = new LogViewer(this, this.newWidgetId, this.containerDiv, this.controllerUrl,
                                     this.logViewerURL, schematic);
    this.widgets.push(newLogViewer);
    this.newWidgetId += 1;
    if (this.hasTightBorders) {
        newLogViewer.tightBorders();
    }
};

WidgetManager.prototype.addStatusPlot = function(schematic) {
    var newStatusPlot = new StatusPlot(this, this.newWidgetId, this.containerDiv, this.controllerUrl,
                                       this.statusPlotURL, schematic);
    this.widgets.push(newStatusPlot);
    this.newWidgetId +=1;
    if (this.hasTightBorders) {
        newStatusPlot.tightBorders();
    }
};

WidgetManager.prototype.addHistogram = function(schematic) {
    var newHistogram = new Histogram(this, this.newWidgetId, this.containerDiv, this.controllerUrl, schematic);
    this.widgets.push(newHistogram);
    this.newWidgetId +=1;
    if (this.hasTightBorders) {
        newHistogram.tightBorders();
    }
};

WidgetManager.prototype.addDualHistogram = function(schematic) {
    var newDualHistogram = new DualHistogram(this, this.newWidgetId, this.containerDiv, this.controllerUrl, schematic);
    this.widgets.push(newDualHistogram);
    this.newWidgetId +=1;
    if (this.hasTightBorders) {
        newDualHistogram.tightBorders();
    }
};

WidgetManager.prototype.addInstrumentGraph = function(schematic) {
    var newInstrumentGraph = new InstrumentGraph(this, this.newWidgetId, this.containerDiv, this.controllerUrl,
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
        this.widgets[i - 1].remove();  // Need to explicitly call each widget's remove function to clear all html
        this.widgets.splice(i - 1, 1);
    }
}

WidgetManager.prototype.updateBorders = function() {
    // This function checks the current status of the hasTightBorders variable and either tightens or widens all
    // widget borders appropriately.  Only really used to facilitate correct borders when loading a dashboard.
    if (this.hasTightBorders) {
        this.tightBorders();
    } else {
        this.wideBorders();
    }
}

WidgetManager.prototype.tightBorders = function() {
    // Set widgets to automatically resize dependent upon contents
    this.hasTightBorders = true;
    for (var i = 0; i < this.widgets.length; i ++) {
        this.widgets[i].tightBorders();
    }
}

WidgetManager.prototype.wideBorders = function() {
    // Set widgets to a fixed size
    this.hasTightBorders = false;
    for (var i = 0; i < this.widgets.length; i ++) {
        this.widgets[i].wideBorders();
    }
}



// Configuration Parameter superclass and subtypes
function ConfigParameter(id, name, label, defaultValue) {
    // Object representing a widget configuration parameter
    this.id = id;              // Unique identifier.  Helps distinguish between multiple instances of parameters
    this.name = name;          // Name of the parameter
    this.label = label;        // Label for the generated configuration parameter element
    this.type = 'abstract';    // Type of config parameter.  Used for loading the dashboard back in
    this.value = defaultValue; // Current value of parameter.  Default given at creation
}

ConfigParameter.prototype.isValidValue = function(value) {
    // Up to the subclasses to validate values.  If there is no defined validity checking function, defaults to true
    return true;
}

ConfigParameter.prototype.buildConfigElement = function() {
    // Create the html config element that will allow the user to select and save the proper value to this object
    var configElement = document.createElement('div');  // Defaults to an empty div
    return configElement;
}

ConfigParameter.prototype.loadFromConfigElement = function() {
    // Load in the value in the config element.  Defaults to doing nothing, must be set for each ConfigParameter type
}

ConfigParameter.prototype.setValue = function(value) {
    this.value = value;
    return value;
}

ConfigParameter.prototype.getRepresentation = function() {
    // Return a dictionary defining the parts needed to recreate the object.
    return {
        "type": this.type,
        "name": this.name,
        "label": this.label,
        "value": this.value,
        }
}



function ConfigString(id, name, label, defaultValue, maxLength) {
    // Defines a string with a maximum length.  'null' indicates no maximum length
    ConfigParameter.call(this, id, name, label, defaultValue);

    this.type = 'string';                       // Marks the type of widget, enabling recreation from representation
    this.inputId = name + '-input-' + this.id;  // Uses the passed (presumably unique) id to create a unique HTML ID
    this.maxLength = maxLength;                 // Maximum length of string. 'null' indicates no limit
}
// This must occur before any other prototyped functions are set, or they will be overwritten by these calls
ConfigString.prototype = Object.create(ConfigParameter.prototype);
ConfigString.prototype.constructor = ConfigString;

ConfigString.prototype.isValidValue = function(value) {
    var isValid = false;

    if (value === null) {
        isValid = true;
    };

    if (typeof value === "string") {
        if (value.length <= this.maxLength) {
            isValid = true;
        };
    };

    return isValid;
}

ConfigString.prototype.buildConfigElement = function() {
    // Returns a configuration element with the label and its corresponding input box
    var configElement = document.createElement('div');

    var divLabel = document.createElement('label');
    divLabel.htmlFor = this.inputId;
    divLabel.innerHTML = this.label;
    configElement.appendChild(divLabel);

    var divInput = document.createElement('input');
    divInput.type = 'text';
    divInput.id = this.inputId;
    if (!(this.maxLength === null) & (this.maxLength >= 1)) {
        divInput.maxLength = this.maxLength;
        this.value = this.value.substring(0, this.maxLength);  // Truncate the current value to the maximum length
    };
    divInput.value = this.value;                               // Pre-fill input with current value
    configElement.appendChild(divInput);

    return configElement;
}

ConfigString.prototype.loadFromConfigElement = function() {
    // Get the current value of the input element
    var inputElement = document.getElementById(this.inputId);
    return inputElement.value;
}

ConfigString.prototype.getRepresentation = function() {
    // Return a dictionary defining the parts needed to recreate the object.
    return {
        "type": this.type,
        "name": this.name,
        "label": this.label,
        "value": this.value,
        "maxLength": this.maxLength,
        }
}


function ConfigNumber(id, name, label, defaultValue, lowerLimit, upperLimit) {
    // Defines a number with limits on the valid values
    ConfigParameter.call(this, id, name, label, defaultValue);

    this.type = 'number';                      // Marks the type of widget, enabling recreation from representation
    this.inputId = name + '-input-' + this.id; // Uses the (presumably unique) id to create a unique HTML ID for input
    this.errorId = name + '-error-' + this.id; // Uses the (presumably unique) id to create a unique HTML ID for errors
    this.lowerLimit = lowerLimit;              // A 'null' here means no lower limit for the value
    this.upperLimit = upperLimit;              // A 'null' here means no upper limit for the value
}

// This must occur before any other prototyped functions are set, or they will be overwritten by these calls
ConfigNumber.prototype = Object.create(ConfigParameter.prototype);
ConfigNumber.prototype.constructor = ConfigNumber;

ConfigNumber.prototype.isValidValueWithReason = function(value) {
    var isValid = false;
    var error = "";

    // Value must be a valid JavaScript number
    if (typeof value === "number" && !isNaN(value)) {
        // Value must be within given limits.  A 'null' in either limit indicates no limit on that end.
        if (( (this.lowerLimit === null) || (value >= this.lowerLimit) ) &&
            ( (this.upperLimit === null) || (value <= this.upperLimit) )) {
            isValid = true;
        } else {
            // This should not be reached if both limits are null, so that case is not handled here
            error = "";
            if (!(this.lowerLimit === null)) {
                error += "Value must be at least " + this.lowerLimit + ". ";
            };
            if (!(this.upperLimit === null)) {
                error += "Value must not be greater than " + this.upperLimit + ".";
            };
        };
    } else {
        error = "Value must be a number.";
    }

    // Returns both the boolean indicating valid/not valid and the error if it was not valid.
    return [isValid, error];
}

ConfigNumber.prototype.isValidValue = function(value) {
    // For the simple case where you just want to know if the value is valid without needing the reasons
    result = this.isValidValueWithReason(value);
    return result[0];
}

ConfigNumber.prototype.buildConfigElement = function() {
    // Returns a configuration element with the label, its sinput box, and a div to display validation errors
    var configElement = document.createElement('div');

    // Label explaining the input purpose/format
    var divLabel = document.createElement('label');
    divLabel.htmlFor = this.inputId;
    divLabel.innerHTML = this.label;
    configElement.appendChild(divLabel);

    // Input box for the value
    var divInput = document.createElement('input');
    divInput.type = 'text';
    divInput.id = this.inputId;
    divInput.value = this.value;
    configElement.appendChild(divInput);

    // Error div to display any validation errors
    var divError = document.createElement('div');
    divError.id = this.errorId;
    divError.className = 'config-error'; // For now just uses a generic error class
    configElement.appendChild(divError);

    return configElement;
}

ConfigNumber.prototype.loadFromConfigElement = function() {
    var inputElement = document.getElementById(this.inputId);
    var errorElement = document.getElementById(this.errorId);
    floatValue = parseFloat(inputElement.value);

    // Check if the input is valid
    result = this.isValidValueWithReason(floatValue);

    if (result[0]) {
        // If the value is valid, clear any error text and return the value
        errorElement.innerHTML = "";
        return floatValue;
    } else {
        // If the given value was invalid
        errorElement.innerHTML = result[1]; // Sets the error element with the returned error
        return NaN;  // If this is passed to a validation check, will correctly be marked as invalid
    };
}

ConfigNumber.prototype.getRepresentation = function() {
    // Return a dictionary defining the parts needed to recreate the object
    return {
        "type": this.type,
        "name": this.name,
        "label": this.label,
        "value": this.value,
        "lowerLimit": this.lowerLimit,
        "upperLimit": this.upperLimit,
        }
}


function ConfigInteger(id, name, label, defaultValue, lowerLimit, upperLimit) {
    // Defines a number with limits on the valid values
    ConfigParameter.call(this, id, name, label, defaultValue);

    this.type = 'integer';                      // Marks the type of widget, enabling recreation from representation
    this.inputId = name + '-input-' + this.id;  // Uses the (presumably unique) id to create a unique HTML ID for input
    this.errorId = name + '-error-' + this.id;  // Uses the (presumably unique) id to create a unique HTML ID for errors
    this.lowerLimit = lowerLimit;               // A 'null' here means no lower limit for the value
    this.upperLimit = upperLimit;               // A 'null' here means no upper limit for the value
}

// This must occur before any other prototyped functions are set, or they will be overwritten by these calls
ConfigInteger.prototype = Object.create(ConfigParameter.prototype);
ConfigInteger.prototype.constructor = ConfigInteger;

ConfigInteger.prototype.isValidValueWithReason = function(value) {
    var isValid = false;
    var error = "";

    // Will not allow strings to represent numbers. Must be converted beforehand
    if (isInt(value) && typeof value === "number"){
        // Value must be within given limits.  A 'null' in either limit indicates no limit on that end.
        if (( (this.lowerLimit === null) || (value >= this.lowerLimit) ) &&
            ( (this.upperLimit === null) || (value <= this.upperLimit) )) {
            isValid = true;
        } else {
            // This should not be reached if both limits are null, so that case is not handled here
            error = "";
            if (!(this.lowerLimit === null)) {
                error += "Value must be at least " + this.lowerLimit + ". ";
            };
            if (!(this.upperLimit === null)) {
                error += "Value must not be greater than " + this.upperLimit + ".";
            };
        };
    } else {
        error = "Value must be an integer.";
    }

    // Returns both the boolean indicating valid/not valid and the error if it was not valid.
    return [isValid, error];
}

ConfigInteger.prototype.isValidValue = function(value) {
    // For the simple case where you just want to know if the value is valid without needing the reason.
    result = this.isValidValueWithReason(value);
    return result[0];
}

ConfigInteger.prototype.buildConfigElement = function() {
    // Returns a configuration element with the label, its input box, and a div to display validation errors
    var configElement = document.createElement('div');

    // Label explaining the input purpose/format
    var divLabel = document.createElement('label');
    divLabel.htmlFor = this.inputId;
    divLabel.innerHTML = this.label;
    configElement.appendChild(divLabel);

    // Input box for the value
    var divInput = document.createElement('input');
    divInput.type = 'text';
    divInput.id = this.inputId;
    divInput.value = this.value;
    configElement.appendChild(divInput);

    // Error div to display any validation errors
    var divError = document.createElement('div');
    divError.id = this.errorId;
    divError.className = 'config-error';  // For now just uses a generic error class
    configElement.appendChild(divError);

    return configElement;
}

ConfigInteger.prototype.loadFromConfigElement = function() {
    var inputElement = document.getElementById(this.inputId);
    var errorElement = document.getElementById(this.errorId);
    floatValue = parseFloat(inputElement.value);

    // Checking against float version then converting to integer if it is valid prevents unintended rounding in parseInt
    result = this.isValidValueWithReason(floatValue);

    if (result[0]) {
        // If the value is valid, clear any error text and return the value
        errorElement.innerHTML = "";
        return parseInt(inputElement.value);
    } else {
        // If the given value was invalid
        errorElement.innerHTML = result[1];  // Sets the error element with the returned error
        return NaN; // If this is passed to a validation check, will correctly be marked as invalid
    };
}

ConfigInteger.prototype.getRepresentation = function() {
    // Return a dictionary defining the parts needed to recreate the object
    return {
        "type": this.type,
        "name": this.name,
        "label": this.label,
        "value": this.value,
        "lowerLimit": this.lowerLimit,
        "upperLimit": this.upperLimit,
        }
};

function ConfigCheckbox(id, name, label, defaultValue) {
    // Defines checkbox for a boolean
    ConfigParameter.call(this, id, name, label, defaultValue);

    this.type = "checkbox";                         // Marks the type of widget, enabling creation from representation
    this.inputId = this.name + "-input-" + this.id; // Uses the (presumably unique) id to create a unique HTML ID
}

// This must occur before any other prototyped functions are set, or they will be overwritten by these calls
ConfigCheckbox.prototype = Object.create(ConfigParameter.prototype);
ConfigCheckbox.prototype.constructor = ConfigCheckbox;

ConfigCheckbox.prototype.isValidValue = function(value) {
    if (typeof value == "boolean") {
        return true;
    } else {
        return false;
    };
}

ConfigCheckbox.prototype.buildConfigElement = function() {
    // Returns a configuration element with the label and its input box
    var configElement = document.createElement('div');

    // Label explaining the input purpose/format
    var divLabel = document.createElement('label');
    divLabel.htmlFor = this.inputId;
    divLabel.innerHTML = this.label;
    configElement.appendChild(divLabel);

    // Input box for the value
    var divInput = document.createElement('input');
    divInput.type = 'checkbox';
    divInput.id = this.inputId;
    if (this.value) {
        divInput.checked = true;
    };
    configElement.appendChild(divInput);

    return configElement;
}

ConfigCheckbox.prototype.loadFromConfigElement = function() {
    // Returns a boolean specifying whether the input checkbox is checked or not
    var inputElement = document.getElementById(this.inputId);

    if (inputElement.checked) {
        return true;
    } else {
        return false;
    };
}

function ConfigSelect(id, name, label, defaultValue, options) {
    // Defines a select field with defined options.  The 'defaultValue' must be one of the options' values
    ConfigParameter.call(this, id, name, label, defaultValue);

    this.type = "select";                           // Marks the type of widget, enabling creation from representation
    this.inputId = this.name + "-input-" + this.id; // Uses the (presumably unique) id to create a unique HTML ID
    this.options = options; // Array where each element is an option of the array form '[optionText, value]'
}

// This must occur before any other prototyped functions are set, or they will be overwritten by these calls
ConfigSelect.prototype = Object.create(ConfigParameter.prototype);
ConfigSelect.prototype.constructor = ConfigSelect;

ConfigSelect.prototype.isValidValue = function(value) {
    // If one of the 'options' value matches the given value, return true
    for (var i = 0; i < this.options.length; i++) {
        if (value == this.options[i][1]) {
            return true;
        };
    };

    return false;
}

ConfigSelect.prototype.buildConfigElement = function() {
    // Returns a configuration element with the label and its input box
    var configElement = document.createElement('div');

    // Label explaining the input's purpose
    var divLabel = document.createElement('label');
    divLabel.htmlFor = this.inputId;
    divLabel.innerHTML = this.label;
    configElement.appendChild(divLabel);

    // Input selector for the value.  Filled with the parameter's options
    var divInput = document.createElement('select');
    divInput.id = this.inputId;
    for (var i = 0; i < this.options.length; i ++) {
        var opt = document.createElement('option');
        opt.innerHTML = this.options[i][0];
        opt.value = this.options[i][1];
        if (opt.value == this.value) {
            opt.selected = true;
        };
        divInput.appendChild(opt);
    };
    configElement.appendChild(divInput);

    return configElement;
}

ConfigSelect.prototype.loadFromConfigElement = function() {
    // Get the value of the currently selected option
    var inputElement = document.getElementById(this.inputId);

    return inputElement.value;
}

ConfigSelect.prototype.getRepresentation = function() {
    // Return a dictionary defining the parts needed to recreate the object
    return {
        "type": this.type,
        "name": this.name,
        "label": this.label,
        "value": this.value,
        "options": this.options,
        }
}


// Class definition for generic Widget
function Widget(manager, id, containerDiv, schematic) {
    this.manager = manager;                          // Reference to the WidgetManager that controls this Widget
    this.id = id;                                    // ID for the Widget, should be unique among other Widgets on page

    this.parentDiv = document.createElement('div');  // Parent div, holds all widget contents
    this.parentDiv.className = 'wd';
    this.parentDiv.id = 'widget-' + this.id;
    containerDiv.appendChild(this.parentDiv);
    this.schematic = schematic;                      // Dashboard schematic to rebuild Widget

    this.active = true;
    this.activeCounter = false;                      // True if actively counting ticks and triggering jobs.
    this.controlDiv = document.createElement('div'); // The div for the main view and controls of the Widget
    this.configDiv = document.createElement('div');  // The div containing the configuration controls of the Widget

    this.triggerCounter = 0;                         // Counter object, incremented per tick, reset after job triggered

    // The first element of each parameter is the unique name for it.  Must not be any repeats for this Widget.
    this.configParameters = [];
}

Widget.prototype.tick = function() {
    // When the parent WidgetManager has passed a certain interval, calls this 'tick' function
    // If the counter is active, will increment the counter, and if it is past the configurable number,
    // the counter will reset and the Widget's 'job' will be triggered
    if (this.activeCounter === true) {
        this.triggerCounter += 1;
        if (this.triggerCounter >= this.getConfigParameter("triggerTickNumber")){
            this.triggerCounter = 0;
            this.triggerJob();
        };
    };
};

Widget.prototype.initializeAndBuild = function () {
    // Initialize the parameters for the Widget and build the HTML controls and configuration inputs
    this.initializeParameters();  // Should be called before buildConfigDiv, function sets correct configParameters
    this.buildControlDiv();       // Likely to be overwritten for every subclass.  Different widgets, different controls
    this.buildConfigDiv();        // Likely to stay the same for subclasses.  Dynamic based on 'configParameters'
}

Widget.prototype.initializeParameters = function() {
    // Initialize the configuration parameters.  If there is a valid schematic, attempts to build from schematic
    // If there is no valid schematic, builds default parameters.  The 'buildDefaultParameters' function is
    // expected to change for different Widget subclasses, as it will define Widget specific options
    this.configParameters = [];

    var localSchematic = this.schematic;

    if (typeof this.schematic == "string") {
        localSchematic = JSON.parse(this.schematic);
    }

    if (localSchematic) {
        // Build from schematic
        configParameterSchematics = localSchematic["configParameters"];
        for (var i = 0; i < configParameterSchematics.length; i++) {
            this.configParameters.push(this.buildParameterFromRepresentation(configParameterSchematics[i]));
        }
    } else {
        // Build defaults
        this.buildDefaultParameters();  // Likely to be overwritten for every subclass
    }
}

Widget.prototype.buildDefaultParameters = function () {
    // Subclasses will likely overload this function.  Every widget should have the 'triggerTickNumber' parameter and
    // should follow this format, but different widgets will have different configuration parameters for their functions.
    this.configParameters = [
        new ConfigInteger(this.id, "triggerTickNumber", "Update Frequency in Minutes (positive integer): ", 1, 1, null),
    ];
};

Widget.prototype.buildParameterFromRepresentation = function(representation) {
    // Builds the proper ConfigParameter for whichever representation is passed to it.  Representations can be created
    // using a config parameter's 'getRepresentation()' call
    if (representation["type"] === "string") {
        return new ConfigString(this.id, representation["name"], representation["label"], representation["value"]);

    } else if (representation["type"] === "checkbox") {
        return new ConfigCheckbox(this.id, representation["name"], representation["label"], representation["value"]);

    } else if (representation["type"] === "integer") {
        return new ConfigInteger(this.id, representation["name"], representation["label"],  representation["value"],
                                 representation["lowerLimit"], representation["upperLimit"]);

    } else if (representation["type"] === "number") {
        return new ConfigNumber(this.id, representation["name"], representation["label"], representation["value"],
                                representation["lowerLimit"], representation["upperLimit"]);

    } else if (representation["type"] === "select") {
        return new ConfigSelect(this.id, representation["name"], representation["label"], representation["value"],
                                representation["options"]);
    }
    return null;
}

Widget.prototype.getConfigParameter = function (name) {
    // Finds the configuration parameter with the given name and returns its value
    for (var i = 0; i < this.configParameters.length; i++) {
        if (name == this.configParameters[i].name) {
            return this.configParameters[i].value;
        };
    };
    return null;
}

Widget.prototype.getConfigParameterRepresentations = function() {
    // Builds a list of representations for all configuration parameters of a Widget, then returns the list
    var configParameterRepresentations = [];
    for (var i = 0; i < this.configParameters.length; i ++) {
        representation = this.configParameters[i].getRepresentation();
        configParameterRepresentations.push(representation);
    };

    return configParameterRepresentations;
};

Widget.prototype.saveDashboard = function() {
    // This function is likely to be different per widget.  They should all package up the configuration parameters in
    // this way, but should also add their own Widget specific keys/value pairs.
    dashboard = {};

    // Package up the configuration parameters
    dashboard["configParameters"] = this.getConfigParameterRepresentations();

    return JSON.stringify(dashboard);
};

Widget.prototype.loadDashboard = function() {};  // Dashboard loads will be Widget specific, this is just a placeholder

Widget.prototype.buildControlDiv = function () {
    // This just creates a basic control div with a button that switches over to the configuration div.  Each widget
    // is likely to have its own implementation of this, but this serves as a basic example
    this.controlDiv.className = 'wd';
    this.controlDiv.innerHTML = "";
    this.controlDiv.id = 'widget-' + this.id;

    configButton = document.createElement('button');
    configButton.innerHTML = "Conf";
    var that = this;
    configButton.onclick = function(){that.showConfig()};
    this.controlDiv.appendChild(configButton);

    this.parentDiv.appendChild(this.controlDiv);
};

Widget.prototype.buildConfigDiv = function() {
    // Builds a configuration div for a widget dynamically based on the configuration parameters.  Might be a little
    // ugly, but most widgets should be able to use this default implementation
    this.configDiv.id = 'config-' + this.id;
    this.configDiv.className = "widget_config";
    this.configDiv.innerHTML = "";

    for (var i = 0; i < this.configParameters.length; i++) {
        this.configDiv.appendChild(this.configParameters[i].buildConfigElement());
    };

    controlButton = document.createElement('button');
    controlButton.innerHTML = "<< Return";
    var that = this;
    controlButton.onclick = function(){that.hideConfig()};
    this.configDiv.appendChild(controlButton);

    saveButton = document.createElement('button');
    saveButton.innerHTML = "Apply";
    var that = this;
    saveButton.onclick = function(){that.saveConfig()};
    this.configDiv.appendChild(saveButton);

    this.parentDiv.appendChild(this.configDiv);
};

Widget.prototype.validateConfig = function() {
    // Only returns true if all of the entries are valid, otherwise returns false.  Want to make sure all
    // 'loadFromConfigElement' functions are called to display all errors at once though.
    allValid = true;
    for (var i = 0; i < this.configParameters.length; i++) {
        value = this.configParameters[i].loadFromConfigElement();
        if (!this.configParameters[i].isValidValue(value)) {
            allValid = false;
        };
    };
    return allValid;
};
Widget.prototype.saveConfig = function() {
    // If all the configuration parameter inputs are valid, reads in and sets the parameters to the new values.
    // The return indicates 'true' for success, 'false' for failure to save
    allEntriesValid = this.validateConfig();
    if (allEntriesValid) {
        for (var i = 0; i < this.configParameters.length; i++) {
            value = this.configParameters[i].loadFromConfigElement();
            this.configParameters[i].setValue(value);
        };
        return true;
    } else {
        return false;
    };
};

// This is the job that is triggered every so many 'tick's.  It is meant to be overwritten by individual Widgets to
// define which tasks are to be run regularly
Widget.prototype.triggerJob = function() {};

Widget.prototype.showConfig = function() {
    // Hides the control div, showing the configuration div
    this.controlDiv.style.display = "none";
    this.configDiv.style.display = "block";
};

Widget.prototype.hideConfig = function() {
    // Hides the configuration div, showing the control div
    this.controlDiv.style.display = "block";
    this.configDiv.style.display = "none";
};

Widget.prototype.remove = function() {
    // Removes HTML elements for the widget and marks the widget as inactive (meaning the WidgetManager will remove it)
    if (this.parentDiv.parentNode) {  // If there is no parent, may have already been removed
        this.parentDiv.parentNode.removeChild(this.parentDiv);
    }
    this.active = false;
};

Widget.prototype.tightBorders = function () {
    this.parentDiv.className = "wd_tight";
};

Widget.prototype.wideBorders = function () {
    this.parentDiv.className = "wd";
};

// TUTORIAL WIDGET
function CurrentTime(manager, id, containerDiv, schematic) {
    Widget.call(this, manager, id, containerDiv, schematic);


    this.time = "";
    this.inUTC = false;

    // Should always be called
    this.initializeAndBuild();

    // Good function to have for dashboard parameters
    this.loadDashboard(schematic);

    this.initializeElements();
};

CurrentTime.prototype = Object.create(Widget.prototype);
CurrentTime.prototype.constructor = CurrentTime;

CurrentTime.prototype.buildDefaultParameters = function () {
    var colorOptions = [
        ["Black", "black"],
        ["Red", "darkRed"],
        ["Blue", "darkBlue"],
        ["Green", "green"],
    ];

    this.configParameters = [
        new ConfigInteger(this.id, "triggerTickNumber", "Update Frequency in Minutes (positive integer): ", 1, 1, null),
        new ConfigInteger(this.id, "fontSize", "Font size for time (integer 6-30): ", 16, 6, 30),
        new ConfigSelect(this.id, "fontColor", "Font color for time", "black", colorOptions),
    ];
};

CurrentTime.prototype.buildControlDiv = function () {
    this.controlDiv.innerHTML = "";
    this.controlDiv.id = 'control-' + this.id;    // this.id is unique, so the div ID will also be unique

    var configButton = document.createElement('button');
    configButton.innerHTML = "Config";
    var that = this;   // Because using 'this' inside the next function references the function itself, not this Widget
    configButton.onclick = function(){that.showConfig()};
    this.controlDiv.appendChild(configButton);

    var generateButton = document.createElement('button');
    generateButton.innerHTML = "Get Time";
    generateButton.onclick = function(){that.generateTime()};
    this.controlDiv.appendChild(generateButton);

    var utcLabel = document.createElement('label');
    utcLabel.htmlFor = "widget-utc-" + this.id;
    utcLabel.innerHTML = "UTC Time: ";
    var utcCheckbox = document.createElement('input');
    utcCheckbox.setAttribute("type", "checkbox");
    utcCheckbox.id = "widget-utc-" + this.id;
    this.controlDiv.appendChild(utcLabel);
    this.controlDiv.appendChild(utcCheckbox);

    var removeButton = document.createElement('button');
    removeButton.innerHTML = "X";
    removeButton.onclick = function(){that.remove()};
    removeButton.style.float = "right";
    this.controlDiv.appendChild(removeButton);

    var timeDiv = document.createElement("div");
    timeDiv.innerHTML = this.time;
    timeDiv.id = "widget-time-" + this.id;
    this.controlDiv.appendChild(timeDiv);

    this.parentDiv.appendChild(this.controlDiv);  // Always remember to actually add your control div to the parent
};

CurrentTime.prototype.triggerJob = function () {
    this.generateTime();
};

CurrentTime.prototype.saveDashboard = function () {
    var configRepresentation = this.getConfigParameterRepresentations();
    data = {
        "inUTC": this.inUTC,
        "configParameters": configRepresentation,
    }
    return {"type": "CurrentTime", "data": data};
};

CurrentTime.prototype.loadDashboard = function (schematic) {
    if (schematic) {
        this.inUTC = schematic["inUTC"];
    } else {
        this.inUTC = false;
    }
};

CurrentTime.prototype.initializeElements = function () {
    var utcCheckbox = document.getElementById("widget-utc-" + this.id);
    utcCheckbox.checked = this.inUTC;
};

CurrentTime.prototype.generateTime = function () {
    this.activeCounter = true;  // Enables automatic updates

    var utcCheckbox = document.getElementById("widget-utc-" + this.id);
    this.inUTC = utcCheckbox.checked;

    var currentDate = new Date();
    if (this.inUTC) {
        this.time = currentDate.toUTCString();
    } else {
        this.time = currentDate.toString();
    }
    var timeDiv = document.getElementById("widget-time-" + this.id);

    var fontColor = this.getConfigParameter('fontColor');
    var fontSize = this.getConfigParameter('fontSize');

    timeDiv.style.color = fontColor;
    timeDiv.style.fontSize = fontSize;
    timeDiv.innerHTML = this.time;
};

// WIDGETS

// Log Viewer section
function LogViewer(manager, id, containerDiv, controllerURL, logViewerURL, schematic) {
    Widget.call(this, manager, id, containerDiv, schematic);

    this.finishedLoading = true;
    this.logViewerURL = logViewerURL;
    this.controllerURL = controllerURL;
    this.instrumentId = -1;
    this.maxLogs = 5;
    this.quickDisplay = false;

    this.initializeAndBuild();
    if (schematic) {
        this.loadDashboard(schematic);
    };
}

LogViewer.prototype = Object.create(Widget.prototype);
LogViewer.prototype.constructor = LogViewer;

LogViewer.prototype.buildDefaultParameters = function () {
    this.configParameters = [
        new ConfigInteger(this.id, "triggerTickNumber", "Update Frequency in Minutes (positive integer): ", 1, 1, null),
        new ConfigInteger(this.id, "maxLogs", "Number of logs to display at a time (positive integer): ", 5, 1, null),
    ];
};

LogViewer.prototype.buildControlDiv = function() {
    this.controlDiv.innerHTML = "LogViewer";
    this.parentDiv.appendChild(this.controlDiv);

    var parameterizedURL = this.controllerURL + "?widget_name=log_viewer&widget_id=" + this.id;
    this.ajaxLoadURL(this.controlDiv, parameterizedURL);
};

LogViewer.prototype.saveDashboard = function() {
    var configRepresentation = this.getConfigParameterRepresentations();
    var data = {"instrumentId": this.instrumentId, "configParameters": configRepresentation};
    return {"type": "LogViewer", "data": data};
}

LogViewer.prototype.loadDashboard = function(schematic) {
    this.finishedLoading = false;
    this.quickDisplay = true;  // Forces the full view generation in the ajaxLoadUrl from the LogViewer Creation
    this.instrumentId = schematic["instrumentId"];
    //ConfigParameters should already have been loaded in when the widget was constructed
    var instrumentIdSelect = document.getElementById("log-viewer-instrument-selector-" + this.id);
    if (instrumentIdSelect) {  // If the element exists, update and generate, if not, should be taken care of by setting quickDisplay above
        instrumentIdSelect.value = this.instrumentId;
        this.generateLogViewer();
    };

};

LogViewer.prototype.ajaxLoadURL = function(element, url) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
            // To get JSON and HTML parts, need to do custom extraction.
            element.innerHTML = xmlHttp.responseText;

            var configButton = document.getElementById("config-open-button-" + that.id);
            configButton.onclick = function () { that.showConfig(); };
            var addButton = document.getElementById("add-log-viewer-button-" + that.id);
            addButton.onclick = function () { that.generateLogViewer(); };
            var copyButton = document.getElementById("copy-log-viewer-button-" + that.id);
            copyButton.onclick = function () { that.manager.copyWidget(that.id); };
            var removeButton = document.getElementById("remove-log-viewer-button-" + that.id);
            removeButton.onclick = function () { that.remove(); };
            var instrumentIdSelect = document.getElementById("log-viewer-instrument-selector-" + that.id);
            instrumentIdSelect.value = that.instrumentId;

            if (that.quickDisplay === true) {  // If quick display was set, will immediately display with current setup.
                that.generateLogViewer();      // It's an ugly workaround for ajax behaviour for dashboard loading
            };
        };
    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();
};

LogViewer.prototype.triggerJob = function() {
    this.generateLogViewer();
};

LogViewer.prototype.generateLogViewer = function() {
    this.activeCounter = true;

    var fillElement = document.getElementById("log-viewer-container-" + this.id);
    this.instrumentId = document.getElementById("log-viewer-instrument-selector-" + this.id).value;
    this.maxLogs = this.getConfigParameter("maxLogs");
    var url = this.logViewerURL + '?instrument_id=' + this.instrumentId + '&max_logs=' + this.maxLogs;

    ajaxLoadUrl(fillElement, url)  // Generic helper load, not this.ajaxLoadURL
};

// Status Plot section
function StatusPlot(manager, id, containerDiv, controllerURL, statusPlotURL, schematic) {
    Widget.call(this, manager, id, containerDiv, schematic);

    this.controllerURL = controllerURL;  // URL to HTML for the controls/main page
    this.statusPlotURL = statusPlotURL;  // URL for updating the status plot
    this.siteId = -1;                    // Current site ID selected. -1 indicates all sites
    this.quickDisplay;                   // quickDisplay allows for ajax friendly loading of the dashboard?

    this.initializeAndBuild();
    if (schematic) {
        this.loadDashboard(schematic);
    };

}

StatusPlot.prototype = Object.create(Widget.prototype);
StatusPlot.prototype.constructor = StatusPlot;

StatusPlot.prototype.buildDefaultParameters = function () {
    this.configParameters = [
        new ConfigInteger(this.id, "triggerTickNumber", "Update Frequency in Minutes (positive integer): ", 1, 1, null),
    ];
};

StatusPlot.prototype.buildControlDiv = function() {
    this.controlDiv.innerHTML = "StatusPlot";
    this.parentDiv.appendChild(this.controlDiv);

    var parameterizedURL = this.controllerURL + "?widget_name=status_plot&widget_id=" + this.id;
    this.ajaxLoadURL(this.controlDiv, parameterizedURL);
};

StatusPlot.prototype.saveDashboard = function () {
    var configRepresentation = this.getConfigParameterRepresentations();
    var data = {"siteId": this.siteId, "configParameters": configRepresentation};
    return {"type": "StatusPlot", "data": data};
};

StatusPlot.prototype.loadDashboard = function(schematic) {
    this.finishedLoading = false;
    this.quickDisplay = true;  // Forces the full view generation in the ajaxLoadURL form the StatusPlot Creation
    this.siteId = schematic["siteId"];
    //ConfigParameters should already have been loaded when the Widget was constructed
    var siteIdSelect = document.getElementById("status-plot-site-selector-" + this.id);
    if (siteIdSelect) { // If the element exists, update and generate, if not, should be taken care of by setting quickDisplay above
        siteIdSelect.value = this.siteId;
        this.generateStatusPlot();
    };
};

StatusPlot.prototype.ajaxLoadURL = function(element, url) {
    var xmlHttp = new XMLHttpRequest();
    var that = this;  // Need this because when we enter the function, 'this' points to a different object (the request)
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        {
            // To get JSON and HTML parts, need to do custom extraction.
            element.innerHTML = xmlHttp.responseText;

            var configButton = document.getElementById("config-open-button-" + that.id);
            configButton.onclick = function () { that.showConfig(); };
            var addButton = document.getElementById("add-status-plot-button-" + that.id);
            addButton.onclick = function () { that.generateStatusPlot(); };
            var copyButton = document.getElementById("copy-status-plot-button-" + that.id);
            copyButton.onclick = function () { that.manager.copyWidget(that.id); };
            var removeButton = document.getElementById("remove-status-plot-button-" + that.id);
            removeButton.onclick = function () { that.remove(); };

            var siteIdSelect = document.getElementById("status-plot-site-selector-" + that.id);
            siteIdSelect.value = that.siteId;

            if (that.quickDisplay === true) {  // If quick display was set, will immediately display with current setup
                that.generateStatusPlot();     // It's an ugly workaround for ajax behaviour for dashboard loading
            };
        };
    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();
};

StatusPlot.prototype.triggerJob = function() {
    this.generateStatusPlot();
};

StatusPlot.prototype.generateStatusPlot = function() {
    this.activeCounter = true;

    var fillElement = document.getElementById("status-plot-container-" + this.id);
    this.siteId = document.getElementById("status-plot-site-selector-" + this.id).value;

    var url = this.statusPlotURL + '?site_id=' + this.siteId;

    ajaxLoadUrl(fillElement, url);  // Generic helper load, not this.ajaxLoadURL
};

// Real Time Gauge section
function RealTimeGauge(manager, id, containerDiv, controllerURL, schematic) {
    Widget.call(this, manager, id, containerDiv, schematic);

    this.minimum = 0;                    // Minimum value of gauge, set on first data retrieval
    this.maximum = 0;                    // Maximum value of gauge, set on first data retrieval
    this.controllerURL = controllerURL;  // URL to retrieve controller HTML

    this.instrument_list = [];           // Filled by ajax request
    this.column_list = [];               // Filled by ajax request
    this.gauge = null;                   // The actual graph gauge object

    this.initializeAndBuild();
}

RealTimeGauge.prototype = Object.create(Widget.prototype);
RealTimeGauge.prototype.constructor = RealTimeGauge;

RealTimeGauge.prototype.buildControlDiv = function() {
    this.controlDiv.innerHTML = "RealTimeGauge";
    this.parentDiv.appendChild(this.controlDiv);

    this.loadDashboard();  // Loads the schematic's non-config parameters into RealTimeGauge

    var parameterizedURL = this.controllerURL + "?widget_name=real_time_gauge&widget_id=" + this.id;
    var validSchematic = false;
    if (this.schematic) {
        validSchematic = true;
    }
    this.ajaxLoadURL(this.controlDiv, parameterizedURL, validSchematic);
};

RealTimeGauge.prototype.ajaxLoadURL = function(element, url, loadDashboard) {
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
};

RealTimeGauge.prototype.loadDashboard = function () {
    // Load in non-configuration parameters.  Configuration parameters should load where config is built.
    var schematic = this.schematic;
    if (schematic) {
        this.instrumentId = schematic["instrumentId"];         // ID of currently selected instrument
        this.attribute = schematic["attribute"];               // Currently selected attribute of instrument
        this.controllerHidden = schematic["controllerHidden"]; // Boolean, true if controller is collapsed
        this.gaugeSize = schematic["gaugeSize"];               // Gauge size, 'small', 'medium' or 'large'
    } else {
        this.instrumentId = null;                              // Default: None selected
        this.attribute = null;                                 // Default: No attribute chosen
        this.controllerHidden = false;                         // Default: Full controller shown
        this.gaugeSize = "medium";                             // Default: medium sized gauge
    }
};

RealTimeGauge.prototype.initializeElements = function (loadDashboard) {
    var that = this;  // Substitution allows inline function assignments to reference 'this' rather than themselves

    if (loadDashboard) {
        document.getElementById("real-time-gauge-size-button-" + that.gaugeSize + "-" + that.id).checked = true;

        if (that.controllerHidden) {
            that.hideController();
        }
    }

    // Selector for which instrument the attributes are for
    // When changed should update all options for attribute selector
    var selector = document.getElementById("instrument-select-" + that.id);
    selector.onchange = function () { that.updateSelect(false); };

    // Button to copy Real Time Gauge widget. Disabled until data is graphed (or data will not properly copy)
    var copyButton = document.getElementById("real-time-gauge-copy-button-" + that.id);
    copyButton.onclick = function () { that.manager.copyWidget(that.id); };
    copyButton.disabled = true;
    copyButton.title = "Cannot Copy Until Gauge Displayed";

    // Button to remove Real Time Gauge widget
    var removeButton = document.getElementById("real-time-gauge-remove-button-" + that.id);
    removeButton.onclick = function () { that.remove(); };

    // Button to generate Real Time Gauge from data parameter controls
    var addButton = document.getElementById("real-time-gauge-add-button-" + that.id);
    addButton.onclick = function () { that.generateRealTimeGauge(); };

    // Data parameter controls: Hide and Reveal
    var hideButton = document.getElementById("real-time-gauge-hide-button-" + that.id);
    hideButton.onclick = function () { that.hideController(); };
    var revealButton = document.getElementById("real-time-gauge-reveal-button-" + that.id);
    revealButton.onclick = function () { that.revealController(); };

    // Config control binding: Show
    var configOpenButton = document.getElementById("config-open-button-" + that.id);
    configOpenButton.onclick = function () { that.showConfig(); };

    // Update attribute selector with options
    that.updateSelect(loadDashboard);

    if (loadDashboard) {
        that.generateRealTimeGauge();
    }
};

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
    var instrumentId = instrumentSelect.value;
    var instrumentValidColumns = this.columnList[instrumentId];
    instrumentValidColumns.sort();

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
};

RealTimeGauge.prototype.saveDashboard = function() {
    var configRepresentation = this.getConfigParameterRepresentations();
    data = {
        "controllerHidden": this.controllerHidden,
        "gaugeSize": this.gaugeSize,
        "instrumentId": this.instrumentId,
        "attribute": this.attribute,
        "configParameters": configRepresentation,
    };

    return {"type": "RealTimeGauge", "data": data};
};

RealTimeGauge.prototype.generateRealTimeGauge = function () {
    this.activeCounter = true;  // Activates the periodic update checks

    var gauge_div = document.getElementById("real-time-gauge-container-" + this.id);

    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var attributeInput = document.getElementById("attribute-input-" + this.id);

    var instrumentName = instrumentSelect.options[instrumentSelect.selectedIndex].text;
    this.instrumentId = instrumentSelect.value;

    this.attribute = attributeInput.value;

    // Enable copy button and change title to reflect functionality
    var copyButton = document.getElementById("real-time-gauge-copy-button-" + this.id);
    copyButton.disabled = false;
    copyButton.title = "Copy This Widget";

    // Set default gauge sizes
    var gaugeSize = '140%';     // % of gauge default size in relation to gauge div size. Re-sizes with gauge div.
    var gaugeHeight = 300;      // Gauge div height in pixels
    var gaugeWidth = 300;       // Gauge div width in pixels
    var gaugeFontSize = '24px';

    var gaugeSizeElement = document.querySelector('input[name="real-time-gauge-size-' + this.id + '"]:checked');
    if (gaugeSizeElement) {
        this.gaugeSize = gaugeSizeElement.value;
    }

    // Alter gauge element sizes to fit the selected size option.
    if (this.gaugeSize == "small") {
        gaugeHeight = 100;
        gaugeWidth = 150;
        gaugeFontSize = '12px';
    } else if (this.gaugeSize == "medium") {
        gaugeHeight = 200;
        gaugeWidth = 300;
        gaugeFontSize = '24px';
    } else if (this.gaugeSize == "large") {
        gaugeHeight = 400;
        gaugeWidth = 600;
        gaugeFontSize = '36px';
    }

    var that = this;  // Allows 'this' object to be accessed correctly within the XMLHttpRequest state change function

    // The request for the initial data also gets statistics for the entry, for the min/max of the gauge
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            recMessage = JSON.parse(xmlhttp.responseText);
            // TODO update last received here

            if (recMessage.length > 0) {
                // Only should be one value returned per attribute
                var responseDict = recMessage[0];

                var newTime = new Date(responseDict["data"]["time"] + "Z"); // Have to add 'Z' to return, indicates UTC
                that.lastReceived = newTime;
                that.updateLastReceived();

                that.updateTitle();

                that.minimum = responseDict["data"]["stats"]["min"];
                that.maximum = responseDict["data"]["stats"]["max"];
                that.currentValue = responseDict["data"]["value"]
                if (that.minimum == that.maximum) {
                    that.minimum -= 0.00000001;  // Little bit of a fudge factor to guarantee a range
                }

                var gaugeOptions = {  // Gauge by 'Highcharts'
                    chart: {
                        type: 'solidgauge',
                        height: gaugeHeight,
                        width: gaugeWidth
                    },

                    title: null,

                    pane: {
                        center: ['50%', '85%'],
                        size: gaugeSize,
                        startAngle: -90,
                        endAngle: 90,
                        background: {
                            backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                            innerRadius: '60%',
                            outerRadius: '100%',
                            shape: 'arc'
                        }
                    },

                    tooltip: {
                        enabled: false
                    },

                    yAxis: {
                        stops: [
                            [0.1, '#55BF3B'], //green
                            [0.5, '#DDDF0D'], //yellow
                            [0.9, '#DF5353']  //red
                        ],
                        lineWidth: 0,
                        minortickInterval: null,
                        tickAmount: 2,
                        title: {
                            y: 0
                        },
                        labels: {
                            y: 16,
//                            style: {
//                                fontSize: '8px'
//                            }
                        }
                    },

                    plotOptions: {
                        solidgauge: {
                            dataLabels: {
                               y: 5,
                               borderWidth: 0,
                               useHTML: true
                            }
                        }
                    }
                };

                that.gauge = Highcharts.chart(gauge_div, Highcharts.merge(gaugeOptions, {
                    yAxis: {
                        min: that.minimum,
                        max: that.maximum
                    },

                    credits: {
                        enabled: false
                    },

                    series: [{
                        name: instrumentName + ":" + that.attribute,
                        data: [that.currentValue],
                        dataLabels: {
                            format: '<div style="text-align:center;"><span style="font-size:' + gaugeFontSize + ';color:' +
                                ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                                   '<span style="font-size:12px;color:silver"></span></div>'
                        },
                    }]
                }));

            }
        }
    }

    var url = "/recent_values" +
              "?keys=" + this.attribute +
              "&instrument_id=" + this.instrumentId +
              "&do_stats=1";

    xmlhttp.open("POST", url, true);
    xmlhttp.send();

};

RealTimeGauge.prototype.updateLastReceived = function() {
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
    // Extra spaces for padding looks nice in the finished result
    document.getElementById("last-received-" + this.id).innerHTML = "&nbsp &nbsp " + lastReceivedUTC;

    var currentTime = new Date();
    var differenceMinutes = (currentTime - this.lastReceived) / (60000); // Difference starts in milliseconds

    if ((0 <= differenceMinutes) && (differenceMinutes < 5)) {
        statusBubble.className = "db_receive_status db_status_good";
    } else if ((5 <= differenceMinutes) && (differenceMinutes <= 15)) {
        statusBubble.className = "db_receive_status db_status_weak";
    } else {
        statusBubble.className = "db_receive_status db_status_dead";
    }
};

RealTimeGauge.prototype.triggerJob = function () {
    this.generateRealTimeGauge();
};

RealTimeGauge.prototype.updateTitle = function() {
    var titleDiv = document.getElementById("real-time-gauge-title-" + this.id);
    var instrumentSelect = document.getElementById("instrument-select-" + this.id);
    var instrumentName = instrumentSelect.options[instrumentSelect.selectedIndex].text;
    titleDiv.innerHTML = instrumentName + "<br>" + this.attribute;
};

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

// Histogram Section
// If schematic is null, loads up with defaults.  If schematic exists, loads the schematic and displays the histogram
function Histogram(manager, id, containerDiv, controllerURL, schematic) {
    Widget.call(this, manager, id, containerDiv, schematic);

    this.instrumentList = [];            // Filled by ajax request
    this.columnList = [];                // Filled by ajax request
    this.lastReceived = null;            // The timestamp for the last data received
    this.controllerURL = controllerURL;  // URL to retrieve controller HTML

    this.initializeAndBuild();
}

Histogram.prototype = Object.create(Widget.prototype);
Histogram.prototype.constructor = Histogram;

Histogram.prototype.buildDefaultParameters = function () {
    this.configParameters = [
        new ConfigInteger(this.id, "triggerTickNumber", "Update Frequency in Minutes (positive integer): ", 5, 1, null),
        new ConfigInteger(this.id, "binNumber", "Number of bins, '0' for automatic (positive integer): ", 0, 0, null),
        new ConfigInteger(this.id, "colorRed", "Graph Color: Red (Integer 0-255): ", 0, 0, 255),
        new ConfigInteger(this.id, "colorBlue", "Graph Color: Blue (Integer 0-255): ", 226, 0, 255),
        new ConfigInteger(this.id, "colorGreen", "Graph Color: Green (Integer 0-255): ", 50, 0, 255),
        new ConfigCheckbox(this.id, "convertToDB", "Convert Values to dB ", false),
    ];
};

Histogram.prototype.buildControlDiv = function () {
    this.controlDiv.innerHTML = "Histogram";
    this.parentDiv.appendChild(this.controlDiv);

    this.loadDashboard();  // Loads the schematic's non-config parameters into Histogram

    var parameterizedURL = this.controllerURL + "?widget_name=histogram&widget_id=" + this.id;
    // If there was a valid schematic, ajaxLoadUrl will load from the schematic rather than set defaults.
    var validSchematic = false;
    if (this.schematic) {
        validSchematic = true;
    }
    this.ajaxLoadURL(this.controlDiv, parameterizedURL, validSchematic);
};

Histogram.prototype.ajaxLoadURL = function(element, url, loadDashboard) {
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
};

Histogram.prototype.loadDashboard = function () {
    var schematic = this.schematic;
    if (schematic) {
        validSchematic = true;
        this.controllerHidden = schematic["controllerHidden"]; // Boolean, true if controller is collapsed

        this.startUTC = schematic["startUTC"];                 // Beginning time in UTC of 'custom' style time range
        this.endUTC = schematic["endUTC"];                     // End time in UTC of 'custom' style time range
        this.lowerLimit = schematic["lowerLimit"];             // Lower limit
        this.upperLimit = schematic["upperLimit"];             // Upper limit
        this.graphSize = schematic["graphSize"];               // Graph size, 'small', 'medium' or 'large'

        this.instrumentId = schematic["instrumentId"];         // ID of currently selected instrument
        this.attribute = schematic["attribute"];              // Selected attribute of instrument
        this.constraintStyle = schematic["constraintStyle"];   // Data constraint controls available, 'auto' or 'custom'
        this.constraintRange = schematic["constraintRange"];   // Sliding window range if style is 'auto':  'tenminute',
                                                               // 'hour', 'sixhour', 'day', 'week', 'fortnight', 'month'
    } else {
        this.controllerHidden = false;                         // Default: Full controller shown

        this.startUTC = "01/01/2000 00:00";                    // Default: Generic start time before our earliest data
        this.endUTC = "01/01/2170 00:00:00";                   // Default: In the future, covers large range of time
        this.lowerLimit = "";                                  // Default: No lower limit
        this.upperLimit = "";                                  // Default: No upper limit
        this.graphSize = "medium";                             // Default: Medium sized graph

        this.instrumentId = null;                              // Default: No instrument selected
        this.attribute = null;                                 // Default: No attribute chosen
        this.constraintStyle = "custom";                       // Default: Custom time ranges
        this.constraintRange = "sixhour";                      // Default: Six hours if constraint style set to 'auto'
    }
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

    // Config control binding: Show
    var configOpenButton = document.getElementById("histogram-config-open-button-" + that.id);
    configOpenButton.onclick = function () { that.showConfig(); };

    // Update attribute selector with options
    that.updateSelect(loadDashboard);

    if (loadDashboard) {
        that.generateHistogram()
    }
};

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
};

Histogram.prototype.saveDashboard = function () {
    var configRepresentation = this.getConfigParameterRepresentations();
    data = {
        "controllerHidden": this.controllerHidden,
        "startUTC": this.startUTC,
        "endUTC": this.endUTC,
        "lowerLimit": this.lowerLimit,
        "upperLimit": this.upperLimit,
        "graphSize": this.graphSize,
        "instrumentId": this.instrumentId,
        "attribute": this.attribute,
        "constraintStyle": this.constraintStyle,
        "constraintRange": this.constraintRange,
        "configParameters": configRepresentation,
    }

    return {"type": "Histogram", "data": data};
};

Histogram.prototype.generateHistogram = function () {
    this.activeCounter = true; // Activates the periodic update checks

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

    var that = this; // Allows 'this' object to be accessed correctly within the XMLHttpRequest state change functions.
                     // Inside the function 'this' references the function rather than the Histogram object we want.

    // Request for most recent data
    var lastReceivedXmlhttp = new XMLHttpRequest();

    lastReceivedXmlhttp.onreadystatechange = function() {
        //After the asynchronous request successfully returns
        if (lastReceivedXmlhttp.readyState == 4 && lastReceivedXmlhttp.status == 200)
        {
            recMessage = JSON.parse(lastReceivedXmlhttp.responseText);
            var recMessageKeys = Object.keys(recMessage);

            for (var i = 0; i < recMessageKeys.length; i ++)
            {
                if (recMessage[recMessageKeys[i]]["data"]["time"])
                {
                    var newTime = new Date(recMessage[recMessageKeys[i]]["data"]["time"] + "Z");
                    if (that.lastReceived) {
                        if (newTime > that.lastReceived)
                        {
                            that.lastReceived = newTime;
                        }
                    }
                    else
                    {
                        that.lastReceived = newTime;
                    }
                }
            }

            // Forces the HTML to update immediately, rather than after all data comes in
            that.updateLastReceived();
        }
    }

    var url = "/recent_values" +
              "?keys=" + this.attribute +
              "&instrument_id=" + this.instrumentId;

    lastReceivedXmlhttp.open("POST", url, true);
    //Send out the  request
    lastReceivedXmlhttp.send();

    // Request for histogram data
    var dataXmlhttp = new XMLHttpRequest();

    dataXmlhttp.onreadystatechange = function () {
        if (dataXmlhttp.readyState == 4 && dataXmlhttp.status == 200) {
            var response = JSON.parse(dataXmlhttp.responseText);

            delete that.lastReceived;

            if (response == "[]") {
                // There was an error.  This is probably a poor way to indicate errors from server->client
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

                // Local versions of config variables
                var convertToDB = that.getConfigParameter("convertToDB");
                var colorRed = that.getConfigParameter("colorRed");
                var colorGreen = that.getConfigParameter("colorGreen");
                var colorBlue = that.getConfigParameter("colorBlue");
                var binNumber = that.getConfigParameter("binNumber");

                field1 = field1.filter(isNotSentinel);
                if (convertToDB) {
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

                if (binNumber > 0) {
                    nbins = binNumber;
                } else {
                    nbins = Math.sqrt(field1.length);
                }

                // If upper and lower limits are set and valid, set the bin and range limits to them
                if (!isNaN(that.lowerLimit)
                    && !(that.lowerLimit === "")
                    && !isNaN(that.upperLimit)
                    && !(that.upperLimit === ""))
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
                            color: 'rgba(' + colorRed + ', ' + colorGreen + ', ' + colorBlue + ', 0.7)',
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
    dataXmlhttp.open("POST", url, true);

    //Send out the request
    dataXmlhttp.send();
};

Histogram.prototype.updateLastReceived = function () {
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
};


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
};

Histogram.prototype.triggerJob = function() {
    this.generateHistogram();
};

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
};

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
};

// DualHistogram Section
// If schematic is null, loads up with defaults.  If schematic exists, loads the schematic and displays the histogram
function DualHistogram(manager, id, containerDiv, controllerURL, schematic) {
    Widget.call(this, manager, id, containerDiv, schematic);

    this.instrumentList = [];            // Filled by ajax request
    this.columnList = [];                // Filled by ajax request
    this.lastReceived = null;            // The timestamp for the last data received
    this.controllerURL = controllerURL;  // URL to retrieve controller HTML

    this.initializeAndBuild();
}

DualHistogram.prototype = Object.create(Widget.prototype);
DualHistogram.prototype.constructor = DualHistogram;

DualHistogram.prototype.buildDefaultParameters = function () {
    var colorScaleOptions = [
        ["Hot", "Hot"],
        ["Jet", "Jet"],
        ["Earth", "Earth"],
        ["Blackbody", "Blackbody"],
        ["Portland", "Portland"],
        ["Electric", "Electric"],
        ["Picnic", "Picnic"],
        ["Greys", "Greys"],
        ["Greens", "Greens"],
        ["Blue Red", "Bluered"],
        ["Red Blue", "RdBu"],
        ["Yellow Orange Red", "YIOrRd"],
        ["Yellow Green Blue", "YIGnBu"],
    ];

    this.configParameters = [
        new ConfigInteger(this.id, "triggerTickNumber", "Update Frequency in Minutes (positive integer): ", 5, 1, null),
        new ConfigSelect(this.id, "colorScale", "Heat Map Color Scale: ", "Hot", colorScaleOptions),
        new ConfigInteger(this.id, "colorRed", "Graph Color: Red (Integer 0-255): ", 0, 0, 255),
        new ConfigInteger(this.id, "colorBlue", "Graph Color: Blue (Integer 0-255): ", 226, 0, 255),
        new ConfigInteger(this.id, "colorGreen", "Graph Color: Green (Integer 0-255): ", 50, 0, 255),
        new ConfigCheckbox(this.id, "convertToDB", "Convert Values to dB ", false),
    ];
};

DualHistogram.prototype.buildControlDiv = function () {
    this.controlDiv.innerHTML = "DualHistogram";
    this.parentDiv.appendChild(this.controlDiv);

    this.loadDashboard();  // Loads the schematic's non-config parameters into DualHistogram

    var parameterizedURL = this.controllerURL + "?widget_name=dual_histogram&widget_id=" + this.id;
    // If there was a valid schematic, ajaxLoadURL will load from the schematic rather than set defaults
    var validSchematic = false;
    if (this.schematic) {
        validSchematic = true;
    }
    this.ajaxLoadURL(this.controlDiv, parameterizedURL, validSchematic);
};

DualHistogram.prototype.ajaxLoadURL = function(element, url, loadDashboard) {
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

            that.initializeElements(loadDashboard);  //
        }

    };

    xmlHttp.open("GET", url, true); // true for asynchronous
    xmlHttp.send();
};

DualHistogram.prototype.loadDashboard = function () {
    // Load in non-configuration parameters.  Configuration parameters should load where config is built
    var schematic = this.schematic;
    if (schematic) {
        this.controllerHidden = schematic["controllerHidden"]; // Boolean, true if controller is collapsed

        this.startUTC = schematic["startUTC"];                 // Beginning time in UTC of 'custom' style time range
        this.endUTC = schematic["endUTC"];                     // End time in UTC of 'custom' style time range
        this.xLowerLimit = schematic["xLowerLimit"];           // X Axis lower limit, for 'attribute1'
        this.xUpperLimit = schematic["xUpperLimit"];           // X Axis upper limit, for 'attribute1'
        this.yLowerLimit = schematic["yLowerLimit"];           // Y Axis lower limit, for 'attribute2'
        this.yUpperLimit = schematic["yUpperLimit"];           // Y Axis upper limit, for 'attribute2'
        this.graphSize = schematic["graphSize"];               // Graph size, 'small', 'medium' or 'large'

        this.instrumentId = schematic["instrumentId"];         // ID of currently selected instrument
        this.attribute1 = schematic["attribute1"];             // First selected attribute of instrument, on X Axis
        this.attribute2 = schematic["attribute2"];             // Second selected attribute of instrument, on Y Axis

        this.constraintStyle = schematic["constraintStyle"];   // Data constraint controls available, 'auto' or 'custom'
        this.constraintRange = schematic["constraintRange"];   // Sliding window range if style is 'auto':  'tenminute',
                                                               // 'hour', 'sixhour', 'day', 'week', 'fortnight', 'month'
    } else {
        this.controllerHidden = false;                         // Default: Full controller shown

        this.startUTC = "01/01/2000 00:00";                    // Default: Generic start time before our earliest data
        this.endUTC = "01/01/2170 00:00:00";                   // Default: In the future, covers large range of time
        this.xLowerLimit = "";                                 // Default: No lower X limit
        this.xUpperLimit = "";                                 // Default: No upper X limit
        this.yLowerLimit = "";                                 // Default: No lower Y limit
        this.yUpperLimit = "";                                 // Default: No upper Y limit
        this.graphSize = "medium";                             // Default: Medium sized graph

        this.instrumentId = null;                              // Default: No instrument selected
        this.attribute1 = null;                                // Default: No X attribute chosen
        this.attribute2 = null;                                // Default: No Y attribute chosen
        this.constraintStyle = "custom";                       // Default: Custom time ranges
        this.constraintRange = "sixhour";                      // Default: Six hours if constraint style set to 'auto'
    }
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

        if (that.controllerHidden) {
            that.hideController();
        };
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
    addButton.onclick = function () { that.generateDualHistogram(); };

    // Secondary generate Histogram button inside the controller
    var controllerAddButton = document.getElementById("controller-histogram-add-" + that.id);
    controllerAddButton.onclick = function () { that.generateDualHistogram(); };

    // Data parameter controls: Hide and Reveal
    var hideButton = document.getElementById("histogram-hide-button-" + that.id);
    hideButton.onclick = function () { that.hideController(); };
    var revealButton = document.getElementById("histogram-reveal-button-" + that.id);
    revealButton.onclick = function () { that.revealController(); };

    // Config control binding: Show
    var configOpenButton = document.getElementById("histogram-config-open-button-" + that.id);
    configOpenButton.onclick = function () { that.showConfig(); };

    // Update attribute selector with options
    that.updateSelect(loadDashboard);

    if (loadDashboard) {
        that.generateDualHistogram()
    }
};

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
    removeOptions(attributeSelect2);
    var instrumentId = instrumentSelect.value;
    var instrumentValidColumns = this.columnList[instrumentId];
    instrumentValidColumns.sort();

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
};

DualHistogram.prototype.saveDashboard = function () {
    var configRepresentation = this.getConfigParameterRepresentations();
    data = {
        "controllerHidden": this.controllerHidden,
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
        "constraintStyle": this.constraintStyle,
        "constraintRange": this.constraintRange,
        "configParameters": configRepresentation,
    }
    return {"type": "DualHistogram", "data": data};
}

DualHistogram.prototype.generateDualHistogram = function () {
    this.activeCounter = true;  // Activates the periodic update checks

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

    var that = this; // Allows 'this' object to be accessed correctly within the XMLHttpRequest state change functions.
                     // Inside the function 'this' references the function rather than the Histogram object we want.

    // Request for most recent data
    var lastReceivedXmlhttp = new XMLHttpRequest();

    lastReceivedXmlhttp.onreadystatechange = function() {
        //After the asynchronous request successfully returns
        if (lastReceivedXmlhttp.readyState == 4 && lastReceivedXmlhttp.status == 200)
        {
            recMessage = JSON.parse(lastReceivedXmlhttp.responseText);
            var recMessageKeys = Object.keys(recMessage);

            for (var i = 0; i < recMessageKeys.length; i ++)
            {
                if (recMessage[recMessageKeys[i]]["data"]["time"])
                {
                    var newTime = new Date(recMessage[recMessageKeys[i]]["data"]["time"] + "Z");
                    if (that.lastReceived) {
                        if (newTime > that.lastReceived)
                        {
                            that.lastReceived = newTime;
                        }
                    }
                    else
                    {
                        that.lastReceived = newTime;
                    }
                }
            }

            // Forces the HTML to update immediately, rather than after all data comes in
            that.updateLastReceived();
        }
    }

    var url = "/recent_values" +
              "?keys=" + this.attribute1 + "," + this.attribute2 +
              "&instrument_id=" + this.instrumentId;

    lastReceivedXmlhttp.open("POST", url, true);
    //Send out the  request
    lastReceivedXmlhttp.send();

    // Request for the histogram data
    var dataXmlhttp = new XMLHttpRequest();

    dataXmlhttp.onreadystatechange = function () {
        if (dataXmlhttp.readyState == 4 && dataXmlhttp.status == 200) {
            var response = JSON.parse(dataXmlhttp.responseText);

            delete that.lastReceived;

            if (response == "[]") {
                // There was an error.  This is probably a poor way to indicate errors from server->client
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

                // Local versions of config variables
                var convertToDB = that.getConfigParameter("convertToDB");
                var colorRed = that.getConfigParameter("colorRed");
                var colorGreen = that.getConfigParameter("colorGreen");
                var colorBlue = that.getConfigParameter("colorBlue");
                var colorScale = that.getConfigParameter("colorScale");

                if (convertToDB) {
                    x = x.map(toDB);
                    y = y.map(toDB);
                }



                // If upper and lower limits are set and valid, set the bin and range limits to them
                // For X
                var xUseAutorange = true;
                var xRange = [0, 1]

                if (!isNaN(that.xLowerLimit)
                    && !(that.xLowerLimit === "")
                    && !isNaN(that.xUpperLimit)
                    && !(that.xUpperLimit === ""))
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
                    && !(that.yLowerLimit === "")
                    && !isNaN(that.yUpperLimit)
                    && !(that.yUpperLimit === ""))
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
                        color: 'rgb(' + colorRed + ', ' + colorGreen + ', ' + colorBlue + ')',
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
                    colorscale: colorScale,
                    reversescale: true,
                    showscale: false,
                    type: 'histogram2dcontour'
                };
                var trace3 = {
                    x: x,
                    name: 'x density',
                    marker: {color: 'rgb(' + colorRed + ', ' + colorGreen + ', ' + colorBlue + ')'},
                    yaxis: 'y2',
                    type: 'histogram'
                };
                var trace4 = {
                    y: y,
                    name: 'ydensity',
                    marker: {color: 'rgb(' + colorRed + ', ' + colorGreen + ', ' + colorBlue + ')'},
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
    dataXmlhttp.open("POST", url, true);

    //Send out the request
    dataXmlhttp.send();

};


DualHistogram.prototype.updateLastReceived = function () {
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
};

DualHistogram.prototype.triggerJob = function() {
    this.generateDualHistogram();
};


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
};

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
};

function InstrumentGraph(manager, id, containerDiv, controllerURL, genGraphURL, schematic) {
    Widget.call(this, manager, id, containerDiv, schematic);

    this.controllerURL = controllerURL;      // URL to retrieve controller HTML
    this.genGraphURL = genGraphURL;          // URL to generate graph data

    this.instrumentList = [];                // Filled by ajax request
    this.columnList = [];                    // Filled by ajax request
    this.nextAttributeId = 1;                // For making unique ids for new attributes. 0 already in template HTML
    this.graphData = [];                     // List of data points for the graph. Filled when the graph is generated
    this.graphTitle = null;                  // Title for they DyGraph
    this.dygraph = "";                       // Actual DyGraph object. None until first generated
    this.lastReceived = null;                // The timestamp for the last data received
    this.statsHidden = true;                 // Whether the extra statistics for the data (min, max, etc) are displayed

    // Statistic fields, only handled if statsEnabled is true when the graph is generated
    this.statsEnabled = false;               // 'true' indicates that extra statistics should be gathered and displayed
    this.selLowerDeviation = 0;              // Lower deviation for selected range
    this.selUpperDeviation = 0;              // Upper deviation for selected range
    this.minimum = 0;
    this.maximum = 0;
    this.median = 0;
    this.average = 0;
    this.stdDeviation = 0;                   // Standard deviation
    this.forceRedraw = false;                // When set to true, redraws the whole Dygraph.  Used to update stat lines
    this.statCount = 0; // Counter for requests without stat generation.

    this.selectPairList = []; // Holds the id, instrument selector element, and attribute selector element for each
                              // attribute row.  Allows for updating multiple attribute selectors.

    this.initializeAndBuild();
}

InstrumentGraph.prototype = Object.create(Widget.prototype);
InstrumentGraph.prototype.constructor = InstrumentGraph;

InstrumentGraph.prototype.buildDefaultParameters = function () {
    this.configParameters = [
        new ConfigInteger(this.id, "triggerTickNumber", "Update Frequency in Minutes (positive integer): ", 1, 1, null),
        new ConfigInteger(this.id, "statUpdateFrequency", "No. of Updates Before Statistics Update (positive integer: ",
                          1, 1, null),
        new ConfigInteger(this.id, "rollPeriod", "Graph Rolling Average Window (positive integer): ", 3, 1, null),
        new ConfigCheckbox(this.id, "convertToDB", "Convert Values to dB ", false),
    ];
};

InstrumentGraph.prototype.buildControlDiv = function () {
    this.controlDiv.innerHTML = "InstrumentGraph";
    this.parentDiv.appendChild(this.controlDiv);

    this.loadDashboard();  // Loads the schematic's non-config parameters into InstrumentGraph

    var parameterizedURL = this.controllerURL + "?widget_name=instrument_graph&widget_id=" + this.id;
    // If there was a valid schematic, ajaxLoadURL will load from the schematic rather than set defaults
    var validSchematic = false;
    if (this.schematic) {
        validSchematic = true;
    }
    this.ajaxLoadURL(this.controlDiv, parameterizedURL, validSchematic);
};

InstrumentGraph.prototype.ajaxLoadURL = function(element, url, loadDashboard) {
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
};

InstrumentGraph.prototype.loadDashboard = function () {
    // Load in non-configuration parameters.  Configuration parameters should load where config is built
    var schematic = this.schematic;
    if (schematic) {
        this.controllerHidden = schematic["controllerHidden"];  // Boolean, true if controller is collapsed
        this.instrumentId = schematic["instrumentId"];          // ID of currently selected instrument
        this.graphSize = schematic["graphSize"];                // Graph size, 'small', 'medium', or 'large'
        this.keys = schematic["attributes"];                    // List of attributes selected for current instrument
        this.constraintStyle = schematic["constraintStyle"];    // Type of controls selected, 'custom' or 'auto' range
        this.constraintRange = schematic["constraintRange"];    // Range when 'auto' control. 'tenminute', 'hour',
                                                                // 'sixhour', 'day', 'week', 'fortnight', 'month'
        this.lowerLimit = schematic["lowerLimit"];              // Lower y-value range bound.  Null means automatic
        this.upperLimit = schematic["upperLimit"];              // Upper y-value range bound.  Null means automatic

        // Each of these times requires a " UTC" on the end, or will assume local time when parsed
        this.beginningTime = new Date(schematic["beginningUTC"] + " UTC"); // Beginning time for next set of data. Moves
                                                                           // with each data set to get only new values
        this.endTime = new Date(schematic["endUTC"] + " UTC");  // End time for the next data request
        this.originTime = this.beginningTime; // Beginning time for whole graph.  Allows gathering stats on entire graph

    } else {
        this.controllerHidden = false;     // Default: Full controller shown
        this.instrumentId = null;          // Default: No instrument selected
        this.graphSize = "medium";         // Default: Medium sized graph
        this.keys = [];                    // Default: No attributes selected
        this.constraintStyle = "custom";   // Default: Custom time ranges
        this.constraintRange = "sixhour";  // Default: Six hours if constraint style set to 'auto'
        this.lowerLimit = null;            // Default: Automatic lower limit
        this.upperLimit = null;            // Default: Automatic upper limit

        this.beginningTime = null;         // Default: No defined start time
        this.endTime = null;               // Default: No defined end time
        this.originTime = null;            // Default: No defined origin time
    }

    this.statCount = this.getConfigParameter("statUpdateFrequency") - 1; // Guarantees the first request generates stats
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
        updateStartTime(that.id, 7);  // Defaults the graph beginning time to 7 days ago
        that.showConstraintCustom();  // Default is to show custom time controls
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

    // Config control binding: Show
    var configOpenButton = document.getElementById("inst-graph-config-open-button-" + that.id);
    configOpenButton.onclick = function () { that.showConfig(); };

    // Update attribute selector with options
    that.updateSelect(loadDashboard);

    if (loadDashboard) {
        that.generateInstrumentGraph();
    }
};

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
};

InstrumentGraph.prototype.saveDashboard = function() {
    var configRepresentation = this.getConfigParameterRepresentations();

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
        "beginningUTC": beginningUTC,
        "endUTC": endUTC,
        "graphSize": this.graphSize,
        "constraintStyle": this.constraintStyle,
        "constraintRange": this.constraintRange,
        "lowerLimit": this.lowerLimit,
        "upperLimit": this.upperLimit,
        "configParameters": configRepresentation,
    }
    return {"type": "InstrumentGraph", "data": data}
};

InstrumentGraph.prototype.generateInstrumentGraph = function(){
    // For this widget, this function is only for new graphs, with the regular updates being in their own function
    // TODO Manage this function better?  211 lines is a bit oppressive
    this.activeCounter = true;  // Activates the periodic update checks

    // Clear out old data.
    this.keys = [];
    this.beginningTime = null;
    this.endTime = null;
    this.originTime = null
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
    this.forceRedraw = false;
    this.statCount = this.getConfigParameter("statUpdateFrequency") - 1;

    var masterDiv = document.getElementById('instrument-graph-container-' + this.id);
    var constraintRange = document.querySelector('input[name="time-range-' + this.id + '"]:checked');
    if (constraintRange) {
        this.constraintRange = constraintRange.value;
    }

    // Set default sized variables, then get the chosen size from the radio set and update size if necessary
    this.graphSize = "medium";
    var graphWidth = 500;
    var graphHeight = 400;
    var graphSizeElement = document.querySelector('input[name="inst-graph-size-' + this.id + '"]:checked');

    if (graphSizeElement) {
        this.graphSize = graphSizeElement.value;
    }

    // Set sizes according to the selection
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

    // Get all of the attribute keys that are to be graphed
    var keyElems = document.getElementsByName("attribute-input-" + this.id);
    this.keys = [];
    for (var i = 0; i < keyElems.length; i++) {
        this.keys.push(keyElems[i].value);
    }

    // If the range is 'auto' (sliding window), generate the beginning time. If 'custom', pull string from element
    startStr = document.getElementById("datetime-input-start-" + this.id).value;
    if (this.constraintStyle == "auto") {
        this.originTime = this.getAutomaticBeginning();
        this.beginningTime = this.getAutomaticBeginning();
    } else {
        this.originTime = new Date(startStr + " UTC");     // Have to add " UTC" for parser, otherwise assumes local
        this.beginningTime = new Date(startStr + " UTC");  // Have to add " UTC" for parser, otherwise assumes local
    }

    // If the range is 'auto' (sliding window), end time for data is now. If 'custom', pull string from element
    endStr = document.getElementById("datetime-input-end-" + this.id).value;
    if (this.constraintStyle == "auto") {
        delete this.endTime;
        this.endTime = new Date();
    } else {
        this.endTime = new Date(endStr + " UTC");  // Have to add " UTC" for parser, otherwise assumes local
    }

    // Get y-axis range limits
    this.upperLimit = parseFloat(document.getElementById("inst-graph-upper-limit-" + this.id).value);
    this.lowerLimit = parseFloat(document.getElementById("inst-graph-lower-limit-" + this.id).value);

    // Clear Master Div
    while (masterDiv.firstChild) {
        masterDiv.removeChild(masterDiv.lastChild)
    }

    // Partition out divs.  TODO Wow this is ugly.  Change this to DOM
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

    // Get the most recent values for the selected attributes
    var that = this;
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        //After the asynchronous request successfully returns
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
        {
            recMessage = JSON.parse(xmlhttp.responseText);
            var recMessageKeys = Object.keys(recMessage);

            for (var i = 0; i < recMessageKeys.length; i ++)
            {
                if (recMessage[recMessageKeys[i]]["data"]["time"])
                {
                    var newTime = new Date(recMessage[recMessageKeys[i]]["data"]["time"] + "Z");
                    if (that.lastReceived) {
                        if (newTime > that.lastReceived)
                        {
                            that.lastReceived = newTime;
                        }
                    }
                    else
                    {
                        that.lastReceived = newTime;
                    }
                }
            }

            // Forces the HTML to update immediately, rather than after all data comes in
            that.updateLastReceived();
        }
    }

    var url = "/recent_values" + "?keys=" + this.keys + "&instrument_id=" + this.instrumentId;

    xmlhttp.open("POST", url, true);
    //Send out the  request
    xmlhttp.send();


    this.dygraph = "";
    this.updateInstrumentGraph();
};

InstrumentGraph.prototype.enableStats = function() {
    // Even though this is a Graph's 'enable stats' function, it was necessary to pass the graph to allow it
    // to be dynamically called by a button generated by the Graph.

    this.statsEnabled = true; // Graph will now display and track stats
    this.forceRedraw = true;  // Graph will be redrawn on next update to show std deviation lines

    // TODO Change to DOM
    this.dataDiv.innerHTML = '<b>Selection 95th Percentile:</b><br>' +
                               'Loading...' +
                               '<br><b>Entire Database:</b><br>' +
                               '<div class="graph_stats_half">Current: Loading...' +
                               '<br>Average: Loading...' +
                               '<br>Std. Dev.: Loading...' + '</div>' +
                               '<div class="graph_stats_half">Minimum: Loading...' +
                               '<br>Maximum: Loading...' +
                               '<br>Median: Loading...' + '</div>';

    this.updateInstrumentGraph();
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

    this.nextAttributeId += 1;  // Increment the nex added attribute's ID to keep them unique
};

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
};

InstrumentGraph.prototype.updateWithValues = function(values) {
    // Read in the various statistics for the Graph
    var upper = this.selUpperDeviation.toPrecision(4);
    var lower = this.selLowerDeviation.toPrecision(4);
    var minimum = this.minimum.toPrecision(4);
    var maximum = this.maximum.toPrecision(4);
    var median = this.median.toPrecision(4);
    var average = this.average.toPrecision(4);
    var stdDeviation = this.stdDeviation.toPrecision(4);

    // Filter out sentinel values
    values = values.filter(pairIsNotSentinel);

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

        // TODO Change this to DOM
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
        if (this.getConfigParameter("convertToDB")) {
            this.graphData = this.graphData.concat(values.filter(dataToDB));
        } else {
            this.graphData = this.graphData.concat(values);
        }
        this.forceRedraw = false;

        if (this.graphData.length > 0){
            delete this.lastReceived
            this.lastReceived = new Date(this.graphData[this.graphData.length - 1][0]) // Timestamp from most recent data

            yRange = [null, null];   // Default is automatic ranging

            // If the upper and lower limits are somewhat reasonable, use them instead for the y-axis range
            if (!isNaN(this.lowerLimit)
                && !(this.lowerLimit === "")
                && !isNaN(this.upperLimit)
                && !(this.upperLimit === ""))
            {
                yRange = [this.lowerLimit, this.upperLimit];
            }

            this.dygraph = new Dygraph(
            this.innerDiv,
            this.graphData,
            {
                title: this.graphTitle,
                rollPeriod: this.getConfigParameter("rollPeriod"),
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

            if (this.getConfigParameter("convertToDB")) {
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
};

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

};

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
                // There was an error.  This is probably a poor way to indicate errors from server->client
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
    //If stats are enabled, set 'doStats' every 'statUpdateFrequency' times
    if(this.statsEnabled) {
        this.statCount += 1;
        if (this.statCount >= this.getConfigParameter("statUpdateFrequency")) {
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
};

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

};

InstrumentGraph.prototype.triggerJob = function() {
    this.updateInstrumentGraph();
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

InstrumentGraph.prototype.toggleStatsHidden = function () {
    var statsHiddenButton = document.getElementById("stats-hidden-button-" + this.id);
    if (this.dataDiv.style.display == "none") {
        this.dataDiv.style.display = "";
        statsHiddenButton.innerHTML = "Hide"
    } else {
        this.dataDiv.style.display = "none";
        statsHiddenButton.innerHTML = "Stats";
    }
};

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
 if (value == -999 || value == -999.0){
     return false;
 } else {
     return true;
 }
};

function pairIsNotSentinel(value){
  // This version of the sentinel check assumes arrays where the second element is the value in question.
  if (value[1] == -999 || value[1] == -999.0) {
    return false;
  } else {
    return true;
  }
}

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

// http://stackoverflow.com/questions/14636536/how-to-check-if-a-variable-is-an-integer-in-javascript
function isInt(value) {
  if (isNaN(value)) {
    return false;
  }
  var x = parseFloat(value);
  return (x | 0) === x;
}
function GraphManager() {
    this.graph_index = 0;
    this.graphs = [];
    this.timer = setInterval(this.tick.bind(this), 60000)
};

GraphManager.prototype.tick = function(){
    for (i = 0; i < this.graphs.length; i++){
        // Only do updates on graphs that have not been removed from the HTML
        if (this.graphs[i].div.parentNode != null)
            this.graphs[i].tick()
    }
};

GraphManager.prototype.add_graph = function(keys, instrument_id, base_url, beginning_time, end_time, master_div) {
    this.graphs.push(new Graph(this, this.graph_index, keys, instrument_id, base_url, beginning_time, end_time, master_div));
    this.graph_index += 1;
};

GraphManager.prototype.get_count = function() {
    return this.graph_index;
};



function Graph(manager, id, keys, instrument_id, base_url, beginning_time, end_time, master_div) {
    this.manager = manager
    this.id = id;
    this.keys = keys;
    this.instrument_id = instrument_id;
    this.base_url = base_url;
    this.beginning_time = beginning_time;
    this.end_time = end_time;
    this.origin_time = beginning_time;
    this.graph_data = [];
    this.sel_lower_deviation = 0;
    this.sel_upper_deviation = 0;
    this.minimum = 0;
    this.maximum = 0;
    this.average = 0;
    this.std_deviation = 0;
    this.stat_frequency = 10;
    //Guarantees the first request gets stats
    this.stat_count = this.stat_frequency - 1;

    this.div_id = "graphdiv" + id;
    this.div = document.createElement('div');
    this.div.className = "instrument_dygraph";
    this.div.innerHTML = '<div id = "' + this.div_id + '-parent"><button type="button" onclick="remove_graph(this)">Remove Graph</button><br><div id="' + this.div_id + '" style="width: 400px; height: 250px; display: inline-block;"></div></div>'

    this.data_div_id = "datadiv" + id;
    this.data_div = document.createElement('div');

    //This only fills in if there is only one attribute for the graph
    if (String(this.keys).split(",").length ==1){
        this.data_div.innerHTML = '<b>Selection:</b><br>' +
                                  'BLUE= Upper bound: Loading...' +
                                  '<br>RED = Lower bound: Loading...' +
                                  '<br><i>2 standard deviations for selected set</i>' +
                                  '<br><b>Entire Database</b>' +
                                  '<br>Current Value: Loading...' +
                                  '<br>Minimum: Loading...' +
                                  '<br>Maximum: Loading...' +
                                  '<br>Average: Loading...' +
                                  '<br>Standard Deviation: Loading...';
    }

    master_div.insertBefore(this.div, master_div.firstChild);
    //Appending data_div onto this div assures that it will be removed with the graph if the graph is removed
    this.div.firstChild.appendChild(this.data_div)
    this.inner_div = document.getElementById(this.div_id);
    this.inner_div.innerHTML = "<p><br><i>Loading Graph...</i></p>"

    this.dygraph = "";

    this.request_values(keys, beginning_time, end_time, beginning_time);

};

Graph.prototype.update_with_values = function(values) {
    //Read in the upper and lower deviations
    var upper = this.sel_upper_deviation;
    var lower = this.sel_lower_deviation;
    var minimum = this.minimum;
    var maximum = this.maximum;
    var average = this.average;
    var std_deviation = this.std_deviation;

    if (String(this.keys).split(",").length == 1) {
        //Add extra information if there is only one attribute

        //Get the current value (either the most recent incoming value, or if there are no incoming values,
        //the most recent value currently stored.

        var current = 0
        if (values.length > 0) {
            current = values[values.length - 1][1];
        }
        else if (this.graph_data.length > 0) {
            current = this.graph_data[this.graph_data.length - 1][1];
        }

        this.data_div.innerHTML = '<b>Selection:</b><br>' +
                                  'BLUE= Upper bound: ' + upper +
                                  '<br>RED = Lower bound: ' + lower +
                                  '<br><i>2 standard deviations</i>' +
                                  '<br><b>Entire Database</b>' +
                                  '<br>Current Value: ' + current +
                                  '<br>Minimum: ' + minimum +
                                  '<br>Maximum: ' + maximum +
                                  '<br>Average: ' + average +
                                  '<br>Standard Deviation: ' + std_deviation;


        //Callback handles drawing the deviation lines on the graph.
        deviation_callback = function(canvas, area, g) {
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
        deviation_callback = null;
    }
    if (this.graph_data.length >= 0) {
        //switch from <= 0 to >= 0, now redraws graph every time, keeps selection's deviation range current.
        if (values.length > 0){
            this.graph_data = this.graph_data.concat(values)
            delete this.dygraph;
            this.dygraph = new Dygraph(
            this.inner_div,
            this.graph_data,
            {
                rollPeriod: 3,
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
                underlayCallback: deviation_callback
            });

        }
        else {
            this.inner_div.innerHTML = "<p>No Data Available<br>Verify that the start and end times are valid and formatted correctly.</p>";
        }
    }
    else
    {
        if (values.length > 0) {
            this.graph_data = this.graph_data.concat(values);
            this.dygraph.updateOptions({ 'file': this.graph_data });
        }
    }
    //Set the beginning time for this graph to now.  This means updating the graph will only add new values.
    //Need to use the last entry from the database, since local clock may be off
    delete this.beginning_time;
    this.beginning_time = new Date(this.graph_data[this.graph_data.length - 1][0]);
    //Tiny increment so it doesnt pull the same data repeatedly
    this.beginning_time.setUTCSeconds(this.beginning_time.getUTCSeconds() + 1);
}

Graph.prototype.tick = function(){
    //Only update if the last update finished before the specified end time
    if (this.beginning_time <= this.end_time) {
        this.request_values(this.keys, this.beginning_time, this.end_time, this.origin_time);
    }
};

Graph.prototype.request_values = function(keys, beginning_time, end_time, origin_time) {
    //Gets the next set of data values
    graph_data = "";
    var this_graph = this;
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        //After the asyncronous request successfully returns
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
        {
            //Pull out the response text from the request
            var rec_message = JSON.parse(xmlhttp.responseText);
            for (i = 0; i < rec_message['data'].length; i ++)
            {
                // Have add a Z to the given UTC time to convert in JavaScript
                rec_message['data'][i][0] = new Date(rec_message['data'][i][0] + "Z");
            }

            this_graph.sel_upper_deviation = rec_message['upper_deviation'];
            this_graph.sel_lower_deviation = rec_message['lower_deviation'];
            if (rec_message['min']){
                this_graph.minimum = rec_message['min'];}
            if (rec_message['max']){
                this_graph.maximum = rec_message['max'];}
            if (rec_message['average']){
                this_graph.average = rec_message['average'];}
            if (rec_message['average']){
                this_graph.std_deviation = rec_message['std_deviation'];}

            this_graph.update_with_values(rec_message['data']);
        }
    };
    //Send JSON POST XMLHTTPRequest to generator controller.
    //Include keys for the generated graph, and convert start and end datetimes to a valid argument format
    //Assume input is in UTC

    var origin_utc = origin_time.toUTCString();
    var start_utc = beginning_time.toUTCString();
    var end_utc = end_time.toUTCString();

    var do_stats = 0;
    //If there is only one key, set 'do_stats' every 'this.stat_frequency' times
    if(String(this.keys).split(',').length == 1) {
            this.stat_count += 1;
            if (this.stat_count >= this.stat_frequency) {
                this.stat_count = 0;
                do_stats = 1;
            }
        }

    var url = this.base_url + "?keys=" + keys + "&instrument_id=" + this.instrument_id + "&start=" + start_utc + "&end=" + end_utc + "&origin=" + origin_utc + "&do_stats=" + do_stats;
    xmlhttp.open("POST", url, true);

    //Send out the request
    xmlhttp.send();

};

function remove_graph(e)
{
    elem = e.closest("div").parentNode;
    elem.parentNode.removeChild(elem);
};
function GraphManager() {
    this.graph_index = 0;
    this.graphs = [];
    this.timer = setInterval(this.tick.bind(this), 60000)
};

GraphManager.prototype.tick = function(){
    for (i = 0; i < this.graphs.length; i++){
        if (this.graphs[i].div.childElementCount > 0)
            this.graphs[i].tick()
        else
            this.graphs.splice(i, 1)
    }
};

GraphManager.prototype.add_graph = function(key, instrument_id, base_url, beginning_time, end_time, master_div) {
    this.graphs.push(new Graph(this, this.graph_index, key, instrument_id, base_url, beginning_time, end_time, master_div));
    this.graph_index += 1;
};

GraphManager.prototype.get_count = function() {
    return this.graph_index;
};



function Graph(manager, id, key, instrument_id, base_url, beginning_time, end_time, master_div) {
    this.manager = manager
    this.id = id;
    this.key = key;
    this.instrument_id = instrument_id;
    this.base_url = base_url;
    this.beginning_time = beginning_time;
    this.end_time = end_time;
    this.graph_data = [];

    this.div_id = "graphdiv" + id;
    this.div = document.createElement('div');
    this.div.innerHTML = '<div id = "' + this.div_id + '-parent"><div id="' + this.div_id + '" style="width: 400px; height: 250px; display: inline-block;"></div><br><button type="button" onclick="remove_graph(this)">Remove Graph</button></div>'

    master_div.insertBefore(this.div, master_div.firstChild);
    this.inner_div = document.getElementById(this.div_id);

    this.dygraph = "";

    this.request_values(key, beginning_time, end_time);
};

Graph.prototype.update_with_values = function(values) {
    if (this.graph_data.length <= 0) {
        if (values.length > 0){
            this.graph_data = this.graph_data.concat(values)
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

                title: this.key,
                labelsUTC: true,
                labels: ["Time", ""],
                axes: {
                    ticker: function (a, b, pixels, opts, dygraph, vals) {
                                return Dygraph.getDateAxis(a, b, Dygraph.ANNUAL, opts, dygraph);
                    }
                }
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
    this.beginning_time = new Date(this.graph_data[this.graph_data.length - 1][0]);
    //Tiny increment so it doesnt pull the same data repeatedly
    this.beginning_time.setUTCSeconds(this.beginning_time.getUTCSeconds() + 1);
}

Graph.prototype.tick = function(){
    //Only update if the last update finished before the specified end time
    if (this.beginning_time <= this.end_time) {
        this.request_values(this.key, this.beginning_time, this.end_time);
    }
};

Graph.prototype.request_values = function(key, beginning_time, end_time) {
    graph_data = "";
    var this_graph = this;
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        //After the asyncronous request successfully returns
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
        {
            //Pull out the response text from the request
            var rec_message = JSON.parse(xmlhttp.responseText);
            var values = []
            if (rec_message["x"].length > 0)
            {
                for (i = 0; i < rec_message["x"].length; i ++)
                {

                    if (!(rec_message["y"][i] === null))
                        values.push([new Date(rec_message["x"][i] + "Z"), rec_message["y"][i]]);
                }
            }

            this_graph.update_with_values(values);
        }
    };
    //Send JSON POST XMLHTTPRequest to generator controller.
    //Include keys for the generated graph, and convert start and end datetimes to a valid argument format
    //Assume input is in UTC

    var start_utc = beginning_time.toUTCString();
    var end_utc = end_time.toUTCString();

    var url = this.base_url + "?key=" + key + "&instrument_id=" + this.instrument_id + "&start=" + start_utc + "&end=" + end_utc;
    xmlhttp.open("POST", url, true);

    //Send out the request
    xmlhttp.send();

};

function remove_graph(e)
{
    id = e.closest("div").id;
    elem = document.getElementById(id);
    elem.parentNode.removeChild(elem);
};
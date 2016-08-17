
function remove_graph(e)
{
    elem = e.closest("div").parentNode;
    elem.parentNode.removeChild(elem);
};

function isSentinel(value){
 if (value == -999){
     return false;
 }else{
     return true;
 }
};

function create_histogram_div(div, instrument_id, instrument_name, field, start_utc, end_utc ) {
    var x = [];
    var data1;
    var trace1;
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var response = JSON.parse(xmlhttp.responseText);
            var field1 = response.data.map(i => i[1]);
            //field1 = field1.filter(isNaN)
            field1.filter(isSentinel)
            nbins = Math.sqrt(field1.length);
            var data = [
                {
                    x: field1,
                    type: 'histogram',
                    marker: {
                        color: 'rgba(0, 50, 226, 0.7)',
                    },
                    nbinsx : nbins,
                }]

        var layout = {
            showlegend: false,
            autosize: true,
            margin: {t: 50, r: 50, b: 50, l: 50, pad:10},
            hovermode: 'closest',
            bargap: 0,
            title: instrument_name + ":" + field,
            xaxis: {
                //domain: [-20, 30],
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


var url = "/generate_instrument_graph" + "?keys=" + field+ "&instrument_id=" + instrument_id + "&start=" + start_utc + "&end=" + end_utc;
xmlhttp.open("POST", url, true);

//Send out the request
xmlhttp.send();

}
;
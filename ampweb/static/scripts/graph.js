//Global Variables
    var source = "";  //The source amplet
    var dest = "";  //The destination amplet/site
    var graph = "";  //Graph currently displayed
    var specificstart = "";  //Start timestamp on the detail graph
    var specificend = "";  //End timestamp on the detail graph
    var generalstart = "";  //Start timestamp on the summary graph
    var generalend = "";  //End timestamp on the summary graph


function changeGraph(graph){
    //If source + dest are not set, stop
    if(source == "" || dest == ""){
        $("#graph").empty();
        return;
    }
    
    //Clear current graph
    $("#graph").html("");

    //Based on graph, display
    switch(graph.graph){
        case "Latency":
            drawLatencyGraph(graph);
            break;
        case "Jitter":
            drawLatencyGraph(graph);
            break;
        case "Loss":
            drawLatencyGraph(graph);
            break;
        case "Path":
            drawLatencyGraph(graph);
            break;
    }

    var graphurl = graph.graph;
    if ( graph.specificstart != undefined ) {
        graphurl += "/" + graph.specificstart;
        if ( graph.specificend != undefined ) {
            graphurl += "/" + graph.specificend;
            if ( graph.generalstart != undefined ) {
                graphurl += "/" + graph.generalstart;
                if ( graph.generalend != undefined ) {
                    graphurl += "/" + graph.generalend;
                }
            }
        }
    }
    
    //Update the url
    goToURL({"name": "graph", "value": graphurl});
}

function goToURL(object){

    //Initialize/Set variables
    var base = window.location.toString().split("graph")[0] + "graph/";
    var urlparts = [];

    //Is a source set?
    var elements = [];
    window.location.toString().split("graph")[1].toString().split("/").forEach(
        function(p){
            if(p != ''){
                elements.push(p);
            }
        });

    //0-Source, 1-Dest, 2-Graph, 3-StartTime, 4-Endtime
    urlparts[0] = elements[0] + "/";
    urlparts[1] = elements[1] + "/";
    urlparts[2] = elements[2] + "/";
    urlparts[3] = elements[3] + "/";
    urlparts[4] = elements[4] + "/";

    //Sets based on users decision
    switch(object.name){
        case "source":
            urlparts[0] = object.value + "/";
            for(var i = 1; i < urlparts.length; i++){
                urlparts[i] = "undefined/";
            }
            break;

        case "dest":
            urlparts[1] = object.value + "/";
            for(var i = 2; i < urlparts.length; i++){
                urlparts[i] = "undefined/";
            }
            break;

        case "graph":
            urlparts[2] = object.value + "/";
            for(var i = 3; i < urlparts.length; i++){
                urlparts[i] = "undefined/";
            }
            break;
    }

    //Build URL
    var url = base;
    for(var i = 0; i < urlparts.length; i++){
        if(urlparts[i] != "undefined/" && urlparts[i] != "--SELECT--/"){
                url += urlparts[i];
            }else{
                break;
            }
    }

    window.history.pushState("object or string", "THIS IS A TITLE", url);
}



////
//Updates page based on object (generally a dropdown)
////
function pageUpdate(object) {

    //Set the global variables
    switch(object.name){
        case "source":
            if(source == "--SELECT--")
                source = "";
            else
                source = object.value;
            break;
        case "dest":
            if(dest == "--SELECT--")
                dest = "";
            else
                dest = object.value;
            break;
        case "graph":
            graph = object.value;
            break;
        case "starttime":
            starttime = object.value;
            break;
        case "endtime":
            starttime = object.value;
            break;
    }

    //Second Dropdown
    if(object.name == "source" && object.value != "--SELECT--"){
        //Get data, update box
        $.ajax({url: "/data/" + source + "/", success: function(data){
            data = data.response.sites;                     
            //Clear current destinations
            $("#dest").empty();
            $("#dest").append("<option>--SELECT--</option>");
            $.each(data, function(index, dst){
                $("<option>" + dst + "</option>").appendTo("#dest");
            });
        //Enable second dropdown
        $("#dest").removeAttr('disabled');
        }});
    }

    //Reset second dropdown
    if(object.name == "source" && object.value == "--SELECT--"){
        $('#dest').empty();
        $('<option>--SELECT--</option>').appendTo("#dest");
        $('#dest').attr('disabled', '');
    }

    //Update url
    goToURL(object);
}

///////////////////////////////////////////////////////////////////////////////
//                        Latency Graph                                      //
///////////////////////////////////////////////////////////////////////////////
function drawLatencyGraph(graph){
    //Get current unix timestamp
    var endtime = Math.round((new Date()).getTime() / 1000);
    //1 day ago
    var starttime = endtime - (60 * 60 * 24);
    
    //Where to put the graph + where to get the data from
    var container = $("#graph");
    var url = "/data/" + source + "/" + dest + "/icmp/0084/" + starttime + "/" +  endtime;

    //Make the request for data
    $.getJSON(url, function(da){
        //Get raw data
        var rawdata = da.response.data;

        //Extract Data
        var x = [], y = [],
            actualdata = [x, y];
        for(var i = 0; i < rawdata.length; i++){
            x.push(rawdata[i].time);
            y.push(rawdata[i].rtt_ms.mean);
        } 
        //Draw graph
        Latency({summarydata: actualdata, detaildata: actualdata, container: container});
    });
}

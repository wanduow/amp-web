/* Global Variables */
var stream = "";
var sumscale = "";
var graph = "";  /* Graph currently displayed */
var endtime = Math.round((new Date()).getTime() / 1000); /* End timestamp on the detail graph */
var starttime = endtime - (24 * 60 * 60 * 2);  /* Start timestamp of detail graph */
/* assume that the api is available on the same host as we are */
var host = location.protocol + "//" + location.hostname +
    (location.port ? ":" + location.port : "");

var generalstart = "";
var generalend = "";
var request; /* save an ongoing ajax request so that it can be cancelled */

/* This is a map to store mappings to stream ids to the appropriate dropdown
 * selections for those streams. We use this to ensure the dropdown boxes are
 * set correctly if the user uses the History to move between graphs
 */
var stream_mappings = new Array();

/*
 * Variables for processed data. These need to be global so that data
 * can be passed from ajax function to ajax function.
 */
var x = [],
    y = [],
    detailData = [x, y],
    x2 = [],
    y2 = [],
    summaryData = [x2, y2],
    rawDetailData,
    rawSummaryData;

/* Updates the displayed graph(s) in response to some user action, e.g.
 * changing the selected area or entering a new URL */
function changeGraph(input) {
    /* TODO move the styles to CSS */
    var graphStyle = "border: 3px solid #0F0F0F; " +
	"border-left: 1px solid white; " +
	"background-color: white;";

    if (input.stream != undefined) {
        stream = input.stream;
    }

    /* If source + dest are not set, stop */
    if (stream == "") {
        $("#graph").empty();
        $("#sparklineLatency").empty();
        $("#sparklineLoss").empty();
        $("#sparklineJitter").empty();
        return;
    }

    /* abort any outstanding requests for graphs */
    if ( request ) {
        request.abort()
    }
    /* Clear current graph */
    $("#graph").empty();
    $("#graph").append("<p>Loading...</p>");

    /* If undefined, set as blank */
    if (input == undefined) {
        input = {graph: "latency" };
    }

    /* Resets the styling on the tabs */
    $("#latency").removeAttr("style");
    $("#jitter").removeAttr("style");
    $("#loss").removeAttr("style");
    $("#path").removeAttr("style");

    /* Based on graph, display */
    switch (input.graph) {
        case "latency":
            graph = "latency";
            drawLatencyGraph(input);
            $("#latency").attr("style", graphStyle);
            break;
        case "jitter":
            graph = "jitter";
            drawJitterGraph(input);
            $("#jitter").attr("style", graphStyle);
            break;
        case "loss":
            graph = "loss";
            drawLossGraph(input);
            $("#loss").attr("style", graphStyle);
            break;
        case "path":
            tracerouteGraph();
            $("#path").attr("style", graphStyle);
            break;
        case "smokeping":
            graph = "smokeping";
            drawSmokepingGraph(input);
            $("#smokeping").attr("style", graphStyle);
            break;
        case "muninbytes":
            graph = "muninbytes";
            drawMuninbytesGraph(input);
            $("#muninbytes").attr("style", graphStyle);
            break;
    }
    
    /* Draw sparklines */
    if ( input.graph != "smokeping" && input.graph != "muninbytes" ) {
	    drawSparkLines();
    }
    
    /* We've drawn a graph for a stream -- ensure we remember what dropdown
     * values belong to that stream */
    saveDropdownState();
}

/* Updates the page title to match the graph being currently displayed.
 */
function setTitle() {

    $.ajax({
        url: "/api/_streaminfo/" + graph + "/" + stream + "/",
        success: function(data) {
            var graphtitle = "ampweb2 - " + data["name"];
            
            /* Despite appearances, the title argument of History.replaceState 
             * isn't guaranteed to have any effect on the current page title
             * so we have to explicitly set the page title */
            document.getElementsByTagName('title')[0].innerHTML = graphtitle;

            /* Change the current entry in the History to match our new title */
            History.replaceState(History.getState().data, graphtitle, 
                    History.getState().url);
        }
    });

}

/* Updates the page URL to match the parameters of the current graph */
function updatePageURL(changedGraph) {
    var base = $(location).attr('href').toString().split("graph")[0] + "graph/";
    
    var newurl = base + graph + "/" + stream + "/";

    /* XXX I'm so sorry for this code */
    if (sumscale != "") {
        newurl += sumscale + "/";
        if (starttime != "") {
            newurl += starttime + "/";

            if (endtime != "") {
                newurl += endtime + "/";
            }
        }
    }

    /* If this function has been called as a result of the graph showing a
     * different stream (e.g. the user has selected a new stream via the
     * dropdowns), we need to push a new History entry and generate a new
     * title.
     */
    if (changedGraph) {
        History.pushState(null, "ampweb2 - Loading", newurl);
        setTitle();
    } else {
        /* Otherwise, just replace the existing URL with the new one */
        History.replaceState(History.getState().data, History.getState().title, newurl);
    }
}

/* Updates the global time variables that describe the display areas of both
 * the detailed and summary graphs. Used by the graph templates to tell us
 * which area the user has selected so we can update our internal state
 * accordingly.
 */
function updateSelectionTimes(times) {

    if (times.specificstart != undefined)
        starttime = times.specificstart;
    if (times.specificend != undefined)
        endtime = times.specificend;

    /* Update the URL using the current graph / stream info */
    /* Our stream hasn't changed so we can reuse our last title */
    newurl = updatePageURL(false);

}

/*
 * Grabs the current URL and sets our internal parameters to match the values
 * (presumably) provided by the user, i.e. if the provided URL contains start
 * and end times, we should assume that those are what the user wants to see!
 */
function decomposeURLParameters() {
    /* Get url */
    var url = $(location).attr('href').toString();
    url = url.replace("#", "");
    var urlparts = url.split("graph")[1].split("/");

    /* Get rid of leading blank */
    urlparts.splice(0, 1);

    /* Make up array to at least 7 */
    for (var i = 0; i <= 6; i++) {
	    urlparts.push("");
    }

    /* Set variables */
    graph = urlparts[0];
    stream = urlparts[1];
    
    
    if (urlparts[2] == "") {
        sumscale = 30;
    } else {
        sumscale = urlparts[2];
    }
    
    now = Math.round((new Date()).getTime() / 1000);

    /* Make sure we set sensible defaults if there is no specific time period
     * provided.
     */
    if ( urlparts[3] == "" ) {
        starttime = Math.round((new Date()).getTime() / 1000) - 
                (60 * 60 * 24 * 2);
    } else {
        starttime = parseInt(urlparts[3]);
    }

    if ( urlparts[4] == "" ) {
        endtime = now;
    } else {
        endtime = parseInt(urlparts[4]);
    }

    calcDefaultSummaryRange(starttime, endtime, now, sumscale);
}


function calcDefaultSummaryRange(start, end, now, scale) {

    /* Number of 'months' needed to cover the entire detailed graph */
    range = (Math.floor((end - start) / (60 * 60 * 24 * scale)) + 1);
    range = range * scale * 24 * 60 * 60;

    unselected = range - (end - start);

    /* A 75-25 split of the remaining space available in the summary seems a
     * decent starting point */
    trailing = unselected * 0.25;
    preceding = unselected * 0.75;

    /* If we don't have enough data to show the full amount of 'trailing' 
     * data, then we should try and show more preceding data instead. This
     * will avoid empty sections in the summary graph */
    if (end + trailing > now) {
        overage = (end + trailing - now);
        trailing -= overage;
        preceding += overage;
    }

    generalstart = start - preceding;
    generalend = end + trailing;

}

function generateSummaryXTics(start, end) {

    var ticlabels = [];
    var startdate = new Date(start * 1000.0);
    var enddate = new Date(end * 1000.0);
    
    startdate.setHours(0);
    startdate.setMinutes(0);
    startdate.setSeconds(0);
    startdate.setMilliseconds(0);

    var days = (end - start) / (60 * 60 * 24);
    var dayskip = Math.floor(days / 15);

    if (dayskip == 0)
        dayskip = 1;

    var ticdate = startdate;
    var nextlabel = startdate;

    while (ticdate.getTime() <= enddate.getTime()) {
            
        var xtic = ticdate.getTime();
        var parts = ticdate.toDateString().split(" ");

        if (ticdate.getTime() == nextlabel.getTime()) {
            ticlabels.push([xtic, parts[1] + " " + parts[2]]);
            nextlabel = new Date(ticdate.getTime() + (dayskip * 24 * 60 * 60 * 1000));
        }
        else {
            ticlabels.push([xtic, ""]);
        }

        ticdate = new Date(ticdate.getTime() + (24 * 60 * 60 * 1000));
        
        /* Jumping ahead a fixed number of hours is fine, right up until you
         * hit a daylight savings change and now you are no longer aligned to
         * midnight. I don't trust arithmetic on the hours field, so I'm going
         * to just make sure I'm in the right day and set hours back to zero.
         */
        if (ticdate.getHours() != 0) {
            if (ticdate.getHours() < 12) {
                /* Round down */
                ticdate.setHours(0);
            } else {
                /* Round up */
                ticdate = new Date(ticdate.getTime() + (24 * 60 * 60 * 1000));
                ticdate.setHours(0);
            }
        }
        
        if (nextlabel.getHours() != 0) {
            if (nextlabel.getHours() < 12) {
                /* Round down */
                nextlabel.setHours(0);
            } else {
                /* Round up */
                nextlabel = new Date(nextlabel.getTime() + (24 * 60 * 60 * 1000));
                nextlabel.setHours(0);
            }
        }

    }
    return ticlabels;
}

/* 
 * Calls the appropriate startup function for any selection widgets on the
 * page.
 */
function initSelectors() {
    
    switch(graph) {
        case "smokeping":
            initSmokepingDropdown(stream);
            break;
        case "muninbytes":
            initMuninDropdown(stream);
            break;
    }
}

/* Returns the currently selected values from the dropdown boxes */
function getDropdownState() {
    switch (graph) {
        case "smokeping":
            return getSmokepingDropdownState();
        case "muninbytes":
            return getMuninDropdownState();
    }
}

/* Reverts the state of the dropdown boxes to match the selections from a
 * previous stream id */
function revertDropdowns(streamid) {
   
    var key = "strm" + streamid;
    var state = stream_mappings[key];
    
    switch (graph) {
        case "smokeping":
            setSmokepingDropdownState(state);
            break
        case "muninbytes":
            setMuninDropdownState(state);
            break;
    }
}

/* Saves the current dropdown box state into our stream->dropdowns map */
function saveDropdownState() {
    var lastdropstate = getDropdownState();
    var key = "strm" + stream;

    stream_mappings[key] = lastdropstate;
}

/*
 * Updates page based on a selection event occurring in a dropdown menu.
 */
function dropdownCallback(origin, basetype) {

    switch(basetype) {
        case "smokeping":
            smokepingDropdownCB(origin);
            break;
        case "muninbytes":
            muninDropdownCB(origin);
            break;
    }
}

/*
 * Templates for Sparklines
 */
var sparkline_ts_template = {
            type: "line",
            disableInteraction: "true",
            disableTooltips: "true",
            width: "15em",
            height: "1.5em",
            chartRangeMin: 0,
            spotColor: false,
            minSpotColor: false,
            maxSpotColor: false,
            highlightSpotColor: false,
            highlightLineColor: false
        };
/*
 *  Updates the sparklines
 *  FIXME: Process on the server side and send the raw data back to the clients
 */
function drawSparkLines() {
    /* Initial Setup For data fetching */
    var endtime = Math.round((new Date()).getTime() / 1000);
    var starttime = endtime - (60 * 60 * 24);
    var url = "/api/" + source + "/" + dest + "/icmp/0084/" + starttime +
        "/" +  endtime + "/900";

    /* Send request for data */
    $.getJSON(url, function(input) {

        /* Latency */
        var rawdata = input.response.data;
        var actualdata = [];
        for (var i = 0; i < rawdata.length; i++) {
            if (rawdata[i].rtt_ms.loss != 1) {
                actualdata.push(rawdata[i].rtt_ms.mean);
            }
        }
        $("#sparklineLatency").sparkline(actualdata, sparkline_ts_template);

        /* Jitter */
        actualdata = [];
        for (var i = 0; i < rawdata.length; i++) {
            actualdata.push(rawdata[i].rtt_ms.jitter);
        }
        $("#sparklineJitter").sparkline(actualdata, sparkline_ts_template);

        /* Loss */
        actualdata =[];
        for (var i = 0; i < rawdata.length; i++) {
            actualdata.push(rawdata[i].rtt_ms.missing /
                    (rawdata[i].rtt_ms.missing + rawdata[i].rtt_ms.count)*100);
        }
        $("#sparklineLoss").sparkline(actualdata, sparkline_ts_template);
    });
}

/* FIXME: There is definitely a better way of coding this so that only one json function is needed instead of three */

/*
 *  Latency Graph
 */
function drawLatencyGraph(graph) {
    $("#graph").empty();
    BasicTimeSeries({
        container: $("#graph"),
        /* TODO do something sensible with start and end times, urls */
        start: starttime * 1000,
        end: endtime * 1000,
        generalstart: generalstart * 1000,
        generalend: generalend * 1000,
        urlbase: host+"/api/_graph/latency/"+source+"/"+dest,
	miny: 0,
	ylabel: "Latency (ms)"
    });
}

/*
 *  Jitter graph
 */
function drawJitterGraph(graph) {
    $("#graph").empty();
    BasicTimeSeries({
        container: $("#graph"),
        start: starttime * 1000,
        end: endtime * 1000,
        generalstart: generalstart * 1000,
        generalend: generalend * 1000,
        urlbase: host+"/api/_graph/jitter/"+source+"/"+dest,
	miny: 0,
	ylabel: "Jitter (ms)"
    });
}

/*
 *  Loss graph
 */
function drawLossGraph(graph){
    $("#graph").empty();
    BasicTimeSeries({
        container: $("#graph"),
        start: starttime * 1000,
        end: endtime * 1000,
        generalstart: generalstart * 1000,
        generalend: generalend * 1000,
        urlbase: host+"/api/_graph/loss/"+source+"/"+dest,
	miny: 0,
	maxy: 100,
	ylabel: "Loss (%)"
    });
}

/*
 *  Smokeping Latency Graph
 */
function drawSmokepingGraph(graph) {
    $("#graph").empty();
    Smoke({
        container: $("#graph"),
        /* TODO do something sensible with start and end times, urls */
        start: starttime * 1000,
        end: endtime * 1000,
        generalstart: generalstart * 1000,
        generalend: generalend * 1000,
        urlbase: host+"/api/_graph/smokeping/"+stream,
        event_urlbase: host+"/api/_event/smokeping/"+stream,
        xticlabels: generateSummaryXTics(generalstart, generalend),
    });
}

function drawMuninbytesGraph(graph) {
    $("#graph").empty();
    BasicTimeSeries({
        container: $("#graph"),
        /* TODO do something sensible with start and end times, urls */
        start: starttime * 1000,
        //start: (endtime - (60*60*2)) * 1000,
        end: endtime * 1000,
        generalstart: generalstart * 1000,
        generalend: generalend * 1000,
        urlbase: host+"/api/_graph/muninbytes/"+stream,
        event_urlbase: host+"/api/_event/muninbytes/"+stream,
        xticlabels: generateSummaryXTics(generalstart, generalend),
    	miny: 0,
    	ylabel: "MBs"
    });
}

/*
 * Goes to the last visited matrix page
 */
function backToMatrix() {
    /* Get the cookies */
    var last_Matrix = $.cookie("last_Matrix").replace("matrix", "#matrix");

    /* Redirect */
    if (last_Matrix) {
        window.location = last_Matrix;
    } else {
        window.location = "/matrix/latency/nz/nz";
    }
}


/*
 * Function that deals with traceroute graphs
 */
function tracerouteGraph() {
    $("#graph").append("<p>(This will take a while)</p>");
    ajax1 = $.getJSON("/api/_graph/tracemap/" + source +"/" + dest + "/", function(data) {
        $("#graph").empty()
        $.amptraceview($('#graph'), data , "right", "pruned");
    });
}

/*
 * This is called whenever the graph page is first loaded. As such, it needs
 * to extract any user-provided info from the URL and then render the page
 * components appropriately.
 */
$(document).ready(function() {
    /* Solves problem of no slash on the end of the url */
        /* Only a problem with Hashbangs */

    if ($(location).attr("href").slice(-5) == "graph") {
        window.location = "/graph/";
    }

    var urlparts = [];
    var isHashbang = false;

    /* Update page variables, and draw graph */
    decomposeURLParameters();
    initSelectors();
    if (stream != "") {
        changeGraph({graph: graph});
        setTitle();
    }

});

/* Get's history.js running */
(function(window,undefined) {
    /* Prepare */
    var History = window.History;
    if (!History.enabled) {
         /*
          * History.js is disabled for this browser.
          * This is because we can optionally choose to support HTML4 browsers or not.
          */
        return false;
    }
})(window);

/* If the user clicks the back or forward buttons, we want to return them
 * to that previous view as best we can */
window.addEventListener('popstate', function(event) {
    decomposeURLParameters();
    revertDropdowns(stream);
    changeGraph({graph: graph});
    
});


// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :
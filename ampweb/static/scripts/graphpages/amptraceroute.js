function AmpTracerouteHopsGraphPage() {
    CuzGraphPage.call(this);
    this.colname = "amp-traceroute_pathlen";
    this.graphstyle = "amp-traceroute-hops";
    this.generictitle = "AMP Traceroute Graphs";
    this.modal = new AmpTracerouteModal();
}

function AmpTracerouteRainbowGraphPage() {
    CuzGraphPage.call(this);
    this.colname = "amp-astraceroute";
    this.graphstyle = "amp-astraceroute";
    this.generictitle = "AMP AS Traceroute Graphs";
    this.modal = new AmpTracerouteRainbowModal();
}

function AmpTracerouteMapPage() {
    CuzGraphPage.call(this);
    this.colname = "amp-traceroute";
    this.graphstyle = "amp-traceroute";
    this.generictitle = "AMP Traceroute Graphs";
    this.modal = new AmpTracerouteMapModal();
}


AmpTracerouteHopsGraphPage.prototype = new CuzGraphPage();
AmpTracerouteHopsGraphPage.prototype.constructor = AmpTracerouteHopsGraphPage;

AmpTracerouteRainbowGraphPage.prototype = new CuzGraphPage();
AmpTracerouteRainbowGraphPage.prototype.constructor = AmpTracerouteRainbowGraphPage;

AmpTracerouteMapPage.prototype = new CuzGraphPage();
AmpTracerouteMapPage.prototype.constructor = AmpTracerouteMapPage;

AmpTracerouteHopsGraphPage.prototype.getTabs = function() {
    return [];
}

AmpTracerouteRainbowGraphPage.prototype.getTabs = function() {
    return [
        { 'graphstyle': 'amp-astraceroute',
          'title': 'AS Path', 'selected': true},
        { 'graphstyle': 'amp-traceroute',
          'title': 'Path Map', 'selected': false}
    ];
}

AmpTracerouteMapPage.prototype.getTabs = function() {
    return [
        { 'graphstyle': 'amp-astraceroute',
          'title': 'AS Path', 'selected': false},
        { 'graphstyle': 'amp-traceroute',
          'title': 'Path Map', 'selected': true}
    ];
}

AmpTracerouteRainbowGraphPage.prototype.drawGraph = function(start, end,
        first, legend) {
    this.graph = new RainbowGraph({
        container: $("#graph"),
        start: start,
        end: end,
        firstts: first,
        legenddata: legend,
        lines: [ {id:this.view} ], //XXX to work with existing streams code
        urlbase: API_URL + "/_view/amp-astraceroute/",
        event_urlbase: API_URL + "/_event/amp-astraceroute/",
        miny: 0,
        drawEventsBehind: false,
        units: "hops",
        ylabel: "Number of Hops",
        measureLatency: false,
        minHopHeight: 5
    });

    this.graph.createGraphs();
}

AmpTracerouteHopsGraphPage.prototype.drawGraph = function(start, end, first,
        legend) {
    this.graph = new SmokepingGraph({
        container: $("#graph"),
        start: start,
        end: end,
        firstts: first,
        legenddata: legend,
        lines: [ {id:this.view} ], //XXX to work with existing streams code
        urlbase: API_URL + "/_view/amp-traceroute_pathlen/",
        event_urlbase: API_URL + "/_event/amp-astraceroute/",
        miny: 0,
        units: "hops",
        ylabel: "Number of Hops"
    });

    this.graph.createGraphs();
}

AmpTracerouteMapPage.prototype.drawGraph = function(start, end, first, legend) {
    this.graph = new TracerouteMap({
        container: $("#graph"),
        start: start,
        end: end,
        firstts: first,
        legenddata: legend,
        lines: [ {id:this.view} ], //XXX to work with existing streams code
        urlbase: API_URL + "/_view/amp-traceroute/",
        event_urlbase: API_URL + "/_event/amp-astraceroute/"
    });

    this.graph.createGraphs();
}

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

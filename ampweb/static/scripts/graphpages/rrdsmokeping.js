function RRDSmokepingGraphPage() {
    CuzGraphPage.call(this);
    this.colname = "rrd-smokeping";
    this.generictitle = "Cuz - Smokeping Graphs";
}

RRDSmokepingGraphPage.prototype = new CuzGraphPage();
RRDSmokepingGraphPage.prototype.constructor = RRDSmokepingGraphPage;

RRDSmokepingGraphPage.prototype.initDropdowns = function(stream) {
    this.dropdowns = new SmokepingDropdown(stream);
}

RRDSmokepingGraphPage.prototype.drawGraph = function(start, end, first) {
    this.graph = new SmokepingGraph({
        container: $("#graph"),
        start: start ,
        end: end ,
        firstts: first,
        lines: this.streams,
        urlbase: API_URL + "/_graph/rrd-smokeping/",
        event_urlbase: API_URL + "/_event/rrd-smokeping/",
        miny: 0,
        ylabel: "Latency (ms)",
    });

    this.graph.createGraphs();
}

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :
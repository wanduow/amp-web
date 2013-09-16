function LPIBytesGraphPage() {
    CuzGraphPage.call(this);
    this.colname = "lpi-bytes";
    this.generictitle = "Cuz - LPI Bytes Graphs";
}

LPIBytesGraphPage.prototype = new CuzGraphPage();
LPIBytesGraphPage.prototype.constructor = LPIBytesGraphPage;

LPIBytesGraphPage.prototype.initDropdowns = function(stream) {
    this.dropdowns = new LPIBasicDropdown(stream, "lpi-bytes");
}

LPIBytesGraphPage.prototype.drawGraph = function(start, end, first) {
    this.graph = new BasicTimeSeriesGraph({
        container: $("#graph"),
        start: start,
        end: end,
        firstts: first,
        urlbase: API_URL + "/_graph/lpi-bytes/" + this.streams[0],
        event_urlbase: API_URL + "/_event/lpi-bytes/" + this.streams[0],
        miny: 0,
        ylabel: "Mbps",
    });

    this.graph.createGraphs();
}


// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

function RRDSmokepingGraphPage() {
    CuzGraphPage.call(this);
    this.colname = "rrd-smokeping";
    this.graphstyle = "rrd-smokeping";
    this.generictitle = "Smokeping Graphs";
    this.modal = new SmokepingModal();
}

RRDSmokepingGraphPage.prototype = new CuzGraphPage();
RRDSmokepingGraphPage.prototype.constructor = RRDSmokepingGraphPage;

RRDSmokepingGraphPage.prototype.getTabs = function() {
    return [ 
        { 'graphstyle': 'rrd-smokeping', 
          'title': 'Latency', 'selected':true }
    ];
}


RRDSmokepingGraphPage.prototype.drawGraph = function(start, end, first, legend) {
    this.graph = new SmokepingGraph({
        container: $("#graph"),
        start: start ,
        end: end ,
        firstts: first,
        legenddata: legend,
        lines: [ {id:this.view} ],
        urlbase: API_URL + "/_view/rrd-smokeping/full/",
        event_urlbase: API_URL + "/_event/rrd-smokeping/",
        miny: 0,
        ylabel: "Latency (ms)"
    });

    this.graph.createGraphs();
}

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

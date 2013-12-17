/* Class that implements a traceroute map graph type within Cuz. The graph has
 * two components: a detail graph and a summary graph for navigation purposes.
 * In contrast to a regular time series graph, the detail view of this graph is
 * not plotted with axes but the summary view is used to pan through time,
 * changing the data shown in the detail view.
 *
 * This class removes some of the functionality of the basic time series graph
 * it overrides, such as events.
 */
function TracerouteMap(params) {
    BasicTimeSeriesGraph.call(this, params);

    /* Configuration for the detail graph */
    this.detailgraph.options.config.grid = {
                verticalLines: false,
                horizontalLines: false,
                outline: "",
                outlineWidth: 0
            };
    this.detailgraph.options.config.xaxis.showLabels = false;

    /* Override the basic line style with our traceroute map style */
    this.configureStyle = function() {
        this.detailgraph.options.config.tracemap =
                jQuery.extend(true, {}, CuzTracerouteMapConfig);
        this.summarygraph.options.config.tracemap =
                jQuery.extend(true, {}, CuzTracerouteMapConfig);

        /* Force hide all events - although we do not ever fetch event data,
         * this avoids trying to do any extra hit detection etc. */
        this.detailgraph.options.config.events.show = false;
        this.summarygraph.options.config.events.show = false;
    }

    /**
     * Creates both the summary and detail graphs, populates them with data
     * based on the initial selection and draws the graphs.
     *
     * Generally, you'll want to call this as soon as you've instantiated
     * your instance of this class.
     */
    this.createGraphs = function() {
        /* Define our line styles */
        this.configureStyle();

        /* Calculate the amount of summary data we'll need */
        this.calcSummaryRange();

        /* Queue loading states */
        this.loadingStates = [
            ["detail", "Fetched detailed data"],
            ["summary", "Fetched summary data"],
            ["layout", "Processed layout"]
        ];
        this.loadingStart();

        /* Create the envision components for our graphs */
        createEnvision(this);

        /* Queries for data from the summary graph, and queries for data from
         * the detail graph in its callback (after summary data has been
         * fetched) */
        this.fetchSummaryData(true);
    }

    /**
     * Queries for data required to draw the summary graph and processes it when
     * it is received. Optionally also requests that the detail graph be updated
     * after data has been received. The detail graph must be updated after the
     * summary data has been fetched, so this argument should be set to true for
     * the first invocation of this method.
     * @param {boolean} updateDetail - if true, updates the detail graph after
     *     data has been received
     */
    this.fetchSummaryData = function(updateDetail) {
        /* If we have an outstanding query for summary data, abort it */
        if (this.summaryreq)
            this.summaryreq.abort();

        var url = this.makeURL(this.dataurl, this.summarygraph);

        var graph = this;
        return $.getJSON(url, function(sumdata) {
            graph.stateLoaded("summary");
            graph.processSummaryData(sumdata);
            /* processSummaryData() spawns a worker thread if possible and comes
             * back to execute updateDetailGraph() */
            if ( updateDetail ) {
                graph.updateDetailGraph();
            }
        });
    }

    /**
     * Queries for data required to draw the detailed graph and processes it
     * when it is received.
     */
    this.fetchDetailData = function() {
        /* If we have an outstanding query for detail data, abort it */
        if (this.detailreq)
            this.detailreq.abort();

        /* build up a url with all of the stream ids in it */
        var url = this.makeURL(this.dataurl, this.detailgraph);

        var graph = this;
        return $.getJSON(url, function(detaildata) {
            graph.stateLoaded("detail");
            graph.processDetailedData(detaildata);
        });
    }

    this.processEvents = function(isDetailed) {
        return;
    }

    /* Processes the data fetched for the summary graph. */
    this._processSummaryData = this.processSummaryData;
    this.processSummaryData = function(sumdata) {
        this._processSummaryData(sumdata);
        console.log(this);
        this.makePaths(this.summarygraph);
    }

    /* Processes the data fetched for the detail graph and forms an
     * appropriate dataset for plotting.
     */
    this.processDetailedData = function(detaildata) {
        this.mergeDetailSummary(detaildata);
        this.makePaths(this.detailgraph);
        return;
    }

    /**
     * Fetches new summary data, but only if the selection has changed
     */
    this.updateSummaryGraph = function() {
        /* Don't bother changing anything if our summary range hasn't changed.
         */
        if (this.calcSummaryRange() == false)
            return;

        this.fetchSummaryData();
    }

    this.updateDetailGraph = function() {
        window.clearTimeout(this.selectingtimeout);
        this.selectingtimeout = null;

        this.fetchDetailData();
    }

    this.makePaths = function(graph) {
        var tracemap = this;

        if ( typeof(Worker) !== undefined ) {
            var worker = new Worker("/static/scripts/tracemap-worker.js");
            
            worker.onmessage = function(event) {
                graph.options.config.tracemap.paths = event.data.paths;
                if ( graph.options.height > 150 ) {
                    TracerouteMap.prototype.digraph = event.data.digraph;
                    tracemap.stateLoaded("layout");
                }
                
                tracemap.makePathsCallback(graph);
            };

            worker.postMessage({
                data: graph.options.data,
                start: graph.start,
                end: graph.end,
                createDigraph: (graph.options.height > 150)
            });
        } else {
            graph.options.config.tracemap.paths = TracerouteDigraph.prototype
                    .createPaths(graph.options.data, graph.start, graph.end);
            if ( graph.options.height > 150 ) {
                TracerouteMap.prototype.digraph = TracerouteDigraph.prototype
                        .drawDigraph(graph.options.config.tracemap.paths);
                tracemap.stateLoaded("layout");
            }

            this.makePathsCallback(graph);
        }
    }

    this.makePathsCallback = function(graph) {
        if ( graph.options.height > 150 ) {
            this.drawDetailGraph();

            /* Update the displayed summary range, if needed */
            this.updateSummaryGraph();
        } else {
            /* Redraw the summary, but leave detail alone */
            this.summarycomponent.draw();

            /* Trigger a selection event to redraw the handles and
             * selection box. */
            if ( this.detailgraph.start !== undefined ) {
                this.triggerSelection(this.detailgraph.start,
                        this.detailgraph.end);
            } else {
                this.updateDetailGraph();
            }

            /* display the legend once pretty much everything has loaded */
            this.displayLegend();
        }
    }

    this.detailgraph.options.config.mouse.trackFormatter =
            TracerouteMap.prototype.displayTooltip;

}

/* This is a convenient way of passing the digraph layout data structure around.
 * If we were to store this object with options, whenever options are passed to
 * methods, a recursive merge is performed to clone properties, which takes
 * forever. By storing the layout here we can access it directly and avoid
 * unnecessary object merging/cloning overhead. */
TracerouteMap.prototype.digraph = null;

TracerouteMap.prototype = inherit(BasicTimeSeriesGraph.prototype);
TracerouteMap.prototype.constructor = TracerouteMap;
TracerouteMap.prototype.displayTooltip = function(o) {
    if ( o.nearest.host ) {
        return o.nearest.host;
    } else if ( o.nearest.path ) {
        var times = o.nearest.path.times;
        var occurrences = "";

        for ( j = 0; j < times.length; j++ ) {
            occurrences += convertToTime( new Date(times[j] * 1000) );
            if ( j + 2 == times.length )
                occurrences += " and ";
            else if ( j + 1 < times.length )
                occurrences += ", ";
        }

        return "" + times.length +
                (times.length == 1 ? " occurrence" : " occurrences") +
                (times.length > 6 ? "" : " on " + occurrences);
    }
}

/* TODO Unify with Flotr2 dates as appear on axes
 * Although this code *should* produce dates of the same
 * format, it would be nicer to keep this together */
function convertToTime(unixTimestamp) {
    var a = new Date(unixTimestamp);
    var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug',
            'Sep','Oct','Nov','Dec'];
    var year = a.getFullYear();
    var month = months[a.getMonth()];
    var day = a.getDate();
    var hour = a.getHours();
    var min = a.getMinutes();
    var sec = a.getSeconds();

    return month + ' ' + day + ', ' + hour + ':' +
            min.padLeft(2) + ':' + sec.padLeft(2);
}

Number.prototype.padLeft = function(n, str) {
    return Array(n-String(this).length+1).join(str||'0')+this;
}

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

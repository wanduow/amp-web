function CuzGraphPage() {

    this.streams = ""
    this.tabrequest = undefined;
    this.streamrequest = undefined;
    this.colname = "";
    this.graph = undefined;

    this.getCurrentSelection = function() {
        if (this.graph)
            return this.graph.getSelectionRange();

        return null;
    }

    this.changeView = function(newview, start, end) {
        if (newview != undefined)
            this.view = newview;

        // If start and end are set to null, try to use the current selection.
        if (start == null || end == null) {
            if (this.graph) {
                var times = this.graph.getSelectionRange();
                start = times.start;
                end = times.end;
            }
        }

        $("#graph").empty();

        /* If stream is not set or is invalid, clear the graph and exit */
        if (this.view == "" || this.view.length == 0) {
            if (this.view.length == 0) {
                $("#graph").append("<p>No valid view selected.</p>");
            }
            return;
        }

        $("#graph").append("<p>Loading graph...</p>");

        if (this.streamrequest)
            this.streamrequest.abort();

        var graphobj = this;
        var i = 0;

        var infourl = API_URL + "/_legend/" + graphobj.colname + "/" 
                + this.view;
        var legenddata = {};

        this.streamrequest = $.ajax({
            url: infourl,
            success: function(data) {
                $.each(data, function(index, result) {
                    legenddata[result.group_id] = result;
                });
                graphobj.drawGraph(start, end, 0, legenddata);
            }
        });

        /* XXX this doesn't do a lot either, we probably do want tabs */
        this.populateTabs();
    }

    this.formRelatedStreamsCallback = function(relobj) {
        var selected = false;
        var cb = "changeTab({graph: '" + relobj['collection'] + "',";
        cb += "stream: [";

        // Iterate over our current streams
        $.each(this.streams, function(index, stream) {
            // Find the related stream for the current stream
            var relid = relobj.streamid[stream.id];

            // No related stream for this stream, skip it
            if (relid == undefined)
                return;

            /* If the related stream id is the same as the original, we're
             * looking at the currently selected "tab" */
            if (relid == stream.id)
                selected = true;

            /* Otherwise, we want to describe a new object that has all the
             * same properties as the original stream, e.g. line colour etc.,
             * but has the new stream id.
             */
            cb += "{id: " + relid + ",";

            /* TODO Copy other stream properties here */
            cb += "},";
        });
        cb += "]})";

        return {'callback':cb, 'selected':selected};
    }

    this.populateTabs = function() {
        $('#graphtablist').children().remove();

        if (this.streams == "" || this.streams.length == 0)
            return;

        if (this.tabrequest)
            this.tabrequest.abort();

        var graphobj = this;
        var i = 0;
        var relurl = API_URL + "/_relatedstreams/" + graphobj.colname + "/";

        for (i; i < this.streams.length; i++) {
            relurl += this.streams[i].id + "/";
        }
        /* Get a suitable set of tabs via an ajax query */
        this.tabrequest = $.ajax({
            url: relurl,
            success: function(data) {
                var nexttab = 0;
                $.each(data, function(index, obj) {
                    var tabid = "graphtab" + nexttab;
                    var sparkid = "minigraph" + nexttab;
                    var cb = graphobj.formRelatedStreamsCallback(obj);
                    var li = "<li id=\"" + tabid + "\" ";

                    li += "onclick=\"";
                    li += cb['callback'];
                    li += "\" ";

                    if (cb['selected'])
                        li += "class=\"selectedicon\">";
                    else
                        li += "class=\"icon\">";
                    li += "<span id=\"" + sparkid + "\"></span>";
                    li += "<br>" + obj['title'] + "</li>"
                    $('#graphtablist').append(li);
                    nexttab ++;
                });
            }
        });
    }

    this.updateTitle = function() {
        if (this.streams == "" || this.streams.length == 0)
        {
            setTitle("CUZ - Graphs");
            return;
        }

        if (this.streams.length == 1) {

            $.ajax({
                url: API_URL + "/_streaminfo/" + this.colname + "/" +
                        this.streams[0].id + "/",
                success: function(data) {
                    var graphtitle = "CUZ - " + data[0]["name"];
                    setTitle(graphtitle);
                }
            });
        } else {
            if (this.generictitle != undefined)
                setTitle(this.generictitle);
            else
                setTitle("Cuz - Graphs");
        }


    }

    this.displayLegend = function(legend) {
        /* TODO put addresses in a tooltip with line colours? */
        /* TODO list all line colours in the main label for each dataset? */
        /* TODO make the data in legend much more generic so it works on all */
        var node = $('#dropdowndiv');
        node.empty();

        /* display the button to add more lines to the view */
        node.append("<a data-toggle='modal' data-target='#modal-foo' " +
                "href='/modal/" + this.colname + "' " +
                "class='btn btn-primary btn-xs'>" +
                "<span class='glyphicon glyphicon-plus'>" +
                "</span>Add new data series</a>");
        node.append("<br />");

        for ( var label in legend ) {

            var groupid = legend[label]['groupid']

            html = "<span class='label label-default'>";
            for ( var item in legend[label]["series"] ) {
                
                var series = legend[label]["series"][item]["colourid"];
                var colour = "hsla(" + ((series * 222.49223594996221) % 360) +
                    ", 90%, 50%, 1.0)";
                html += "<label style='color:"+colour+";'>&mdash;</label>";
            }
            html += "&nbsp;" + label + "&nbsp;" +
                    "<button type='button' class='btn btn-default btn-xs' " +
                    "onclick='graphPage.modal.removeSeries(\"" + groupid + "\")'>" +
                    "<span class='glyphicon glyphicon-remove'></span>" +
                    "</button> </span>";
            node.append(html);
        }
    }

}

CuzGraphPage.prototype.drawGraph = function(start, end, first, labels) {};

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :
/*
 * This file is part of amp-web.
 *
 * Copyright (C) 2013-2017 The University of Waikato, Hamilton, New Zealand.
 *
 * Authors: Shane Alcock
 *          Brendon Jones
 *
 * All rights reserved.
 *
 * This code has been developed by the WAND Network Research Group at the
 * University of Waikato. For further information please see
 * http://www.wand.net.nz/
 *
 * amp-web is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * amp-web is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with amp-web; if not, write to the Free Software Foundation, Inc.
 * 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 *
 * Please report any bugs, questions or comments to contact@wand.net.nz
 */

/*
 * Draw a time series line graph showing roughly when events occurred (binned
 * at 30 minute intervals to actually have numbers greater than one appear
 * on the plot).
 */
function drawEventFrequencies(object) {
    var container = object.container;
    var url = object.urlbase + "/" + object.start + "/" + object.end;

    request = $.getJSON(url, function(data) {
        Flotr.draw(container,
            [
                { color: "rgb(51, 102, 204)", data: data }
                //{ label:"groups", color: "red", data:data["groups"] }
            ], {
            lines: {
                show: true,
                fill: true,
                fillOpacity: 1.0
            },
            xaxis: {
                mode: "time",
                timeFormat: "%H:%M<br>%b %d",
                timeMode: "local",
                /* TODO stop ticks from being so sparse. This option is
                 * deprecated in Flotr2. See
                 * https://github.com/HumbleSoftware/Flotr2/issues/113 */
                //tickSize: [4, "hour"],
                noTicks: 10 // magic number for four hour intervals
            },
            yaxis: {
                min: 0
            },
            /* do we want tooltips, are they useful? */
            mouse: {
                margin: 0,
                track: true,
                relative: true,
                sensibility: 5,
                trackFormatter: function(o) {
                    var date = new Date(Math.round(o.x));
                    var desc = date.toLocaleString();
                    desc += "<br />";
                    desc += "Events: " + Math.round(o.y);
                    return desc;
                }
            }
        });
    }).fail(function(jqXHR, textStatus, errorThrown) {
        /* Don't error on user aborted requests */
        if (globalVars.unloaded || errorThrown == 'abort') {
            return;
        }
        displayAjaxAlert("Failed to fetch event frequencies", textStatus,
            errorThrown);
    });
}

/*
 * Draw a bar graph showing the sources/targets that have the most events
 * in the last time period. Limit it to the 5 largest.
 */
function drawEventSiteFrequencies(object) {
    var container = object.container;
    var url = object.urlbase + "/" + object.start + "/" + object.end;
    var name_cutoff = 21;
    var max_sites = 5;

    request = $.getJSON(url, function(data) {

        /* build data array and ticks array together */
        var sites = [];
        var labels = [];
        var label;
        var max;

        /* limit the graph to showing no more than 5 bars */
        max = Math.min(max_sites, data.length);
        for (var i = 0; i < max; i++) {
            /* array is back to front because of the horizontal bars */
            sites.push([data[i].count, max - i]);
            label = data[i].site;
            /* shorten any long labels as they impact the graph width */
            if (label.length > name_cutoff) {
                label = label.substr(0, name_cutoff) + "...";
            }
            /*
             * label array is simply value:label, so it appears to be the
             * right way around.
             */
            labels.push([max - i, label]);
        }

        Flotr.draw(container,
            [
                { color: "rgb(51, 102, 204)", data: sites }
            ], {
            bars: {
                show: true,
                horizontal: true,
                fillOpacity: 1.0,
                shadowSize: 0,
                barWidth: 0.75
            },
            xaxis: {
                /* TODO make ticks whole numbers only */
                min: 0
            },
            yaxis: {
                ticks: labels
            },
            grid: {
                horizontalLines: false
            },
            mouse: {
                margin: 0,
                track: true,
                relative: true,
                sensibility: 5,
                position: 'n',
                lineColor: '#081a8a',
                horizbar: true,
                trackFormatter: function(o) {
                    var ind = o.index;
                    if (ind === undefined || ind < 0 || ind >= data.length)
                            return "Unknown";
                    var desc = data[ind].tooltip;
                    return desc;
                }
            }
        });
    }).fail(function(jqXHR, textStatus, errorThrown) {
         /* Don't error on user aborted requests */
        if (globalVars.unloaded || errorThrown == 'abort') {
            return;
        }
        displayAjaxAlert("Failed to fetch site event frequencies", textStatus,
            errorThrown);
    });
}


function drawCommonEventFrequencies(object) {
    var container = object.container;
    var name_cutoff = 21;

    var url = object.urlbase + "/" + object.start + "/" + object.end + "/";
    url += object.maxstreams;

    request = $.getJSON(url, function(data) {
        var table = new Array(), j = -1;

        var max = Math.min(object.maxstreams, data.length);
        table[++j] = '<tr><th>Rank</th><th>Description</th>';
        table[++j] = '<th>Type</th><th>Count</th></tr>';

        for (var i = 0; i < max; i++) {
            table[++j] = '<tr><td>';
            table[++j] = i + 1;
            table[++j] = '</td><td>';
            table[++j] = data[i].tooltip;
            table[++j] = '</td><td>';
            switch (data[i].eventtype) {
                case 'incr':
                    table[++j] = "<span class='glyphicon glyphicon-circle-arrow-up groupicon' data-toggle='tooltip' data-placement='bottom' title='Latency Increased'></span>";
                    break;
                case 'decr':
                    table[++j] = "<span class='glyphicon glyphicon-circle-arrow-down groupicon' data-toggle='tooltip' data-placement='bottom' title='Latency Decreased'></span>";
                    break;
                case 'pathchange':
                    table[++j] = "<span class='glyphicon glyphicon-random groupicon' data-toggle='tooltip' data-placement='bottom' title='Route Changed'></span>";
                    break;
                case 'loss':
                    table[++j] = "<span class='glyphicon glyphicon-fire groupicon' data-toggle='tooltip' data-placement='bottom' title='Packet Loss'></span>";
                    break;
                default:
                    table[++j] = "<span class='glyphicon glyphicon-question-sign groupicon' data-toggle='tooltip' data-placement='bottom' title='Unknown Event'></span>";
                    break;
            }
            table[++j] = '</td><td>';
            table[++j] = data[i].count;
            table[++j] = '</td></tr>';

            $(container).html(table.join(''));
            $('[data-toggle="tooltip"]').tooltip();
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
         /* Don't error on user aborted requests */
        if (globalVars.unloaded || errorThrown == 'abort') {
            return;
        }
        displayAjaxAlert("Failed to fetch common events", textStatus,
            errorThrown);
    });
}

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

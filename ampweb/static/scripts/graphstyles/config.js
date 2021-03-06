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

/* Initial configuration for the summary and detail graphs */

var CuzDefaultDetailConfig = {
    name: "detail",
    skipPreprocess: true,
    data: [
        /*
         * This empty data series is used to hang mouse events onto so that we
         * can display network event labels. All other data series have mouse
         * tracking disabled so that they don't trigger popups on mouseover
         * when we don't really have anything interesting to display.
         */
        []
    ],
    height: 300,
    config: {
        HtmlText: false,
        title: " ",
        events: {
            show: true,
            events: [],
            hits: {},
            binDivisor: 50.0,
            drawBehind: true,
            categoriseSeverity: true, // separate into severity levels
            severityColours: true,
            greyLines: true,
            greyMarkers: false,
            greyscale: false
        },
        mouse: {
            margin: 0,
            track: true,
            relative: true,
            trackY: true,
            trackAll: false,
            trackFormatter: null
        },
        xaxis: {
            showLabels: true,
            mode: "time",
            timeformat: "%h:%M:%S",
            timeMode: "local",
            margin: true,
            tickFormatter: null
        },
        yaxis: {
            min: null,
            max: null,
            showLabels: true,
            autoscale: true,
            title: null,
            margin: true,
            titleAngle: 90
        },
        grid: {
            color: "#0F0F0F",
            verticalLines: true,
            horizontalLines: true,
            outline: "sw",
            outlineWidth: 1,
            labelMargin: 8
        }
    }
};

var CuzBasicLineConfig = {
    show: true,
    fill: false,
    fillColor: "#CEE3F6",
    fillOpacity: 0.7,
    lineWidth: 2
    //color: "#00A8F0"
};

var CuzSmokeConfig = {
    show: true
};

var CuzRainbowConfig = {
    show: true,
    measureLatency: false,
    minHopHeight: 5
};

var CuzJitterRainbowConfig = {
    show: true,
};

var CuzVideoRainbowConfig = {
    show: true,
    minHopHeight: 1
};

var CuzTracerouteMapConfig = {
    show: true
};

var CuzDefaultSummaryConfig = {
    name: "summary",
    skipPreprocess: true,
    /*
     * This empty data series is the one responsible for making sure the events
     * get drawn, and is the only one where events will be enabled. Every
     * series that has events enabled results in the events being drawn again.
     */
    data: [[]],
    height: 90,
    config: {
        HtmlText: false,
        title: " ",
        events: {
            show: true,
            events: [],
            hits: {},
            binDivisor: 50.0,
            drawBehind: true,
            categoriseSeverity: true, // separate into severity levels
            severityColours: true,
            greyLines: true,
            greyMarkers: false,
            greyscale: false
        },
        selection: {
            mode: "x",
            color: "#00AAFF"
        },
        handles: {
            show: true
        },
        xaxis: {
            ticks: null,
            mode: "time",
            title: getTZLabel(),
            showLabels: true,
            timeformat: "%h:%M:%S",
            timeMode: "local",
            margin: true,
            min: null
        },
        yaxis: {
            autoscale: true,
            autoscaleMargin: 2.0,
            min: null,
            max: null
        },
        grid: {
            color: "#0F0F0F",
            verticalLines: true,
            labelMargin: 8,
            outline: "s",
            outlineWidth: 1,
            outlineColor: "#999999"
        }
    }
};

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

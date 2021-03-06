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
 * This is a slightly modified version of the selection handles plugin
 * from flotr2. Make sure you include this *after* envision.js so that this
 * plugin will override the standard 'selection' plugin!
 *
 * Options
 *  show - True enables the handles plugin.
 *  drag - Left and Right drag handles
 *  scroll - Scrolling handle
 */
(function () {

function isLeftClick (e, type) {
    return (e.which ? (e.which === 1) : (e.button === 0 || e.button === 1));
}

function boundX(x, graph) {
    /* XXX This used to be plotWidth - 1, but that prevents us from selecting
     * the most recent data.
     */
    return Math.min(Math.max(0, x), graph.plotWidth);
}

function boundY(y, graph) {
    return Math.min(Math.max(0, y), graph.plotHeight);
}

var
    D = Flotr.DOM,
    E = Flotr.EventAdapter,
    _ = Flotr._;


Flotr.addPlugin('selection', {

    options: {
        pinchOnly: null,       // Only select on pinch
        mode: null,            // => one of null, 'x', 'y' or 'xy'
        color: '#B6D9FF',      // => selection box color
        fps: 20                // => frames-per-second
    },

    callbacks: {
        'flotr:mouseup' : function (event) {
            var
                options = this.options.selection,
                selection = this.selection,
                pointer = this.getEventPosition(event);

            if (!options || !options.mode) return;

            if (selection.interval)
                clearInterval(selection.interval);

            if (this.multitouches) {
                selection.updateSelection();
            } else if (!options.pinchOnly && selection.selectMode == "select") {
                selection.setSelectionPos(selection.selection.second, pointer);
            }

            if (selection.selection.first.x == selection.selection.second.x) {
                selection.selection.first = selection.prevSelection.first;
                selection.selection.second = selection.prevSelection.second;
            }

            selection.clearSelection();

            if(selection.selectionIsSane()){
                selection.drawSelection();
                selection.fireSelectEvent();
                this.ignoreClick = true;
            }
            selection.selectMode = "none";
        },

        'flotr:mousemove' : function (event, position) {

            if (this.selection.selectMode != "drag")
                return;

            var delta = position.x - this.lastMousePos.x,
                area = this.selection.getArea(),
                selection = this.selection.selection;

            area.x1 += delta;
            area.x2 += delta;

            this.selection.setSelection(area, true, true);
        },

        'flotr:mousedown' : function (event) {

            var
                options = this.options.selection,
                selection = this.selection,
                pointer = this.getEventPosition(event);

            if (!options || !options.mode)
                return;
            if (!options.mode || (!isLeftClick(event)
                    && _.isUndefined(event.touches)))
                return;

            /* If the mouse pointer is within the selection area, we want to
             * drag the selection box rather than start a new selection. */
            if (selection.clickSelection(pointer)) {
                selection.selectMode = "drag";
            } else {
                selection.selectMode = "selection";

                if (!options.pinchOnly)
                    selection.setSelectionPos(selection.selection.first,
                            pointer);
                if (selection.interval)
                    clearInterval(selection.interval);

                this.lastMousePos.pageX = null;
                selection.selecting = false;
                selection.interval = setInterval(
                        _.bind(selection.updateSelection, this),
                        1000 / options.fps
                );
            }
        },
        'flotr:destroy' : function (event) {
            clearInterval(this.selection.interval);
        }
    },

    // TODO This isn't used.  Maybe it belongs in the draw area and fire
    // select event methods?
    getArea: function() {

        var
            s = this.selection.selection,
            a = this.axes,
            first = s.first,
            second = s.second,
            x1, x2, y1, y2;

        x1 = a.x.p2d(s.first.x);
        x2 = a.x.p2d(s.second.x);
        y1 = a.y.p2d(s.first.y);
        y2 = a.y.p2d(s.second.y);

        return {
            x1 : Math.min(x1, x2),
            y1 : Math.min(y1, y2),
            x2 : Math.max(x1, x2),
            y2 : Math.max(y1, y2),
            xfirst : x1,
            xsecond : x2,
            yfirst : y1,
            ysecond : y2
        };
    },

    selection: {first: {x: -1, y: -1}, second: {x: -1, y: -1}},
    prevSelection: null,
    interval: null,
    selectMode: "none",

    /**
     * Fires the 'flotr:select' event when the user made a selection.
     */
    fireSelectEvent: function(name){
        var area = this.selection.getArea();
        name = name || 'select';
        area.selection = this.selection.selection;
        E.fire(this.el, 'flotr:'+name, [area, this]);
    },

    /**
     * Allows the user to manually select an area.
     * @param {Object} area - Object with coordinates to select.
     */
    setSelection: function(area, preventEvent, setBoth){
        var options = this.options,
        xa = this.axes.x,
        ya = this.axes.y,
        vertScale = ya.scale,
        hozScale = xa.scale,
        selX = options.selection.mode.indexOf('x') != -1,
        selY = options.selection.mode.indexOf('y') != -1,
        s = this.selection.selection;

        this.selection.clearSelection();

        /* bound the selection to the edge of the graph */
        s.first.y  = boundY((selX && !selY) ? 0 :
                (ya.max - area.y1) * vertScale, this);
        s.second.y = boundY((selX && !selY) ? this.plotHeight - 1:
                (ya.max - area.y2) * vertScale, this);
        s.first.x  = boundX((selY && !selX) ? 0 :
                (area.x1 - xa.min) * hozScale, this);
        s.second.x = boundX((selY && !selX) ? this.plotWidth :
                (area.x2 - xa.min) * hozScale, this);

        /*
         * If we hit the edge of the graph while scrolling in either direction
         * we still move the non-bounded edge by the full amount, which shrinks
         * the selection. Lets NOT do that, because that is stupid. If we are
         * moving both sides then add the amount we were over by back onto the
         * non-bounded edge. Don't do anything special if we are only moving
         * one edge of the selection.
         */
        if ( setBoth ) {
            if ( this.axes.x.d2p(area.x2) > s.second.x ) {
                /* overflowed to the right */
                s.first.x -= this.axes.x.d2p(area.x2) - s.second.x;
            } else if ( this.axes.x.d2p(area.x1) < s.first.x ) {
                /* overflowed to the left */
                s.second.x += s.first.x - this.axes.x.d2p(area.x1);
            }
        }


        this.selection.drawSelection();
        if (!preventEvent)
            this.selection.fireSelectEvent();
    },

    /**
     * Calculates the position of the selection.
     * @param {Object} pos - Position object.
     * @param {Event} event - Event object.
     */
    setSelectionPos: function(pos, pointer) {
        var mode = this.options.selection.mode,
            selection = this.selection.selection;

        if(mode.indexOf('x') == -1) {
            pos.x = (pos == selection.first) ? 0 : this.plotWidth;
        } else {
            pos.x = boundX(pointer.relX, this);
        }

        if (mode.indexOf('y') == -1) {
            pos.y = (pos == selection.first) ? 0 : this.plotHeight - 1;
        } else {
            pos.y = boundY(pointer.relY, this);
        }
    },

    /**
     * Draws the selection box.
     */
    drawSelection: function() {

        this.selection.fireSelectEvent('selecting');

        var s = this.selection.selection,
            octx = this.octx,
            options = this.options,
            plotOffset = this.plotOffset,
            prevSelection = this.selection.prevSelection;

        if (prevSelection &&
                s.first.x == prevSelection.first.x &&
                s.first.y == prevSelection.first.y &&
                s.second.x == prevSelection.second.x &&
                s.second.y == prevSelection.second.y) {
            return;
        }

        octx.save();
        octx.strokeStyle = this.processColor(options.selection.color,
                {opacity: 0.8});
        octx.lineWidth = 1;
        octx.lineJoin = 'miter';
        octx.fillStyle = this.processColor(options.selection.color,
                {opacity: 0.4});

        this.selection.prevSelection = {
            first: { x: s.first.x, y: s.first.y },
            second: { x: s.second.x, y: s.second.y }
        };

        var x = Math.min(s.first.x, s.second.x),
            y = Math.min(s.first.y, s.second.y),
            w = Math.abs(s.second.x - s.first.x),
            h = Math.abs(s.second.y - s.first.y);

        octx.fillRect(x + plotOffset.left+0.5, y + plotOffset.top+0.5, w, h);
        octx.strokeRect(x + plotOffset.left+0.5, y + plotOffset.top+0.5, w, h);
        octx.restore();
    },

    clickSelection: function(pointer) {
        var mode = this.options.selection.mode,
            selection = this.selection.selection,
            prev = this.selection.prevSelection,
            clickcoord = { x: 0, y: 0 };

        /* TODO Deal with the y axis as well -- we don't really need it for
         * amp-web (we only care about horizontal selection) but probably
         * should add it in case we need it in the future
         */

        if(mode.indexOf('x') == -1) {
            clickcoord.x = 0;
        } else {
            clickcoord.x = boundX(pointer.relX, this);
        }

        if (clickcoord.x >= Math.min(prev.first.x, prev.second.x) &&
                clickcoord.x <= Math.max(prev.first.x, prev.second.x))
            return true;
        return false;
    },


    /**
     * Updates (draws) the selection box.
     */
    updateSelection: function(){
        if (!this.lastMousePos.pageX) return;

        this.selection.selecting = true;

        if (this.multitouches) {
            this.selection.setSelectionPos(this.selection.selection.first,
                    this.getEventPosition(this.multitouches[0]));
            this.selection.setSelectionPos(this.selection.selection.second,
                    this.getEventPosition(this.multitouches[1]));
        } else if (this.options.selection.pinchOnly) {
            return;
        } else {
            this.selection.setSelectionPos(this.selection.selection.second,
                    this.lastMousePos);
        }

        this.selection.clearSelection();

        if(this.selection.selectionIsSane()) {
            this.selection.drawSelection();
        }
    },

    /**
     * Removes the selection box from the overlay canvas.
     */
    clearSelection: function() {
        if (!this.selection.prevSelection) return;

        var prevSelection = this.selection.prevSelection,
            lw = 1,
            plotOffset = this.plotOffset,
            x = Math.min(prevSelection.first.x, prevSelection.second.x),
            y = Math.min(prevSelection.first.y, prevSelection.second.y),
            w = Math.abs(prevSelection.second.x - prevSelection.first.x),
            h = Math.abs(prevSelection.second.y - prevSelection.first.y);

        this.octx.clearRect(x + plotOffset.left - lw + 0.5,
                        y + plotOffset.top - lw,
                        w + 2 * lw + 0.5,
                        h + 2 * lw + 0.5);

        this.selection.prevSelection = null;
    },

    /**
     * Determines whether or not the selection is sane and should be drawn.
     * @return {Boolean} - True when sane, false otherwise.
     */
    selectionIsSane: function(){
        var s = this.selection.selection;
        return Math.abs(s.second.x - s.first.x) >= 5 ||
                Math.abs(s.second.y - s.first.y) >= 5;
    }

});

})();

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

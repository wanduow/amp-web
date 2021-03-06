#
# This file is part of amp-web.
#
# Copyright (C) 2013-2017 The University of Waikato, Hamilton, New Zealand.
#
# Authors: Shane Alcock
#          Brendon Jones
#
# All rights reserved.
#
# This code has been developed by the WAND Network Research Group at the
# University of Waikato. For further information please see
# http://www.wand.net.nz/
#
# amp-web is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# amp-web is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with amp-web; if not, write to the Free Software Foundation, Inc.
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Please report any bugs, questions or comments to contact@wand.net.nz
#

from ampweb.views.collections.collection import CollectionGraph

class AmpTracerouteHopsGraph(CollectionGraph):
    def __init__(self):
        self.minbin_option = "ampweb.minbin.traceroute"

    def _convert_raw(self, dp):
        result = [dp["timestamp"] * 1000]
        if "length" in dp:
            result += self._format_percentile(dp, "length")
        elif "path_length" in dp:
            result += self._format_percentile(dp, "path_length")

        return result

    def _convert_matrix(self, dp):
        result = [dp["timestamp"] * 1000]

        if 'path_length' in dp and dp['path_length'] is not None:
            if self._completed(dp):
                result.append(int(dp['path_length']))
            else:
                result.append("Unreachable")
        else:
            result.append(-1)

        return result

    def format_data(self, data):
        """ Format the data appropriately for display in the web graphs """
        results = {}
        for line, datapoints in data.items():
            groupresults = []
            for datapoint in datapoints:
                result = self._convert_raw(datapoint)
                if len(result) > 0:
                    groupresults.append(result)

            results[line] = groupresults
        return results

    def format_raw_data(self, descr, data, start, end):
        """ Format the data appropriately for raw download """
        results = []

        for line, datapoints in data.items():
            gid = int(line.split("_")[1])
            # build the metadata block for each stream
            metadata = [("collection", descr[gid]["collection"]),
                        ("source", descr[gid]["source"]),
                        ("destination", descr[gid]["destination"]),
                        # prefer the family in the line info rather than the
                        # one listed in the "aggregation" field, as that could
                        # have a special value. The line id will always be the
                        # actual value.
                        ("family", line.split("_")[2].lower()),
                        ("packet_size", descr[gid]["packet_size"]),
                       ]

            thisline = []
            for datapoint in datapoints:
                if "timestamp" not in datapoint:
                    continue
                # the block caching will modify the range of data to match the
                # block boundaries, ignore data outside our query range
                if datapoint["timestamp"] < start or datapoint["timestamp"] > end:
                    continue

                # If responses is missing then it would appear this measurement
                # was fabricated to make the line graph properly break at this
                # point. Shouldn't be possible for a real measurement to be
                # missing the field.
                if "path_length" not in datapoint:
                    continue

                if datapoint['path_length'] is None:
                    pathlen = None
                else:
                    pathlen = int(datapoint['path_length'])

                result = {
                    "timestamp": datapoint["timestamp"],
                    "path_length": pathlen,
                    "completed": self._completed(datapoint)
                }
                thisline.append(result)

            # don't bother adding any lines that have no data
            if len(thisline) > 0:
                results.append({
                    "metadata": metadata,
                    "data": thisline,
                    "datafields":["timestamp", "path_length", "completed"]
                })
        return results

    def _format_percentile(self, datapoint, column):
        """ Format path length percentile values for smokeping style graphs """
        result = []

        median = None
        if column in datapoint and datapoint[column] is not None:
            count = len(datapoint[column])
            if count > 0 and count % 2:
                median = float(datapoint[column][count//2])
            elif count > 0:
                median = (float(datapoint[column][count//2]) +
                        float(datapoint[column][count//2 - 1]))/2.0
            # Remove any fractional components used to indicate incomplete paths
            median = int(median)
        result.append(median)
        # this is normally the loss value, could we use error codes here?
        result.append(0)

        if column in datapoint and datapoint[column] is not None:
            for value in datapoint[column]:
                if value is None:
                    result.append(None)
                else:
                    result.append(int(value))
        return result

    def getMatrixTabs(self):
        return [
            {'id': 'hops-tab', 'descr': "Path Length", 'title': "Path Length"}
        ]

    def getMatrixCellDuration(self):
        return 60 * 10

    def getMatrixCellDurationOptionName(self):
        return 'ampweb.matrixperiod.hops'

    def formatTooltipText(self, result, test, metric):
        if result is None:
            return "Unknown / Unknown"

        formatted = {"ipv4": "No data", "ipv6": "No data"}

        for label, dp in result.items():
            if label.lower().endswith("_ipv4"):
                key = 'ipv4'
            if label.lower().endswith("_ipv6"):
                key = 'ipv6'

            if len(dp) == 0:
                continue

            if 'path_length' in dp[0] and dp[0]['path_length'] is not None:
                if self._completed(dp[0]):
                    formatted[key] = "%d hops" % (int(dp[0]['path_length']))
                else:
                    formatted[key] = "%d hops*" % \
                            (int(dp[0]['path_length'] - 0.5))

        return '%s / %s' % (formatted['ipv4'], formatted['ipv6'])

    def generateSparklineData(self, dp, test, metric):
        if 'path_length' not in dp or dp['path_length'] is None:
            return None

        return int(dp['path_length'])

    def generateMatrixCell(self, src, dst, urlparts, cellviews, recent,
            daydata=None):

        if (src, dst) in cellviews:
            view_id = cellviews[(src, dst)]
        else:
            view_id = -1

        keyv4 = "%s_%s_ipv4" % (src, dst)
        keyv6 = "%s_%s_ipv6" % (src, dst)
        if keyv4 not in recent and keyv6 not in recent:
            return {'view':-1}

        result = {'view':view_id, 'ipv4': -1, 'ipv6': -1}
        if keyv4 in recent and len(recent[keyv4]) > 0:
            result['ipv4'] = [1, self._convert_matrix(recent[keyv4][0])[1]]

            if daydata and keyv4 in daydata and len(daydata[keyv4]) > 0:
                result['ipv4'].append(self._convert_matrix(daydata[keyv4][0])[1])
            else:
                result['ipv4'].append(-1)


        if keyv6 in recent and len(recent[keyv6]) > 0:
            result['ipv6'] = [1, self._convert_matrix(recent[keyv6][0])[1]]
            if daydata and keyv6 in daydata and len(daydata[keyv6]) > 0:
                result['ipv6'].append(self._convert_matrix(daydata[keyv6][0])[1])
            else:
                result['ipv6'].append(-1)
        return result

    def get_collection_name(self):
        return "amp-traceroute_pathlen"

    def get_default_title(self):
        return "AMP Traceroute Hops Graphs"

    def get_matrix_viewstyle(self):
        return "amp-traceroute_pathlen"

    def get_event_label(self, streamprops):
        """ Return a formatted event label for traceroute events """
        label = "  AMP AS Traceroute from %s to " % (streamprops["source"])
        label += "%s (%s)" % (streamprops["destination"], streamprops["family"])

        return label

    def get_event_sources(self, streamprops):
        return [streamprops['source']]

    def get_event_targets(self, streamprops):
        return [streamprops['destination']]

    # TODO can we push any of this back to ampy, so that ampweb sees only one
    # style of results?
    def _parse_ippath_to_list(self, path):
        if isinstance(path, str):
            # old psycopg2 < 2.7 returns the path as a string
            if not path.startswith("{") or not path.endswith("}"):
                return None
            return path.strip("{}").split(",")
        elif isinstance(path, list):
            # psycopg2 >= 2.7 returns the path as a list
            return path
        return None

    def _parse_ippath_to_string(self, path):
        if isinstance(path, str):
            # old psycopg2 < 2.7 returns the path as a string
            if not path.startswith("{") or not path.endswith("}"):
                return ""
            return path.strip("{}")
        elif isinstance(path, list):
            # psycopg2 >= 2.7 returns the path as a list
            return ",".join([x if x else "" for x in path])
        return ""

    def get_browser_collections(self):
        # Return empty list to avoid duplicates from amp-traceroute
        return []

    # an incomplete path has 0.5 added to the length as a marker, so any
    # length that is an odd number after being doubled must not have
    # reached the destination
    # TODO use a better marker
    def _completed(self, datapoint):
        if datapoint['path_length'] is None:
            return False
        if (datapoint['path_length'] * 2) % 2 == 0:
            return True
        return False

    def get_required_scripts(self):
        return [
            "modals/amptraceroute_modal.js",
            "graphpages/amptraceroute.js",
        ]


class AmpTracerouteGraph(AmpTracerouteHopsGraph):
    def _format_ippath_summary_data(self, data):

        results = {}
        for line, datapoints in data.items():
            groupresults = []

            for dp in datapoints:
                if 'path_id' in dp:
                    groupresults.append([dp['timestamp'] * 1000, dp['path_id']])
                else:
                    groupresults.append([dp['timestamp'] * 1000, None])

            results[line] = groupresults

        return results

    def format_data(self, data):
        results = {}
        for line, datapoints in data.items():
            groupresults = []
            paths = {}

            # elements might be missing the fields we are interested in if
            # there is no data in that bin, so unfortunately we'll have to
            # look at all the data until we find one that has enough info
            # to confirm the type of result
            for datapoint in datapoints:
                # if path_id exists then this datapoint has valid data
                if 'path_id' in datapoint:
                    # if path exists then this is ippath data
                    if 'path' in datapoint:
                        break
                    # if it doesn't exist then this is ippath-summary data
                    return self._format_ippath_summary_data(data)

            for datapoint in datapoints:
                if 'aspath' not in datapoint:
                    continue
                if 'path' not in datapoint or datapoint['path'] is None:
                    continue
                if 'path_id' not in datapoint or datapoint['path_id'] is None:
                    continue

                ippath = self._parse_ippath_to_list(datapoint['path'])
                if ippath is None:
                    continue
                pathid = datapoint['path_id']

                if 'path_count' in datapoint:
                    freq = datapoint['path_count']
                else:
                    freq = 0

                if 'error_type' in datapoint:
                    errtype = datapoint['error_type']
                else:
                    errtype = None

                if 'error_code' in datapoint:
                    errcode = datapoint['error_code']
                else:
                    errcode = None

                if pathid not in paths:
                    paths[pathid] = {
                        'path':ippath,
                        'freq':freq,
                        'errtype':errtype,
                        'errcode':errcode,
                        'aspath':datapoint['aspath'],
                        'mints':datapoint['min_timestamp'],
                        'maxts':datapoint['timestamp']
                    }
                else:
                    paths[pathid]['freq'] += freq

                    if errtype > paths[pathid]['errtype']:
                        paths[pathid]['errtype'] = errtype
                    if errcode > paths[pathid]['errcode']:
                        paths[pathid]['errcode'] = errcode
                    if paths[pathid]['aspath'] is None:
                        paths[pathid]['aspath'] = datapoint['aspath']

                    if datapoint['min_timestamp'] < paths[pathid]['mints']:
                        paths[pathid]['mints'] = datapoint['min_timestamp']
                    if datapoint['timestamp'] > paths[pathid]['maxts']:
                        paths[pathid]['maxts'] = datapoint['timestamp']

            for path in list(paths.values()):
                ippath = path['path']
                if path['aspath'] is None:
                    fullpath = list(zip([0] * len(ippath), ippath))
                else:
                    aspath = []
                    astext = []
                    for x in path['aspath']:
                        aspath.append(x[2])
                        astext.append(x[0])

                    aspath = [x[2] for x in path['aspath']]
                    astext = [x[0] for x in path['aspath']]
                    fullpath = list(zip(aspath, ippath, astext))

                groupresults.append([
                        path['mints'] * 1000,
                        path['maxts'] * 1000,
                        fullpath,
                        path['errtype'],
                        path['errcode'],
                        path['freq']
                ])

            results[line] = groupresults
        return results

    def format_raw_data(self, descr, data, start, end):
        """ Format the data appropriately for raw download """
        results = []

        for line, datapoints in data.items():
            gid = int(line.split("_")[1])
            # build the metadata block for each stream
            metadata = [("collection", descr[gid]["collection"]),
                        ("source", descr[gid]["source"]),
                        ("destination", descr[gid]["destination"]),
                        # prefer the family in the line info rather than the
                        # one listed in the "aggregation" field, as that could
                        # have a special value. The line id will always be the
                        # actual value.
                        ("family", line.split("_")[2].lower()),
                        ("packet_size", descr[gid]["packet_size"]),
                       ]

            thisline = []
            for datapoint in datapoints:
                if "timestamp" not in datapoint:
                    continue
                # the block caching will modify the range of data to match the
                # block boundaries, ignore data outside our query range
                if datapoint["timestamp"] < start or datapoint["timestamp"] > end:
                    continue

                if "path" not in datapoint:
                    continue

                result = {
                    "timestamp": datapoint["timestamp"],
                    "hop_count": datapoint["length"],
                    "path": self._parse_ippath_to_string(datapoint["path"]),
                }
                thisline.append(result)

            # don't bother adding any lines that have no data
            if len(thisline) > 0:
                results.append({
                    "metadata": metadata,
                    "data": thisline,
                    "datafields":["timestamp", "hop_count", "path"]
                })
        return results

    def get_collection_name(self):
        return "amp-traceroute"

    def get_default_title(self):
        return "AMP Traceroute Graphs"

    def get_browser_collections(self):
        # Put all of our supported graphs in the base collection
        return [
        {
          "family": "AMP",
          "label": "Traceroute Map",
          "description": "Visualise all traceroute paths from an AMP monitor to a target name.",
          "link": "view/amp-traceroute"
        },

        {
          "family":"AMP",
          "label": "AS Traceroute Path",
          "description": "Measure the autonomous systems in the path from an AMP monitor to a target name.",
          "link":"view/amp-astraceroute"
        },

        {
          "family":"AMP",
          "label": "Traceroute Hop Count",
          "description":"Measure the path length from an AMP monitor to a target name.",
          "link":"view/amp-traceroute-hops"
        },
        ]

    def get_required_scripts(self):
        parentscripts = super(AmpTracerouteGraph, self).get_required_scripts()
        return parentscripts + [
            "graphtypes/tracemap.js",
            "graphstyles/tracemap-common.js",
            "graphstyles/tracemap.js",
        ]


class AmpAsTracerouteGraph(AmpTracerouteHopsGraph):
    def format_data(self, data):
        """ Format the data appropriately for display in the web graphs """
        results = {}
        for line, datapoints in data.items():
            groupresults = []
            for datapoint in datapoints:
                if "timestamp" not in datapoint:
                    continue
                result = [datapoint["timestamp"] * 1000]
                # we are able to have two different sorts of traceroute data
                # and they need to be formatted slightly differently depending
                # on how they are going to be graphed
                if "aspath" in datapoint or "path" in datapoint:
                    result += self._format_path(datapoint)
                elif "responses" in datapoint:
                    result += self._format_percentile(datapoint, "responses")

                if len(result) > 0:
                    groupresults.append(result)

            results[line] = groupresults
        return results

    def format_raw_data(self, descr, data, start, end):
        """ Format the data appropriately for raw download """
        results = []

        for line, datapoints in data.items():
            gid = int(line.split("_")[1])
            # build the metadata block for each stream
            metadata = [("collection", descr[gid]["collection"]),
                        ("source", descr[gid]["source"]),
                        ("destination", descr[gid]["destination"]),
                        # prefer the family in the line info rather than the
                        # one listed in the "aggregation" field, as that could
                        # have a special value. The line id will always be the
                        # actual value.
                        ("family", line.split("_")[2].lower()),
                        ("packet_size", descr[gid]["packet_size"]),
                       ]

            thisline = []
            for datapoint in datapoints:
                if "timestamp" not in datapoint:
                    continue
                # the block caching will modify the range of data to match the
                # block boundaries, ignore data outside our query range
                if datapoint["timestamp"] < start or datapoint["timestamp"] > end:
                    continue

                if "aspath" not in datapoint:
                    continue

                pathlen = 0
                aspath = []

                for asn in (datapoint['aspath'] or []):
                    # This is all very similar to the work done in ampy, but
                    # we don't want to do the lookups for AS names etc. We
                    # also want to be able to use different labels here.
                    asnsplit = asn.split('.')
                    if len(asnsplit) != 2:
                        continue

                    if asnsplit[1] == "-2":
                        aslabel = "rfc1918"
                    elif asnsplit[1] == "-1":
                        aslabel = ""
                    elif asnsplit[1] == "0":
                        aslabel = "unknown"
                    else:
                        aslabel = asnsplit[1]

                    repeats = int(asnsplit[0])
                    pathlen += repeats

                    for i in range(0, repeats):
                        aspath.append(aslabel)

                result = {
                    "timestamp": datapoint["timestamp"],
                    "hop_count": pathlen,
                    "aspath": ",".join(aspath),
                }
                thisline.append(result)

            # don't bother adding any lines that have no data
            if len(thisline) > 0:
                results.append({
                    "metadata": metadata,
                    "data": thisline,
                    "datafields":["timestamp", "hop_count", "aspath"]
                })
        return results

    def get_collection_name(self):
        return "amp-astraceroute"

    def get_default_title(self):
        return "AMP AS Traceroute Graphs"

    def get_browser_collections(self):
        # Return empty list to avoid duplicates from amp-traceroute
        return []

    def _format_path(self, datapoint):
        """ Format full path descriptions for rainbow style graphs """
        result = []

        if "aspath" in datapoint:
            result.append(datapoint['aspath'])
        else:
            result.append([])

        if 'aspathlen' in datapoint:
            result.append(datapoint['aspathlen'])
        else:
            result.append(0)

        return result

    def get_required_scripts(self):
        parentscripts = super(AmpAsTracerouteGraph, self).get_required_scripts()
        return parentscripts + [
            "graphstyles/rainbow.js",
            "graphtypes/rainbow.js",
        ]

# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

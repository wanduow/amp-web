from pyramid.view import view_config
from ampy import ampdb
from ampweb.views.TraceMap import return_JSON
import json
import time,datetime
import eventlabels

from threading import Lock

NNTSCConn = None
NNTSCLock = Lock()

def connect_nntsc(request):
    global NNTSCConn
    nntschost = request.registry.settings['ampweb.nntschost']
    nntscport = request.registry.settings['ampweb.nntscport']

    NNTSCConn = ampdb.create_nntsc_engine(nntschost, nntscport)

@view_config(route_name='api', renderer='json')
def api(request):
    """ Determine which API a request is being made against and fetch data """
    urlparts = request.matchdict['params']

    # Dictionary of possible internal API methods we support
    apidict = {
        '_tracemap': tracemap,
        '_matrix': matrix,
        '_matrix_axis': matrix_axis,
        '_tooltip': tooltip,
        '_event': event,
    }

    nntscapidict = {
        '_graph': graph,
        '_destinations': destinations,
        '_streams': streams,
        '_streaminfo': streaminfo,
    }

    # /api/_* are private APIs
    # /api/* is the public APIs that looks similar to the old one
    if len(urlparts) > 0:
        interface = urlparts[0]
        if interface.startswith("_"):
            if interface in nntscapidict:
                
                # API requests are asynchronous so we need to be careful
                # about avoiding race conditions on the NNTSC connection
                NNTSCLock.acquire()
                if NNTSCConn == None:
                    connect_nntsc(request); 
                NNTSCLock.release()               
                result = nntscapidict[interface](request)
                return result
            elif interface in apidict:
                return apidict[interface](request)
            else:
                return {"error": "Unsupported API method"}
    return public(request)

def public(request):
    """ Public API """
    urlparts = request.matchdict['params']

    source = None
    dest = None
    test = None
    options = None
    start = None
    end = None
    binsize = 60
    response = {}

    # What type of response is it
    rtype = {0 : "sites",
            1 : "sites",
            2 : "tests",
            3 : "subtypes",
            4 : "data",
            5 : "data",
            6 : "data",
            7 : "data",
           }

    # Keep reading until we run out of arguments
    try:
        source = urlparts[0]
        dest = urlparts[1]
        test = urlparts[2]
        options = urlparts[3]
        start = int(urlparts[4])
        end = int(urlparts[5])
        binsize = int(urlparts[6])
    except IndexError:
        pass

    db = ampdb.create()
    try:
        data = db.get(source, dest, test, options, start, end, binsize)
    except:
        return {"error": "Incorrect number of arguments"}

    # TODO check memory usage of this if a large amount of data is fetched
    # at once. Can we stream this back rather than giving it all in one go?
    response[rtype[len(urlparts)]] = []
    for d in data:
        response[rtype[len(urlparts)]].append(d)
    return {"response": response}

def tracemap(request):
    urlparts = request.matchdict['params'][1:]
    
    return return_JSON(urlparts[0], urlparts[1])


def destinations(request):
    urlparts = request.matchdict['params'][1:]
    metric = urlparts[0]

    NNTSCConn.create_parser(metric)

    params = {}

    if metric == "rrd-smokeping":
        if len(urlparts) == 1:
            params['source'] = None
        else:
            params['source'] = urlparts[1]

    if metric == "rrd-muninbytes":
        if len(urlparts) < 2:
            params['switch'] = None
        else:
            params['switch'] = urlparts[1]

        if len(urlparts) >= 3:
            params['interface'] = urlparts[2]

    if metric == "lpi-bytes":
        if len(urlparts) < 2:
            params['source'] = None
        else:
            params['source'] = urlparts[1]
        params['_requesting'] = 'users'

    return NNTSCConn.get_selection_options(metric, params)

def streaminfo(request):
    urlparts = request.matchdict['params'][1:]
    
    metric = urlparts[0]
    stream = int(urlparts[1])

    NNTSCConn.create_parser(metric)
    return NNTSCConn.get_stream_info(stream)

#    if metric == "smokeping":
#        db = ampdb.create_smokeping_engine(nntschost, nntscport)
#        streaminfo = db.get_stream_info(stream)

#    if metric == "muninbytes":
#        db = ampdb.create_muninbytes_engine(nntschost, nntscport)
#        streaminfo = db.get_stream_info(stream)

#    return streaminfo

def streams(request):
    urlparts = request.matchdict['params'][1:]
    metric = urlparts[0]

    params = {}
    NNTSCConn.create_parser(metric)

    # XXX Perhaps we should include a URL parts to params function within
    # the ampy parsers?

    if metric == "rrd-smokeping":
        if len(urlparts) > 1:
            params['source'] = urlparts[1]
        if len(urlparts) > 2:
            params['host'] = urlparts[2]

    if metric == "rrd-muninbytes":
        if len(urlparts) > 1:
            params['switch'] = urlparts[1]
        if len(urlparts) > 2:
            params['interface'] = urlparts[2]
        if len(urlparts) > 3:
            params['direction'] = urlparts[3]
    
    if metric == "lpi-bytes":
        if len(urlparts) > 1:
            params['source'] = urlparts[1]
        if len(urlparts) > 2:
            params['user'] = urlparts[2]
        if len(urlparts) > 3:
            params['protocol'] = urlparts[3]
        if len(urlparts) > 4:
            params['direction'] = urlparts[4]
        
    return NNTSCConn.get_stream_id(metric, params)

def format_smokeping_data(data):
    
    # Turn preprocessing off in the graph and we can return useful
    # data to flotr rather than the braindead approach envision wants.
    # It still has to be an array of various bits in special locations
    # though, if you give it an object with nice names it interprets
    # each object as a series - what about an object, with a list of
    # objects within it? that might work, though it seems like it
    # might cause difficulties for auto axis detection etc.
    results = []
    for datapoint in data:
        result = [
            datapoint["timestamp"] * 1000,
            datapoint["median"],
        ]
        if datapoint["loss"] is None:
            result.append(None)
        else:
            result.append(float(str(datapoint["loss"])))
        for ping in datapoint["pings"]:
            result.append(ping)
        results.append(result)
    return results

def format_muninbytes_data(data):
    x_values = []
    y_values = []

    for datapoint in data:
        x_values.append(datapoint["timestamp"] * 1000)
        if "mbps" in datapoint and datapoint["mbps"] != None:
            y_values.append(float(datapoint["mbps"]))
        else:
            y_values.append(None)

    return [x_values, y_values]

def format_lpibytes_data(data):
    x_values = []
    y_values = []

    for datapoint in data:
        x_values.append(datapoint["timestamp"] * 1000)
        if datapoint["mbps"] != None:
            y_values.append(float(datapoint["mbps"]))
        else:
            y_values.append(None)
    return [x_values, y_values] 

def request_nntsc_data(metric, params, detail):
    stream = int(params[0])
    start = int(params[1])
    end = int(params[2])

    if len(params) >= 4:
        binsize = int(params[3])
    else:
        binsize = int((end - start) / 300)

    NNTSCConn.create_parser(metric)
    data = NNTSCConn.get_period_data(stream, start, end, binsize, detail)

    return data

def graph(request):
    """ Internal graph specific API """
    urlparts = request.matchdict['params'][1:]
    if len(urlparts) < 2:
        return [[0], [0]]

    data = request_nntsc_data(urlparts[0], urlparts[1:], "full")

    # Unfortunately, we still need to mess around with the data and put it
    # in exactly the right format for our graphs
    if urlparts[0] == "rrd-smokeping":
        return format_smokeping_data(data)
    elif urlparts[0] == "rrd-muninbytes":
        return format_muninbytes_data(data) 
    elif urlparts[0] == "lpi-bytes":
        return format_lpibytes_data(data)
    else:
        return [[0],[0]]


def get_formatted_latency(conn, src, dst, duration):
    """ Fetch the average latency and format it for printing with units """
    result = conn.get_recent_data(src, dst, "icmp", "0084", duration)
    if result.count() > 0:
        value = result.fetchone()["rtt_ms"]["mean"]
        if value >= 0:
            return "%dms" % round(value)
    return "No data"

def get_formatted_loss(conn, src, dst, duration):
    """ Fetch the average loss and format it for printing with units """
    result = conn.get_recent_data(src, dst, "icmp", "0084", duration)
    if result.count() > 0:
        data = result.fetchone()
        return "%d%%" % round(data["rtt_ms"]["loss"] * 100)
    return "No data"

def get_formatted_hopcount(conn, src, dst, duration):
    """ Fetch the average hopcount and format it for printing with units """
    result = conn.get_recent_data(src, dst, "trace", "trace", duration)
    if result.count() > 0:
        data = result.fetchone()
        if data["path"] is not False:
            return "%d hops" % (len(data["path"]) + 1)
    return "No data"


def stats_tooltip(src, dst, rows, sparkline):
    """ Generate the HTML for a tooltip showing aggregate statistics """
    # Build header with source an destination names
    html = '<table class="tooltip">'
    html += '<tr><td class="tooltip_title" colspan="2">'
    html += '<b>%s</b><br> to <br><b>%s</b>' % (src, dst)
    html += '</td></tr>'

    # TODO make the "top" style actually do something (bold)
    for row in rows:
        html += '<tr><td class="tooltip_metric %s">' % row["classes"]
        html += '%s:</td>' % row["label"]
        html += '<td class="tooltip_period_value %s">' % row["classes"]
        html += '%s' % row["value"]
        html += '</td></tr>'

    if sparkline:
        html += '<tr><td colspan="2" id="tooltip_sparkline_descrip">'
        #html += 'Highest value in 24 hours: %dms<br />' % summary["max"]
        #html += 'Lowest value in 24 hours: %dms' %  summary["min"]
        html += 'Last 24 hours:'
        html += '</td></tr>'
        html += '<tr><td colspan="2" id="tooltip_sparkline"></td></tr>'
    else:
        html += '<tr><td colspan="2" id="tooltip_sparkline_none">'
        html += 'No data available for the last 24 hours'
        html += '</td></tr>'

    html += "</table>"
    return html


def site_info_tooltip(site):
    """ Generate the HTML for a tooltip describing a single site """
    conn = ampdb.create()
    info = conn.get_site_info(site)
    if len(info) > 0:
        return {
            "site": "true", # why not a boolean True?
            # TODO only add description if there is one? formatting? bold?
            "site_info": "<p>%s (%s)</p><p>%s</p>" % (
                    info["longname"],
                    info["location"],
                    info["description"])
        }
    return {}


def get_full_name(conn, site):
    """ Get the full name of a site """
    info = conn.get_site_info(site)
    if len(info) > 0:
        return info["longname"]
    return site


def get_tooltip_data(conn, src, dst, data_func):
    """ Get the tooltip data for different time periods over the last week """
    return [
        {
            "label": "Current",
            "value": data_func(conn, src, dst, 60*10),
            "classes": "top"
        },
        {
            "label": "1 hour average",
            "value": data_func(conn, src, dst, 60*60),
            "classes": ""
        },
        {
            "label": "24 hour average",
            "value": data_func(conn, src, dst, 60*60*24),
            "classes": ""
        },
        {
            "label": "7 day average",
            "value": data_func(conn, src, dst, 60*60*24*7),
            "classes": "bottom"
        },
    ]


def get_sparkline_data(conn, src, dst, metric):
    """ Get highly aggregated data from the last 24 hours for sparklines """
    duration = 60 * 60 * 24
    binsize = 1800
    sparkline = []
    #mean = -1
    minimum = -1
    maximum = -1

    if metric == "latency":
        data = conn.get_recent_data(src, dst, "icmp", "0084", duration, binsize)
        for datapoint in data:
            if datapoint["rtt_ms"]["mean"] >= 0:
                sparkline.append(int(round(datapoint["rtt_ms"]["mean"])))
            else:
                sparkline.append("null")
        sparkline_ints = [x for x in sparkline if isinstance(x, int)]
        if len(sparkline_ints) > 0:
            minimum = min(sparkline_ints)
            maximum = max(sparkline_ints)
            #mean =

    elif metric == "loss":
        data = conn.get_recent_data(src, dst, "icmp", "0084", duration, binsize)
        for datapoint in data:
            sparkline.append(int(round(datapoint["rtt_ms"]["loss"] * 100)))
        maximum = max(sparkline)
        minimum = min(sparkline)
        #mean =

    elif metric == "hops":
        # TODO mark cells where the traceroute didn't complete properly
        data = conn.get_recent_data(src, dst, "trace", "trace", duration,
                binsize)
        for datapoint in data:
            if datapoint["path"]:
                sparkline.append(len(datapoint["path"]))
            else:
                sparkline.append("null")
        sparkline_ints = [x for x in sparkline if isinstance(x, int)]
        if len(sparkline_ints) > 0:
            minimum = min(sparkline_ints)
            maximum = max(sparkline_ints)
            #mean =
    else:
        return {}

    return {
        "sparklineDataMin": minimum,
        "sparklineDataMax": maximum,
        #"sparklineDataMean": mean,
        "sparklineData": sparkline,
    }


def build_data_tooltip(src, dst, metric, data_func):
    """ Build a tooltip showing data between a pair of sites for one metric """
    conn = ampdb.create()
    # ideally the bits of sparkline data shouldn't be at the top level?
    data = get_sparkline_data(conn, src, dst, metric)
    rows = get_tooltip_data(conn, src, dst, data_func)
    data['tableData'] = stats_tooltip(get_full_name(conn, src),
            get_full_name(conn, dst), rows,
            True if data["sparklineDataMax"] >= 0 else False)
    data['test'] = metric
    data['site'] = "false"
    return data



# TODO move all the tooltip functions out into their own source file
def tooltip(request):
    """ Internal tooltip specific API """
    urlparts = request.GET
    cell_id = urlparts['id']
    # Remove the src__ and dst__ tags, as they're only needed on the client side
    cell_id = cell_id.replace("src__", "").replace("dst__", "")

    # if there is only a single name, return a tooltip for a site
    if cell_id.find("__to__") == -1:
        return json.dumps(site_info_tooltip(cell_id))

    # If there are two names then return a detailed tooltip and sparkline data
    # Split the ID into the src and dst ID's
    site_names = cell_id.split("__to__", 1)
    src = site_names[0]
    dst = site_names[1]

    data = {}
    if "test" in urlparts:
        test = urlparts["test"]
        if test == "latency":
            data = build_data_tooltip(src, dst, test, get_formatted_latency)
        elif test == "loss":
            data = build_data_tooltip(src, dst, test, get_formatted_loss)
        elif test == "hops":
            data = build_data_tooltip(src, dst, test, get_formatted_hopcount)
        # TODO: Mtu tooltip information
        elif test == "mtu":
            data = {}
    return json.dumps(data)

def matrix(request):
    """ Internal matrix specific API """
    urlparts = request.GET
    conn = ampdb.create()

    ampy_test = None
    subtest = None
    index = None
    sub_index = None
    src_mesh = "nz"
    dst_mesh = "nz"
    test = "latency"

    # Keep reading until we run out of arguments
    try:
        test = urlparts['testType']
        src_mesh = urlparts['source']
        dst_mesh = urlparts['destination']
    except IndexError:
        pass

    # Display a 10 minute average in the main matrix cells: 60s * 10min.
    duration = 60 * 10

    if test == "latency":
        ampy_test = "icmp"
        subtest = "0084"
    elif test == "loss":
        ampy_test = "icmp"
        subtest = "0084"
    elif test == "hops":
        ampy_test = "trace"
        subtest = "trace"
        duration = 60 * 15
    elif test == "mtu":
        # TODO add MTU data
        return {}

    sources = conn.get_sources(mesh=src_mesh)

    tableData = []
    # Query for data between every source and destination
    for src in sources:
        rowData = [src]
        # Get all the destinations that are in this mesh. We can't exclude
        # the site we are testing from because otherwise the table won't
        # line up properly - it expects every cell to have data
        destinations = conn.get_destinations(mesh=dst_mesh)
        for dst in destinations:
            # Get IPv4 data
            result4 = conn.get_recent_data(src, dst, ampy_test, subtest,
                    duration)
            if result4.count() > 0:
                queryData = result4.fetchone()
                if test == "latency":
                    recent = int(round(queryData["rtt_ms"]["mean"]))
                    # Get the last weeks average for the dynamic scale
                    result_24_hours = conn.get_recent_data(src, dst, ampy_test,
                            subtest, 86400)
                    day_data = result_24_hours.fetchone()
                    minimum = int(round(day_data["rtt_ms"]["min"]))
                    value = [recent, minimum]
                elif test == "loss":
                    value = int(round(queryData["rtt_ms"]["loss"] * 100))
                elif test == "hops":
                    if queryData["path"]:
                        value = len(queryData["path"]) + 1
                    else:
                        value = -1
                rowData.append(value)
            else:
                # This value marks src/dst combinations that do not have data.
                # eg testing to self, or to a dest that isn't tested to from
                # this particular source (but is still in the same mesh).
                rowData.append("X")
            # Get IPv6 data
            # src6 = src + ":v6"
            # dst6 = dst + ":v6"
            # result6 = conn.get_recent_data(src6, dst6, ampy_test, subtest,
            #        duration)
            # if result6.count() > 0:
                # queryData = result6.fetchone()
                # if test == "latency":
                    # value = int(round(queryData[index][sub_index]))
                # elif test == "loss":
                    # missing = queryData[index]["missing"]
                    # present = queryData[index]["count"]
                    # loss = 100.0 * missing / (missing + present)
                    # value = int(round(loss))
                # rowData.append(value)
            # else:
                # rowData.append("X")
        tableData.append(rowData)

    # Create a dictionary to store the data in a way that DataTables expects
    data_list_dict = {}
    data_list_dict.update({'aaData': tableData})
    return data_list_dict

def matrix_axis(request):
    """ Internal matrix thead specific API """
    urlparts = request.GET
    conn = ampdb.create()

    # Get the list of source and destination nodes and return it
    src_mesh = urlparts['srcMesh']
    dst_mesh = urlparts['dstMesh']
    result_src = conn.get_sources(mesh=src_mesh)
    result_dst = conn.get_destinations(mesh=dst_mesh)
    result = {'src': result_src, 'dst': result_dst}
    return result

# TODO we probably want to think about moving some of these functions outside
# of this file, all the different APIs are getting crammed in here together.
def event(request):
    """ Internal event fetching API """
    start = None
    end = None
    result = []
    urlparts = request.matchdict['params']
    eventdb = request.registry.settings['ampweb.eventdb']

    # if it's only 4 parts then assume it's a statistic, a start time and an
    # end time, and that we are only after high level statistics, not the
    # individual events
    if len(urlparts) == 4:
        # count of events over the time period, currently with fixed 30m bins
        if urlparts[1] == "count":
            start = int(urlparts[2])
            end = int(urlparts[3])
            conn = ampdb.create_netevmon_engine(None, eventdb, None)
            groups = conn.get_event_groups(start, end)

            # 30 minute bins, every bin must be present, even if empty
            binsize = 60 * 30
            bin_count = 0
            binstart = 0
            result = []

            # fetch all the data now - there shouldn't be a lot of it and
            # it makes it much easier to check it all.
            # TODO Could do something smarter that means we don't have to
            # check through the whole data list every time, but this works
            # for now
            events = []
            event_ids = []
            for group in groups:
                group_events = conn.get_events_in_group(group["group_id"])
                for group_event in group_events:
                    # avoid counting events twice if they have multiple groups
                    if group_event["event_id"] not in event_ids:
                        events.append(group_event)

            # loop across the whole bin space, looking at every bin even if
            # it's possibly empty - we still need to put a zero there.
            while binstart < end:
                event_count = 0
                # figure out when the current bin starts and ends
                binstart = start + (bin_count * binsize)
                binend = binstart + binsize

                for event in events:
                    # count each event that fits within this bin
                    ts = time.mktime(event["event_time"].timetuple())
                    if ts >= binstart and ts < binend:
                        event_count += 1
                result.append([binstart * 1000, event_count])
                bin_count += 1
            return result

        # per source/target event counts for the time period, for bar graphs
        if urlparts[1] == "source" or urlparts[1] == "target":
            start = int(urlparts[2])
            end = int(urlparts[3])
            conn = ampdb.create_netevmon_engine(None, eventdb, None)
            groups = conn.get_event_groups(start, end)
            sites = {}
            for group in groups:
                events = conn.get_events_in_group(group["group_id"])
                # count this event for the source or target
                for event in events:
                    if event["%s_name" % urlparts[1]] in sites:
                        sites[event["%s_name" % urlparts[1]]] += 1
                    else:
                        sites[event["%s_name" % urlparts[1]]] = 1
            # massage the dict into a list of objects that we can then sort
            # by the number of events. This seems a bit convoluted.
            result = []
            for site,count in sites.items():
                result.append({"site": site, "count": count})
            result.sort(lambda x,y: y["count"] - x["count"])
            return result

        if urlparts[1] == "groups":
            start = int(urlparts[2])
            end = int(urlparts[3])
            conn = ampdb.create_netevmon_engine(None, eventdb, None)
            data = conn.get_event_groups(start, end)

            groups = []
            for group in data:
                # build the label describing the event group
                label = group["group_start_time"].strftime(
                        "%H:%M:%S %A %B %d %Y")
                label += " (%s, %s)" % (
                        eventlabels.get_site_count_label(
                            group["group_site_count"]),
                        eventlabels.get_event_count_label(
                            group["group_event_count"])
                        )

                # get all the events in the event group ready for display
                group_events = conn.get_events_in_group(group["group_id"])
                events = []
                for event in group_events:
                    # insert most recent events at the front of the list
                    events.insert(0, {
                        "label": eventlabels.get_event_label(event),
                        "description": event["event_description"],
                        "href": eventlabels.get_event_href(event),
                    })

                # add the most recent event groups at the front of the list
                groups.insert(0, {
                        "id": group["group_id"],
                        "label": label,
                        "events": events,
                })

            return groups

    # if it didn't match any of the short forms, then it has to be a longer
    # url with more information or it is invalid.
    if len(urlparts) < 4:
        return {}

    try:
        datatype = urlparts[1]
        stream = int(urlparts[2])
        start = int(urlparts[3])
        end = int(urlparts[4])
    except IndexError:
        pass

    # TODO stop hardcoding all these values!
    conn = ampdb.create_netevmon_engine(None, eventdb, None)
    data = conn.get_stream_events(stream, start, end)

    for datapoint in data:
        result.append({
            "description": datapoint["event_description"],
            "severity": datapoint["severity"],
            "ts": datapoint["timestamp"] * 1000,
        })
    return result

# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

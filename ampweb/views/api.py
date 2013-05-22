from pyramid.view import view_config
from ampy import ampdb
from ampweb.views.TraceMap import return_JSON
import json

@view_config(route_name='api', renderer='json')
def api(request):
    """ Determine which API a request is being made against and fetch data """
    urlparts = request.matchdict['params']

    # Dictionary of possible internal API methods we support
    apidict = {
        '_graph': graph,
        '_matrix': matrix,
        '_matrix_axis': matrix_axis,
        '_tooltip': tooltip,
        '_event': event,
    }

    # /api/_* are private APIs
    # /api/* is the public APIs that looks similar to the old one
    if len(urlparts) > 0:
        interface = urlparts[0]
        if interface.startswith("_"):
            if interface in apidict:
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

# TODO move dest out of here, use the public api for those if we can
# TODO make timeseries and tracemap two different apis...
def graph(request):
    """ Internal graph specific API """
    graphtypes = {
        "latency": "mean",
        "jitter": "jitter",
         "loss": "loss",
         "smokeping": "smokeping",
         "muninbytes": "muninbytes"
         }
    urlparts = request.matchdict['params'][1:]

    # Returns Destinations for a given Source
    if urlparts[0] == "dest":
        # XXX so hax, there has to be a much better way
        # what other information do we have at this point? It looks like we
        # need to rearrange the URL so that the test is included near the
        # front so we know what sort of data we need.
        if urlparts[1] == "prophet":
            return ampdb.create_smokeping_engine("prophet", 61234).get_destinations(src=urlparts[1])
        elif "Red Cable" in urlparts[1]:
            # Sorry, just made it more hax -- Shane
            return ampdb.create_muninbytes_engine("prophet", 61234).get_destinations(src=urlparts[1])
        else:
            return ampdb.create().get_destinations(src=urlparts[1])

    # Returns the traceroute tree for the path analysis graph
    if urlparts[0] == "tracemap":
        return return_JSON(urlparts[1], urlparts[2])

    if urlparts[0] == "timeseries":
        if len(urlparts) < 5:
            return [[0], [0]]

        # XXX this whole metric handling thing is balls
        metric = graphtypes[urlparts[1]]
        src = urlparts[2]
        dst = urlparts[3]
        start = int(urlparts[4])
        end = int(urlparts[5])
        if len(urlparts) >= 7:
            binsize = int(urlparts[6])
        else:
            binsize = int((end - start) / 300)

        if urlparts[1] not in graphtypes:
            return [[0], [0]]

        if urlparts[1] == "smokeping":
            data = ampdb.create_smokeping_engine("prophet", 61234).get_all_data(src, dst, start, end, binsize)
        elif urlparts[1] == "muninbytes":
            data = ampdb.create_muninbytes_engine("prophet", 61234).get_all_data(src, dst, start, end, binsize)
        else:
            data = ampdb.create().get(src, dst, "icmp", "0084", start, end, binsize)
        if data.count() < 1:
            return [[0], [0]]

        if metric == "smokeping":
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

        else:
            x_values = []
            y_values = []
            for datapoint in data:
                if metric == "muninbytes":
                    x_values.append(datapoint["timestamp"] * 1000)
                else:
                    x_values.append(datapoint["time"] * 1000)

                if metric == "muninbytes":
                    if datapoint["bytes"] != None:
                        y_values.append(float(datapoint["bytes"]) / 1000000.0)
                    else:
                        y_values.append(None)
                elif metric == "loss":
                    y_values.append(datapoint["rtt_ms"]["loss"] * 100)
                elif datapoint["rtt_ms"][metric] >= 0:
                    y_values.append(datapoint["rtt_ms"][metric])
                else:
                    y_values.append(None)
            return [x_values, y_values]
    return False

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


def event(request):
    """ Internal event fetching API """
    start = None
    end = None
    result = []
    urlparts = request.matchdict['params']
    if len(urlparts) < 4:
        return {}
    try:
        datatype = urlparts[1]
        src = urlparts[2]
        dst = urlparts[3]
        start = int(urlparts[4])
        end = int(urlparts[5])
    except IndexError:
        pass

    # TODO stop hardcoding all these values!
    
    if datatype == "smokeping":
        db = ampdb.create_smokeping_engine("prophet", 61234)
    elif datatype == "muninbytes":
        db = ampdb.create_muninbytes_engine("prophet", 61234)
    else:
        return {}
    
    conn = ampdb.create_netevmon_engine(None, "event_test2", None)
    data = conn.get_stream_events(db.get_stream_id(src, dst), start, end)

    for datapoint in data:
        result.append({
            "description": datapoint["event_description"],
            "severity": datapoint["severity"],
            "ts": datapoint["timestamp"] * 1000,
        })
    return result

# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from ampweb.views.common import getCommonScripts, initAmpy
import datetime
import time
import eventlabels

@view_config(route_name='home', renderer='../templates/skeleton.pt')
@view_config(route_name="dashboard", renderer="../templates/skeleton.pt")
def dashboard(request):
    """ Generate the content for the basic overview dashboard page """
    page_renderer = get_renderer("../templates/dashboard.pt")
    body = page_renderer.implementation().macros["body"]

    # display events from the last 24 hours
    end = time.time()
    start = end - (60 * 60 * 24)

    ampy = initAmpy(request)
    if ampy is None:
        print "Unable to start ampy while generating event dashboard"
        return None

    data = ampy.get_event_groups(start, end)
    groups = []
    total_event_count = 0
    total_group_count = 0

    # count global event/group statistics
    for group in data:
        total_group_count += 1
        total_event_count += group["event_count"]

    # get extra information about the 10 most recent event groups
    for group in data[-10:]:
        # build the label describing roughly what the event group contains
        dt = datetime.datetime.fromtimestamp(group["ts_started"])
        label = dt.strftime("%H:%M:%S %A %B %d %Y")

        label += " %s detected for %s %s" % ( \
                eventlabels.get_event_count_label(group["event_count"]),
                group['grouped_by'], group['group_val'])

        # get all the events in the event group ready for display
        group_events = ampy.get_event_group_members(group["group_id"])
        events = []
        for event in group_events:
            streamprops = ampy.get_stream_properties(event['collection'], event['stream'])
            # insert most recent events at the front of the list
            events.insert(0, {
                "label": eventlabels.get_event_label(event, streamprops),
                "description": event["description"],
                "href": eventlabels.get_event_href(event),
            })

        # add the most recent event groups at the front of the list
        groups.insert(0, {
                "id": group["group_id"],
                "label": label,
                "events": events,
        })

    dashboard_scripts = getCommonScripts() + [
        "pages/dashboard.js",
        "graphplugins/hit.js",
        "graphstyles/event_frequency.js",
    ]

    return {
            "title": "Event Dashboard",
            "page": "dashboard",
            "body": body,
            "styles": None,
            "scripts": dashboard_scripts,
            "groups": groups,
            "total_event_count": total_event_count,
            "total_group_count": total_group_count,
            "extra_groups": total_group_count - len(groups),
           }


# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

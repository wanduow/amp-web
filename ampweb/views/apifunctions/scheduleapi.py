import getopt
import json
from pyramid.view import view_config
from pyramid.httpexceptions import *
from ampweb.views.common import initAmpy

# TODO Check http caching is disabled for all these views

# XXX GET THESE FROM AMPY?
SCHEDULE_OPTIONS = ["test", "source", "destination", "frequency", "start",
                    "end", "period", "mesh_offset", "args"]
PERMISSION = 'edit'

def validate_args(test, args):
    testopts = {
        "icmp": "s:",
        "traceroute": "I:abfp:rs:S:4:6:",
        "dns": "I:q:t:c:z:rsn4:6:",
        "tcpping": "I:p:P:rs:S:4:6:",
        "throughput": "I:t:d:p:P:4:6:",
        "http": "u:cp",
        "udpstream": "I:d:D:n:p:P:z:4:6:",
    }

    if test not in testopts:
        return False

    optstring = testopts[test]

    # We don't care about the actual arguments and what their values are, we
    # only care that it was able to be parsed 100%. The test itself will
    # double check that it has sane values for each option. Maybe we should
    # do more here, so we don't end up with tests that will fail on startup.
    try:
        _, remaining = getopt.getopt(args.split(), optstring)
        # make sure all arguments were parsed
        if len(remaining) > 0:
            return False
    except getopt.GetoptError:
        # any error parsing causes this to fail
        return False
    return True


@view_config(
    route_name='schedules',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def get_source_schedule(request):
    return HTTPNotImplemented()


@view_config(
    route_name='schedules',
    request_method='POST',
    renderer='json',
    permission=PERMISSION,
)
def create_schedule(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    try:
        body = request.json_body
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "invalid body"}))

    # XXX who should verify that some of the other stuff makes sense? like only
    # http tests having zero destinations. or will that just not be an issue
    # as we can schedule tests with no targets perfectly ok. But maybe we want
    # to ensure all tests meet minumum/maximum number of targets (which amplet
    # client and ampweb/static/scripts/modals/schedule_modal.js knows)
    # XXX can we populate that javascript from a python file?
    for item in SCHEDULE_OPTIONS:
        if item not in body:
            return HTTPBadRequest(body=json.dumps(
                        {"error": "Missing option '%s'" % item}))

    if not validate_args(body["test"], body["args"]):
        return HTTPBadRequest(body=json.dumps(
                {"error": "Bad arguments '%s'" % body["args"]}))

    schedule_id = ampy.schedule_new_amp_test(body)
    if schedule_id >= 0:
        url = request.route_url('schedule',
                name=request.matchdict["name"], schedule_id=schedule_id)
        return HTTPCreated(headers=[("Location", url)], body=json.dumps({
                    "schedule_id": schedule_id,
                    "url": url,
                    }))
    return HTTPBadRequest()


@view_config(
    route_name='schedule',
    request_method='PUT',
    renderer='json',
    permission=PERMISSION,
)
def modify_schedule(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    try:
        body = request.json_body
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "invalid body"}))

    if len(set(SCHEDULE_OPTIONS).intersection(body)) == 0:
        return HTTPBadRequest(body=json.dumps(
                    {"error": "No valid options to update"}))

    # if args is present then the test name also needs to be set to validate
    if "args" in body:
        if "test" not in body:
            return HTTPBadRequest(body=json.dumps(
                        {"error":"Missing test type"}))
        if not validate_args(body["test"], body["args"]):
            return HTTPBadRequest(body=json.dumps(
                        {"error": "Bad arguments %s" % body["args"]}))

    result = ampy.update_amp_test(request.matchdict["schedule_id"], body)

    if result is None:
        return HTTPInternalServerError()
    if result:
        return HTTPNoContent()
    return HTTPNotFound()


@view_config(
    route_name='schedule',
    request_method='DELETE',
    renderer='json',
    permission=PERMISSION,
)
def delete_schedule(request):
    """ Delete the specified schedule test item """
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    result =  ampy.delete_amp_test(request.matchdict["schedule_id"])

    if result is None:
        return HTTPInternalServerError()
    if result:
        return HTTPNoContent()
    return HTTPNotFound()


@view_config(
    route_name='status',
    request_method='PUT',
    renderer='json',
    permission=PERMISSION,
)
def set_schedule_status(request):
    """ Set the enabled status of the specified schedule test item """
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    try:
        body = request.json_body
        status = body["status"]
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "missing status"}))

    if status in ["enable", "enabled", "on", "active", "yes"]:
        result = ampy.enable_amp_test(request.matchdict["schedule_id"])
    elif status in ["disable", "disabled", "off", "inactive", "no"]:
        result = ampy.disable_amp_test(request.matchdict["schedule_id"])
    else:
        return HTTPBadRequest(body=json.dumps({"error":"invalid status value"}))

    if result is None:
        return HTTPInternalServerError()
    if result:
        return HTTPNoContent()
    return HTTPNotFound()


@view_config(
    route_name='status',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def schedule_status(request):
    """ Get the enabled status of the specified schedule test item """
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    status = ampy.is_amp_test_enabled(request.matchdict["schedule_id"])
    if status is None:
        response = HTTPNotFound()
    else:
        if status:
            response = HTTPOk(body=json.dumps({"status": "enabled"}))
        else:
            response = HTTPOk(body=json.dumps({"status": "disabled"}))
    return response


@view_config(
    route_name='destinations',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def get_destinations(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    item = ampy.get_amp_schedule_by_id(request.matchdict["schedule_id"])

    if item is None:
        return HTTPInternalServerError()
    if len(item) == 0:
        return HTTPNotFound()

    sites = item["dest_site"] if "dest_site" in item else []
    meshes = item["dest_mesh"] if "dest_mesh" in item else []
    return HTTPOk(body=json.dumps({"dest_sites": sites, "dest_meshes": meshes}))


@view_config(
    route_name='destinations',
    request_method='POST',
    renderer='json',
    permission=PERMISSION,
)
def add_endpoint(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    try:
        body = request.json_body
        destination = body["destination"]
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "missing destination"}))

    result = ampy.add_amp_test_endpoints(request.matchdict["schedule_id"],
            request.matchdict["name"], destination)

    if result is None:
        return HTTPInternalServerError()
    if result:
        return HTTPNoContent()
    return HTTPBadRequest()


@view_config(
    route_name='destination',
    request_method='DELETE',
    renderer='json',
    permission=PERMISSION,
)
def delete_endpoint(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    result = ampy.delete_amp_test_endpoints(request.matchdict["schedule_id"],
            request.matchdict["name"], request.matchdict["destination"])

    if result is None:
        return HTTPInternalServerError()
    if result:
        return HTTPNoContent()
    return HTTPNotFound()


@view_config(
    route_name='schedule',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def get_single_schedule(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    item = ampy.get_amp_schedule_by_id(request.matchdict["schedule_id"])

    if item is None:
        return HTTPInternalServerError()
    if len(item) == 0:
        return HTTPNotFound()
    return HTTPOk(body=json.dumps(item))


# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

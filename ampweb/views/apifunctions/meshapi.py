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

import json
import re
import urllib.request, urllib.parse, urllib.error
from pyramid.view import view_config
from pyramid.httpexceptions import *
from ampweb.views.common import initAmpy, escapeURIComponent
from ampweb.views.item import get_mesh_members

# TODO better name for api? it covers sites and meshes but is called mesh

PERMISSION = 'editconfig'

@view_config(
    route_name='meshsites',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
@view_config(
    route_name='sitemeshes',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def get_members(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    if request.matched_route.name == "sitemeshes":
        members = ampy.get_meshes(None,
                site=urllib.parse.unquote(request.matchdict["name"]))
    elif request.matched_route.name == "meshsites":
        # TODO using this function is not ideal, could be done better in ampy
        members = get_mesh_members(ampy,
                urllib.parse.unquote(request.matchdict["mesh"]))

    # TODO deal with not existing vs zero mesh membership
    if members is None:
        return HTTPInternalServerError()
    if members is False:
        return HTTPNotFound()

    return HTTPOk(body=json.dumps({"membership": members}))


@view_config(
    route_name='meshsites',
    request_method='POST',
    renderer='json',
    permission=PERMISSION,
)
@view_config(
    route_name='sitemeshes',
    request_method='POST',
    renderer='json',
    permission=PERMISSION,
)
def add_member(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    try:
        body = request.json_body
        if request.matched_route.name == "meshsites":
            mesh = urllib.parse.unquote(request.matchdict["mesh"])
            site = body["site"]
        else:
            mesh = body["mesh"]
            site = urllib.parse.unquote(request.matchdict["name"])
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "missing value"}))

    if re.search("[^.:/a-zA-Z0-9_-]", site) is not None:
        return HTTPBadRequest(body=json.dumps({
            "error": "bad characters in site name"
        }))

    if ampy.add_amp_mesh_member(mesh, site):
        return HTTPNoContent()
    return HTTPNotFound()


@view_config(
    route_name='meshsite',
    request_method='DELETE',
    renderer='json',
    permission=PERMISSION,
)
@view_config(
    route_name='sitemesh',
    request_method='DELETE',
    renderer='json',
    permission=PERMISSION,
)
def remove_member(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    if ampy.delete_amp_mesh_member(urllib.parse.unquote(request.matchdict["mesh"]),
            urllib.parse.unquote(request.matchdict["name"])):
        return HTTPNoContent()
    return HTTPNotFound()


@view_config(
    route_name='allsites',
    request_method='GET',
    renderer='json',
    # if you can read the data, you should be able to list the sites (so use
    # the default permission here)
    #permission=,
)
@view_config(
    route_name='allmeshes',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def get_all_items(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    if request.matched_route.name == "allsites":
        items = ampy.get_amp_sites()
        label = "sites"
    elif request.matched_route.name == "allmeshes":
        items = ampy.get_meshes(None)
        label = "meshes"

    if items is None:
        return HTTPInternalServerError()
    return HTTPOk(body=json.dumps({label: items}))


@view_config(
    route_name='allsites',
    request_method='POST',
    renderer='json',
    permission=PERMISSION,
)
@view_config(
    route_name='allmeshes',
    request_method='POST',
    renderer='json',
    permission=PERMISSION,
)
def create_item(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    try:
        body = request.json_body
        ampname = body["ampname"]
        longname = body["longname"]
        description = body["description"]
        if request.matched_route.name == "allsites":
            location = body["location"]
        elif request.matched_route.name == "allmeshes":
            public = body["public"]
            issource = body["issource"]
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "missing value"}))

    if re.search("[^.:/a-zA-Z0-9_-]", ampname) is not None:
        return HTTPBadRequest(body=json.dumps({
            "error": "bad characters in ampname"
        }))

    if request.matched_route.name == "allsites":
        result = ampy.add_amp_site(ampname, longname, location, description)
        url = request.route_url("onesite", name=escapeURIComponent(ampname))
        label = "site"
    elif request.matched_route.name == "allmeshes":
        result = ampy.add_amp_mesh(ampname, longname, description, public,
                issource)
        url = request.route_url("onemesh", mesh=escapeURIComponent(ampname))
        label = "mesh"
    else:
        return HTTPBadRequest()

    if result:
        return HTTPCreated(headers=[("Location", url)], body=json.dumps({
                    label: {
                        "ampname": ampname,
                        "url": url,
                    }}))

    return HTTPBadRequest()


@view_config(
    route_name='onesite',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
@view_config(
    route_name='onemesh',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def get_item(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    if request.matched_route.name == "onesite":
        item = ampy.get_amp_site_info(urllib.parse.unquote(request.matchdict["name"]))
        label = "site"
    elif request.matched_route.name == "onemesh":
        item = ampy.get_amp_mesh_info(urllib.parse.unquote(request.matchdict["mesh"]))
        label = "mesh"

    if item is None:
        return HTTPInternalServerError()
    if "unknown" in item and item["unknown"] is True:
        return HTTPNotFound()

    return HTTPOk(body=json.dumps({label: item}))


@view_config(
    route_name='onesite',
    request_method='PUT',
    renderer='json',
    permission=PERMISSION,
)
@view_config(
    route_name='onemesh',
    request_method='PUT',
    renderer='json',
    permission=PERMISSION,
)
def update_item(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    try:
        body = request.json_body
        longname = body["longname"]
        description = body["description"]
        if request.matched_route.name == "onesite":
            location = body["location"]
        elif request.matched_route.name == "onemesh":
            public = body["public"]
            issource = body["issource"]
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "missing value"}))

    if request.matched_route.name == "onesite":
        if ampy.update_amp_site(urllib.parse.unquote(request.matchdict["name"]),
                longname, location, description):
            return HTTPNoContent()
    elif request.matched_route.name == "onemesh":
        if ampy.update_amp_mesh(urllib.parse.unquote(request.matchdict["mesh"]),
                longname, description, public, issource):
            return HTTPNoContent()

    return HTTPBadRequest()


@view_config(
    route_name='onesite',
    request_method='DELETE',
    renderer='json',
    permission=PERMISSION,
)
@view_config(
    route_name='onemesh',
    request_method='DELETE',
    renderer='json',
    permission=PERMISSION,
)
def delete_item(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    if request.matched_route.name == "onesite":
        result = ampy.delete_amp_site(urllib.parse.unquote(request.matchdict["name"]))
    elif request.matched_route.name == "onemesh":
        result = ampy.delete_amp_mesh(urllib.parse.unquote(request.matchdict["mesh"]))

    if result is None:
        return HTTPInternalServerError()
    if result:
        return HTTPNoContent()
    return HTTPNotFound()


@view_config(
    route_name='meshtests',
    request_method='GET',
    renderer='json',
    permission=PERMISSION,
)
def get_flagged_mesh_tests(request):
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    mesh = urllib.parse.unquote(request.matchdict["mesh"])
    tests = ampy.get_flagged_mesh_tests(mesh)

    if tests is None:
        return HTTPInternalServerError()
    if tests is False:
        return HTTPNotFound()

    return HTTPOk(body=json.dumps({"tests": tests}))


@view_config(
    route_name='meshtests',
    request_method='PUT',
    renderer='json',
    permission=PERMISSION,
)
def flag_mesh_tests(request):
    # XXX is it a good idea to be doing more than one operation at once here?
    # should the calling mesh info modal make a request per change?
    ampy = initAmpy(request)
    if ampy is None:
        return HTTPInternalServerError()

    mesh = urllib.parse.unquote(request.matchdict["mesh"])

    try:
        body = request.json_body
        tests = body["tests"]
    except (ValueError, KeyError):
        return HTTPBadRequest(body=json.dumps({"error": "missing tests"}))

    current = ampy.get_flagged_mesh_tests(mesh)

    # return error before we do any modifications
    for test in tests:
        if test not in ["latency", "tput", "hops", "http", "youtube", "external", "sip"]:
            return HTTPBadRequest(body=json.dumps({"error": "unknown test"}))

    # add new tests that aren't currently enabled
    for test in tests:
        if test not in current:
            result =  ampy.flag_mesh_test(mesh, test)
            if result is None:
                return HTTPInternalServerError()
            if result is False:
                return HTTPNotFound()

    # remove old tests that should no longer be enabled
    for test in current:
        if test not in tests:
            result = ampy.unflag_mesh_test(mesh, test)
            if result is None:
                return HTTPInternalServerError()
            if result is False:
                return HTTPNotFound()

    return HTTPNoContent()


#@view_config(
#    route_name='meshtest',
#    request_method='PUT',
#    renderer='json',
#    permission=PERMISSION,
#)
#def flag_mesh_test(request):
#    ampy = initAmpy(request)
#    if ampy is None:
#        return HTTPInternalServerError()
#
#    mesh = urllib.unquote(request.matchdict["mesh"])
#    test = urllib.unquote(request.matchdict["test"])
#
#    if test not in ["latency", "tput", "hops", "http"]:
#        return HTTPBadRequest(body=json.dumps({"error": "unknown test"}))
#
#    try:
#        body = request.json_body
#        status = body["status"]
#    except (ValueError, KeyError):
#        return HTTPBadRequest(body=json.dumps({"error": "missing status"}))
#
#    if status in ["enable", "enabled", "on", "active", "yes"]:
#        result = ampy.flag_mesh_test(mesh, test)
#    elif status in ["disable", "disabled", "off", "inactive", "no"]:
#        result = ampy.unflag_mesh_test(mesh, test)
#    else:
#        return HTTPBadRequest(body=json.dumps({"error":"invalid status value"}))
#
#    if result is None:
#        return HTTPInternalServerError()
#    if result:
#        return HTTPNoContent()
#    return HTTPNotFound()


# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

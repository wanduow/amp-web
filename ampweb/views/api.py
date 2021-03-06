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

from pyramid.view import view_config
from pyramid.httpexceptions import *
from pyramid.renderers import get_renderer, render_to_response
#from ampweb.views.TraceMap import return_JSON
import ampweb.views.apifunctions.viewapi as viewapi
import ampweb.views.apifunctions.matrixapi as matrixapi
import ampweb.views.apifunctions.eventapi as eventapi
import ampweb.views.apifunctions.tooltipapi as tooltipapi
from ampweb.views.common import initAmpy, getBannerOptions, getGATrackingID
from pyramid.security import authenticated_userid, has_permission


@view_config(
    route_name="api",
    renderer="json",
    # depending on the auth.publicdata configuration option then this will
    # either be open to the public or require the "read" permission
    # permission=
)
def api(request):
    """ Determine which API a request is being made against and fetch data """
    urlparts = request.matchdict['params']

    # Dictionary of possible internal API methods we support
    apidict = {
        #'_tracemap': tracemap,
    }

    ampyapidict = {
        '_view': viewapi.graph,
        '_legend': viewapi.legend,
        '_createview': viewapi.create,
        '_destinations': viewapi.destinations,
        '_event': eventapi.event,
        '_matrix': matrixapi.matrix,
        '_matrix_axis': matrixapi.matrix_axis,
        '_matrix_mesh': matrixapi.matrix_mesh,
        '_tooltip': tooltipapi.tooltip,
        '_validatetab': viewapi.validatetab,
    }

    # /api/_* are private APIs
    # /api/* is the public APIs that looks similar to the old one
    if len(urlparts) > 0:
        interface = urlparts[0]
        if interface.startswith("_"):
            if interface in ampyapidict:

                ampy = initAmpy(request)
                if ampy is None:
                    print("Failed to start ampy!")
                    return None

                result = ampyapidict[interface](ampy, request)

                # Allow responses for certain API calls to be cached for 2 mins
                if request.registry.settings['prevent_http_cache'] is not True:
                    if interface in ['_view']:
                        request.response.cache_expires = 120

                return result
            elif interface in apidict:
                return apidict[interface](request)
            else:
                return {"error": "Unsupported API method"}
    return public(request)

def public(request):
    """ Public API """
    urlparts = request.matchdict['params']

    publicapi = {
        'csv': viewapi.raw,
        'json': viewapi.raw,
    }

    if len(urlparts) > 0:
        interface = urlparts[0]

        if interface in publicapi:
            ampy = initAmpy(request)
            if ampy is None:
                print("Failed to start ampy!")
                return None
            result = publicapi[interface](ampy, request)

            # cache the raw json/csv data for a couple of minutes
            request.response.cache_expires = 120

            if interface == "json":
                return result

            if interface == "csv":
                request.override_renderer = 'string'

                if result is None:
                    # TODO improve error reporting
                    return "# Error"

                resultstr = ""
                for line in result:
                    if "metadata" in line:
                        # report data for a defined stream
                        resultstr += "# " + ",".join(str(k) for k,v in line["metadata"])
                        resultstr += "," + ",".join(line["datafields"]) + "\n"
                        metadata = ",".join(str(v) for k, v in line["metadata"])
                        for item in line["data"]:
                            linedata = []
                            for field in line["datafields"]:
                                linedata.append(str(item[field]))
                            resultstr += metadata + "," + ",".join(linedata) + "\n"
                    else:
                        # report stream properties that the user needs to set
                        resultstr += "# %s\n" % line
                        for item in result[line]:
                            resultstr += str(item) + "\n"
                return resultstr

    # no API call provided, show them the documentation
    page_renderer = get_renderer("../templates/api.pt")
    body = page_renderer.implementation().macros["body"]

    banopts = getBannerOptions(request)

    # ignore the default json renderer and build our own response
    return render_to_response("../templates/skeleton.pt", {
        "title": "AMP Public API Documentation",
        "page": "api",
        "body": body,
        "styles": [],
        "scripts": [],
        "logged_in": authenticated_userid(request),
        "show_config": has_permission("viewconfig", request.context, request),
        "show_users": has_permission("editusers", request.context, request),
        "url": request.url,
        "gtag": getGATrackingID(request),
        "show_dash": banopts['showdash'],
        "show_matrix": banopts['showmatrix'],
        "bannertitle": banopts['title'],
    }, request=request)

#def tracemap(request):
#    urlparts = request.matchdict['params'][1:]
#
#    return return_JSON(urlparts[0], urlparts[1])

# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

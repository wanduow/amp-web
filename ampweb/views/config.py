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

import urllib.request, urllib.parse, urllib.error
from pyramid.view import view_config


@view_config(
    route_name='config',
    renderer='../templates/config.txt',
    permission="yaml",
)
def fetch_amp_config(request):
    """ Generate the script to configure the amplet """

    request.response.content_type = "text/plain"

    return {
        "ampname": urllib.parse.unquote(request.matchdict["name"]),
    }

# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

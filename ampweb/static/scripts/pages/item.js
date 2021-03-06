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

function enable_test(source, schedule_id) {
    $.ajax({
        type: "PUT",
        url: API_URL + "/v2/sites/" +
                encodeURIComponent(encodeURIComponent(source)) +
                "/schedule/" + encodeURIComponent(schedule_id) + "/status",
        data: JSON.stringify({"status": "enable"}),
        contentType: "application/json",
        success: function() {
            location.reload();
        }
    });
}


function disable_test(source, schedule_id) {
    $.ajax({
        type: "PUT",
        url: API_URL + "/v2/sites/" +
                encodeURIComponent(encodeURIComponent(source)) +
                "/schedule/" + encodeURIComponent(schedule_id) + "/status",
        data: JSON.stringify({"status": "disable"}),
        contentType: "application/json",
        success: function() {
            location.reload();
        }
    });
}


function sign_certificate(name) {
    $.ajax({
        type: "POST",
        url: API_URL + "/v2/certificates/" +
                encodeURIComponent(encodeURIComponent(name)),
        success: function() {
            location.reload();
        },
        error: function() {
            location.reload();
        }
    });
}


function revoke_certificate(name) {
    $.ajax({
        type: "DELETE",
        url: API_URL + "/v2/certificates/" +
                encodeURIComponent(encodeURIComponent(name)),
        success: function() {
            location.reload();
        },
        error: function() {
            location.reload();
        }
    });
}

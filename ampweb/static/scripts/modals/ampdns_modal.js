/* TODO reset any selectors below the one that has been changed? Can we
 * keep the existing value if it is still valid and only reset if the value
 * is no longer valid?
 */

function AmpDnsModal(/*stream*/) {
    Modal.call(this);
}

AmpDnsModal.prototype = new Modal();
AmpDnsModal.prototype.constructor = AmpDnsModal;

/* list all the selectables that can change/reset, in order of display */
AmpDnsModal.prototype.selectables = ["source", "server", "query", "type"]

AmpDnsModal.prototype.update = function(name) {
    switch ( name ) {
        case "source": this.updateServer(); break;
        case "server": this.updateQuery(); break;
        case "query": this.updateType(); break;
        case "type": this.updateSubmit(); break;
        default: break;
    };
}


/* we've just changed the source, disable submission and update servers */
AmpDnsModal.prototype.updateServer = function() {
    var source;
    var modal = this;

    if ( $("#source option:selected").val() != this.marker ) {
        source = $("#source option:selected").val().trim();
    } else {
        source = "";
    }
    if ( source != "" ) {
        /* Populate the targets dropdown */
        $.ajax({
            url: "/api/_destinations/amp-dns/" + source + "/",
            success: function(data) {
                modal.populateDropdown("server", data, "server");
                modal.updateSubmit();
            }
        });
    }
}

/* we've just changed the server, disable submission and update queries */
AmpDnsModal.prototype.updateQuery = function () {
    var source, server;
    var modal = this;

    if ( $("#source option:selected").val() != this.marker ) {
        source = $("#source option:selected").val().trim();
    } else {
        source = "";
    }

    if ( $("#server option:selected").val() != this.marker ) {
        server = $("#server option:selected").val().trim();
    } else {
        server = "";
    }

    if ( source != "" && server != "" ) {
        /* Populate the targets dropdown */
        $.ajax({
            url: "/api/_destinations/amp-dns/"+source+"/"+server+"/",
            success: function(data) {
                modal.populateDropdown("query", data, "query");
                modal.updateSubmit();
            }
        });
    }
}

/* we've just changed the query, disable submission and update types */
AmpDnsModal.prototype.updateType = function () {
    var source, server, query;
    var modal = this;

    if ( $("#source option:selected").val() != this.marker ) {
        source = $("#source option:selected").val().trim();
    } else {
        source = "";
    }

    if ( $("#server option:selected").val() != this.marker ) {
        server = $("#server option:selected").val().trim();
    } else {
        server = "";
    }

    if ( $("#query option:selected").val() != this.marker ) {
        query = $("#query option:selected").val().trim();
    } else {
        query = "";
    }

    if ( source != "" && server != "" && query != "" ) {
        /* Populate the targets dropdown */
        $.ajax({
            /* XXX this currently returns the responding address, don't care */
            /* TODO it should be the query class/type */
            url: "/api/_destinations/amp-dns/"+source+"/"+server+"/"+query+"/",
            success: function(data) {
                modal.populateDropdown("type", data, "type");
                modal.updateSubmit();
            }
        });
    }
}


AmpDnsModal.prototype.updateSubmit = function() {
    for ( var i in this.selectables ) {
        var value = $("#" + this.selectables[i] + " option:selected").val();
        if ( value == undefined || value == this.marker ) {
            /* something isn't set, disable the submit button */
            $("#submit").prop("disabled", true);
            return;
        }
    }

    /* everything is set properly, enable the submit button */
    $("#submit").prop("disabled", false);
}


AmpDnsModal.prototype.submit = function() {
    /* get new view id */
    var source, server, query, type;

    if ( $("#source option:selected").val() != this.marker ) {
        source = $("#source option:selected").val().trim();
    } else {
        source = "";
    }

    if ( $("#server option:selected").val() != this.marker ) {
        server = $("#server option:selected").val().trim();
    } else {
        server = "";
    }

    if ( $("#query option:selected").val() != this.marker ) {
        query = $("#query option:selected").val().trim();
    } else {
        query = "";
    }

    if ( $("#type option:selected").val() != this.marker ) {
        type = $("#type option:selected").val().trim();
    } else {
        type = "";
    }

    if ( source != "" && server != "" && query != "" && type != "" ) {
        $.ajax({
            url: "/api/_createview/add/amp-dns/" + currentview + "/" + source +
                "/" + server + "/" + query + "/IN/" + type + "/4096",
            success: function(data) {
                /* hide modal window */
                $("#modal-foo").modal('hide');
                /* current view is what changeView() uses for the new graph */
                currentview = data;
                /* fetch new data */
                graphPage.changeView(data);
            }
        });
    }
}

// vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

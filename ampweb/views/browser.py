from pyramid.view import view_config
from pyramid.renderers import get_renderer
from ampweb.views.common import initAmpy, createGraphClass, getCommonScripts
from operator import itemgetter


@view_config(route_name="browser", renderer="../templates/skeleton.pt")
def browser(request):
    page_renderer = get_renderer("../templates/browser.pt")
    body = page_renderer.implementation().macros["body"]

    ampy = initAmpy(request)
    if ampy is None:
        print "Failed to start ampy while creating collection browser"
        return None

    collections = []
        
    nntsccols = ampy.get_collections()
    

    for c in nntsccols.values():
        graphclass = createGraphClass(c['name'])
        if graphclass != None:
            collections += graphclass.get_browser_collections()

    sortcols = sorted(collections, key=itemgetter('family', 'label'))

    return {
        "title":"Graph Browser",
        "body": body,
        "styles": None,   
        "scripts": getCommonScripts(),
        "collections": sortcols
    }


# vim: set smartindent shiftwidth=4 tabstop=4 softtabstop=4 expandtab :

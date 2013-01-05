# Create your views here.
#from vectorformats.Formats import Django, GeoJSON
from GPSTracker.models import Client, Group, Report, Point, Line, Poly
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext, loader
from django.shortcuts import render_to_response
from GPSTracker.forms import UploadFileForm1, betaUploadFileForm1, betaUploadFileForm2

from GPSTracker.file_uploads import preprocess_shapefile, import_shapefile

# Project Shortcuts
from shortcuts import djangoToExportFormat

def index(request):
    return render_to_response('gpstracker/index.html',{},context_instance=RequestContext(request))

def about(request):
    return render_to_response('gpstracker/about.html',{},context_instance=RequestContext(request))

def clients(request):
    """Return a list of clients."""
    client_list = Client.objects.all()
    group_list = Group.objects.all()
    return render_to_response('gpstracker/clients.html', {'client_list': client_list, 'group_list': group_list}, context_instance=RequestContext(request))

def group(request):
    """Return a list of clients."""
    client_list = Client.objects.all()
    group_list = Group.objects.all()
    return render_to_response('gpstracker/group.html', {'client_list': client_list, 'group_list': group_list}, context_instance=RequestContext(request))

def group_detail(request, group_id):
    """Return a list of GPS Features for a GPS Group."""
    args = dict()
    args['group'] = Group.objects.get(pk=group_id)
    point_list = Point.objects.filter(group__pk = group_id)
    line_list = Line.objects.filter(group__pk = group_id)
    poly_list = Poly.objects.filter(group__pk = group_id)
    geom_dict = {'point_list':point_list,'line_list':line_list,'poly_list':poly_list}
    # Only send to render_to_response those geoms (point/line/poly) that exist
    for geom_key, geom_value in geom_dict.iteritems():
        if geom_value.exists():
            args[geom_key] = geom_value
    return render_to_response('gpstracker/group_detail.html', args, context_instance=RequestContext(request))

def geom_export(request, feat_id, geom_type, geom_format, group=False):
    """Return a serialized representation of geom and properties from a Django GeoQuerySet"""
    # Grab appropriate model
    modelMap = {'point':Point,'line':Line,'poly':Poly}
    if geom_type.lower() in modelMap.keys():
        # Test if we're dealing with a geom group, or a individual geom
        if group:
            geom_rep = modelMap[geom_type].objects.filter(group__pk=feat_id)
        elif not group:
            geom_rep = modelMap[geom_type].objects.filter(pk=feat_id)
    geom_out = djangoToExportFormat(request, geom_rep, format=geom_format)
    # If exporting a KML, Add MIME TYPE https://developers.google.com/kml/documentation/kml_tut#kml_server
    if geom_format.lower() == 'kml':
        return HttpResponse(geom_out, content_type="application/vnd.google-earth.kml+xml")
    else:
        return HttpResponse(geom_out)

def uploadfile1(request):
    """
    Present user with file upload screen...
    if successful, send them to a second form page to begin field mapping.
    if unsuccessful, have them retry.
    """
    if request.method == 'POST':
        form = betaUploadFileForm1(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            # DO SOMETHING WITH CLEAN DATA
            shpPath = preprocess_shapefile(cd)
            request.session['shpPath'] = shpPath
            return HttpResponseRedirect('./2')
#            return HttpResponseRedirect('../session/response')
        else:
            print form.errors
    else:
        form = betaUploadFileForm1()
    return render_to_response('gpstracker/uploadfile1.html', {'form': form} ,context_instance=RequestContext(request))

def uploadfile2(request):
    """
    """
    if request.method == 'POST':
        # Required to repass shpPath kwarg
        form = betaUploadFileForm2(request.POST,shpPath=request.session['shpPath'])
        if form.is_valid():
            cd = form.cleaned_data
            # DO SOMETHING WITH CLEAN DATA
            import_shapefile(cd, request.session['shpPath'])
            return HttpResponseRedirect('gpstracker/success/')
        else:
            print form.errors
    else:
        form = betaUploadFileForm2(shpPath=request.session['shpPath'])
    return render_to_response('gpstracker/uploadfile2.html', {'form': form} ,context_instance=RequestContext(request))

def session_request(request):
    myFile = 'path/to/shp'
    request.session['shpPath'] = myFile
    if 'filePath' in request.session:
        return HttpResponseRedirect('./response')

def session_response(request):
    if 'shpPath' in request.session:
        return HttpResponse('File Path: %s' % request.session['shpPath'])
    else:
        return HttpResponse('File Path Not Set')

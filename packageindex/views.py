from django.http import HttpResponseRedirect
from django.db.models import F
from django.shortcuts import render_to_response, get_object_or_404

from models import Application, Package, PackageIndex

def application_list(request):
    #TODO make on the fly refresh togable
    PackageIndex.objects.refresh_stale_indexes()
    applications = Application.objects.all()
    return render_to_response('packageindex/application_list.html',
                              {'object_list':applications})

def application_detail(request, name):
    application = get_object_or_404(Application, name=name)
    #TODO make on the fly fetch packages togable
    application.refresh_stale_packages()
    packages = application.package_dictionary()
    if not packages:
        return render_to_response('packageindex/package_list.html',
                                  {'object_list':list(),
                                   'application':application})
    if len(packages) > 1:
        desired_priority = max(*packages.keys())
    else:
        desired_priority = packages.keys()[0]
    return render_to_response('packageindex/package_list.html',
                              {'object_list':packages[desired_priority],
                               'application':application})

def download_package(request, object_id):
    package = get_object_or_404(Package, pk=object_id)
    Package.objects.filter(pk=object_id).update(downloads=F('downloads')+1)
    return HttpResponseRedirect(package.get_download_url())

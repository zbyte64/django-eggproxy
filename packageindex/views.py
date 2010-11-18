from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.db.models import F
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404

from models import Application, Package, PackageIndex, PackageAccessKey

def access_key_view(func):
    def wrapper(request, **kwargs):
        if 'access_key' in kwargs:
            access_key = kwargs['access_key']
            access_key = get_object_or_404(PackageAccessKey, access_key=access_key)
            request.user = access_key.user
        else:
            kwargs['access_key'] = None
        return func(request, **kwargs)
    return wrapper

@access_key_view
def application_list(request, access_key):
    #TODO make on the fly refresh togable
    PackageIndex.objects.refresh_stale_indexes()
    applications = Application.objects.all()
    return render_to_response('packageindex/application_list.html',
                              {'object_list':applications,
                               'access_key':access_key,})

@access_key_view
def application_detail(request, name, access_key):
    try:
        application = Application.objects.get(name=name)
    except Application.DoesNotExist:
        application = get_object_or_404(Application, name__iexact=name)
        return HttpResponseRedirect(application.get_absolute_url(access_key))
    #TODO make on the fly fetch packages togable
    application.refresh_stale_packages()
    package_indexes = PackageIndex.objects.indexes_for_user(request.user)
    packages = application.package_dictionary(package_indexes)
    if not packages:
        return render_to_response('packageindex/package_list.html',
                                  {'object_list':list(),
                                   'application':application,
                                   'access_key':access_key,})
    if len(packages) > 1:
        desired_priority = max(*packages.keys())
    else:
        desired_priority = packages.keys()[0]
    return render_to_response('packageindex/package_list.html',
                              {'object_list':packages[desired_priority],
                               'application':application,
                               'access_key':access_key,})

@access_key_view
def download_package(request, name, title, access_key):
    packages = get_list_or_404(Package, title=title, application__name=name)
    package = None
    for candidate_package in packages:
        if not candidate_package.package_index.can_read(request.user):
            continue
        if not package or candidate_package.package_index.priority > package.package_index.priority:
            package = candidate_package
    if not package:
        return HttpResponseForbidden('Cannot download this package')
    Package.objects.filter(pk=package.pk).update(downloads=F('downloads')+1)
    return HttpResponseRedirect(package.get_download_url())

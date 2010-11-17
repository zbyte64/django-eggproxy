import datetime

import urllib
from urlparse import urlparse

from django.db import models
from django.core.files import File
from django.contrib.auth.models import User

from utils import PackageIndexScraper

def create_or_update(model, **lookups):
    update = lookups.pop('update', {})
    try:
        obj = model.objects.get(**lookups)
    except model.DoesNotExist:
        obj = model(**lookups)
    for key, value in update.iteritems():
        setattr(obj, key, value)
    obj.save()
    return obj

UPDATE_FREQUENCY = datetime.timedelta(days=1)

class PackageAccessKey(models.Model):
    user = models.OneToOneField(User)
    access_key = models.CharField(max_length=64, unique=True)

class PackageIndexManager(models.Manager):
    def refresh_stale_indexes(self):
        stale = self.proxies().filter(last_update__lte=datetime.datetime.now()-UPDATE_FREQUENCY)
        for package_index in stale:
            package_index.populate_applications()
    
    def proxies(self):
        return self.exclude(url="")
    
    def indexes_for_user(self, user):
        ret = list()
        for package_index in self.all():
            if package_index.can_read(user):
                ret.append(package_index)
        return ret

class PackageIndex(models.Model):
    name = models.CharField(max_length=50, unique=True)
    priority = models.IntegerField(default=0)
    url = models.URLField(blank=True)
    last_update = models.DateTimeField(default=datetime.datetime.now)
    
    objects = PackageIndexManager()
    
    def __unicode__(self):
        return self.name
    
    def can_read(self, user):
        return user.has_perm('view_index', self)
    
    def get_scraper(self):
        return PackageIndexScraper(index_url=self.url)
    
    def populate_applications(self):
        scraper = self.get_scraper()
        scraper.scan_all()
        package_names = scraper.package_pages.keys()
        applications = list()
        for package_name in package_names:
            applications.append(Application.objects.get_or_create(name=package_name)[0])
        self.last_update = datetime.datetime.now()
        self.save()
        return applications
    
    def populate_packages(self, application):
        scraper = self.get_scraper()
        downloads = scraper.get_package_downloads(application.name)
        packages = list()
        for download in downloads:
            package = create_or_update(Package,
                                       application=application,
                                       package_index=self,
                                       title=download['filename'],
                                       update={'active':True,
                                               'md5':download['md5'],
                                               'source_download':download['location']},)
            packages.append(package)
        #any package not found in this list is inactive
        Package.objects.filter(application=application, package_index=self, active=True).exclude(pk__in=[pkg.pk for pkg in packages]).update(active=False)
        create_or_update(ApplicationUpdate,
                         application=application,
                         package_index=self,
                         update={'last_update':datetime.datetime.now()})
        return packages
    
    def populate_applications_and_packages(self):
        for application in self.populate_applications():
            self.populate_packages(application)
    
    class Meta:
        permissions = (
            ("view_index", "Can view packages from this index"),
        )

class Application(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
    
    @models.permalink
    def get_absolute_url(self, access_key=None):
        if access_key:
            return ('packageindex.keyed_application_detail',
                    [],
                    {'access_key':access_key,
                     'name':self.name,})
        else:
            return ('packageindex.application_detail', [self.name], {})
    
    def package_dictionary(self, package_indexes=None):
        package_qs = self.package_set.filter(active=True)
        if package_indexes is not None:
            package_qs = package_qs.filter(package_index__in=package_indexes)
        #filter by Package Index with highest priority
        packages = dict()
        for package in package_qs:
            priority = package.package_index.priority
            packages.setdefault(priority, [])
            packages[priority].append(package)
        return packages
    
    def populate_packages(self):
        for package_index in PackageIndex.objects.proxies():
            package_index.populate_packages(self)
    
    def refresh_stale_packages(self):
        cutoff = datetime.datetime.now() - UPDATE_FREQUENCY
        #TODO consolidate queries
        for package_index in PackageIndex.objects.proxies():#.filter(applicationupdate__application=self, applicationupdate__last_update__lte=UPDATE_FREQUENCY)
            try:
                app_update = ApplicationUpdate.objects.get(application=self, package_index=package_index)
            except ApplicationUpdate.DoesNotExist:
                package_index.populate_packages(self)
            else:
                if app_update.last_update < cutoff:
                    package_index.populate_packages(self)

class ApplicationUpdate(models.Model):
    application = models.ForeignKey(Application)
    package_index = models.ForeignKey(PackageIndex)
    last_update = models.DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        unique_together = [('application', 'package_index')]

class PackageManager(models.Manager):
    def get_pending_downloads(self):
        return self.filter(download='', downloads__gt=0, active=True).exclude(source_download='')
    
    def populate_pending_downloads(self):
        for package in self.get_pending_downloads():
            package.populate_download()

class Package(models.Model):
    title = models.CharField(max_length=100)
    version = models.CharField(max_length=20, blank=True)
    application = models.ForeignKey(Application)
    package_index = models.ForeignKey(PackageIndex)
    active = models.BooleanField(default=True, db_index=True)
    order = models.IntegerField(default=0)
    md5 = models.CharField(max_length=64, blank=True)
    download = models.FileField(upload_to='packages', blank=True)
    source_download = models.URLField(verify_exists=False, blank=True)
    downloads = models.PositiveIntegerField(default=0)
    
    objects = PackageManager()
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ['-order']
    
    @models.permalink
    def get_counting_download_url(self, access_key=None):
        if access_key:
            return ('packageindex.keyed_download_package',
                    [],
                    {'access_key':access_key,
                     'name':self.application.name,
                     'title':self.title,})
        else:
            return ('packageindex.download_package',
                    [],
                    {'name':self.application.name,
                     'title':self.title,})
    
    def get_download_url(self):
        if self.download:
            return self.download.url
        return self.source_download
    
    def populate_download(self):
        if not self.download:
            name = urlparse(self.source_download).path.split('/')[-1]
            content = urllib.urlretrieve(self.source_download)
            self.download.save(name, File(open(content[0])), save=True)


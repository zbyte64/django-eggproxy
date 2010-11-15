from django.core.management.base import BaseCommand

from packageindex.models import PackageIndex, Package

class Command(BaseCommand):
    help='''Generate a document of box tickets'''
   
    def execute(self, *args, **kwargs):
        PackageIndex.objects.refresh_stale_indexes()
        Package.objects.populate_pending_downloads()

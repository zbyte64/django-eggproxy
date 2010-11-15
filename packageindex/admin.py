from django.contrib import admin

from models import PackageIndex, Application, Package, PackageAccessKey

from admin_permissions import UserPermissionInline, GroupPermissionInline

class PackageAccessKeyAdmin(admin.ModelAdmin):
    raw_id_fields = ['user']
    list_display = ['user', 'access_key']

admin.site.register(PackageAccessKey, PackageAccessKeyAdmin)

class PackageIndexAdmin(admin.ModelAdmin):
    inlines = [UserPermissionInline, GroupPermissionInline]
    actions = ['populate_index',
               'populate_packages']
    
    def populate_index(self, request, queryset):
        for package_index in queryset:
            package_index.populate_applications()
    
    def populate_packages(self, request, queryset):
        for package_index in queryset:
            package_index.populate_applications_and_packages()

admin.site.register(PackageIndex, PackageIndexAdmin)

class ApplicationAdmin(admin.ModelAdmin):
    actions = ['populate_packages']
    
    def populate_packages(self, request, queryset):
        for application in queryset:
            application.populate_packages()

admin.site.register(Application, ApplicationAdmin)

class PackageAdmin(admin.ModelAdmin):
    raw_id_fields = ['application', 'package_index']
    actions = ['populate_download']
    
    def populate_download(self, request, queryset):
        for package in queryset:
            package.populate_download()

admin.site.register(Package, PackageAdmin)



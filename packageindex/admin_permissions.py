from django import forms, template
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext, ugettext_lazy as _
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.formsets import all_valid
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.shortcuts import get_perms_for_model

class BasePermissionInline(generic.GenericTabularInline):
    extra = 1
    ct_fk_field = 'object_pk'

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'permission':
            perm_choices = get_perms_for_model(self.parent_model)
            kwargs['queryset'] = perm_choices
            return db_field.formfield(**kwargs)
        return super(BasePermissionInline, self).formfield_for_dbfield(db_field, **kwargs)

class UserPermissionInline(BasePermissionInline):
    model = UserObjectPermission
    raw_id_fields = ['user']

class GroupPermissionInline(BasePermissionInline):
    model = GroupObjectPermission
    raw_id_fields = ['group']

class UserActionPermissionInline(UserPermissionInline):
    template = 'admin/edit_inline/action_tabular.html'

class GroupActionPermissionInline(GroupPermissionInline):
    template = 'admin/edit_inline/action_tabular.html'

class ActionErrorList(forms.util.ErrorList):
    def __init__(self, inline_formsets):
        for inline_formset in inline_formsets:
            self.extend(inline_formset.non_form_errors())
            for errors_in_inline_form in inline_formset.errors:
                self.extend(errors_in_inline_form.values())

def edit_permissions(modeladmin, request, queryset): #TODO this does not work
    opts = modeladmin.model._meta
    app_label = opts.app_label
    # Check that the user has the permission to edit permissions
    if not (request.user.is_superuser or
            request.user.has_perm('guardian.change_permission') or
            request.user.has_perm('guardian.change_foreign_permissions')):
        raise PermissionDenied
    actions = modeladmin.get_actions(request)
    if hasattr(actions, 'keys'):
        actions = actions.keys()
    action_index = actions.index('edit_permissions')
    inline = UserActionPermissionInline(queryset.model, modeladmin.admin_site)
    formsets = []
    for obj in queryset:
        prefixes = {}
        FormSet = inline.get_formset(request, obj)
        prefix = "%s-%s" % (FormSet.get_default_prefix(), obj.pk)
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
        if prefixes[prefix] != 1:
            prefix = "%s-%s-%s" % (prefix, prefixes[prefix])
        if request.POST.get('post'):
            formset = FormSet(data=request.POST, files=request.FILES,
                              instance=obj, prefix=prefix)
        else:
            formset = FormSet(instance=obj, prefix=prefix)
        formsets.append(formset)

    media = modeladmin.media
    inline_admin_formsets = []
    for formset in formsets:
        fieldsets = list(inline.get_fieldsets(request))
        inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
        inline_admin_formsets.append(inline_admin_formset)
        media = media + inline_admin_formset.media

    ordered_objects = opts.get_ordered_objects()
    if request.POST.get('post'):
        if all_valid(formsets):
            for formset in formsets:
                formset.save()
        # redirect to full request path to make sure we keep filter
        return HttpResponseRedirect(request.get_full_path())

    context = {
        'errors': ActionErrorList(formsets),
        'title': ugettext('Permissions for %s') % force_unicode(opts.verbose_name_plural),
        'inline_admin_formsets': inline_admin_formsets,
        'root_path': modeladmin.admin_site.root_path,
        'app_label': app_label,
        'change': True,
        'ordered_objects': ordered_objects,
        'form_url': mark_safe(''),
        'opts': opts,
        'target_opts': queryset.model._meta,
        'content_type_id': ContentType.objects.get_for_model(queryset.model).id,
        'save_as': False,
        'save_on_top': False,
        'is_popup': False,
        'media': mark_safe(media),
        'show_delete': False,
        'action_index': action_index,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'queryset': queryset,
        "object_name": force_unicode(opts.verbose_name),
    }
    template_name = getattr(modeladmin, 'permission_change_form_template', [
        "admin/%s/%s/permission_change_form.html" % (app_label, opts.object_name.lower()),
        "admin/%s/permission_change_form.html" % app_label,
        "admin/permission_change_form.html"
    ])
    return render_to_response(template_name, context,
                              context_instance=template.RequestContext(request))
edit_permissions.short_description = _("Edit permissions for selected %(verbose_name_plural)s")

admin.site.add_action(edit_permissions, 'edit_permissions')


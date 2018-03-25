==========
Change Log
==========

0.7
===

* Removed default implementations of _user_can_change_*() and _user_can_delete_*() on CommonInfoMixin - this was far too specific a use-case to be the default


0.6.1
=====

* Fixed #2: Object level access now defaults open when no model method exists to define it explicitly

0.6
===

* Renamed project
* Added csrfify_ajax template tag
* Added paginate template tag
* Added form_field and checkbox template tags
* Added MessageMiddleware
* Added MessagingRequestFactory
* Added TemplateRendererMixin
* Updated AjaxResponse to allow message strings marked as safe to skip being escaped
* Moved AjaxResponse from djem.misc.AjaxResponse to djem.ajax.AjaxResponse. Also removed shortcut import djem.AjaxResponse.
* Moved get_page() from djem.misc.get_page to djem.pagination.get_page. Also removed shortcut import djem.get_page.

0.5
===

Never released: project renaming took precedence. These features were released under 0.6, and the new project name, instead.

* Added replacements for permission_required decorator and PermissionRequiredMixin that support object-level permissions
* Added get_page() helper function
* Added Table helper class
* Added M and Mon helper classes for simple code performance debugging
* Added mon() decorator as a shortcut for monitoring a function
* Added inspection/prettyprint utilities for debugging
* Added extensible Developer class as a home for shortcuts to common user-based operations useful to developers

0.4.3
=====

* Added authenticate() method to ObjectPermissionsBackend, fixing a bug where it broke authentication if a user's credentials were not authenticated by earlier backends

0.4.2
=====

* Fixed missing commits under 0.4.1 tag

0.4.1
=====

* Fixed documentation build issues on readthedocs.org

0.4
===

* Added AjaxResponse
* Added GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE setting
* Added object-level permission support (ObjectPermissionsBackend, ifperm and ifnotperm template tags)
* Updated CommonInfoMixin to provide default object-level permissions for subclasses, based on ownership

0.3
===

* Added TimeZoneField/TimeZoneHelper
* Cleaned code as per isort and flake8

Pre-0.3
=======

* CommonInfoMixin, with associated manager and queryset
* ArchivableMixin, with associated manager and queryset
* VersioningMixin, with associated manager and queryset
* StaticAbstract parent model, with associated manager and queryset
* CommonInfoForm for ModelForms based on CommonInfoMixin models

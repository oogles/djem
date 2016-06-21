==========
Change Log
==========

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

==========
Change Log
==========

0.9.0 (unreleased)
==================

* Improved customisability of pagination template
* Updated ``UNDEFINED`` to ensure it cannot be deep copied (it will always be the same instance)
* Updated the ``Archivable.archive()`` method to raise ``ProtectedError`` and ``RestrictedError`` as ``delete()`` would, when inbound foreign keys using ``on_delete=models.PROTECT`` or ``on_delete=models.RESTRICT`` are detected against unarchived records

0.8.0 (2022-12-12)
==================

* Added compatibility with Django versions 4.0 and 4.1
* Dropped support for Django versions below 3.2
* Updated ``Auditable`` and ``Versionable`` to use ``self._state.adding`` to differentiate between records being added or updated
* Switched development environment from Vagrant to Docker

Note: As of this release, ``TimeZoneField``/``TimeZoneHelper`` still require ``pytz``, despite the Django 4.0+ move to ``zoneinfo``.

0.7.2 (2021-10-05)
==================

* Removed public ``djem.auth.get_user_log_verbosity()`` function due to the apparent potential for causing cyclic imports, as observed in real world usage.

0.7.1 (2021-08-25)
==================

* Fixed readthedocs configuration
* Fixed README badges

0.7 (2021-08-24)
================

A number of features are renamed. In all cases, the old names remain available for backwards compatibility, but are deprecated.

* Dropped support for Python 2 (minimum supported version is 3.6)
* Dropped support for Django versions below 2.2
* Renamed ``CommonInfoMixin`` and ``CommonInfoQuerySet`` to ``Auditable`` and ``AuditableQuerySet``, respectively
* Renamed ``ArchivableMixin`` to ``Archivable``
* Renamed ``VersioningMixin`` and ``VersioningQuerySet`` to ``Versionable`` and ``VersionableQuerySet``, respectively
* Renamed ``CommonInfoForm`` to ``AuditableForm``
* Renamed ``DJEM_COMMON_INFO_USER_REQUIRED_ON_SAVE`` setting to ``DJEM_AUDITABLE_USER_REQUIRED_ON_SAVE``
* Added ``UNDEFINED`` constant
* Added ``Loggable`` for instance-based logging
* Added ``OLPMixin`` for custom user models, to support advanced OLP-related functionality
* Added ``MixableQuerySet`` mixin for custom ``QuerySet`` classes
* Added ``DJEM_UNIVERSAL_OLP`` setting
* Added ``DJEM_PERM_LOG_VERBOSITY`` setting
* Added ``AuditableQuerySet`` ``create()``, ``get_or_create()``, and ``update_or_create()`` methods
* Added ``ArchivableQuerySet`` ``archived()`` and ``unarchived()`` methods
* Added ``ajax_login_required()`` decorator
* Added ``UserSavable`` mixin for forms
* Removed default implementations of ``_user_can_change_*()`` and ``_user_can_delete_*()`` on ``Auditable`` - this was far too specific a use-case to be the default
* Removed ``ArchivableQuerySet``'s ``archive()`` and ``unarchive()`` methods
* Removed ``Archivable``'s ``live`` and ``archived`` Managers
* Removed explicit ``Manager`` classes for mixins
* Moved custom ``QuerySet`` classes for mixins into ``djem.models.models``

0.6.4 (2018-12-06)
==================

* Fixed setup.py to include ``include_package_data=True``

0.6.3 (2018-12-06)
==================

* Updated MANIFEST.in to include the templates directory

0.6.2 (2018-03-25)
==================

* Fixed #2: Object level access now defaults open when no model method exists to define it explicitly

0.6.1 (2018-03-02)
==================

* Updated PyPi details

0.6 (2018-03-02)
================

* Renamed project
* Added ``csrfify_ajax`` template tag
* Added ``paginate`` template tag
* Added ``form_field`` and ``checkbox`` template tags
* Added ``MessageMiddleware``
* Added ``MessagingRequestFactory``
* Added ``TemplateRendererMixin``
* Updated ``AjaxResponse`` to allow message strings marked as safe to skip being escaped
* Moved ``AjaxResponse`` from ``djem.misc.AjaxResponse`` to ``djem.ajax.AjaxResponse``. Also removed shortcut import ``djem.AjaxResponse``.
* Moved ``get_page()`` from ``djem.misc.get_page`` to ``djem.pagination.get_page``. Also removed shortcut import ``djem.get_page``.

0.5 (unreleased)
================

Never released: project renaming took precedence. These features were released under 0.6, and the new project name, instead.

* Added replacements for ``permission_required`` decorator and ``PermissionRequiredMixin`` that support object-level permissions
* Added ``get_page()`` helper function
* Added ``Table`` helper class
* Added ``M`` and ``Mon`` helper classes for simple code performance debugging
* Added ``mon()`` decorator as a shortcut for monitoring a function
* Added inspection/prettyprint utilities for debugging
* Added extensible ``Developer`` class as a home for shortcuts to common user-based operations useful to developers

0.4.3 (2016-09-17)
==================

* Added ``authenticate()`` method to ``ObjectPermissionsBackend``, fixing a bug where it broke authentication if a user's credentials were not authenticated by earlier backends

0.4.2 (2016-06-21)
==================

* Fixed missing commits under 0.4.1 tag

0.4.1 (2016-06-21)
==================

* Fixed documentation build issues on ``readthedocs.org``

0.4 (2016-06-21)
================

* Added ``AjaxResponse``
* Added ``GOODIES_COMMON_INFO_REQUIRE_USER_ON_SAVE`` setting
* Added object-level permission support (``ObjectPermissionsBackend``, ``ifperm`` and ``ifnotperm`` template tags)
* Updated ``CommonInfoMixin`` to provide default object-level permissions for subclasses, based on ownership

0.3 (2016-03-19)
================

* Added ``TimeZoneField``/``TimeZoneHelper``
* Cleaned code as per ``isort`` and ``flake8``

Pre-0.3
=======

* ``CommonInfoMixin``, with associated manager and queryset
* ``ArchivableMixin``, with associated manager and queryset
* ``VersioningMixin``, with associated manager and queryset
* ``StaticAbstract`` parent model, with associated manager and queryset
* ``CommonInfoForm`` for ModelForms based on ``CommonInfoMixin`` models

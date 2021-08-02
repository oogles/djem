from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.test import RequestFactory, TestCase, override_settings

from djem.utils.tests import TemplateRendererMixin

from .models import AuditableTest


@override_settings(AUTHENTICATION_BACKENDS=[
    'django.contrib.auth.backends.ModelBackend',
    'djem.auth.ObjectPermissionsBackend'
])
class PermTagTestCase(TemplateRendererMixin, TestCase):
    
    def setUp(self):
        
        user = get_user_model().objects.create_user('test', 'fakepassword')
        
        # Grant the user all permissions for AuditableTest to ensure the tests
        # focus on object-level permissions
        permissions = Permission.objects.filter(
            content_type__app_label='djemtest',
            content_type__model='auditabletest'
        )
        user.user_permissions.set(permissions)
        
        self.user = user


class IfPermTestCase(PermTagTestCase):
    
    def test_ifperm__no_args(self):
        """
        Test the ifperm template tag raises TemplateSyntaxError when not
        provided any arguments.
        """
        
        template_string = (
            '{% load djem %}'
            '{% ifperm %}'
            '   IF'
            '{% endifperm %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_ifperm__too_few_args(self):
        """
        Test the ifperm template tag raises TemplateSyntaxError when provided
        too few arguments.
        """
        
        template_string = (
            '{% load djem %}'
            '{% ifperm "blah" %}'
            '   IF'
            '{% endifperm %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_ifperm__too_many_args(self):
        """
        Test the ifperm template tag raises TemplateSyntaxError when provided
        too many arguments.
        """
        
        template_string = (
            '{% load djem %}'
            '{% ifperm "blah" "blah" "blah" "blah" %}'
            '   IF'
            '{% endifperm %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_ifperm__invalid_permission(self):
        """
        Test the ifperm template tag does not render the "if" block of the tag,
        with no "else" block defined, when an invalid permission is provided.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user "djemtest.not_a_real_permission" obj %}'
            '   IF'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, '')
    
    def test_ifperm__invalid_permission__else(self):
        """
        Test the ifperm template tag renders the "else" block of the tag, when
        defined, when an invalid permission is provided.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user "djemtest.not_a_real_permission" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'ELSE')
    
    def test_ifperm__with_permission(self):
        """
        Test the ifperm template tag renders the "if" block of the tag, with no
        "else" block defined, when a user has a permission on an object.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifperm__with_permission__else(self):
        """
        Test the ifperm template tag renders the "if" block of the tag, with an
        "else" block defined, when a user has a permission on an object.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifperm__without_permission(self):
        """
        Test the ifperm template tag does not renders the "if" block of the tag,
        with no "else" block defined, when a user does not have a permission on
        an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = AuditableTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, '')
    
    def test_ifperm__without_permission__else(self):
        """
        Test the ifperm template tag renders the "else" block of the tag, when
        defined, when a user does not have a permission on an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = AuditableTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'ELSE')
    
    def test_ifperm__complex_user_arg(self):
        """
        Test the ifperm template tag handles the user argument being a complex
        template variable.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifperm some.complex.variable "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': self.user
                }
            },
            'obj': obj
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifperm__complex_permission_arg(self):
        """
        Test the ifperm template tag handles the permission argument being a
        complex template variable.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user some.complex.variable obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj,
            'some': {
                'complex': {
                    'variable': 'djemtest.change_auditabletest'
                }
            }
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifperm__complex_object_arg(self):
        """
        Test the ifperm template tag handles the object argument being a
        complex template variable.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifperm user "djemtest.change_auditabletest" some.complex.variable %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        output = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': obj
                }
            }
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifperm__view__anonymous(self):
        """
        Test the ifperm template tag when used in a template rendered as part of
        a request/response cycle (i.e. standard real world usage), when there
        is no authenticated user.
        """
        
        def view(r, o):
            
            template_string = (
                '{% load djem %}'
                '{% ifperm user "djemtest.change_auditabletest" obj %}'
                '   IF'
                '{% else %}'
                '   ELSE'
                '{% endifperm %}'
            )
            
            output = self.render_template(template_string, {
                'obj': o
            }, r)
            
            return HttpResponse(output)
        
        obj = AuditableTest()
        obj.save(self.user)
        
        request = RequestFactory().get('/test/')
        response = view(request, obj)
        
        self.assertContains(response, 'ELSE', status_code=200)
    
    def test_ifperm__view__login(self):
        """
        Test the ifperm template tag when used in a template rendered as part of
        a request/response cycle (i.e. standard real world usage), when there
        is an authenticated user.
        """
        
        def view(r, o):
            
            template_string = (
                '{% load djem %}'
                '{% ifperm user "djemtest.change_auditabletest" obj %}'
                '   IF'
                '{% else %}'
                '   ELSE'
                '{% endifperm %}'
            )
            
            output = self.render_template(template_string, {
                'obj': o
            }, r)
            
            return HttpResponse(output)
        
        obj = AuditableTest()
        obj.save(self.user)
        
        request = RequestFactory().get('/test/')
        request.user = self.user  # simulate login
        response = view(request, obj)
        
        self.assertContains(response, 'IF', status_code=200)


class IfNotPermTestCase(PermTagTestCase):
    
    def test_ifnotperm__no_args(self):
        """
        Test the ifnotperm template tag raises TemplateSyntaxError when not
        provided any arguments.
        """
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_ifnotperm__too_few_args(self):
        """
        Test the ifnotperm template tag raises TemplateSyntaxError when provided
        too few arguments.
        """
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm "blah" %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_ifnotperm__too_many_args(self):
        """
        Test the ifnotperm template tag raises TemplateSyntaxError when provided
        too many arguments.
        """
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm "blah" "blah" "blah" "blah" %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_ifnotperm__invalid_permission(self):
        """
        Test the ifnotperm template tag renders the "if" block of the tag, with
        no "else" block defined, when an invalid permission is provided.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user "djemtest.not_a_real_permission" obj %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifnotperm__invalid_permission__else(self):
        """
        Test the ifnotperm template tag renders the "if" block of the tag, when
        defined, when an invalid permission is provided.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user "djemtest.not_a_real_permission" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifnotperm__with_permission(self):
        """
        Test the ifnotperm template tag does not render the "if" block of the
        tag, with no "else" block defined, when a user has a permission on an
        object.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, '')
    
    def test_ifnotperm__with_permission__else(self):
        """
        Test the ifnotperm template tag renders the "else" block of the tag,
        when defined, when a user has a permission on an object.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'ELSE')
    
    def test_ifnotperm__without_permission(self):
        """
        Test the ifnotperm template tag renders the "if" block of the tag, with
        with no "else" block defined, when a user does not have a permission on
        an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = AuditableTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifnotperm__without_permission__else(self):
        """
        Test the ifnotperm template tag renders the "if" block of the tag, with
        with an "else" block defined, when a user does not have a permission on
        an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = AuditableTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEqual(output, 'IF')
    
    def test_ifperm__complex_user_arg(self):
        """
        Test the ifperm template tag handles the user argument being a complex
        template variable.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm some.complex.variable "djemtest.change_auditabletest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': self.user
                }
            },
            'obj': obj
        })
        
        self.assertEqual(output, 'ELSE')
    
    def test_ifnotperm__complex_permission_arg(self):
        """
        Test the ifnotperm template tag handles the permission argument being a
        complex template variable.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user some.complex.variable obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'obj': obj,
            'some': {
                'complex': {
                    'variable': 'djemtest.change_auditabletest'
                }
            }
        })
        
        self.assertEqual(output, 'ELSE')
    
    def test_ifnotperm__complex_object_arg(self):
        """
        Test the ifnotperm template tag handles the object argument being a
        complex template variable.
        """
        
        obj = AuditableTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('djemtest.change_auditabletest', obj))
        
        template_string = (
            '{% load djem %}'
            '{% ifnotperm user "djemtest.change_auditabletest" some.complex.variable %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        output = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': obj
                }
            }
        })
        
        self.assertEqual(output, 'ELSE')
    
    def test_ifnotperm__view__anonymous(self):
        """
        Test the ifnotperm template tag when used in a template rendered as part
        of a request/response cycle (i.e. standard real world usage), when there
        is no authenticated user.
        """
        
        def view(r, o):
            
            template_string = (
                '{% load djem %}'
                '{% ifnotperm user "djemtest.change_auditabletest" obj %}'
                '   IF'
                '{% else %}'
                '   ELSE'
                '{% endifnotperm %}'
            )
            
            output = self.render_template(template_string, {
                'obj': o
            }, r)
            
            return HttpResponse(output)
        
        obj = AuditableTest()
        obj.save(self.user)
        
        request = RequestFactory().get('/test/')
        response = view(request, obj)
        
        self.assertContains(response, 'IF', status_code=200)
    
    def test_ifnotperm__view__login(self):
        """
        Test the ifnotperm template tag when used in a template rendered as part
        of a request/response cycle (i.e. standard real world usage), when there
        is an authenticated user.
        """
        
        def view(r, o):
            
            template_string = (
                '{% load djem %}'
                '{% ifnotperm user "djemtest.change_auditabletest" obj %}'
                '   IF'
                '{% else %}'
                '   ELSE'
                '{% endifnotperm %}'
            )
            
            output = self.render_template(template_string, {
                'obj': o
            }, r)
            
            return HttpResponse(output)
        
        obj = AuditableTest()
        obj.save(self.user)
        
        request = RequestFactory().get('/test/')
        request.user = self.user  # simulate login
        response = view(request, obj)
        
        self.assertContains(response, 'ELSE', status_code=200)


class CsrfifyAjaxTestCase(TemplateRendererMixin, TestCase):
    
    def test_valid__explicit(self):
        """
        Test the csrfify_ajax template tag when used in a request/response
        cycle with a present CSRF token, and with an explicitly provided valid
        target library.
        """
        
        def view(r):
            
            template_string = "{% load djem %}\n{% csrfify_ajax 'jquery' %}"
            
            output = self.render_template(template_string, {}, r)
            
            return HttpResponse(output)
        
        request = RequestFactory().get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content, b"('X-CSRFToken', '[a-zA-Z0-9]{64}')")
    
    def test_valid__implicit(self):
        """
        Test the csrfify_ajax template tag when used in a request/response
        cycle with a present CSRF token, and with no arguments (therefore using
        the default target library).
        """
        
        def view(r):
            
            template_string = "{% load djem %}\n{% csrfify_ajax %}"
            
            output = self.render_template(template_string, {}, r)
            
            return HttpResponse(output)
        
        request = RequestFactory().get('/test/')
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content, b"('X-CSRFToken', '[a-zA-Z0-9]{64}')")
    
    def test_invalid(self):
        """
        Test the csrfify_ajax template tag when used in a request/response
        cycle with a present CSRF token, and with an explicitly provided but
        invalid target library.
        """
        
        def view(r):
            
            template_string = "{% load djem %}\n{% csrfify_ajax 'invalid' %}"
            
            self.render_template(template_string, {}, r)
        
        request = RequestFactory().get('/test/')
        
        with self.assertRaisesMessage(TemplateDoesNotExist, 'invalid.html'):
            view(request)


class PaginateTestCase(TemplateRendererMixin, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        user = get_user_model().objects.create_user('test')
        
        for i in range(23):
            AuditableTest().save(user)
        
        # All tests will use the same Paginator with 5 results per page
        cls.paginator = Paginator(AuditableTest.objects.order_by('pk'), 5)
        
        # All tests will render the same basic template - just the
        # {% paginate %} tag on the given Page. It is the Page object that will
        # differ between tests.
        cls.template_string = (
            '{% load djem %}'
            '{% paginate page %}'
        )
        
        cls.user = user  # for TemplateRendererMixin
    
    def test_no_argument(self):
        """
        Test the paginate template tag when not provided with an argument. It
        should raise a TemplateSyntaxError - a single argument is required.
        """
        
        template_string = (
            '{% load djem %}'
            '{% paginate %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_multiple_arguments(self):
        """
        Test the paginate template tag when provided with multiple arguments. It
        should raise a TemplateSyntaxError - a single argument is required.
        """
        
        template_string = (
            '{% load djem %}'
            '{% paginate "multiple" "arguments" %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_first_page(self):
        """
        Test the paginate template tag when used on the first Page of a
        Paginator. It should render without previous/first links.
        """
        
        page = self.paginator.page(1)
        
        output = self.render_template(self.template_string, {'page': page})
        
        # The pagination block for the first page should:
        #  - show the page number and the number of pages
        #  - contain links to "Next" and "Last"
        #  - not contain links to "Previous" or "First"
        self.assertIn('Page 1 of 5', output)
        
        self.assertIn('"?page=2">Next', output)
        self.assertIn('"?page=5">Last', output)
        
        self.assertNotIn('Previous', output)
        self.assertNotIn('First', output)
    
    def test_last_page(self):
        """
        Test the paginate template tag when used on the last Page of a
        Paginator. It should render without next/last links.
        """
        
        page = self.paginator.page(5)
        
        output = self.render_template(self.template_string, {'page': page})
        
        # The pagination block for the first page should:
        #  - show the page number and the number of pages
        #  - contain links to "Previous" and "First"
        #  - not contain links to "Next" or "Last"
        self.assertIn('Page 5 of 5', output)
        
        self.assertIn('"?page=4">Previous', output)
        self.assertIn('"?page=1">First', output)
        
        self.assertNotIn('Next', output)
        self.assertNotIn('Last', output)
    
    def test_middle_page(self):
        """
        Test the paginate template tag when used on a middle Page of a
        Paginator. It should render with all navigation links.
        """
        
        page = self.paginator.page(3)
        
        output = self.render_template(self.template_string, {'page': page})
        
        # The pagination block for the first page should:
        #  - show the page number and the number of pages
        #  - contain links to "Previous" and "First"
        #  - contain links to "Next" and "Last"
        self.assertIn('Page 3 of 5', output)
        
        self.assertIn('"?page=2">Previous', output)
        self.assertIn('"?page=1">First', output)
        
        self.assertIn('"?page=4">Next', output)
        self.assertIn('"?page=5">Last', output)
    
    def test_invalid_page(self):
        """
        Test the paginate template tag when given something other than a Page
        object. Due to not having the attributes expected on a Page object, it
        should render without navigation links or valid page numbers.
        """
        
        output = self.render_template(self.template_string, {'page': None}, flatten=False)
        
        self.assertIn('Page  of ', output)
        
        self.assertNotIn('Previous', output)
        self.assertNotIn('First', output)
        
        self.assertNotIn('Next', output)
        self.assertNotIn('Last', output)


class FormFieldTestCase(TemplateRendererMixin, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        class TestForm(forms.Form):
            
            required_css_class = 'form-field--required'
            
            field = forms.CharField(required=False, label='Test Field')
            required_field = forms.CharField()
            help_field = forms.CharField(help_text='Some helpful text.')
        
        cls.form = TestForm
    
    def test_no_argument(self):
        """
        Test the form_field template tag when not provided with an argument. It
        should raise a TemplateSyntaxError - at least one argument is required.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field %}'
        )
        
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template_string, {})
    
    def test_default_wrapper(self):
        """
        Test the form_field template tag when no custom ``DJEM_FORM_FIELD_TAG``
        setting has been specified. It should use a <div> as the wrapping
        element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.field %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertEqual(output[:25], '<div class="form-field" >')
        self.assertEqual(output[-6:], '</div>')
    
    @override_settings(DJEM_FORM_FIELD_TAG='li')
    def test_custom_wrapper(self):
        """
        Test the form_field template tag when a custom ``DJEM_FORM_FIELD_TAG``
        setting has been specified. It should use the specified tag as the
        wrapping element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.field %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertEqual(output[:24], '<li class="form-field" >')
        self.assertEqual(output[-5:], '</li>')
    
    def test_content(self):
        """
        Test the form_field template tag in basic usage. It should output all
        expected HTML.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.field %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        expected_output = (
            '<div class="form-field" >'
            '<label for="id_field">Test Field:</label>'
            '<input type="text" name="field" id="id_field">'
            '</div>'
        )
        
        self.assertEqual(output, expected_output)
    
    def test_errors(self):
        """
        Test the form_field template tag when used with a field that contains
        errors after a form submission. It should add an element containing the
        list of errors.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.required_field %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertNotIn('<ul class="errors">', output)
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.required_field %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form({})  # bind form
        })
        
        self.assertIn('<ul class="errorlist"><li>This field is required.</li></ul>', output)
    
    def test_help_text(self):
        """
        Test the form_field template tag when used with a field that defines
        help text. It should add an element containing the help text.
        """
        
        form = self.form()
        template_string = (
            '{% load djem %}'
            '{% form_field form.field %}'
        )
        
        output = self.render_template(template_string, {
            'form': form
        })
        
        self.assertNotIn('<div class="form-field__help">', output)
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.help_field %}'
        )
        
        output = self.render_template(template_string, {
            'form': form
        })
        
        self.assertIn('<div class="form-field__help">Some helpful text.</div>', output)
    
    def test_css_classes(self):
        """
        Test the form_field template tag when used with a field that defines
        css classes. It should add those classes to the wrapping element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.required_field %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertIn('class="form-field form-field--required"', output)
    
    def test_extra_classes__string(self):
        """
        Test the form_field template tag when the ``extra_classes`` argument is
        given as a string. It should include those classes on the wrapping
        element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.field "testclass1 testclass2" %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertIn('class="form-field testclass1 testclass2"', output)
    
    def test_extra_classes__variable(self):
        """
        Test the form_field template tag when the ``extra_classes`` argument is
        given as a template context variable. It should include those classes
        on the wrapping element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.required_field classes %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form(),
            'classes': 'testclass1 testclass2'
        })
        
        self.assertIn('class="form-field form-field--required testclass1 testclass2"', output)
    
    def test_extra_attributes__strings(self):
        """
        Test the form_field template tag when keyword arguments are given with
        values as strings. It should include those arguments as HTML attributes
        on the wrapping element, replacing underscores with dashes as necessary.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.field data_id="1234" %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertIn('<div class="form-field" data-id="1234" >', output)
    
    def test_extra_attributes__variables(self):
        """
        Test the form_field template tag when keyword arguments are given with
        values as template context variables. It should include those arguments
        as HTML attributes on the wrapping element, replacing underscores with
        dashes as necessary.
        """
        
        template_string = (
            '{% load djem %}'
            '{% form_field form.field data_id=id %}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form(),
            'id': '1234'
        })
        
        self.assertIn('<div class="form-field" data-id="1234" >', output)


class CheckboxTestCase(TemplateRendererMixin, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        class TestForm(forms.Form):
            
            required_css_class = 'form-field--required'
            
            field = forms.BooleanField(required=False, label='Test Field')
            required_field = forms.BooleanField()
            help_field = forms.BooleanField(help_text='Some helpful text.')
        
        cls.form = TestForm
    
    def test_no_argument(self):
        """
        Test the checkbox template tag when not provided with an argument. It
        should raise a TemplateSyntaxError - at least one argument is required.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox %}{% endcheckbox%}'
        )
        
        with self.assertRaisesMessage(TemplateSyntaxError, "'checkbox' takes at least one argument"):
            self.render_template(template_string, {})
    
    def test_no_end_tag(self):
        """
        Test the checkbox template tag when not provided with an argument. It
        should raise a TemplateSyntaxError - at least one argument is required.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field %}'
        )
        
        with self.assertRaisesMessage(TemplateSyntaxError, 'Unclosed tag'):
            self.render_template(template_string, {
                'form': self.form()
            })
    
    def test_default_wrapper(self):
        """
        Test the checkbox template tag when no custom ``DJEM_FORM_FIELD_TAG``
        setting has been specified. It should use a <div> as the wrapping
        element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertEqual(output[:25], '<div class="form-field" >')
        self.assertEqual(output[-6:], '</div>')
    
    @override_settings(DJEM_FORM_FIELD_TAG='li')
    def test_custom_wrapper(self):
        """
        Test the checkbox template tag when a custom ``DJEM_FORM_FIELD_TAG``
        setting has been specified. It should use the specified tag as the
        wrapping element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertEqual(output[:24], '<li class="form-field" >')
        self.assertEqual(output[-5:], '</li>')
    
    def test_content(self):
        """
        Test the checkbox template tag in basic usage. It should output all
        expected HTML.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        expected_output = (
            '<div class="form-field" >'
            '<input type="checkbox" name="field" id="id_field">'
            '<label class="check-label" for="id_field"> Click this </label>'
            '</div>'
        )
        
        self.assertEqual(output, expected_output)
    
    def test_content__empty(self):
        """
        Test the checkbox template tag when no content in entered between the
        start and end tags. It should use the field's own label.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field %}{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        expected_output = (
            '<div class="form-field" >'
            '<input type="checkbox" name="field" id="id_field">'
            '<label class="check-label" for="id_field"> Test Field </label>'
            '</div>'
        )
        
        self.assertEqual(output, expected_output)
    
    def test_errors(self):
        """
        Test the checkbox template tag when used with a field that contains
        errors after a form submission. It should add an element containing the
        list of errors.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.required_field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertNotIn('<ul class="errors">', output)
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.required_field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form({})  # bind form
        })
        
        self.assertIn('<ul class="errorlist"><li>This field is required.</li></ul>', output)
    
    def test_help_text(self):
        """
        Test the checkbox template tag when used with a field that defines
        help text. It should add an element containing the help text.
        """
        
        form = self.form()
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': form
        })
        
        self.assertNotIn('<div class="form-field__help">', output)
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.help_field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': form
        })
        
        self.assertIn('<div class="form-field__help">Some helpful text.</div>', output)
    
    def test_css_classes(self):
        """
        Test the checkbox template tag when used with a field that defines
        css classes. It should add those classes to the wrapping element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.required_field %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertIn('class="form-field form-field--required"', output)
    
    def test_extra_classes__string(self):
        """
        Test the checkbox template tag when the ``extra_classes`` argument is
        given as a string. It should include those classes on the wrapping
        element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field "testclass1 testclass2" %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertIn('class="form-field testclass1 testclass2"', output)
    
    def test_extra_classes__variable(self):
        """
        Test the checkbox template tag when the ``extra_classes`` argument is
        given as a template context variable. It should include those classes
        on the wrapping element.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.required_field classes %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form(),
            'classes': 'testclass1 testclass2'
        })
        
        self.assertIn('class="form-field form-field--required testclass1 testclass2"', output)
    
    def test_extra_attributes__strings(self):
        """
        Test the checkbox template tag when keyword arguments are given with
        values as strings. It should include those arguments as HTML attributes
        on the wrapping element, replacing underscores with dashes as necessary.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field data_id="1234" %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form()
        })
        
        self.assertIn('<div class="form-field" data-id="1234" >', output)
    
    def test_extra_attributes__variables(self):
        """
        Test the checkbox template tag when keyword arguments are given with
        values as template context variables. It should include those arguments
        as HTML attributes on the wrapping element, replacing underscores with
        dashes as necessary.
        """
        
        template_string = (
            '{% load djem %}'
            '{% checkbox form.field data_id=id %}Click this{% endcheckbox%}'
        )
        
        output = self.render_template(template_string, {
            'form': self.form(),
            'id': '1234'
        })
        
        self.assertIn('<div class="form-field" data-id="1234" >', output)

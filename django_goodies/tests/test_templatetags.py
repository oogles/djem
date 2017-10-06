from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.template import TemplateDoesNotExist, TemplateSyntaxError, engines
from django.test import Client, TestCase

from .app.models import CommonInfoTest


class TemplateRendererMixin(object):
    """
    A helper for the following test cases, which render templates they provide
    as strings (not paths to files).
    
    Requires a ``user`` attribute be accessible on the class.
    """
    
    def render_template(self, template_string, context):
        
        context['user'] = self.user
        
        output = engines['django'].from_string(template_string).render(context)
        
        return output.strip()  # remove unnecessary whitespace


class PermTagTestCase(TemplateRendererMixin, TestCase):
    
    def setUp(self):
        
        user = get_user_model().objects.create_user('test', 'fakepassword')
        
        # Grant the user all permissions for CommonInfoTest to ensure the tests
        # focus on object-level permissions
        permissions = Permission.objects.filter(
            content_type__app_label='app',
            content_type__model='commoninfotest'
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
            '{% load goodies %}'
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
            '{% load goodies %}'
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
            '{% load goodies %}'
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
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user "app.not_a_real_permission" obj %}'
            '   IF'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, '')
    
    def test_ifperm__invalid_permission__else(self):
        """
        Test the ifperm template tag renders the "else" block of the tag, when
        defined, when an invalid permission is provided.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user "app.not_a_real_permission" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'ELSE')
    
    def test_ifperm__with_permission(self):
        """
        Test the ifperm template tag renders the "if" block of the tag, with no
        "else" block defined, when a user has a permission on an object.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifperm__with_permission__else(self):
        """
        Test the ifperm template tag renders the "if" block of the tag, with an
        "else" block defined, when a user has a permission on an object.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifperm__without_permission(self):
        """
        Test the ifperm template tag does not renders the "if" block of the tag,
        with no "else" block defined, when a user does not have a permission on
        an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = CommonInfoTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, '')
    
    def test_ifperm__without_permission__else(self):
        """
        Test the ifperm template tag renders the "else" block of the tag, when
        defined, when a user does not have a permission on an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = CommonInfoTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'ELSE')
    
    def test_ifperm__complex_user_arg(self):
        """
        Test the ifperm template tag handles the user argument being a complex
        template variable.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm some.complex.variable "app.change_commoninfotest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': self.user
                }
            },
            'obj': obj
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifperm__complex_permission_arg(self):
        """
        Test the ifperm template tag handles the permission argument being a
        complex template variable.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user some.complex.variable obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj,
            'some': {
                'complex': {
                    'variable': 'app.change_commoninfotest'
                }
            }
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifperm__complex_object_arg(self):
        """
        Test the ifperm template tag handles the object argument being a
        complex template variable.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifperm user "app.change_commoninfotest" some.complex.variable %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifperm %}'
        )
        
        template = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': obj
                }
            }
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifperm__view__anonymous(self):
        """
        Test the ifperm template tag when used in an actual request/response
        cycle, using a template file rendered by the render() shortcut in a view
        function (i.e. standard real world usage).
        In this case, the user passed to the tag is the AnonymousUser, as added
        to the template context by the "auth" context processor when no user is
        logged in.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        response = self.client.get(reverse('ifperm__render'))
        
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'ELSE')
    
    def test_ifperm__view__login(self):
        """
        Test the ifperm template tag when used in an actual request/response
        cycle, using a template file rendered by the render() shortcut in a view
        function (i.e. standard real world usage).
        In this case, the user passed to the tag is a logged in user, as added
        to the template context by the "auth" context processor.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        # Log the user in so the "user" variable in the template context is
        # correct
        self.client.force_login(self.user)
        
        response = self.client.get(reverse('ifperm__render'))
        
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'IF')


class IfNotPermTestCase(PermTagTestCase):
    
    def test_ifnotperm__no_args(self):
        """
        Test the ifnotperm template tag raises TemplateSyntaxError when not
        provided any arguments.
        """
        
        template_string = (
            '{% load goodies %}'
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
            '{% load goodies %}'
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
            '{% load goodies %}'
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
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user "app.not_a_real_permission" obj %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifnotperm__invalid_permission__else(self):
        """
        Test the ifnotperm template tag renders the "if" block of the tag, when
        defined, when an invalid permission is provided.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user "app.not_a_real_permission" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifnotperm__with_permission(self):
        """
        Test the ifnotperm template tag does not render the "if" block of the
        tag, with no "else" block defined, when a user has a permission on an
        object.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, '')
    
    def test_ifnotperm__with_permission__else(self):
        """
        Test the ifnotperm template tag renders the "else" block of the tag,
        when defined, when a user has a permission on an object.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'ELSE')
    
    def test_ifnotperm__without_permission(self):
        """
        Test the ifnotperm template tag renders the "if" block of the tag, with
        with no "else" block defined, when a user does not have a permission on
        an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = CommonInfoTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifnotperm__without_permission__else(self):
        """
        Test the ifnotperm template tag renders the "if" block of the tag, with
        with an "else" block defined, when a user does not have a permission on
        an object.
        """
        
        other_user = get_user_model().objects.create_user('other', 'fakepassword')
        obj = CommonInfoTest()
        obj.save(other_user)
        
        self.assertFalse(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user "app.change_commoninfotest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj
        })
        
        self.assertEquals(template, 'IF')
    
    def test_ifperm__complex_user_arg(self):
        """
        Test the ifperm template tag handles the user argument being a complex
        template variable.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm some.complex.variable "app.change_commoninfotest" obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': self.user
                }
            },
            'obj': obj
        })
        
        self.assertEquals(template, 'ELSE')
    
    def test_ifnotperm__complex_permission_arg(self):
        """
        Test the ifnotperm template tag handles the permission argument being a
        complex template variable.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user some.complex.variable obj %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'obj': obj,
            'some': {
                'complex': {
                    'variable': 'app.change_commoninfotest'
                }
            }
        })
        
        self.assertEquals(template, 'ELSE')
    
    def test_ifnotperm__complex_object_arg(self):
        """
        Test the ifnotperm template tag handles the object argument being a
        complex template variable.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        self.assertTrue(self.user.has_perm('app.change_commoninfotest', obj))
        
        template_string = (
            '{% load goodies %}'
            '{% ifnotperm user "app.change_commoninfotest" some.complex.variable %}'
            '   IF'
            '{% else %}'
            '   ELSE'
            '{% endifnotperm %}'
        )
        
        template = self.render_template(template_string, {
            'some': {
                'complex': {
                    'variable': obj
                }
            }
        })
        
        self.assertEquals(template, 'ELSE')
    
    def test_ifnotperm__view__anonymous(self):
        """
        Test the ifnotperm template tag when used in an actual request/response
        cycle, using a template file rendered by the render() shortcut in a view
        function (i.e. standard real world usage).
        In this case, the user passed to the tag is the AnonymousUser, as added
        to the template context by the "auth" context processor when no user is
        logged in.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        response = self.client.get(reverse('ifnotperm__render'))
        
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'IF')
    
    def test_ifnotperm__view__login(self):
        """
        Test the ifnotperm template tag when used in an actual request/response
        cycle, using a template file rendered by the render() shortcut in a view
        function (i.e. standard real world usage).
        In this case, the user passed to the tag is a logged in user, as added
        to the template context by the "auth" context processor.
        """
        
        obj = CommonInfoTest()
        obj.save(self.user)
        
        # Log the user in so the "user" variable in the template context is
        # correct
        self.client.force_login(self.user)
        
        response = self.client.get(reverse('ifnotperm__render'))
        
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'ELSE')


class CsrfifyAjaxTestCase(TestCase):
    
    def test_valid__explicit(self):
        """
        Test the csrfify_ajax template tag when used in a request/response
        cycle with a present CSRF token, and with an explicitly provided valid
        target library.
        """
        
        response = Client().get(reverse('csrfify_ajax__valid__explicit'))
        
        self.assertEquals(response.status_code, 200)
        self.assertRegexpMatches(response.content, "('X-CSRFToken', '[a-zA-Z0-9]{64}')")
    
    def test_valid__implicit(self):
        """
        Test the csrfify_ajax template tag when used in a request/response
        cycle with a present CSRF token, and with no arguments (therefore using
        the default target library).
        """
        
        response = Client().get(reverse('csrfify_ajax__valid__implicit'))
        
        self.assertEquals(response.status_code, 200)
        self.assertRegexpMatches(response.content, "('X-CSRFToken', '[a-zA-Z0-9]{64}')")
    
    def test_invalid(self):
        """
        Test the csrfify_ajax template tag when used in a request/response
        cycle with a present CSRF token, and with an explicitly provided but
        invalid target library.
        """
        
        with self.assertRaisesRegexp(TemplateDoesNotExist, 'invalid.js'):
            Client().get(reverse('csrfify_ajax__invalid'))


class PaginateTestCase(TemplateRendererMixin, TestCase):
    
    @classmethod
    def setUpTestData(cls):
        
        user = get_user_model().objects.create_user('test')
        
        for i in range(23):
            CommonInfoTest().save(user)
        
        # All tests will use the same Paginator with 5 results per page
        cls.paginator = Paginator(CommonInfoTest.objects.all(), 5)
        
        # All tests will render the same basic template - just the
        # {% paginate %} tag on the given Page. It is the Page object that will
        # differ between tests.
        cls.template_string = (
            '{% load goodies %}'
            '{% paginate page %}'
        )
        
        cls.user = user  # for TemplateRendererMixin
    
    def test_no_argument(self):
        """
        Test the paginate template tag when not provided with an argument. It
        should raise a TemplateSyntaxError - a single argument is required.
        """
        
        template_string = (
            '{% load goodies %}'
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
            '{% load goodies %}'
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
        
        output = self.render_template(self.template_string, {'page': None})
        
        self.assertIn('Page  of ', output)
        
        self.assertNotIn('Previous', output)
        self.assertNotIn('First', output)
        
        self.assertNotIn('Next', output)
        self.assertNotIn('Last', output)

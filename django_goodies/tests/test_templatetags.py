from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.template import engines, TemplateSyntaxError, TemplateDoesNotExist
from django.test import Client, TestCase

from .app.models import CommonInfoTest


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


class PermTagTestCase(TestCase):
    
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
    
    def render_template(self, template_string, context):
        
        context['user'] = self.user
        
        output = engines['django'].from_string(template_string).render(context)
        
        return output.strip()  # remove unnecessary whitespace


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

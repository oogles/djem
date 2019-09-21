from djem.utils.tests import setup_test_app

# Use an explicit app label so as not to interfere with the tests of
# setup_test_app() itself (which test implicit app labels)
setup_test_app(__package__, 'djemtest')

# Target for ROOT_URLCONF, since it has to point somewhere
urlpatterns = []

SETTINGS_FILE=$1
PROJECT_NAME=$2
DB_PASS=$3

if [ $4 -eq 1 ]; then
	DEBUG='True'
else
	DEBUG='False'
fi

# Generate SECRET_KEY using a Python script to choose 100 random characters from
# a set of letters, numbers and punctuation. Note: an explicit list of punctuation
# is provided, rather than using string.punctuation, so as to exclude single quotes,
# double quotes and backticks. This is done to avoid SyntaxErrors, both in this script and in
# the env.py file when it is written.
SECRET_KEY=`python -c 'import random; import string; print "".join([random.SystemRandom().choice(string.letters + string.digits + "!#$%&\()*+,-./:;<=>?@[\\]^_{|}~") for i in range(100)])'`

cat <<EOF > "$SETTINGS_FILE"
# Format these environment-specific settings as a dictionary, in order to:
# - mimic the use of environment variables in other settings files
#   os.environ.get() vs env.environ.get()
# - enable the use of defaults
#   env.environ.get('LEVEL_OF_AWESOME', 0)
# - enable the use of Python types (int, bool, etc)
# - provide those with little knowledge of the vagrant provisioning process, or
#   environment variables in general, a single point of reference for all
#   environment-specific settings and a visible source for those magically
#   obtained settings values.
#
# While this is Python, the convention should be to use simple name/value pairs
# in the dictionary below, without the use of code statements (conditionals, 
# loops, etc). Such statements should be left to the other settings files,
# though they could be based on some setting/s below.
# The idea is to provide an easy reference to, and use of, environment-specific
# settings, without violating 12factor (http://12factor.net/) too heavily (by 
# having code that is not committed to source control)
#
# Note that DEBUG should default to false in the primary settings file, and
# should only be defined here for development machines.

environ = {
    'DEBUG': $DEBUG,
    'SECRET_KEY': '$SECRET_KEY',
    'DB_USER': '$PROJECT_NAME',
    'DB_PASSWORD': '$DB_PASS'
}
EOF

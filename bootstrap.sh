#!/usr/bin/env bash

PROJECT_NAME="$1"
FULL_PROJECT="$2"

echo " "
echo "=================================================="
echo " "
echo "START PROVISION FOR \"$PROJECT_NAME\""
echo " "

# Get environment-specific variables from config:
# APP_DB_PASS:  Required. The password to use for the app database created in 
#               PostgreSQL.
# PUBLIC_KEY:   Optional. A custom public key to install in .ssh/authorized_keys.
# DEBUG:        Optional. Set to 1 to set 'DEBUG': True in the environment-specific
#               settings file for the project.
# TIMEZONE:     Optional. The server timezone. Defaults to Australia/Sydney.
if [ -f /vagrant/provision/config/env.sh ]; then
	source /vagrant/provision/config/env.sh
else
	echo "--------------------------------------------------"
	echo "ERROR: Missing required environment-specific config file provision/config/env.sh."
	echo "--------------------------------------------------"
	echo "=================================================="
	exit 1
fi

if [ ! "$APP_DB_PASS" ]; then
	echo "--------------------------------------------------"
	echo "ERROR: No APP_DB_PASS variable defined in provision/config/env.sh."
	echo "--------------------------------------------------"
	echo "=================================================="
	exit 1
fi

# Set timezone
if [ ! "$TIMEZONE" ]; then
	TIMEZONE='Australia/Sydney'
fi
echo " --- Setting timezone ---"
echo "$TIMEZONE" | tee /etc/timezone && dpkg-reconfigure --frontend noninteractive tzdata

echo " "
echo " --- Add/update apt repos ---"

# Add custom apt repo for postgres
/vagrant/provision/postgres-repo.sh

echo " "
echo "Updating..."
apt-get update

# Install all the things
/vagrant/provision/git.sh
/vagrant/provision/postgres.sh "$PROJECT_NAME" "$APP_DB_PASS"
/vagrant/provision/pip-virtualenv.sh "$PROJECT_NAME" "$FULL_PROJECT"

# Create settings file for environment-specific settings, with some known values
# and useful defaults
if [ -n "$FULL_PROJECT" ]; then
    ENV_SETTINGS_FILE="/vagrant/${PROJECT_NAME//-/_}/env.py"
else
    ENV_SETTINGS_FILE="/vagrant/env.py"
fi

if [ ! -f "$ENV_SETTINGS_FILE" ]; then
	/vagrant/provision/write-env-settings.sh "$ENV_SETTINGS_FILE" "$PROJECT_NAME" "$APP_DB_PASS" "$DEBUG"
fi

# Run database migrations
echo " "
echo " --- Run migrations ---"
su - vagrant -c "source ~/.virtualenvs/$PROJECT_NAME/bin/activate && /vagrant/manage.py migrate"

# Add custom scripts
if [ ! -d bin ] ; then
    su - vagrant -c "mkdir ~/bin"
fi

/vagrant/provision/bin/shell+.sh
/vagrant/provision/bin/runserver+.sh

# Add public key to authorized_keys
if [ "$PUBLIC_KEY" ]; then
	if ! grep -Fxq "$PUBLIC_KEY" .ssh/authorized_keys ; then
		echo "$PUBLIC_KEY" >> .ssh/authorized_keys
	fi
else
	echo " "
	echo "--------------------------------------------------"
	echo "WARNING: No PUBLIC_KEY variable defined in provision/config/env.sh."
	echo "No custom public key installed."
	echo "--------------------------------------------------"
fi

echo " "
echo "END PROVISION"
echo " "
echo "=================================================="

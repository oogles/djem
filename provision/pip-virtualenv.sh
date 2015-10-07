echo " "
echo " --- pip/virtualenv ---"

PROJECT_NAME="$1"
FULL_PROJECT="$2"

# Download get-pip.py if it doesn't already exist, install pip
if ! command -v pip; then
    wget -q https://bootstrap.pypa.io/get-pip.py
	python get-pip.py
	rm get-pip.py
fi

# Install virtualenv
pip install virtualenv

echo " "
echo "Creating virtualenv for $PROJECT_NAME..."

ACTIVATE_STR="source ~/.virtualenvs/$PROJECT_NAME/bin/activate"

# Create .virtualenvs directory if it doesn't exist
if [ ! -d .virtualenvs ]; then
    su - vagrant -c "mkdir ~/.virtualenvs"
fi

# Create a virtualenv for the project
if [ ! -d ".virtualenvs/$PROJECT_NAME" ]; then
	su - vagrant -c "virtualenv ~/.virtualenvs/$PROJECT_NAME"
fi

# Configure virtualenv to activate automatically when SSHing in
if ! grep -Fxq "$ACTIVATE_STR" .profile ; then
cat <<EOF >> .profile

$ACTIVATE_STR
cd /vagrant
EOF
fi

# Install Python dependencies
echo " "
echo " --- Python dependencies ---"
if [ -f /vagrant/requirements.txt ]; then
	su - vagrant -c "$ACTIVATE_STR && pip install -r /vagrant/requirements.txt"
else
	echo "None found"
fi

# If not a full project, install django-extensions to aid with dev
if [ -z "$FULL_PROJECT" ]; then
    su - vagrant -c "pip install django-extensions"
fi

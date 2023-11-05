#!/bin/bash

COMMAND_NAME="pvm"

echo "Installing required packages..."

# install required packages
pip install -r requirements.txt

# install the compiler for python
pip install -U pyinstaller

echo "Package Installation complete."

# build the executable
echo "Building the executable..."
pyinstaller --onefile app.py

# move the executable to the bin folder
echo "Executable built, installing the executable, insert root creds to proceed..."
sudo mv dist/app /bin/$COMMAND_NAME

echo "Installation completed, log out and log back in to use the application."
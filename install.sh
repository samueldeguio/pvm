#!/bin/bash

# setup color variables
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

printf  "[${BLUE}INFO${NC}] Installing required packages...\n"

# install required packages
pip3 install -r requirements.txt

# install the compiler for python
pip3 install -U pyinstaller

printf  "[${GREEN}SUCCESS${NC}] Package Installation complete.\n"

# build the executable
printf  "[${BLUE}INFO${NC}] Building PVM executable...\n"
pyinstaller --onedir pvm.py

# move the executable to the bin folder
printf  "[${GREEN}SUCCESS${NC}] Executable built, moving to bin folder...\n"
mv dist/pvm bin/

printf  "[${BLUE}INFO${NC}] Remove build files...\n"
rm -rf build dist pvm.spec

# build the custom PHP command that uses docker
printf "Building custom PHP command...\n"
pyinstaller --onedir php.py

# move the executable to the bin folder
printf  "[${GREEN}SUCCESS${NC}] Executable built, moving to bin folder...\n"
mv dist/php bin/

printf  "[${BLUE}INFO${NC}] Remove build files...\n"
rm -rf build dist php.spec

printf  "${GREEN}Installation completed${NC}\n"
printf  "Add the following line to your start up console script, and reboot the terminal:\n"
printf  "\texport PATH=\"\$PATH:$(pwd)/bin/pvm\"\n"
printf  "\texport PATH=\"\$PATH:$(pwd)/bin/php\"\n"
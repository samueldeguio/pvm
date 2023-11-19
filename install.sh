#!/bin/bash

# setup some variable
WORKING_DIR=$(pwd)

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

# remove previous builded files
printf "[${BLUE}INFO${NC}] Cleaning bin folder...\n"
rm -rf bin/pvm bin/php
printf "[${GREEN}SUCCESS${NC}] Bin folder cleaned.\n"

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

# init the PHP Version manager and the PHP command
cd bin
pvm init

# changing to the start directory
cd $WORKING_DIR

printf  "${GREEN}================== Installation completed ==================${NC}\n"
printf  "Add the following line to your start up console script, and reboot the terminal:\n"
printf  "\texport PATH=\"\$PATH:$(pwd)/bin/pvm\"\n"
printf  "\texport PATH=\"\$PATH:$(pwd)/bin/php\"\n"
# PVM (PHP Versioning System) 

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/samueldeguio/pvm/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/samueldeguio/pvm/releases/tag/v1.0.0)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/samueldeguio/pvm)


> PVM is a powerful PHP versioning system that simplifies managing different versions of PHP using Docker.


## Features ✨

- Easy installation and setup
- Switch and Manage between PHP versions with a single command
- No package left behind when removing a PHP version, we love to keep you PC clean 🧹
- No need to worry about dependencies

## Requirements 📋

 - 🐍 Python 3 Installed on your system 
- 🐳 Docker installed on your system

## Installation 🚀

1. Go to your HOME directory:

    ```bash
    cd ~
    ```

2. Clone the PVM repository:

    ```bash
    git clone https://github.com/samueldeguio/pvm.git
    ```

3. Go into the PVM directory:

    ```bash
    cd pvm
    ```

4. Run the install script:

    ```bash
    ./install.sh
    ```

5. As the installation script suggests, you will need to add the following line to your console file (e.g. `.bashrc`, `.zshrc`, etc.) and reload your CLI:

    ```bash
    export PATH="$PATH:~/pvm/bin/pvm"
    export PATH="$PATH:~/pvm/bin/php"
    ``` 
6. Enjoy! ✨

## Usage 📖
PVM offers you a variety of commands to manage your PHP versions. Here you will find a complete list of all available commands and their usage.
In any case you can see all available commands by running:
```bash
pvm --help
```
### Update PVM Repository
PVM uses a repository system to store all PHP versions and their data fetched directly from [php.watch](https://php.watch/versions). This allows for a faster and more efficient installation but comes with the downside of needed to be updated in case of changes.
To update the repository you can use a command similar to `apt update` for Ubuntu, the command is:
```bash
pvm update
```

### Install PHP Version
To install a PHP version you can use the `install` command followed by the version you want to install. For example to install PHP 8.0.0 you can run:
```bash
pvm install 8.0.0
```
This will install PHP 8.0.0 but it wil **NOT** set it as your version, to do so you need to use the `pvm use` command.
> ℹ️ **Tip**: You can also specify only the major version if you want its latest `pvm install 8.2`.

### Remove PHP Version
To remove a PHP version you can use the `remove` command followed by the version you want to remove. For example to remove PHP 8.0.0 you can run:
```bash
pvm remove 8.0.0
```
> ⚠️ **Warning**: Removing a version that is used on a local project will switch automatically the directory to work with the global version.

### List Versions
To list all installed PHP versions you can use the `ls` command:
```bash
pvm ls
```
This will list all installed PHP versions and highlight the one that are currently installed on the system. By default the command will list only major version, in case you need to see a specific minor version you can use the flag `-m` to specify the major version that you want to see the minor of:
```bash
pvm ls -m 8.2
```

### View Version in use
To view the current PHP version you can use the `which` command:
```bash
pvm which
```
This will print the current PHP version is use and its type (global or local). You can also force the command to show one of the global or local version by using the `--global` or `--local` flags

### Switch PHP Version
On PVM there are 2 types of PHP versions, the global and the local ones. 

The `global` versions are available on all directories and are the default ones. There can be only one global version at a time.

The `local` versions are available only on the directory where they are installed and are used only on that directory. There can be multiple local versions at a time but only one can be used in a directory.

To switch the global version you can use the `use` command followed by the version you want to use. For example to switch to PHP 8.0.0 you can run:
```bash
pvm use 8.0 # you can also use a minor version, just specify it like 8.0.1
```

To switch the local version in the current directory you can use the `local` command followed by the version you want to use. For example to switch to PHP 8.0.0 you can run:
```bash
pvm local 8.0 # you can also use a minor version, just specify it like 8.0.1
```

In case you need to unset a local version to start using the system wide version you can use the `nolocal` command:
```bash
pvm nolocal
```

---

## Limitations 🚧
Currently PVM is only available for Linux like systems and it manage only PHP CLI versions.
We are working to support also Full PHP Package like `php-apache` and `php-fpm`.

## How is done? 💡
This tool is based on [Docker](https://www.docker.com/) to containerize PHP versions and run it when needed.

To manage which container we need to run we created a Python script that is then builded into a binary file using [PyInstaller](https://www.pyinstaller.org/) and acts as the main manager command (PVM) that you can use to install, switch and remove your versions.

The PHP binary is also a custom Python script that is builded into a binary file using [PyInstaller](https://www.pyinstaller.org/) and acts as the PHP command by calling the right image based on your settings.

## Contributing
Made with ❤️ and ☕️ by [Samuel De Guio](https://github.com/samueldeguio)
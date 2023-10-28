import typer

from rich.console import Console

from include.PHPVersionManager import PHPVersionManager, PHPVersionManagerException
from include.ConsoleHelper import ConsoleHelper
from include.PHP import PHP

# setup main app and console object
app = typer.Typer()
console = Console()
ch = ConsoleHelper(console) 

@app.command(help="Install the given PHP version")
def install(version: str = typer.Argument(..., help="PHP version to install to install")):
    pass

@app.command(help="Set the PHP version to use globally")
def use (version: str = typer.Argument(..., help="PHP version to use")):
    pass

@app.command(help="Set the PHP version to use locally on current folder")
def local(version: str = typer.Argument(..., help="PHP version to use locally on current folder")):
    pass

@app.command(help="Unistall the given PHP version")
def remove(version: str = typer.Argument(..., help="PHP version to remove")):
    pass

@app.command(help="List all installed PHP versions")
def ls():
    """
    ls:
        List all available PHP versions
    """

@app.command(help="Update PHP repository with latest versions")
def update():
    """
    update:
        Fetch updates from PHP versions
    """
    

if __name__ == "__main__":
    try:
    
        # first check if minimum dependencies are installed
        PHPVersionManager.checkDependencies()

        # run the app
        app()

    except PHPVersionManagerException as e:
        ch.printError(e.__str__(), wide=True)
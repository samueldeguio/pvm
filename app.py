import typer

from rich.console import Console

from include.PHPVersionManager import PHPVersionManager, PHPVersionManagerException
from include.ConsoleHelper import ConsoleHelper

# setup main app and console object
app = typer.Typer()
console = Console()
ch = ConsoleHelper(console) 

@app.command(help="Install the given PHP version")
def install(version: str):
   PHPVersionManager.installVersion(console=console, version=version) 

@app.command(help="Set the PHP version to use globally")
def use (version: str = typer.Argument(..., help="PHP version to use")):
    pass

@app.command(help="Set the PHP version to use locally on current folder")
def local(version: str = typer.Argument(..., help="PHP version to use locally on current folder")):
    pass

@app.command(help="Unistall the given PHP version")
def remove(version: str = typer.Argument(..., help="PHP version to remove")):
    pass

@app.command(help="List all installed PHP versions" )
def ls(major : str = typer.Option(None, "--major", "-m", help="List only the given major versions")):
 
    """
    ls:
        List all available PHP versions
    """
    PHPVersionManager.listVersions(console=console, major=major)

@app.command(help="Update PHP repository with latest versions")
def update():
    """
    update:
        Fetch updates from PHP versions
    """
    PHPVersionManager.updateRepository(console=console)

if __name__ == "__main__":
    try:
    
        # first check if minimum dependencies are installed
        PHPVersionManager.checkDependencies()

        # run the app
        app()

    except PHPVersionManagerException as e:
        ch.printError(e.__str__(), wide=True)
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
    PHPVersionManager.setGlobalVersion(console=console, version=version)

@app.command(help="Set the PHP version to use locally on current folder")
def local(version: str = typer.Argument(..., help="PHP version to use locally on current folder")):
    PHPVersionManager.setLocalVersion(console=console, version=version)

@app.command(help="Unistall the given PHP version")
def remove(version: str = typer.Argument(..., help="PHP version to remove")):
    pass

@app.command(help="List all available PHP versions" )
def ls(major : str = typer.Option(None, "--major", "-m", help="List only the given major versions")):
 
    """
    ls:
        List all available PHP versions
    """
    PHPVersionManager.listVersions(console=console, major=major)

@app.command(help="Show PHP version in use")
def which( glob: bool = typer.Option(False, "--global", help="Use this flag to show global PHP version"), local : bool = typer.Option(False, "--local", help="Use this flag to show local PHP version")):
    """
    show:
        Show PHP version in use
    """
    vtype = None
    if glob: vtype = "global"
    elif local: vtype = "local"

    data = PHPVersionManager.getPHPVersion(vtype=vtype)
    
    if data["version"] is None : raise PHPVersionManagerException("No PHP version set, view full documentation at `pvm --help`")
    
    console.print("You are running PHP version [white bold]{}[/] {}ly".format(data["version"], data["type"]))

@app.command(help="Remove the local PHP version settings")
def nolocal():
    """
    nolocal:
        Remove the local version settings
    """
    PHPVersionManager.unsetLocalVersion(console=console)

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
import typer
import rich
import os

from include.PHPVersionManager import PHPVersionManager

app = typer.Typer()

@app.command()
def install(version: str = typer.Argument(..., help="PHP version to install to install")):
    pass

@app.command()
def use (version: str = typer.Argument(..., help="PHP version to use")):
    pass

@app.command()
def local(version: str = typer.Argument(..., help="PHP version to use locally on current folder")):
    pass

@app.command()
def remove(version: str = typer.Argument(..., help="PHP version to remove")):
    pass

@app.command()
def ls():
    pass

if __name__ == "__main__":
    app()
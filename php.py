import sys
import subprocess
import time

from rich.console import Console
from include.ConsoleHelper import ConsoleHelper
from include.PHPVersionManager import PHPVersionManager, PHPVersionManagerException

if __name__ == "__main__":

    try:
        # retrieve all the given arguments
        args = ' '.join(sys.argv[1:])

        # create the command to execute
        command = PHPVersionManager.getPHPCommand()+" "+args
        
        # run the command and get the result
        result = subprocess.run(command, shell=True, text=True)

        # exit with the same code as the command
        sys.exit(result.returncode)
    except PHPVersionManagerException as e:
        console = Console()
        ConsoleHelper(console).printError(e.__str__(), wide=True)
import sys
import subprocess
import time
from include.PHPVersionManager import PHPVersionManager, PHPVersionManagerException

if __name__ == "__main__":

    start = time.time()

    # retrieve all the given arguments
    args = ' '.join(sys.argv[1:])

    # create the command to execute
    command = PHPVersionManager.getPHPCommand()+" "+args
    
    # run the command and get the result
    result = subprocess.run(command, shell=True, text=True)

    end = time.time()
    print("Execution time: "+str(end - start))
    # exit with the same code as the command
    sys.exit(result.returncode)
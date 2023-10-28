import subprocess

class PHPVersionManager():

    @classmethod
    def checkDependencies(cls) -> bool :
        """
        CheckDependencies:
            Check if minimum dependencies are installed

        Throws:
            PHPVersionManagerException: if any dependency is not installed

        Returns:
            bool: True if all dependencies are installed, False otherwise
        """

        # check if docker cli is installed
        try:
            subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise PHPVersionManagerException("Docker CLI is not installed")
        
class PHPVersionManagerException(Exception):
    pass

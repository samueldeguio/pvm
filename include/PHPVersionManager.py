import subprocess
import os
import json

from os.path import expanduser

from threading import Thread
from queue import Queue

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, RenderableColumn
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich import print

from include.PHP import PHP, Status

class PHPVersionManager():

    """
    PVM_DIR:
        Path to the PVM system directory
    """
    __PVM_DIR = os.path.join(expanduser("~"), ".pvm/")

    """
    REPOSITORY_FILE:
        Path to the repository file
    """
    __REPOSITORY_FILE =  os.path.join(__PVM_DIR, "PHP_REPOSITORY")

    """
    DATABASE_FILE:
        Path to the database file
    """
    __DATABASE_FILE = os.path.join(__PVM_DIR, "PVMDB")

    """
    STATUS_MAP:
        Map of status to rich text description
    """
    __STATUS_MAP = {
        Status.UNSUPPORTED : "[red blink]Unsupported[/]",
        Status.SECURITY_FIX : "[yellow]Security Fix Only[/]",
        Status.SUPPORTED : "[green]Supported[/]",
        Status.LATEST : "[blue italic]Latest[/]",
        Status.UPCOMING : "[magenta]Upcoming[/]",
        Status.FUTURE_RELEASE : "[purple]Future Release[/]",
    }

    __PHP_COMMAND = "docker run --rm -v $PWD:/usr/src/app -w /usr/src/app php:{version}-cli php"

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

    @classmethod
    def listVersions(cls, console : Console, major = None) -> bool:
        """
        listVersions:
            List all available PHP versions

        Throws:
            PHPVersionManagerException: if the repository file could not be read

        Returns:
            bool: True if the repository file was read, False otherwise
        """

        # load data from the repository file
        php = PHP(cache=cls.__loadRepository())
        data = php.getData()
        
        pvm_data = cls.__loadDatabase()
        
        # check given data
        if major and major not in php.getMajorVersions() : raise PHPVersionManagerException("Invalid major version given")

        # init the table
        grid = Table(box=None)

        if not major:

            grid.add_column("Version")
            grid.add_column("Release Date")
            grid.add_column("Status")
            grid.add_column("Latest", justify="right")
            grid.add_column("")
            
            for mj_idx, mj in data.items():
                grid.add_row(
                    "[bold]PHP {}[/]".format(mj["name"]),
                    mj["date"].strftime("%Y-%m-%d") if mj["date"] else "---",
                    cls.__STATUS_MAP[mj["status"]],
                    (mj["latest"] if mj["latest"] else "---"),
                    "[blue bold]*[/]" if mj["latest"] in pvm_data["installed_versions"] else ""
                )
        else: 
            data = data[major]["releases"]
            if not data :
                console.print(f"[white]No versions available yet for PHP {major}[/]")
                return True

            grid.add_column("Version")
            grid.add_column("Release Date", justify="right")
            grid.add_column("")

            for mj_idx, mj in data.items(): 
                grid.add_row(
                    "[bold]PHP {}[/]".format(mj["name"]),
                    mj["date"].strftime("%Y-%m-%d") if mj["date"] else "---",
                    "[blue bold]*[/]" if mj["name"] in pvm_data["installed_versions"] else ""
                )

        print(grid)
        
        return True  

    @classmethod
    def updateRepository(cls, console : Console  = None) -> bool:
        """
        updateRepository:
            Update the repository file with all available PHP versions

        Throws:
            PHPVersionManagerException: if the repository file could not be updated

        Returns:
            bool: True if the repository file was updated, False otherwise
        """
        
        try:

            # setup some variable to keep track of the tasks and results
            data = {}

            # boot the queue object to pass data between threads
            queue = Queue()

            t = Thread(target=cls.__fetchUpdates, args=(queue,))
            t.start()

            console.print("Updating PHP repository...", style="green")
            with Progress(  
                SpinnerColumn(spinner_name="line"),
                TextColumn("Progress : "), 
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                TextColumn("{task.description}"), 
            ) as progress:
                
                # setup some variables to keep track of the tasks and results
                bar = None
                g_log_idx = 0

                while True:
                    eltype, eldata = queue.get()
                    
                    # if this is the final result, break the loop
                    if eltype == "data":
                        progress.remove_task(bar)
                        data = eldata
                        break

                    # if this is a task, process the task queue                    
                    if eltype == "tasks":
                        
                        # copy the object to prevent it from being modified while iterating
                        tasks = eldata.copy()

                        # get main task (it is always the first one)
                        task_ids = list(tasks.keys())
                        taskid = task_ids[0]
                        task = tasks[taskid]
                        subtask = tasks[task_ids[len(task_ids)-1]]
                        
                        # generate the bar if it does not exist
                        if bar is None:
                            bar = progress.add_task(task["name"], total=task["outof"])
                            current_completed = task["completed"]
                            
                        # update the general task progress and logs interface
                        if task["completed"] != current_completed : 
                            progress.update(bar, completed=task["completed"])
                            current_completed = task["completed"]
                            progress.update(bar, description=subtask["name"])

                        # print new logs arrived
                        c_log_idx = 0
                        for taskid in tasks:                             
                            for log in tasks[taskid]['logs']:
                                c_log_idx += 1 
                                if c_log_idx > g_log_idx : console.print(log)

                        # update the global log index
                        g_log_idx = c_log_idx   

            # join the threads
            t.join()

            # create the base directory if it does not exist
            if not os.path.exists(os.path.dirname(cls.__REPOSITORY_FILE)):
                os.makedirs(os.path.dirname(cls.__REPOSITORY_FILE))

            console.print("Writing repository file...")
            
            # write it to the file
            with open(cls.__REPOSITORY_FILE, "w") as f: json.dump(data, f)

            console.print("Repository file updated!", style="green")            

        except Exception as e:
            raise PHPVersionManagerException("Could not update repository file")
        
        return True
    
    @classmethod
    def installVersion(cls, console : Console, version : str) -> bool:

        # load data from the repository file
        php = PHP(cache=cls.__loadRepository())

        # retrieve the version manager database
        data = cls.__loadDatabase()

        # if this is a major version, get the latest minor version
        version = php.getLatestVersion(version) if php.majorExists(version) else version
       
        # check if the given version is valid
        if not version or not php.minorExists(version) and not php.majorExists(version): raise PHPVersionManagerException("Invalid version given")

        # install the given version
        # TODO : handle also fpm and apache versions
        try:
            
            # attempt to install the php version
            subprocess.run(["docker", "pull", f"php:{version}-cli"])

            # check if the image was installed
            result = subprocess.run(["docker", "image", "inspect", f"php:{version}-cli"], check=True, capture_output=True)
            inspect = json.loads(result.stdout.decode())
            if not inspect : raise PHPVersionManagerException("Error installing PHP image")

            # add the version to the database
            if version not in data["installed_versions"] : data["installed_versions"].append(version)

            # write changes to the database
            cls.__writeDatabase(data)
            
            console.print(f"[green]PHP {version} pulled correctly![/]" )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            raise PHPVersionManagerException("Error installing PHP image")


    @classmethod
    def removeVersion(cls, console : Console, version : str) -> bool:
        """
        removeVersion:
            Remove the given PHP version

        Args:
            version (str): the version to remove

        Throws:
            PHPVersionManagerException: if the given version is not installed

        Returns:
            bool: True if the version was removed, False otherwise
        """
        
        # load data from the repository file
        php = PHP(cache=cls.__loadRepository())

        # retrieve the version manager database
        data = cls.__loadDatabase()

        # if this is a major version, get the latest minor version
        version = php.getLatestVersion(version) if php.majorExists(version) else version

        # check if the given version is installed
        if version not in data["installed_versions"] : raise PHPVersionManagerException("The given version is not installed")

        # ask for user confirmation
        if not Confirm.ask(f"The following version will be removed : {version}\nAre you sure you want to proceed?", console=console, default=True):
            console.print("[green]No changes were made![/]")
            return False

        # retrieve docker image id
        result = subprocess.run(["docker","images",f"php:{version}-cli","-a","-q"], check=True, capture_output=True)
        image_id = result.stdout.decode().strip()

        # check if the image was retrieved
        if not image_id : raise PHPVersionManagerException("Error retrieving docker image, something might be off with docker")

        # remove the image from the system to free up space
        result = subprocess.run(["docker", "rmi", image_id], check=True)

        # check if the image was removed
        if result.returncode != 0 : raise PHPVersionManagerException("Error removing docker image, something might be off with docker")

        # remove the version from the database
        data["installed_versions"].remove(version)

        # remove the version from the local versions
        paths = [key for key, val in data["local_versions"].items() if val == version]
        for path in paths: del data["local_versions"][path]

        # remove the version from the global version
        if data["global_version"] == version : data["global_version"] = None

        # write changes to the database
        cls.__writeDatabase(data)

        console.print(f"[green]PHP {version} removed! All local paths using this version were reverted to the global version[/]" )
        return True

    @classmethod
    def setGlobalVersion(cls, console : Console, version : str) -> bool:
        """
        setGlobalVersion:
            Set the global PHP version to use

        Args:
            version (str): the version to set as global

        Throws:
            PHPVersionManagerException: if the given version is not installed

        Returns:
            bool: True if the global version was set, False otherwise
        """

        # load data from the repository file
        php = PHP(cache=cls.__loadRepository())

        # retrieve the version manager database
        data = cls.__loadDatabase()

        # if this is a major version, get the latest minor version
        version = php.getLatestVersion(version) if php.majorExists(version) else version

        # check if the given version is installed
        if version not in data["installed_versions"] : raise PHPVersionManagerException("The given version is not installed")

        # set the global version
        data["global_version"] = version

        # write changes to the database
        cls.__writeDatabase(data)

        console.print(f"[white]PHP {version} set as global![/]" )
        return True


    @classmethod
    def setLocalVersion(cls, console : Console, version : str) -> bool :
        """
        setLocalVersion:
            Set the local PHP version to use
        Args:
            console (Console): the console object to use
            version (str): the version to set on the current folder

        Returns:
            bool: True if the local version was set, False otherwise 
        """
        
        # load data from the repository file
        php = PHP(cache=cls.__loadRepository())

        # retrieve the version manager database
        data = cls.__loadDatabase()

        # if this is a major version, get the latest minor version
        version = php.getLatestVersion(version) if php.majorExists(version) else version

        # check if the given version is installed
        if version not in data["installed_versions"] : raise PHPVersionManagerException("The given version is not installed")

        # retrieve the current working path
        path = os.getcwd()

        # set the local version
        data["local_versions"][path] = version

        # write changes to the database
        cls.__writeDatabase(data)

        console.print(f"[white]PHP {version} set locally![/]" )
        return True

    @classmethod
    def unsetLocalVersion(cls, console : Console) -> bool:
        """
        unsetLocalVersion:
            Remove the local version settings

        Args:
            console (Console): the console object to use

        Returns:
            bool: True if the local version was unset, False otherwise
        """

        # retrieve the version manager database
        data = cls.__loadDatabase()

        # retrieve the current working path
        path = os.getcwd()

        # check if the local version is set
        if path not in data["local_versions"].keys() : raise PHPVersionManagerException("No local version set")

        # unset the local version
        del data["local_versions"][path]

        # write changes to the database
        cls.__writeDatabase(data)

        console.print(f"[green]Local PHP version unset![/]" )
        return True

    @classmethod
    def getPHPVersion(cls, vtype : str = None) -> dict:
        """
        getPHPVersion:
            Get the PHP version in use

        Args:
            vtype (str, None): the type of version to get

        Returns:
            str: the PHP version in use
        """

        # retrieve the version manager database
        data = PHPVersionManager.__loadDatabase()
        
        # return the version with the highest priority or the requested one
        if os.getcwd() in data["local_versions"].keys() and vtype != "global": return { "type" : "local", "version" : data["local_versions"][os.getcwd()]}
        else: return {"type" : "global", "version" : data["global_version"]}

    @classmethod
    def getPHPCommand(cls):
        """
        getPHPCommand:
            Get the PHP command to use

        Returns:
            str: the PHP command to use
        """


        # retrieve the PHP version in use 
        data = cls.getPHPVersion()
        
        # check if a PHP version is set
        if data["version"] is None : raise PHPVersionManagerException("No PHP version set, view full documentation at `pvm --help`")

        # return the default command
        return cls.__PHP_COMMAND.format(version=data["version"])

    @classmethod
    def __loadDatabase(cls) -> dict:

        # check if the database file exists
        if not os.path.exists(cls.__DATABASE_FILE):
            return {
                "installed_versions" : [],
                "global_version" : None,
                "local_versions" : {}
            }

        # load the database file and return the data
        with open(cls.__DATABASE_FILE, 'r') as f: data = json.load(f)
        
        return data


    @classmethod
    def __writeDatabase(cls, data : dict) -> bool:
        """
        __writeDatabase:
            Write the database file
        Args:
            data (dict): the data to write to the database file

        Returns:
            bool: True if the database file was written, False otherwise
        """
    
        # create the base directory if it does not exist
        if not os.path.exists(os.path.dirname(cls.__DATABASE_FILE)):
            os.makedirs(os.path.dirname(cls.__DATABASE_FILE))

        # write it to the file
        with open(cls.__DATABASE_FILE, "w") as f: json.dump(data, f)

        return True


    def __loadRepository() -> dict:
        """
        __loadRepository:
            Load the repository file

        Throws:
            PHPVersionManagerException: if the repository file could not be read

        Returns:
            dict: the repository data
        """

        # check if the repository file exists
        if not os.path.exists(PHPVersionManager.__REPOSITORY_FILE): return {}
        
        # load the repository file
        with open(PHPVersionManager.__REPOSITORY_FILE, "r") as f: data = json.load(f)

        return data

    def __fetchUpdates(queue) -> None :
        """
        __fetchUpdates:
            Fetch updates from PHP versions

        Args:
            tasks (list): the reference to the list of tasks to update
            queue (Thread.Queue): the queue obj to get the data from the thread

        """

        php = PHP(queue=queue)
        queue.put(("data", php.getData(json=True)))
        
        

class PHPVersionManagerException(Exception):
    pass

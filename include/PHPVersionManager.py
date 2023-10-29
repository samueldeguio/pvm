import subprocess
import os
import json

from os.path import expanduser

from threading import Thread
from queue import Queue

from rich.progress import Progress

from include.PHP import PHP

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
    def updateRepository(cls) -> bool:
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
            printed_tasks = {}
            data = {}

            # boot the queue object to pass data between threads
            queue = Queue()

            # fetch updates from repository with another thread
            t = Thread(target=cls.__fetchUpdates, args=(queue,))
            t.start()

            with Progress() as progress:
                while True:
                    
                    eltype, eldata = queue.get()
                    
                    # if this is the final result, break the loop
                    if eltype == "data": 
                        data = eldata
                        break

                    # if this is a task, process the task queue                    
                    if eltype == "tasks":
                        for taskid, task in eldata.items():

                            # create a new task if it does not exist
                            if taskid not in printed_tasks.keys(): 
                                taskbar = progress.add_task(task["name"], total=task["outof"], completed=task["completed"])
                                printed_tasks[taskid] = taskbar
                            
                            # update the task progress
                            progress.update(printed_tasks[taskid], completed=task["completed"])
            
            # join the threads
            t.join()

            # create the base directory if it does not exist
            if not os.path.exists(os.path.dirname(cls.__REPOSITORY_FILE)):
                os.makedirs(os.path.dirname(cls.__REPOSITORY_FILE))

            # write it to the file
            with open(cls.__REPOSITORY_FILE, "w") as f: json.dump(data, f)

        except Exception as e:
            raise PHPVersionManagerException("Could not update repository file")
        
        return True
    
    
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

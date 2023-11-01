import subprocess
import os
import json

from os.path import expanduser

from threading import Thread
from queue import Queue

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, RenderableColumn
from rich.console import Console

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

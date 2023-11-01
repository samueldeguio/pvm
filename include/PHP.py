import requests
import re
import uuid

from typing import List, Union

from enum import Enum
from datetime import datetime
from bs4 import BeautifulSoup

class Status(Enum):
    UNSUPPORTED = 1000
    SECURITY_FIX = 1001
    SUPPORTED = 1002
    LATEST = 1003
    UPCOMING = 1004
    FUTURE_RELEASE = 1005

class PHP():
    
    """
    DOCS_ENDPOINT:
        URL of the PHP documentation
    """
    __DOCS_ENDPOINT = "https://php.watch" # without final /


    """
    STATUS_MAP:
        Map the status string to the Status enum
    """
    __STATUS_MAP = {
        "Unsupported" : Status.UNSUPPORTED,
        "Security-Fixes Only" : Status.SECURITY_FIX,
        "Supported" : Status.SUPPORTED,
        "Supported (Latest)" : Status.LATEST,
        "Upcoming Release" : Status.UPCOMING,
        "Future Release" : Status.FUTURE_RELEASE,
    }


    def __init__(self, cache : dict = None, queue = None) -> None:
        
        self.__tasks = {}
        self.__queue = queue
        
        self.__data = self.parseCache(cache) if cache else self.fetchData()
    

    def getMajorVersions(self) -> list:
        """
        getMajorVersions:
            Get a list of all major versions

        Returns:
            list: list of all major versions
        """

        return list(self.__data.keys())
    

    def getMinorVersions(self, major : str) -> list:
        """
        getMinorVersions:
            Get a list of all minor versions for a given major version

        Args:
            major (str): the major version to get the minor versions for

        Returns:
            list: list of all minor versions for a given major version
        """

        return list(self.__data[major]["releases"].keys() if major in self.__data and "releases" in self.__data[major] else [] )
    

    def getLatestVersion(self, major : str) -> str:
        """
        getLatestMinorVersion:
            Get the latest minor version for a given major version

        Args:
            major (str): the major version to get the latest minor version for

        Returns:
            str: the latest minor version for a given major version
        """

        return self.__data[major]["latest"] if major in self.__data else None
    

    def majorExists(self, major : str) -> bool:
        """
        majorExists:
            Check if a given major version exists

        Args:
            major (str): the major version to check

        Returns:
            bool: True if the major version exists, False otherwise
        """

        return major in self.__data.keys()
    

    def minorExists(self, minor : str) -> bool:
        """
        minorExists:
            Check if a given minor version exists

        Args:
            minor (str): the minor version to check

        Returns:
            bool: True if the minor version exists, False otherwise
        """

        for major in self.__data:
            if minor in self.__data[major]["releases"].keys():
                return True
            
        return False
    

    def getData(self, json : bool = False) -> dict:
        """
        getData:
            Get complete object data

        Returns:
            dict: all versions
        """

        data = self.__data

        if json:
            for major in data:
                data[major]["date"] = data[major]["date"].strftime("%Y-%m-%d") if data[major]["date"] else None
                data[major]["status"] = data[major]["status"].value if data[major]["status"] else None 
                for minor in data[major]["releases"]:
                    data[major]["releases"][minor]["date"] = data[major]["releases"][minor]["date"].strftime("%Y-%m-%d") if data[major]["releases"][minor]["date"] else None

        return data

    def __flashQueue(self) -> None:
        """
        flashQueue:
            Flash the queue object with the newest data
        """

        if self.__queue: self.__queue.put(("tasks", self.__tasks))

    def __addTask(self, name : str, outof : int = 100) -> int:
        """
        __addTask:
            Add a task to the task log

        Args:
            task (str): the name of the operation
            outof (int, optional): the completion max value. Defaults to 100.

        Returns:
            int: return the task id
        """

        taskid = uuid.uuid4()
        
        self.__tasks[taskid] = {
            "id" : taskid,
            "name" : name,
            "outof" : outof,
            "completed" : 0,
            "logs" : []
        }

        self.__flashQueue()

        return taskid


    def __appendLog(self, task: int, message: Union[str, List[str]]) -> None:
        """
        __appendLog:
            Append a message to the task log

        Args:
            task (int): the task id to append the message to
            message (Union[str, List[str]]): the message or list of messages to append
        """
        
        # check if the task exists
        if task not in self.__tasks.keys(): raise PHPException("Invalid Task ID given")

        # parse the message
        if isinstance(message, str): message = [message] 

        self.__tasks[task]["logs"] += message
        self.__flashQueue()


    def __advanceTask(self, task : int, amount : int = 1) -> None:
        """
        __advanceTask:
            Advance a task in the task log
        Args:
            task (int): the task id to advance
            amount (int, optional): The amount to advance the given task. Defaults to 1.
        """

        if task not in self.__tasks.keys(): raise PHPException("Invalid Task ID given")

        self.__tasks[task]["completed"] += amount
        self.__flashQueue()
    

    def __removeTask(self, task : int) -> None:
        """
        __removeTask:
            Remove a task from the task log

        Args:
            task (int): the task id to remove
        """

        if task not in self.__tasks.keys(): raise PHPException("Invalid Task ID given")

        self.__tasks.pop(task)
        self.__flashQueue()
    

    def __clearTasks(self) -> None:
        """
        __clearTasks:
            Clear all tasks from the task log
        """
        self.__tasks = {}
        self.__flashQueue()


    def parseCache(self, cache : dict) -> dict :
        """
        parseCache:
            parse the raw cache into a valid one

        Args:
            cache (dict): the cache to parse

        Raises:
            PHPException: if the cache is invalid an exception is raised

        Returns:
            dict: returns the parsed cache
        """

        try:
            for major in cache:
                    cache[major]["date"] = datetime.strptime(cache[major]["date"], "%Y-%m-%d") if cache[major]["date"] else None
                    cache[major]["status"] = Status(cache[major]["status"]) if cache[major]["status"] else None 
                    for minor in cache[major]["releases"]:
                        cache[major]["releases"][minor]["date"] = datetime.strptime(cache[major]["releases"][minor]["date"], "%Y-%m-%d") if cache[major]["releases"][minor]["date"] else None
        except Exception:
            raise PHPException("Invalid Cache Given")


    def fetchData(self) -> dict:
        """
        fetchData:
            fetch from PHP documentation all required data

        Returns:
            str: current PHP version
        """

        # setup some varaiables
        data = {}
        rels_pattern = re.compile(r"\/versions\/.*/releases\/(.*)")

        # call the documentation and parse the response
        response = requests.get("{}/versions".format(PHP.__DOCS_ENDPOINT))
        soup = BeautifulSoup(response.content, "html.parser")

        # find all containers
        containers = soup.find_all("div", class_="version-item")

        # start the fetch version task
        tvers = self.__addTask(name="Global Advancement : ", outof=len(containers))
        
        # iterate over the PHP version elements and scrape the data
        for c in containers:
                        
            # scrape version informations 
            version = c.find("h3", class_="is-3 title").text.strip()
            date = c.find("div", class_="tag--release-date").find_all("span")[1].text.strip() if c.find("div", class_="tag--release-date") else None            
            status = c.find("div", class_="tag--release-status").find_all("span")[1].text.strip() if c.find("div", class_="tag--release-status") else None
            latest = c.find("div", class_="tag--releases-list").find_all("span")[1].text.strip() if c.find("div", class_="tag--releases-list") else None

            # advance the task
            self.__advanceTask(tvers)
            self.__appendLog(tvers, [
                f"Found Version [magenta italic]{version}[/] with following data...",
                f"  Release Date : [bright_blue]{date}[/bright_blue]",
                f"  Status : [bright_blue]{status}[/bright_blue]",
                f"  Latest Release : [bright_blue]{latest}[/bright_blue]"
            ])

            # check if the version has any release
            releases = {}
            if c.find("div", class_="tag--releases-list") != None :
                
                self.__appendLog(tvers, f"Fetching PHP {version} Releases...")

                # go to the release list of the version
                response = requests.get("{}/versions/{}/releases".format(PHP.__DOCS_ENDPOINT, version))
                soup = BeautifulSoup(response.content, "html.parser")

                # attempt to find all releases in the timeline object
                timeline = soup.find("div", class_="timeline")

                # if this is a future release, there are no events so skip it
                if timeline != None and (res := timeline.find_all("a")):
                                            
                    # create a second task to fetch all releases
                    trels = self.__addTask(name=f"Storing PHP [magenta italic]{version}[/] Releases : ", outof=len(res))

                    for r in res:

                        # advance the task
                        self.__advanceTask(trels)

                        # attempt to match the release name
                        match = re.search(rels_pattern, r["href"])

                        # skip all events on timeline that are not releases (they have no href)
                        if not match: continue
                        
                        # get the release name and date
                        release = match.group(1)
                        release_date = r.parent.parent.find("time").text.strip() if r.parent.parent.find("time") else None
                        
                        self.__appendLog(trels, f"Found Release : [magenta italic]{release}[/] ([bright_blue]{release_date}[/bright_blue])")
                        
                        # add the release to the releases list
                        releases[release] = {
                            "name": release,
                            "date": datetime.strptime(release_date, "%Y-%m-%d") if release_date else None,
                        }

                        self.__appendLog(trels, f"[green] Release {release} aknowledged![/]")



            data[version] = {
                "name" : version,
                "date" : datetime.strptime(date, "%Y-%m-%d") if date else None,
                "status" : PHP.__STATUS_MAP[status] if status else None,
                "latest" : latest if latest else None,
                "releases" : releases
            }

        return data
    
    @property
    def task(self):
        return self.__tasks

class PHPException(Exception):
    pass

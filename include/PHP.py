import requests
import re

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
    __DOCS_ENDPOINT = "https://php.watch" #without final /

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

    def __init__(self) -> None:
        self.__data = PHP.fetchData()
    

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
    

    def getAllVersions(self, json : bool = False) -> dict:
        """
        getAllVersions:
            Get all versions

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


    @classmethod
    def fetchData(cls) -> dict:
        """
        fetchData:
            fetch from PHP documentation all required data

        Returns:
            str: current PHP version
        """

        data = {}

        # call the documentation and parse the response
        response = requests.get("{}/versions".format(cls.__DOCS_ENDPOINT))
        soup = BeautifulSoup(response.content, 'html.parser')

        # find all containers
        containers = soup.find_all('div', class_="version-item")

        # iterate over the PHP version elements and scrape the data
        for c in containers:

            # scrape version informations 
            version = c.find("h3", class_="is-3 title").text.strip()
            date = c.find("div", class_="tag--release-date").find_all("span")[1].text.strip() if c.find("div", class_="tag--release-date") else None            
            status = c.find("div", class_="tag--release-status").find_all("span")[1].text.strip() if c.find("div", class_="tag--release-status") else None
            latest = c.find("div", class_="tag--releases-list").find_all("span")[1].text.strip() if c.find("div", class_="tag--releases-list") else None

            # check if the version has any release
            releases = {}
            if c.find("div", class_="tag--releases-list") != None :
                
                # go to the release list of the version
                response = requests.get("{}/versions/{}/releases".format(cls.__DOCS_ENDPOINT, version))
                soup = BeautifulSoup(response.content, 'html.parser')

                # attempt to find all releases in the timeline object
                timeline = soup.find("div", class_="timeline")

                # if this is a future release, there are no events so skip it
                if timeline != None:
                    
                    pattern = re.compile(r"\/versions\/.*/releases\/(.*)")
                    res = timeline.find_all("a")

                    for r in res:
                        
                        match = re.search(pattern, r["href"])

                        # skip all events on timeline that are not releases (they have no href)
                        if not match: continue
                        
                        # get the release name and date
                        release = match.group(1)
                        release_date = r.parent.parent.find("time").text.strip() if r.parent.parent.find("time") else None

                        # add the release to the releases list
                        releases[release] = {
                            "name": release,
                            "date": datetime.strptime(release_date, '%Y-%m-%d') if release_date else None,
                        }


            data[version] = {
                "name" : version,
                "date" : datetime.strptime(date, '%Y-%m-%d') if date else None,
                "status" : PHP.__STATUS_MAP[status] if status else None,
                "latest" : latest if latest else None,
                "releases" : releases
            }

        return data
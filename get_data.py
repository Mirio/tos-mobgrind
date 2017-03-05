from bs4 import BeautifulSoup
from datetime import datetime
from operator import itemgetter
from sys import exit
import requests

class GenericError(Exception):
    """An generic error occurred."""


class TosMobgrind:
    def __init__(self):
        """ Init function """
        self.db = []
        self.target_url = "http://www.tosbase.com/database/monsters"

    def get_page(self, url):
        """ Return bsed page of url given """
        try:
            page = requests.get(url)
            if page.status_code == 200:
                return BeautifulSoup(page.text, 'html.parser')
            else:
                raise GenericError("The server not return 200 status code")
        except Exception, e:
            print "Error during getting page, error = '%s'" % e
            exit(1)

    def parse_data(self, page):
        """ Parse the data given and popolate the database """
        for block in page.find_all("table", {"class": "db_table3"}):
            # Skip if location is not present
            for row in block.find_all("tr"):
                try:
                    if row.th.string == "Locations":
                        first_stats = block.find_all("tr")[1].find_all(
                            "td")
                        second_stats = block.find_all("tr")[3].find_all(
                            "td")
                        self.db.append({
                            "name": str(first_stats[0].string),
                            "level": int(first_stats[1].string),
                            "hp": int(second_stats[2].string.replace(",", "")),
                            "element": str(first_stats[4].img["alt"]),
                            "base_exp": int(second_stats[3].string.replace(
                                ",", "")),
                            "job_exp": int(second_stats[4].string.replace(
                                ",", "")),
                            "locations": str(row.find_next("td").text)
                        })
                except AttributeError:
                    pass

    def get_maxpage(self):
        """ Return the max number of page """
        try:
            page = self.get_page(self.target_url)
            page = page.find("ul", {"class": "page_list"})
            page = page.findAll("li")[-1]
            return int(page.a.contents[0])
        except Exception, e:
            print "Error during getting max page, error = '%s'" % e
            exit(1)

    def write_document(self, text):
        """ Write the document in markdown """
        try:
            outfile = open("mobtable.md", "w")
            outfile.write(text)
            outfile.close()
        except Exception, e:
            print "Error during writing document, error = '%s'" % e
            exit(1)

    def main(self):
        """ Main Function """
        for pagecount in xrange(1, self.get_maxpage()):
            page = self.get_page("%s?page=%s" % (self.target_url, pagecount))
            self.parse_data(page=page)

        filecontent = ("## Last Update: %s \nName | Level | HP | Base Exp | "
                       "Job Exp | Element | Locations \n:-: | :-: | :-: | "
                       " :-: | :-: | :-: | :-:\n" % datetime.now().strftime(
                           "%d/%m/%Y"))
        for mob in reversed(sorted(self.db, key=itemgetter("base_exp"))):
            filecontent += "%s | %s | %s | %s | %s | %s | %s \n" % (
                mob["name"], mob["level"], mob["hp"], mob["base_exp"],
                mob["job_exp"], mob["element"], mob["locations"]
            )
        self.write_document(text=filecontent)
        print "Done."


if __name__ == '__main__':
    obj = TosMobgrind()
    obj.main()

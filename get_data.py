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
        self.db = {"exp": [{"lv": 0, "req": 0}, {"lv": 1, "req": 0}],
                   "mob": []}
        self.monster_url = "http://www.tosbase.com/database/monsters"
        self.exp_url = "http://www.tosbase.com/game/exp-tables/base/"
        self.exp_tablebase = 5

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

    def parse_exppage(self, page):
        """ Parse the exp page given and popolate the database """
        for row in page.table.find_all("tr"):
            try:
                row_split = row.find_all("td")
                exp_lv = str(row_split[0].string.replace(",", ""))
                exp_req = int(row_split[1].string.replace(",", ""))
                self.db["exp"].append({"req": exp_req, "lv": int(exp_lv)})
            except IndexError:
                pass

    def parse_mobpage(self, page):
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
                        self.db["mob"].append({
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

    def get_percent(self, percent, value):
        """ Return the percent of the value given """
        try:
            if isinstance(percent, (int, float)):
                if isinstance(value, (int, float)):
                    return float(value)/100.0*float(percent)
                else:
                    raise GenericError("Value is not integer or float")
            else:
                raise GenericError("Percent is not integer or float")
        except ZeroDivisionError:
            return 0
        except Exception, e:
            print "Error during calc percent, error = '%s'" % e
            exit(1)

    def get_maxpage(self):
        """ Return the max number of page """
        try:
            page = self.get_page(self.monster_url)
            page = page.find("ul", {"class": "page_list"})
            page = page.findAll("li")[-1]
            return int(page.a.contents[0])
        except Exception, e:
            print "Error during getting max page, error = '%s'" % e
            exit(1)

    def find_mobs(self, exp_req):
        """ Find the list of monster best for exp given """
        try:
            outdata = []
            limit = int(self.get_percent(percent=10, value=exp_req))
            limit_upper = int(exp_req)+limit
            limit_bottom = int(exp_req)-limit
            for mob in self.db["mob"]:
                if mob["base_exp"] in range(limit_bottom, limit_upper):
                    outdata.append(mob["name"])

            return outdata

        except Exception, e:
            print "Error during finding mobs, error = '%s'" % e
            exit(1)

    def get_lastdivisible(self, value, base):
        """ Find the last value divisible by base """
        try:
            numdivisible = value
            while(True):
                if numdivisible % base == 0:
                    return numdivisible
                else:
                    numdivisible = numdivisible-1
        except ZeroDivisionError:
            return 0
        except Exception, e:
            print "Error during find divisible, error = '%s'" % e
            exit(1)

    def write_document(self, text, filename):
        """ Write the document in markdown """
        try:
            outfile = open(filename, "w")
            outfile.write(text)
            outfile.close()
        except Exception, e:
            print "Error during writing document, error = '%s'" % e
            exit(1)

    def main(self):
        """ Main Function """

        today = datetime.now().strftime("%d/%m/%Y")

        print "Exporting Moblist"
        for pagecount in xrange(1, self.get_maxpage()):
            page = self.get_page(url="%s?page=%s" % (self.monster_url,
                                                     pagecount))
            self.parse_mobpage(page=page)
        filecontent = ("## Last Update: %s \nName | Level | HP | Base Exp | "
        "Job Exp | Element | Locations \n:-: | :-: | :-: | "
        " :-: | :-: | :-: | :-:\n" % today)
        for mob in reversed(sorted(self.db["mob"], key=itemgetter("base_exp"))):
            filecontent += "%s | %s | %s | %s | %s | %s | %s \n" % (
            mob["name"], mob["level"], mob["hp"], mob["base_exp"],
            mob["job_exp"], mob["element"], mob["locations"]
            )
        self.write_document(text=filecontent, filename="mobtable.md")
        print "---> Done."

        print "Exporting Explist"
        page = self.get_page(url=self.exp_url)
        self.parse_exppage(page=page)
        sorted_exptable = sorted(self.db["exp"], key=itemgetter("lv"))

        filecontent = ("## Last Update: %s \nLevel | Exp Required\n"
                       ":-:|:-:\n" % (today))
        for exp_lv in sorted_exptable:
            filecontent += "%s | %s\n" % (exp_lv["lv"], exp_lv["req"])
        self.write_document(text=filecontent, filename="exptable.md")
        print "---> Done."

        print "Exporting Grindlist"
        filecontent = ("## Last Update: %s \nLevel | Mob at 2%% | Mob at 1%% | "
                       "Mob at 0.5%% | Mob at 0.2%%|\n:-:|:-:|:-:|:-:|:-:\n" % (
                           today))
        for lv in xrange(1, self.get_lastdivisible(
                            value=max(sorted_exptable)["lv"],
                            base=self.exp_tablebase)):
            if lv % self.exp_tablebase == 0:
                perc2 = self.find_mobs(exp_req=self.get_percent(
                    percent=2, value=self.db["exp"][lv]["req"]))
                perc1 = self.find_mobs(exp_req=self.get_percent(
                    percent=1, value=self.db["exp"][lv]["req"]))
                perc0 = self.find_mobs(exp_req=self.get_percent(
                    percent=0.5, value=self.db["exp"][lv]["req"]))
                perc02 = self.find_mobs(exp_req=self.get_percent(
                    percent=0.2, value=self.db["exp"][lv]["req"]))
                filecontent += "%s | %s | %s | %s | %s\n" % (lv, perc2, perc1,
                                                             perc0, perc02)
        self.write_document(text=filecontent, filename="grindtable.md")
        print "---> Done."


if __name__ == '__main__':
    obj = TosMobgrind()
    obj.main()

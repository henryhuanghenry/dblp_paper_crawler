# required packages
import requests
import lxml
import urllib
from bs4 import BeautifulSoup
from tqdm import tqdm as tqdm
import numpy as np
import os
import time

# Inputs
conference_names = ["ICSE", "FSE", "ASE", "ISSTA", "SOSP", "OSDI", "ATC", "NSDI",
                    "DSN", "ISSRE", "ASPLOS"]
journal_names = ["TSE", "TOSEM", "TDSC", "TPDS", "ESE"]

key_words = ["AAA BBB", "CCC DDD", "EEE FFF GGG"]

start_year = 2021

result_file_name = "search_result"
# Customize the inputs above, and the crawler is ready to go. 

# Other parameters
## url example "https://dblp.org/search/publ/api?q=NAME%20cause%20venue%3AOSDI&h=1000&format=xml"
base_search_url_front = "https://dblp.org/search/publ/api?q="
base_search_url_tail = "&h=1000&format=xml"

base_conference_url = "https://dblp.org/db/conf/TBD/index.html"
base_journal_url = "https://dblp.org/db/journals/TBD/index.html"


# main codes
result_dict = dict()  # {"name": [(title, year, link), ...]}


## make sure we got valid conference_and journal abbreviations
if os.path.exists("search_result.md") or os.path.exists("search_result.npy"):
    print("Result files exist (would overwrite). Skip the abbreviation checking. ")
    for name in journal_names+conference_names:
        if name not in result_dict.keys():
            result_dict[name] = []
else:
    for name in tqdm(journal_names, desc="{Checking the abbreviations of journals}"):
        tmp_request = requests.get(base_journal_url.replace("TBD", name.lower()))
        # make sure we have a valid conference name
        if tmp_request.status_code == 404:
            print("Warning! Check the abbreviation \"{}\"".format(name))
        if name not in result_dict.keys():
            result_dict[name] = []

    for name in tqdm(conference_names, desc="{Checking the abbreviations of conferences}"):
        tmp_request = requests.get(base_conference_url.replace("TBD", name.lower()))
        # make sure we have a valid conference name
        if tmp_request.status_code == 404:
            print("Warning! Check the abbreviation \"{}\"".format(name))
        if name not in result_dict.keys():
            result_dict[name] = []

## searching
for name in tqdm(conference_names+journal_names, desc="{Searching}", delay=0.1):
    tmp_titlelist = []  # "记录论文名称，防止重复"
    for key_word in key_words:
        # example: "root cause venue:OSDI"
        search_q = urllib.parse.quote(key_word + " venue:" + name)
        search_url = base_search_url_front + search_q + base_search_url_tail
        result_search = requests.get(search_url)
        # warn the 404
        if result_search.status_code == 404:
            print("404 when searching {} in venue {}!".format(key_word, name))
            continue
        # slow down the query and retry
        while result_search.status_code == 429:
            # According to https://dblp.org/faq/Am+I+allowed+to+crawl+the+dblp+website.html
            time.sleep(1)
            result_search = requests.get(search_url)
        # parse the xml result
        result_search_parsed = BeautifulSoup(result_search.text, features="xml")
        result_search_parsed = result_search_parsed.find_all("hit")
        # find title, year, link
        for i in range(len(result_search_parsed)):
            # title
            tmp_title = str(result_search_parsed[i].find_all("title")[0].string)
            # year
            tmp_year = str(result_search_parsed[i].find_all("year")[0].string)
            if int(tmp_year) < start_year:  # filter out
                continue
            # article link
            tmp_link = result_search_parsed[i].find_all("ee")[0]
            if len(tmp_link):
                tmp_link = str(tmp_link.string)
            # link for bibtex
            tmp_biblink = result_search_parsed[i].find_all("key")[0]
            if len(tmp_biblink):
                tmp_biblink = "https://dblp.org/rec/" + str(tmp_biblink.string) + ".html?view=bibtex&param=0"

            # store and avoid duplication
            if tmp_title not in tmp_titlelist:
                result_dict[name].append((tmp_title, tmp_year, tmp_link, tmp_biblink))
                tmp_titlelist.append(tmp_title)
    # sort
    result_dict[name] = sorted(result_dict[name], key=lambda x: x[1], reverse=True)

# output results search_result.md and search_result.npy
with open(result_file_name + ".md", "w", encoding="utf-8") as file:
    file.write("# Results\n")
    for name in result_dict.keys():
        file.write("## {}\n\n".format(name))
        file.write("| year | title | article_link | bib_link|\n")
        file.write("| -- | ----- | --- |---|\n")
        for i in result_dict[name]:
            file.write("| {} | {} | [article_link]({}) | [bib]({}) |\n".format(i[1], i[0], i[2], i[3]))
        file.write("\n\n")

np.save(result_file_name + ".npy", result_dict, allow_pickle=True)


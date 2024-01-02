# required packages
import requests
import lxml
import urllib
from bs4 import BeautifulSoup
from tqdm import tqdm as tqdm
import numpy as np
import os
import time
import pandas as pd
from functools import cmp_to_key
import random


# Other parameters
## url example "https://dblp.org/search/publ/api?q=NAME%20cause%20venue%3AOSDI&h=1000&format=xml"
base_search_url_front = "https://dblp.org/search/publ/api?q="
base_search_url_tail = "&h=500&c=15&format=xml"

base_conference_url = "https://dblp.org/db/conf/TBD/index.html"
base_journal_url = "https://dblp.org/db/journals/TBD/index.html"


def check_abbreviation(result_dict, journal_names, conference_names):
    """
    make sure we got valid conference_and journal abbreviations
    :param result_dict:
    :param journal_names:
    :param conference_names:
    :return:
    """
    if os.path.exists("search_result.md") or os.path.exists("search_result.npy"):
        print("Result files exist (would overwrite). Skip the abbreviation checking. ")
        for venu_name in journal_names + conference_names:
            if venu_name not in result_dict.keys():
                result_dict[venu_name] = []
    else:
        for venu_name in tqdm(journal_names, desc="{Checking the abbreviations of journals}"):
            tmp_request = requests.get(base_journal_url.replace("TBD", venu_name.lower()))
            # make sure we have a valid conference name
            if tmp_request.status_code == 404:
                print("Warning! Check the abbreviation \"{}\"".format(venu_name))
            if venu_name not in result_dict.keys():
                result_dict[venu_name] = []
    
        for venu_name in tqdm(conference_names, desc="{Checking the abbreviations of conferences}"):
            tmp_request = requests.get(base_conference_url.replace("TBD", venu_name.lower()))
            # make sure we have a valid conference name
            if tmp_request.status_code == 404:
                print("Warning! Check the abbreviation \"{}\"".format(venu_name))
            if venu_name not in result_dict.keys():
                result_dict[venu_name] = []
    return result_dict


def func_cmp(x, y):
    x, y = [x[2], x[1]], [y[2], y[1]]
    if x[0] < y[0]:
        return -1
    elif x[0] > y[0]:
        return 1
    else:
        if x[1] < y[1]:
            return -1
        elif x[1] > y[1]:
            return 1
        else:
            return 0




def search(result_dict, journal_names, conference_names, start_year, key_words, max_retries=20):
    """
    :param result_dict:
    :param journal_names:
    :param conference_names:
    :param start_year:
    :param key_words:
    :return: result_search
    """
    for venu_name in tqdm(conference_names+journal_names, desc="{Searching}", delay=0.5):
        time.sleep(2 + 4 * random.random())
        tmp_title_list = []  # "record title of the paper"
        for key_word in key_words:
            time.sleep(2 + 3 * random.random())
            # example: "root cause venue:OSDI"
            if venu_name in conference_names:
                search_q = urllib.parse.quote(key_word + " venue:" + venu_name)
            else:
                search_q = urllib.parse.quote(key_word + " stream:journals/" + venu_name.lower() + ":")
            search_url = base_search_url_front + search_q + base_search_url_tail
            result_search = requests.get(search_url)
            # warn the 404
            if result_search.status_code == 404:
                print("404 when searching {} in venue {}!".format(key_word, venu_name))
                continue
            # slow down the query and retry
            current_retry_times = 0
            while result_search.status_code == 429:
                current_retry_times += 1
                # According to https://dblp.org/faq/Am+I+allowed+to+crawl+the+dblp+website.html
                time.sleep(8 + current_retry_times * (2 + 4 * random.random()))
                result_search = requests.get(search_url)
                print("Return Code = 429. For reason = {}, current_retry_times = {:d}"
                      .format(result_search.reason, current_retry_times))
                assert result_search.reason != "Too Many Requests" and current_retry_times > max_retries
            # parse the xml result
            result_search_parsed = BeautifulSoup(result_search.text, features="xml")
            result_search_parsed = result_search_parsed.find_all("hit")
            # find title, year, link
            for i in range(len(result_search_parsed)):
                # hit score
                tmp_hit_score = str(result_search_parsed[i].attrs["score"])
                # title
                tmp_title = str(result_search_parsed[i].find_all("title")[0].string)
                # year
                tmp_year = str(result_search_parsed[i].find_all("year")[0].string)
                if int(tmp_year) < start_year:  # filter out
                    continue
                # article link
                try:
                    tmp_article_link = result_search_parsed[i].find_all("ee")[0]
                except:
                    tmp_article_link = ""
                if len(tmp_article_link):
                    tmp_article_link = str(tmp_article_link.string)
                # link for bibtex
                try:
                    tmp_bib_link = result_search_parsed[i].find_all("key")[0]
                    if len(tmp_bib_link):
                        tmp_bib_link = "https://dblp.org/rec/" + str(tmp_bib_link.string) + ".html?view=bibtex&param=0"
                except:
                    tmp_bib_link = ""
    
                # store and avoid duplication
                if tmp_title not in tmp_title_list:
                    result_dict[venu_name].append((tmp_title, tmp_hit_score, tmp_year, tmp_article_link, tmp_bib_link))
                    tmp_title_list.append(tmp_title)
        # sort
        result_dict[venu_name] = sorted(result_dict[venu_name], key=cmp_to_key(func_cmp), reverse=True)
        
    return result_dict


def output_results(result_file_name, result_dict, saving_npy=False):
    """
    :param result_file_name:
    :param result_dict:
    :param saving_npy:
    :return:
    """
    with open(result_file_name + ".md", "w", encoding="utf-8") as file:
        file.write("# Results\n")
        for venu_name in result_dict.keys():
            file.write("## {}\n\n".format(venu_name))
            file.write("| year | title | hit_score | article_link | bib_link|\n")
            file.write("| -- | ----- | -- | --- |---|\n")
            for i in result_dict[venu_name]:
                file.write("| {} | {} | {} | [article_link]({}) | [bib]({}) |\n".format(i[2], i[0], i[1], i[3], i[4]))
            file.write("\n\n")

    if not saving_npy:
        return None

    for venu_name in result_dict.keys():
        pd_table = []
        for i in result_dict[venu_name]:
            tmp_dict = {"year": i[1], "title": i[0], "article_link": i[2], "bib_link": i[3]}
            pd_table.append(tmp_dict)
        if len(pd_table):
            pd_table = pd.DataFrame(pd_table)
            if os.path.exists(result_file_name + ".xlsx"):
                mode = "a"
            else:
                mode = "w"
            with pd.ExcelWriter(result_file_name + ".xlsx", mode=mode) as writer:
                # write into different sheet
                pd_table.to_excel(writer,
                                  sheet_name=venu_name,
                                  index=False,
                                  engine="openpyxl"
                                  )

    np.save(result_file_name + ".npy", result_dict, allow_pickle=True)

    return None


if __name__ == "__main__":
    # Inputs
    conference_names = ["KDD", "WWW", "CIKM", "NIPS", "AAAI", "ICDM", "ICML", "ICLR", "SIGIR", "RECSYS", "IJCAI"]
    journal_names = ["TKDE", "PAMI", "TBD", "AI", "PR", "TNN"]
    key_words = ["bias", "recommend"]
    start_year = 2017
    result_file_name = "search_result"
    # Customize the inputs above, and the crawler is ready to go.

    result_dict = dict()
    result_dict = check_abbreviation(result_dict, journal_names, conference_names)
    result_dict = search(result_dict, journal_names, conference_names, start_year, key_words)
    output_results(result_file_name, result_dict)

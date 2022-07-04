![img](output_example_0.png)

# dblp_paper_crawler
- Crawl the dblp for related papers with given venue names and key words.
- Output the title, year, link to the article and link to the bibtex. 
- The main code is in [search_papers_in_dblp.py](./search_papers_in_dblp.py)

# Inputs (Only need to change the below variables in the code)
```python
# Inputs
conference_names = ["ICSE", "FSE", "ASE", "ISSTA", "SOSP", "OSDI", "ATC", "NSDI",
                    "DSN", "ISSRE", "ASPLOS"]
journal_names = ["TSE", "TOSEM", "TDSC", "TPDS", "ESE"]

key_words = ["AAA BBB", "CCC DDD", "EEE FFF GGG"]

start_year = 2021
```

## Outputs

- A Markdown file 
  - year
  - title
  - article link
  - bibtex link
- A ".npy" file

## Required packages

```python
pip install lxml
pip install tqdm
pip install numpy
pip install bs4
pip install urllib
pip install requests
```
 

![img](output_example_0.png)

# dblp_paper_crawler
- Crawl the dblp for related papers with given venue names and key words.
- Output the realted article title, year, link to the article and link to the bibtex. 
- The main code is in [search_papers_in_dblp.py](./search_papers_in_dblp.py)

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
 

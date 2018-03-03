#!/usr/bin/env python3
import os, requests, functools, queue, multiprocessing, sys
from bs4 import BeautifulSoup
from urllib.request import urlparse

MAX_LINKS = 50

def shutdown(q):
    while not q.empty():
        q.get_nowait()

def get_links(html, url):
    links = set()
    soup = BeautifulSoup(html, "lxml")

    # Extract all links from html of html
    for tag in soup.find_all('a', href=True):
        links.add(tag['href'])
    
    links = map(functools.partial(prepend_links, url), links)
    links = filter(validate_links, links)

    return links

def prepend_links(root, url):
    if root[-1] == '/':
        root = root[:-1]
    if url[0] == '/':
        return root + url
    else:
        return url

def validate_links(link):
    return not (urlparse(link).scheme is '' or urlparse(link).netloc is '')

def make_request(url, q, visited, process):
    headers  = {'user-agent': 'reddit-{}'.format(os.environ['USER'])}
    try:
        for _ in range(5):
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                break

        if response.status_code == 200:
            visited.put_nowait(url)
            if visited.qsize() > MAX_LINKS:
                shutdown(q)
                return
            print('{}: Visited url: {}, visited: {}, length of queue: {}'.format(process, url, visited.qsize(), q.qsize()))
            links = get_links(response.text, url)
            for link in links:
                q.put_nowait(link)
    except:
        pass

def crawl(q, visited, process):
    started = False
    while not q.empty() or not started:
        started = True
        make_request(q.get(), q, visited, process)

def main():
    pool = multiprocessing.Pool(2)
    m = multiprocessing.Manager()
    q = m.Queue(MAX_LINKS)
    visited = m.Queue()
    q.put_nowait('https://reddit.com')
    pool.map(functools.partial(crawl, q, visited), range(2))
    pool.close()

if __name__ == "__main__":
    main()

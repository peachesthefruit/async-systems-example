#!/usr/bin/env python3
import os, requests, functools, queue
from bs4 import BeautifulSoup
from urllib.request import urlparse

MAX_LINKS = 50

def shutdown():
    sys.exit(0)

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

def make_request(url, q, visited):
    headers  = {'user-agent': 'reddit-{}'.format(os.environ['USER'])}
    try:
        for _ in range(5):
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                break

        if response.status_code == 200:
            visited.put_nowait(url)
            if visited.qsize() > MAX_LINKS:
                shutdown()
                return
            print('Visited url: {}, visited: {}, length of queue: {}'.format(url, visited.qsize(), q.qsize()))
            links = get_links(response.text, url)
            for link in links:
                if not link in visited:
                    q.put(link)
    except:
        pass

def main():
    global MAX_LINKS
    args = sys.argv[1:]
    while len(args) and args[0].startswith('-') and len(args[0]) > 1:
        arg = args.pop(0)
        if arg == '-n':
            MAX_LINKS = int(args.pop(0))

    q = queue.Queue(MAX_LINKS//2)
    visited = queue.Queue()

    q.put('https://reddit.com')

    while not q.empty():
        make_request(q.get(), q, visited)

if __name__ == "__main__":
    main()

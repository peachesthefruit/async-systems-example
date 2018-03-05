#!/usr/bin/env python3
import os, requests, functools, queue, sys, signal
from bs4 import BeautifulSoup
from urllib.request import urlparse

MAX_LINKS = 50

def signal_handler(signal, frame):
    sys.exit(0)

def shutdown():
    sys.exit(0)

def get_links(html, url):
    '''Extract all links from an html page'''
    links = set()
    soup = BeautifulSoup(html, "lxml")

    # Extract all links from html of html
    for tag in soup.find_all('a', href=True):
        links.add(tag['href'])
    
    links = map(functools.partial(prepend_links, url), links)
    links = filter(validate_links, links)

    return links

def prepend_links(root, url):
    '''If link starts with /, add base url to it'''
    if root[-1] == '/':
        root = root[:-1]
    if url[0] == '/':
        return root + url
    else:
        return url

def validate_links(link):
    '''Validate if link has http or https and a nonempty domain'''
    return not (urlparse(link).scheme is '' or urlparse(link).netloc is '')

def make_request(q, visited):
    '''Make single request, process html and add links to queue'''
    # Get url
    url = q.get()

    headers  = {'user-agent': 'reddit-{}'.format(os.environ['USER'])}
    try:
        # Try to make request
        for _ in range(5):
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                break

        if response.status_code == 200:
            # Add url to visited
            visited.put_nowait(url)
            if visited.qsize() >= MAX_LINKS:
                shutdown()
                return
            print('Visited url: {}, visited: {}, length of queue: {}'.format(url, visited.qsize(), q.qsize()))

            # Get other links
            links = get_links(response.text, url)

            # Add other links to queue
            for link in links:
                q.put_nowait(link)
    except KeyboardInterrupt:
        shutdown()
    except:
        pass

def main():
    global MAX_LINKS
    args = sys.argv[1:]
    while len(args) and args[0].startswith('-') and len(args[0]) > 1:
        arg = args.pop(0)
        if arg == '-m':
            MAX_LINKS = int(args.pop(0))

    q = queue.Queue(MAX_LINKS)
    visited = queue.Queue(MAX_LINKS)

    q.put('https://reddit.com')

    while not q.empty():
        make_request(q, visited)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

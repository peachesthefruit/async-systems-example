#!/usr/bin/env python3
import os, aiohttp, functools, queue, requests, asyncio, time, sys, signal
from bs4 import BeautifulSoup
from urllib.request import urlparse

MAX_LINKS = 50

def signal_handler(signal, frame):
    sys.exit(0)

def shutdown():
    loop.stop()

    # Find all running tasks:
    pending = asyncio.Task.all_tasks()

    # Run loop until tasks done:
    loop.run_until_complete(asyncio.gather(*pending))

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

async def make_request(q, visited, session):
    '''Make single request, process html and add links to queue'''
    # Get url from queue
    url = await q.get()

    headers  = {'user-agent': 'reddit-{}'.format(os.environ['USER'])}
    try:
        # Try to make request
        for _ in range(5):
            response = await session.get(url, headers=headers)

            if response.status == 200:
                break

        if response.status == 200:
            # Add url to visited
            visited.put_nowait(url)
            if visited.qsize() > MAX_LINKS:
                shutdown()
                return
            print('Visited url: {}, visited: {}, length of queue: {}'.format(url, visited.qsize(), q.qsize()))

            # Get other links
            links = get_links(await response.text(), url)

            # Add other links to queue
            for link in links:
                q.put_nowait(link)

                # Add task to event loop
                asyncio.ensure_future(make_request(q, visited, session))
    except KeyboardInterrupt:
        shutdown()
    except:
        pass

async def main():
    # Handle command line arguments
    global MAX_LINKS
    args = sys.argv[1:]
    while len(args) and args[0].startswith('-') and len(args[0]) > 1:
        arg = args.pop(0)
        if arg == '-m':
            MAX_LINKS = int(args.pop(0))

    q = asyncio.Queue(MAX_LINKS//2)
    visited = asyncio.Queue()

    q.put_nowait('https://reddit.com')
    async with aiohttp.ClientSession(loop=loop) as session:
        await make_request(q, visited, session)
        await q.join()

if __name__ == "__main__":
    # Catch Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)

    # Get event loop and add main to it
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main())
    loop.run_forever()

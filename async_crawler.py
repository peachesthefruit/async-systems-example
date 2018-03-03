#!/usr/bin/env python3
import os, aiohttp, functools, queue, requests, asyncio, time, sys
from bs4 import BeautifulSoup
from urllib.request import urlparse

MAX_LINKS = 50

def shutdown():
    loop.stop()

    # Find all running tasks:
    pending = asyncio.Task.all_tasks()

    # Run loop until tasks done:
    loop.run_until_complete(asyncio.gather(*pending))

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

async def make_request(q, visited, session):
    url = await q.get()
    headers  = {'user-agent': 'reddit-{}'.format(os.environ['USER'])}
    try:
        for _ in range(5):
            response = await session.get(url, headers=headers)

            if response.status == 200:
                break

        if response.status == 200:
            visited.put_nowait(url)
            if visited.qsize() > MAX_LINKS:
                shutdown()
                return
            print('Visited url: {}, visited: {}, length of queue: {}'.format(url, visited.qsize(), q.qsize()))
            links = get_links(await response.text(), url)
            for link in links:
                q.put_nowait(link)
                asyncio.ensure_future(make_request(q, visited, session))
    except:
        pass

async def main():
    q = asyncio.Queue(MAX_LINKS)
    visited = asyncio.Queue()

    q.put_nowait('https://reddit.com')
    async with aiohttp.ClientSession(loop=loop) as session:
        await make_request(q, visited, session)
        await q.join()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main())
    loop.run_forever()

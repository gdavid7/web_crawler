import os
import shelve
import time

from collections import defaultdict, deque
from threading import Condition
from urllib.parse import urlparse

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid


class Frontier(object):
    """Thread-safe frontier with per-host politeness scheduling.

    Politeness is enforced inside `get_tbd_url` itself: a URL is only handed
    to a worker when its host is (a) not currently being fetched by another
    worker and (b) past its `next_available` timestamp. When a worker calls
    `mark_url_complete`, the frontier records `now + delay` as the host's
    next-available time. This guarantees a 500ms gap between request
    completion and the next request to the same host, across threads, with
    no extra sleeps in the workers.
    """

    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.delay = config.time_delay

        self._cond = Condition()
        self._pending = defaultdict(deque)   # host -> deque[url]
        self._pending_total = 0
        self._busy_hosts = set()             # hosts with an in-flight fetch
        self._next_available = {}            # host -> monotonic time
        self._inflight = 0                   # urls handed out, not yet completed

        if not os.path.exists(self.config.save_file) and not restart:
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)

        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                host = urlparse(url).netloc.lower()
                self._pending[host].append(url)
                self._pending_total += 1
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        with self._cond:
            while True:
                now = time.monotonic()
                soonest = None
                for host, queue in self._pending.items():
                    if not queue or host in self._busy_hosts:
                        continue
                    avail = self._next_available.get(host, 0.0)
                    if avail <= now:
                        url = queue.popleft()
                        self._pending_total -= 1
                        self._busy_hosts.add(host)
                        self._inflight += 1
                        return url
                    wait = avail - now
                    if soonest is None or wait < soonest:
                        soonest = wait

                # No fetchable host right now. If nothing is queued and nothing
                # is in flight, the crawl is finished — wake any other waiters.
                if self._pending_total == 0 and self._inflight == 0:
                    self._cond.notify_all()
                    return None

                # Otherwise wait until a host becomes ready or work arrives.
                self._cond.wait(timeout=soonest if soonest is not None else 1.0)

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        with self._cond:
            if urlhash in self.save:
                return
            self.save[urlhash] = (url, False)
            self.save.sync()
            host = urlparse(url).netloc.lower()
            self._pending[host].append(url)
            self._pending_total += 1
            self._cond.notify()

    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        host = urlparse(url).netloc.lower()
        with self._cond:
            if urlhash in self.save:
                self.save[urlhash] = (url, True)
                self.save.sync()
            else:
                self.logger.error(
                    f"Completed url {url}, but have not seen it before.")
            self._inflight = max(0, self._inflight - 1)
            self._busy_hosts.discard(host)
            self._next_available[host] = time.monotonic() + self.delay
            self._cond.notify_all()

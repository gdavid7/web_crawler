import os
import re
import json
import atexit
import hashlib
import dbm
import dbm.ndbm
import threading
from urllib.parse import urlparse, urlunparse, urljoin
from bs4 import BeautifulSoup

# Force ndbm backend so shelve works across threads (Python 3.14 defaults to
# sqlite3 which disallows cross-thread access, breaking the frontier worker)
dbm._defaultmod = dbm.ndbm

_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_FILE = os.path.join(_DIR, "Analytics.json")
VISITED_FILE = os.path.join(_DIR, "Visited.json")

# Persist state every N pages (with atexit flush on shutdown)
_FLUSH_INTERVAL = 25

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "cannot", "could", "did", "do", "does", "doing",
    "down", "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "will", "with", "would", "you", "your", "yours",
    "yourself", "yourselves"
}


ALLOWED_DOMAINS = (
    r"(.*\.)?ics\.uci\.edu$",
    r"(.*\.)?cs\.uci\.edu$",
    r"(.*\.)?informatics\.uci\.edu$",
    r"(.*\.)?stat\.uci\.edu$",
)

# Subdomains that aren't academic content (server monitoring, dev infra, etc.)
EXCLUDED_HOSTS = {
    "dale-cooper-v0.ics.uci.edu",  # nginx/php-fpm status pages
    "helpdesk.ics.uci.edu",        # IT support ticket system, likely contains PII
}


# In-memory state. Loaded once on first call, flushed atomically on a counter
# and at process exit. Avoids O(n) per-page disk churn on a growing JSON.
_state_lock = threading.Lock()
_state_loaded = False
_visited_urls = set()
_simhashes = []
_analytics = {
    "unique_pages": 0,
    "longest_page": {"url": "", "word_count": 0},
    "word_frequencies": {},
    "subdomains": {},
}
_pages_since_flush = 0


def _atomic_write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def _load_state():
    global _state_loaded, _visited_urls, _simhashes
    if _state_loaded:
        return
    if os.path.exists(VISITED_FILE):
        try:
            with open(VISITED_FILE) as f:
                v = json.load(f)
            urls = v.get("urls", [])
            # Backwards-compat: prior format stored {url: True}
            if isinstance(urls, dict):
                urls = list(urls.keys())
            _visited_urls = set(urls)
            _simhashes = list(v.get("simhashes", []))
        except (json.JSONDecodeError, OSError):
            pass
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE) as f:
                a = json.load(f)
            for k in ("unique_pages", "longest_page", "word_frequencies", "subdomains"):
                if k in a:
                    _analytics[k] = a[k]
        except (json.JSONDecodeError, OSError):
            pass
    _state_loaded = True


def _flush_state(force=False):
    global _pages_since_flush
    _pages_since_flush += 1
    if not force and _pages_since_flush < _FLUSH_INTERVAL:
        return
    _atomic_write_json(VISITED_FILE, {
        "urls": list(_visited_urls),
        "simhashes": _simhashes,
    })
    _atomic_write_json(ANALYTICS_FILE, _analytics)
    _pages_since_flush = 0


def _flush_on_exit():
    try:
        with _state_lock:
            if _state_loaded:
                _flush_state(force=True)
    except Exception:
        pass


atexit.register(_flush_on_exit)


def _defragment(url):
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, p.query, ""))


def _tokenize(text):
    return [w.lower() for w in re.findall(r"[a-zA-Z]{2,}", text)]


def _simhash(tokens):
    v = [0] * 64
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(64):
            v[i] += 1 if (h >> i) & 1 else -1
    fp = 0
    for i in range(64):
        if v[i] > 0:
            fp |= 1 << i
    return fp


def _hamming(a, b):
    return bin(a ^ b).count("1")


def _is_trap(parsed):
    parts = [p for p in parsed.path.split("/") if p]
    path_lower = parsed.path.lower()
    query = parsed.query

    if len(parts) > 10:
        return True
    # Repeating path segments (e.g. /a/b/a/b/a)
    if len(parts) > 4 and len(set(parts)) < len(parts) // 2:
        return True
    # Lots of query params — almost always a faceted/calendar trap
    if query.count("&") > 2:
        return True
    # DokuWiki: only the canonical view (no query, or just id=) is content
    if "doku.php" in path_lower and query:
        params = {q.split("=")[0] for q in query.split("&") if q}
        if params - {"id"}:
            return True
    # Trac/MediaWiki revision history walkers
    if re.search(r"(^|&)(version|rev|revision|oldid)=", query):
        return True
    if re.search(r"(^|&)action=(diff|history|edit|annotate|log|raw|info|render)", query):
        return True
    # Trac timeline: ?from=...&precision=second walks every event
    if "precision=" in query and "from=" in query:
        return True
    # WordPress comment-reply / share permalinks blow up combinatorially
    if re.search(r"(^|&)(replytocom|share|like_comment|unapproved)=", query):
        return True
    # Calendar/event paginators
    if re.search(r"(^|&)(year|month|day|week|tribe-bar-date|eventDisplay|outlook-ical)=", query, re.IGNORECASE):
        return True
    # Apache mod_autoindex sort variants (?C=N;O=A etc.)
    if re.search(r"[?&;](C|O|F|V|P)=[A-Z]", parsed.query + ";"):
        return True
    # Wiki attachments — never useful text content
    if "/raw-attachment/" in path_lower or "/attachment/wiki/" in path_lower:
        return True
    # CSS theme variants — pure styling, never content
    if "skin=" in query:
        return True
    # Login/logout/auth endpoints
    if re.search(r"(^|&)do=(login|logout|register)", query):
        return True
    # GitLab/Gitweb commit/blob/diff explorers
    if re.search(r"/-/(commits?|tree|blob|blame|raw|compare)/", path_lower):
        return True
    return False


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    # Cache-error statuses (603/604/605) should have been blocked by is_valid,
    # but if one slips through don't crash the worker — just skip it.
    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        return []

    # Skip anything that isn't HTML
    content_type = ""
    headers = getattr(resp.raw_response, "headers", None)
    if headers:
        content_type = (headers.get("Content-Type") or headers.get("content-type") or "").lower()
    if content_type and "html" not in content_type and "xml" not in content_type:
        return []

    # Skip very large pages — they're rarely useful and slow to parse
    content = resp.raw_response.content
    if len(content) > 5_000_000:  # 5 MB
        return []

    with _state_lock:
        _load_state()

        defrag_url = _defragment(url)

        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            return []

        links = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            try:
                links.append(_defragment(urljoin(resp.url, href)))
            except (ValueError, TypeError):
                continue

        if defrag_url in _visited_urls:
            return links

        _visited_urls.add(defrag_url)
        tokens = _tokenize(soup.get_text(separator=" "))

        # Count every unique defragmented URL as a unique page (per spec)
        _analytics["unique_pages"] += 1
        netloc = urlparse(defrag_url).netloc.lower()
        if any(re.match(pat, netloc) for pat in ALLOWED_DOMAINS):
            _analytics["subdomains"][netloc] = _analytics["subdomains"].get(netloc, 0) + 1

        # Dead-200 / no-text page — count it but don't follow links
        if len(tokens) < 50:
            _flush_state()
            return []

        # Large page with very low unique-word ratio = generated/repeated slop
        if len(tokens) > 5000 and len(set(tokens)) / len(tokens) < 0.1:
            _flush_state()
            return []

        # Near-duplicate detection
        fp = _simhash(tokens)
        is_near_dup = any(_hamming(fp, e) <= 3 for e in _simhashes)

        if not is_near_dup:
            _simhashes.append(fp)
            if len(tokens) > _analytics["longest_page"]["word_count"]:
                _analytics["longest_page"] = {"url": defrag_url, "word_count": len(tokens)}
            for token in tokens:
                if token not in STOP_WORDS:
                    _analytics["word_frequencies"][token] = _analytics["word_frequencies"].get(token, 0) + 1

        _flush_state()

        if is_near_dup:
            return []

        return links


def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not any(re.match(pat, parsed.netloc.lower()) for pat in ALLOWED_DOMAINS):
            return False
        if parsed.netloc.lower() in EXCLUDED_HOSTS:
            return False
        if _is_trap(parsed):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv|ipynb|sql|json|xml|txt|tsv"
            + r"|java|class|war|py|jsp|jspx"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            parsed.path.lower())
    except TypeError:
        print("TypeError for", parsed)
        raise

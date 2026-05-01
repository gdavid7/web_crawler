import os
import re
import json
import hashlib
import dbm
import dbm.ndbm
from urllib.parse import urlparse, urlunparse, urljoin
from bs4 import BeautifulSoup

# Force ndbm backend so shelve works across threads (Python 3.14 defaults to
# sqlite3 which disallows cross-thread access, breaking the frontier worker)
dbm._defaultmod = dbm.ndbm

_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_FILE = os.path.join(_DIR, "Analytics.json")
VISITED_FILE = os.path.join(_DIR, "Visited.json")

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


def _load_json(path): # used for loading the analytics and website JSONs
    with open(path) as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def _defragment(url): # defragments the URL (removing the fragment part at the end)
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, p.query, ""))


def _tokenize(text):
    return [w.lower() for w in re.findall(r"[a-zA-Z]{2,}", text)]


def _simhash(tokens): # implementing simhash: https://en.wikipedia.org/wiki/SimHash
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


def _hamming(a, b): # the simhash is measured by the bitwise hamming distance between values
    return bin(a ^ b).count("1")


def _is_trap(parsed): # If its a trap then we have to get out of it
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) > 10:
        return True
    # Repeating path segments (e.g. /a/b/a/b/a)
    if len(parts) > 4 and len(set(parts)) < len(parts) // 2:
        return True
    # Too many query parameters
    if parsed.query.count("&") > 3:
        return True
    # DokuWiki media manager trap
    if "do=media" in parsed.query:
        return True
    return False


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    if resp.status in {603, 604, 605}:
        raise RuntimeError(f"is_valid passed a URL it should have blocked — status {resp.status} for {url}")
    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        return []

    defrag_url = _defragment(url)
    visited = _load_json(VISITED_FILE)

    if defrag_url in visited["urls"]:
        return []

    visited["urls"][defrag_url] = True

    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    tokens = _tokenize(soup.get_text())

    analytics = _load_json(ANALYTICS_FILE)

    # Count every unique defragmented URL as a unique page
    analytics["unique_pages"] += 1
    netloc = urlparse(defrag_url).netloc.lower()
    if any(re.match(pat, netloc) for pat in ALLOWED_DOMAINS):
        analytics["subdomains"][netloc] = analytics["subdomains"].get(netloc, 0) + 1

    # Large page with very low unique-word ratio = generated/repeated slop, skip it
    if len(tokens) > 5000 and len(set(tokens)) / len(tokens) < 0.1:
        _save_json(VISITED_FILE, visited)
        _save_json(ANALYTICS_FILE, analytics)
        return []

    # Near-duplicate detection: skip content analytics and link extraction
    fp = _simhash(tokens)
    is_near_dup = any(_hamming(fp, e) <= 3 for e in visited["simhashes"])

    if not is_near_dup:
        visited["simhashes"].append(fp)
        if len(tokens) > analytics["longest_page"]["word_count"]:
            analytics["longest_page"] = {"url": defrag_url, "word_count": len(tokens)}
        for token in tokens:
            if token not in STOP_WORDS:
                analytics["word_frequencies"][token] = analytics["word_frequencies"].get(token, 0) + 1

    _save_json(VISITED_FILE, visited)
    _save_json(ANALYTICS_FILE, analytics)

    if is_near_dup:
        return []

    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href:
            links.append(_defragment(urljoin(resp.url, href)))
    return links


def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not any(re.match(pat, parsed.netloc.lower()) for pat in ALLOWED_DOMAINS):
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
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            parsed.path.lower())
    except TypeError:
        print("TypeError for", parsed)
        raise

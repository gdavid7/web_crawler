# Web Crawler Assignment 2 — Report

**Group members:**
- Minjun Kim — `kimm27` — 90303106
- David Gershony — `dgerhson` — 535578614
- Suhas Pendekanti — `sspendek` — 47643578
- Namratha Bhat — `namrathb` — 79106417

**Crawl summary:**
- USERAGENT: `IR US26 535578614 79106417 47643578 90303106`
- THREADCOUNT: 4 (multithreaded with per-host 500ms politeness)
- POLITENESS: 0.5s
- Seeds: `https://www.ics.uci.edu`, `https://www.cs.uci.edu`, `https://www.informatics.uci.edu`, `https://www.stat.uci.edu`
- Crawl finished cleanly: all 4 workers reported "Frontier is empty" with 0 unhandled exceptions.

---

## Q1. Number of unique pages

**5261 unique pages.**

Uniqueness is established by the URL after stripping the fragment, per spec.

---

## Q2. Longest page in terms of words

- **URL:** `https://duttgroup.ics.uci.edu/publications`
- **Word count:** 16,436

Words are counted by tokenizing the visible page text (HTML markup excluded, BeautifulSoup `get_text()`) with the regex `[a-zA-Z]{2,}`.

---

## Q3. 50 most common words across all pages

Standard English stopwords are excluded (https://www.ranks.nl/stopwords). Tokens are extracted as in Q2.

```
  1. ics, 8629
  2. research, 8165
  3. data, 7641
  4. uci, 7407
  5. information, 6410
  6. computer, 6040
  7. university, 5641
  8. us, 5435
  9. science, 4874
 10. events, 4803
 11. students, 4792
 12. learning, 4738
 13. irvine, 4246
 14. systems, 4228
 15. search, 4049
 16. ramesh, 3929
 17. software, 3747
 18. news, 3653
 19. computing, 3610
 20. contact, 3604
 21. can, 3478
 22. home, 3397
 23. pdf, 3333
 24. time, 3156
 25. student, 3092
 26. current, 3078
 27. jain, 3030
 28. uc, 2963
 29. project, 2956
 30. new, 2902
 31. projects, 2833
 32. people, 2821
 33. using, 2816
 34. machine, 2713
 35. support, 2531
 36. school, 2526
 37. faculty, 2510
 38. edu, 2476
 39. dataset, 2437
 40. paper, 2408
 41. past, 2404
 42. program, 2401
 43. health, 2369
 44. based, 2362
 45. community, 2343
 46. may, 2237
 47. graduate, 2187
 48. models, 2162
 49. week, 2161
 50. system, 2142
```

---

## Q4. Subdomains under uci.edu (100 total)

Alphabetically ordered with unique-page counts.

```
accessibility.ics.uci.edu, 6
acoi.ics.uci.edu, 109
archive-beta.ics.uci.edu, 10
archive.ics.uci.edu, 215
asterix.ics.uci.edu, 7
betapro.proteomics.ics.uci.edu, 1
cdb.ics.uci.edu, 5
cert.ics.uci.edu, 17
checkin.ics.uci.edu, 6
chenli.ics.uci.edu, 10
cloudberry.ics.uci.edu, 5
cml.ics.uci.edu, 37
code.ics.uci.edu, 14
computableplant.ics.uci.edu, 63
containers.ics.uci.edu, 1
courselisting.ics.uci.edu, 2
create.ics.uci.edu, 7
cs.ics.uci.edu, 12
cs.uci.edu, 2
deeprxn.ics.uci.edu, 31
dgillen.ics.uci.edu, 29
ds4all.ics.uci.edu, 9
duttgroup.ics.uci.edu, 106
dynamo.ics.uci.edu, 32
e2.ics.uci.edu, 1
edgelab.ics.uci.edu, 7
elms.ics.uci.edu, 3
emj.ics.uci.edu, 43
evoke.ics.uci.edu, 4
fellowships.ics.uci.edu, 3
flamingo.ics.uci.edu, 13
fr.ics.uci.edu, 3
futurehealth.ics.uci.edu, 179
gitlab.ics.uci.edu, 2
gradinfo.ics.uci.edu, 1
grape.ics.uci.edu, 72
graphics.ics.uci.edu, 1
hack.ics.uci.edu, 1
hobbes.ics.uci.edu, 10
hpi.ics.uci.edu, 5
hub.ics.uci.edu, 4
icde2023.ics.uci.edu, 46
ics.uci.edu, 770
industryshowcase.ics.uci.edu, 24
informatics.ics.uci.edu, 25
informatics.uci.edu, 7
intranet.ics.uci.edu, 16
ipubmed.ics.uci.edu, 1
isg.ics.uci.edu, 275
jgarcia.ics.uci.edu, 40
julia-hub.ics.uci.edu, 2
luci.ics.uci.edu, 4
mailman.ics.uci.edu, 35
malek.ics.uci.edu, 1
mcs.ics.uci.edu, 12
mdogucu.ics.uci.edu, 1
mds.ics.uci.edu, 9
mhcid.ics.uci.edu, 19
mlphysics.ics.uci.edu, 18
mover.ics.uci.edu, 24
mswe.ics.uci.edu, 10
mupro.proteomics.ics.uci.edu, 3
myip.ics.uci.edu, 1
nalini.ics.uci.edu, 7
netreg.ics.uci.edu, 1
ngs.ics.uci.edu, 737
oai.ics.uci.edu, 6
onboarding.ics.uci.edu, 2
password.ics.uci.edu, 8
pepito.proteomics.ics.uci.edu, 1
psearch.ics.uci.edu, 1
radicle.ics.uci.edu, 6
riscit.ics.uci.edu, 3
scratch.proteomics.ics.uci.edu, 4
seal.ics.uci.edu, 46
selectpro.proteomics.ics.uci.edu, 6
sherlock.ics.uci.edu, 7
signage.ics.uci.edu, 1
speedtest.ics.uci.edu, 1
staging-hub.ics.uci.edu, 1
stairs.ics.uci.edu, 3
stat.ics.uci.edu, 11
stat.uci.edu, 2
summeracademy.ics.uci.edu, 13
support.ics.uci.edu, 4
swiki.ics.uci.edu, 203
tad.ics.uci.edu, 3
tastier.ics.uci.edu, 1
tutoring.ics.uci.edu, 5
unite.ics.uci.edu, 10
vision.ics.uci.edu, 213
wics.ics.uci.edu, 373
wiki.ics.uci.edu, 106
www-db.ics.uci.edu, 25
www.cs.uci.edu, 5
www.ics.uci.edu, 987
www.informatics.ics.uci.edu, 1
www.informatics.uci.edu, 16
www.stat.uci.edu, 5
xtune.ics.uci.edu, 6
```

---

## Crawler design notes (for grader interview)

### What we count as a "page"
A unique URL after fragment-stripping. Even if SimHash near-duplicate detection flags a page as content-similar to one we've already analyzed, we still count it toward `unique_pages` (per the assignment's URL-only uniqueness rule); we just skip its content from word/longest-page analytics so duplicate prose doesn't bias them.

### Politeness
The frontier scheduler enforces a 500ms gap **per host** using a thread-safe `Condition` variable. Workers block in `get_tbd_url` until a host's gap has elapsed, so politeness is enforced at the scheduling layer rather than via `time.sleep` in workers. We verified zero violations across thousands of requests with 4 worker threads.

### Trap detection (`is_valid` / `_is_trap`)
We block URLs matching the following patterns:
- More than 10 path segments, or repeating path segments suggesting `/a/b/a/b/...` cycles
- Query strings with more than 2 `&` separators (faceted/calendar combinatorial explosions)
- DokuWiki: any query other than `id=` (catches `do=*`, `idx=*`, `rev=*`, etc.)
- Trac/MediaWiki revision walkers: `version=`, `rev=`, `revision=`, `oldid=`
- Trac action explorers: `action=diff|history|edit|annotate|log|raw|info|render`
- Trac timeline scrubbers: query containing both `precision=` and `from=`
- WordPress comment-reply / share traps: `replytocom=`, `share=`, `like_comment=`, `unapproved=`
- Calendar paginators: `year=`, `month=`, `day=`, `week=`, `tribe-bar-date=`, `eventDisplay=`, `ical=`, `outlook-ical=`
- Apache mod_autoindex sort variants (`?C=N;O=A` etc.)
- Wiki attachment paths (`/raw-attachment/`, `/attachment/wiki/`)
- CSS skin variants (`skin=` query param)
- Login/logout/auth endpoints (`do=login|logout|register`)
- GitLab/Gitweb explorers (`/-/(commits|tree|blob|blame|raw|compare)/`)
- Bare blog/category paginators (`/page/N`)
- Excluded subdomains: `dale-cooper-v0.ics.uci.edu` (php-fpm status pages), `helpdesk.ics.uci.edu` (IT ticket system, contains PII)

### Low-information detection
- Skip pages where `len(tokens) > 5000` and unique-word ratio is `< 0.1` (auto-generated/repeated content)
- Skip non-HTML responses (Content-Type filtering)
- Skip responses larger than 5MB
- SimHash near-duplicate detection: 64-bit fingerprint, blocked when Hamming distance ≤ 3 from any previously-seen page

### Resilience
- HTTP retries with exponential backoff (1s, 2s, 4s, 8s) up to 5 attempts before giving up on a URL — handles transient cache-server connection drops without crashing
- Atomic JSON state writes via temp+rename, flushed every 25 pages and on `atexit`
- `try/except` around URL parsing so malformed `<a href>` tags (e.g. literal `[YOUR_IP]` placeholder text from a Trac wiki page) don't crash the worker thread
- `try/finally` in worker's main loop guarantees `mark_url_complete` even if scraping raises

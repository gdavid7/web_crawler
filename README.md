# Web Crawler — Assignment 2

Crawls the following UCI domains:
- `*.ics.uci.edu`
- `*.cs.uci.edu`
- `*.informatics.uci.edu`
- `*.stat.uci.edu`

## Setup

A virtual environment is already created at `.venv/`. All dependencies are installed.

If you need to recreate it:
```bash
python3 -m venv .venv
.venv/bin/pip install spacetime-crawler4py/packages/spacetime-2.1.1-py3-none-any.whl
.venv/bin/pip install -r spacetime-crawler4py/packages/requirements.txt
.venv/bin/pip install beautifulsoup4 lxml
```

## Running the Crawler

From the root of the repo:
```bash
.venv/bin/python3 spacetime-crawler4py/launch.py --config_file spacetime-crawler4py/config.ini
```

To restart from scratch (clears frontier progress):
```bash
.venv/bin/python3 spacetime-crawler4py/launch.py --config_file spacetime-crawler4py/config.ini --restart
```

> **Note:** You must be on the UCI network or connected via VPN to reach the cache server.

## Monitoring Progress

Check page count and top words:
```bash
python3 -c "
import json
d = json.load(open('spacetime-crawler4py/Analytics.json'))
print('unique pages:', d['unique_pages'])
print('subdomains:', len(d['subdomains']))
print('longest page:', d['longest_page'])
print('top 10 words:', sorted(d['word_frequencies'].items(), key=lambda x: -x[1])[:10])
"
```

Watch the live log:
```bash
tail -f Logs/Worker.log
```

## Analytics Output

Results are written continuously to:
- `spacetime-crawler4py/Analytics.json` — unique page count, longest page, word frequencies, subdomain counts
- `spacetime-crawler4py/Visited.json` — visited URLs and SimHash fingerprints (used for deduplication)

These files persist across restarts. To reset analytics alongside the frontier, clear both JSON files and run with `--restart`.

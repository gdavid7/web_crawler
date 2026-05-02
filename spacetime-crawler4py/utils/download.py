import requests
import cbor
import time

from utils.response import Response

def download(url, config, logger=None):
    host, port = config.cache_server
    resp = None
    for attempt in range(5):
        try:
            resp = requests.get(
                f"http://{host}:{port}/",
                params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
                timeout=30)
            break
        except requests.exceptions.RequestException as e:
            if logger:
                logger.warning(f"Network error on {url} (attempt {attempt + 1}/5): {e}")
            if attempt == 4:
                if logger:
                    logger.error(f"Giving up on {url} after 5 network failures.")
                return Response({"error": str(e), "status": 0, "url": url})
            time.sleep(2 ** attempt)
    try:
        if resp and resp.content:
            return Response(cbor.loads(resp.content))
    except (EOFError, ValueError) as e:
        pass
    logger.error(f"Spacetime Response error {resp} with url {url}.")
    return Response({
        "error": f"Spacetime Response error {resp} with url {url}.",
        "status": resp.status_code,
        "url": url})

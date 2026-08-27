import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import urllib.request
import json
import time

apis = [
    'http://localhost:5000/api/status',
    'http://localhost:5000/api/ranking',
    'http://localhost:5000/api/universe/funnel_stats'
]

results = {}
for url in apis:
    start_t = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            duration = time.perf_counter() - start_t
            raw = r.read().decode('utf-8')
            data = json.loads(raw)
            results[url] = {'status': r.status, 'duration_sec': round(duration, 4), 'data': data}
            print(f"=== [SUCCESS] {url} (Latency: {duration:.4f}s | HTTP {r.status}) ===")
            snippet = json.dumps(data, ensure_ascii=False, indent=2)
            print(snippet[:600])
            if len(snippet) > 600:
                print("... [truncated]")
            print("-" * 70)
    except Exception as e:
        duration = time.perf_counter() - start_t
        results[url] = {'error': str(e), 'duration_sec': round(duration, 4)}
        print(f"=== [ERROR] {url} (Latency: {duration:.4f}s): {e} ===\n")

print("\n--- LATENCY SUMMARY ---")
for u, res in results.items():
    print(f"{u:<50} : {res.get('duration_sec')} seconds")

import json
import time
import urllib.request
for attempt in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8095/api/health',timeout=1) as r:
            if json.load(r).get('app')=='Switch Field Kit':break
    except OSError:pass
    time.sleep(.5)
else:raise SystemExit('Field Kit did not start')

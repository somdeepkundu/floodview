# Browser tests

Headless Chromium (Playwright for Python) with a fake camera, mocked GPS and synthetic
`deviceorientationabsolute` events, the same events a phone sends.

```bash
python3 -m http.server 8765 &                     # from the repo root
python3 tests/test_capture.py  http://localhost:8765 /tmp/fv-shots   # capture → tags → edit → ZIP → reload/resume
python3 tests/test_explorer.py http://localhost:8765 /tmp/fv-shots   # uses the ZIP from the test above
python3 tests/test_offline.py  http://localhost:8765                 # app, Explorer, capture and export with no network
```

Screenshots land in the output folder. Map tiles fail to load in a sandbox without internet; that's expected.

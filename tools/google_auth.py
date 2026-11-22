#!/usr/bin/env python3
"""google_auth.py - one-time Google login for your own channel's analytics and for saving reports to Drive.

    python3 tools/google_auth.py          # opens your browser once; run again to re-login
    python3 tools/google_auth.py --check  # confirms the saved login still works

Needs client_secret.json (an OAuth "Desktop app" client from your own Google Cloud project) in
the yt-studio folder. See README "Weekly data pull" for the 10-minute setup.

Scopes, all read-only except Drive:
    yt-analytics.readonly   your channel's analytics (views, watch time, retention curves)
    youtube.readonly        your channel's video list
    drive.file              only files and folders this tool creates (it cannot see the rest of your Drive)

The login is saved to ~/.config/yt-studio/google-token.json (only your user can read it). No dependencies.
"""
import base64, hashlib, http.server, json, os, secrets, sys, time, urllib.parse, urllib.request, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(ROOT, "client_secret.json")
CONF = os.path.expanduser("~/.config/yt-studio")
TOKEN = os.path.join(CONF, "google-token.json")
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/drive.file"]
_cache = {}


def _client():
    if not os.path.exists(CLIENT):
        sys.exit(f"Missing {CLIENT}. Download your OAuth Desktop client JSON and save it there (README: Weekly data pull).")
    d = json.load(open(CLIENT))
    return d.get("installed") or d.get("web") or d


def _post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if "invalid_grant" in body:
            raise Expired()
        sys.exit(f"Google token error {e.code}: {body[:300]}")


class Expired(Exception):
    """The saved login no longer works (apps left in Testing expire every 7 days)."""


def login():
    c = _client()
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            if "code" in q or "error" in q:
                got.update(q)
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            msg = "Signed in. You can close this tab and go back to Terminal." if "code" in q else "Sign-in failed: " + q.get("error", "?")
            self.wfile.write(f"<html><body style='font-family:sans-serif;padding:40px'><h2>{msg}</h2></body></html>".encode())

        def log_message(self, *a):
            pass

    host = "127.0.0.1" if "--ip" in sys.argv else "localhost"
    srv = http.server.HTTPServer((host, 0), H)
    redirect = f"http://{host}:{srv.server_port}/"  # matches the Desktop client's registered http://localhost
    url = c.get("auth_uri", "https://accounts.google.com/o/oauth2/auth") + "?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent",
        "code_challenge": challenge, "code_challenge_method": "S256", "state": state})
    print("Opening your browser to sign in to Google...")
    print("Use the Google account that owns the YouTube channel. If Google warns that the app isn't verified,")
    print("click Advanced -> Go to <your app name> (it's your own app).\n")
    print("If the browser doesn't open, paste this link into it:\n" + url + "\n")
    webbrowser.open(url)
    deadline = time.time() + 300
    while not got and time.time() < deadline:
        srv.timeout = 5
        srv.handle_request()
    if "code" not in got:
        sys.exit("Sign-in did not finish: " + got.get("error", "timed out after 5 minutes"))
    if got.get("state") != state:
        sys.exit("Sign-in state mismatch; run again.")
    tok = _post(c.get("token_uri", "https://oauth2.googleapis.com/token"), {
        "code": got["code"], "client_id": c["client_id"], "client_secret": c.get("client_secret", ""),
        "redirect_uri": redirect, "grant_type": "authorization_code", "code_verifier": verifier})
    if "refresh_token" not in tok:
        sys.exit("Google did not return a refresh token. Remove the app at myaccount.google.com/permissions and run again.")
    os.makedirs(CONF, exist_ok=True)
    with open(TOKEN, "w") as f:
        json.dump({"refresh_token": tok["refresh_token"], "scopes": SCOPES}, f)
    os.chmod(TOKEN, 0o600)
    print(f"Saved your Google login to {TOKEN}")


def access_token():
    if "t" in _cache and _cache["exp"] > time.time() + 60:
        return _cache["t"]
    if not os.path.exists(TOKEN):
        sys.exit("Not signed in to Google yet. Run: python3 tools/google_auth.py")
    c = _client()
    for attempt in (1, 2):
        saved = json.load(open(TOKEN))
        try:
            tok = _post(c.get("token_uri", "https://oauth2.googleapis.com/token"), {
                "client_id": c["client_id"], "client_secret": c.get("client_secret", ""),
                "refresh_token": saved["refresh_token"], "grant_type": "refresh_token"})
            break
        except Expired:
            if attempt == 2:
                sys.exit("Google sign-in failed again. Run: python3 tools/google_auth.py")
            # Testing-mode apps expire weekly: open the browser so one click renews it.
            if sys.platform == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e", 'display notification "Your browser is open: click your account to renew it" '
                                'with title "yt-studio: Google sign-in expired"'], capture_output=True)
            print("Google sign-in expired (normal every 7 days while the app is in Testing). Opening the browser to renew...")
            login()
    _cache.update(t=tok["access_token"], exp=time.time() + int(tok.get("expires_in", 3600)))
    return _cache["t"]


def request(url, method="GET", body=None, headers=None, params=None):
    """Authorised call to a Google API. body: dict (sent as JSON) or bytes (sent as-is)."""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    h = {"Authorization": "Bearer " + access_token()}
    h.update(headers or {})
    data = None
    if isinstance(body, dict):
        data = json.dumps(body).encode(); h.setdefault("Content-Type", "application/json")
    elif body is not None:
        data = body
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} {url.split('?')[0]}: {e.read().decode('utf-8', 'replace')[:400]}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        me = request("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet", "mine": "true"})
        items = me.get("items", [])
        print("OK, signed in as channel:", items[0]["snippet"]["title"] if items else "(no channel on this account)")
    else:
        login()
        me = request("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet", "mine": "true"})
        items = me.get("items", [])
        print("Channel:", items[0]["snippet"]["title"] if items else "(this Google account has no YouTube channel - sign in with the right one)")

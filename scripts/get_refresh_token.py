"""
One-off helper to mint a new SPOTIFY_REFRESH_TOKEN.

Spotify apps in Development mode expire refresh tokens after a fixed
lifetime (see the app's dashboard "Refresh Token Lifetime" field), so this
needs to be re-run periodically.

Usage:
    uv run python scripts/get_refresh_token.py

Opens a browser to Spotify's consent screen, catches the redirect on
http://127.0.0.1:8000/callback (must match a Redirect URI registered on
the app -- Spotify only exempts the literal loopback IP, not the
"localhost" hostname, from its HTTPS requirement), exchanges the code
for tokens, and prints the refresh token.
"""

import os
import re
import subprocess
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import requests
import webbrowser
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI = "http://127.0.0.1:8000/callback"
SCOPE = "user-top-read"

authorize_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
    {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [None])[0]
        error = query.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        if error:
            self.wfile.write(f"Authorization failed: {error}".encode())
        else:
            self.wfile.write(b"Authorized. You can close this tab.")

        self.server.auth_code = code
        self.server.auth_error = error

    def log_message(self, *args):
        pass  # silence default request logging


def update_dotenv(refresh_token: str):
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    with open(env_path) as f:
        content = f.read()
    new_content, count = re.subn(
        r"^SPOTIFY_REFRESH_TOKEN=.*$",
        f"SPOTIFY_REFRESH_TOKEN={refresh_token}",
        content,
        flags=re.MULTILINE,
    )
    if count == 0:
        new_content = content.rstrip("\n") + f"\nSPOTIFY_REFRESH_TOKEN={refresh_token}\n"
    with open(env_path, "w") as f:
        f.write(new_content)
    print("Updated local .env")


def update_github_secret_and_redeploy(refresh_token: str):
    repo = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    subprocess.run(
        ["gh", "secret", "set", "SPOTIFY_REFRESH_TOKEN", "--repo", repo],
        input=refresh_token, text=True, check=True,
    )
    print(f"Updated SPOTIFY_REFRESH_TOKEN secret on {repo}")

    subprocess.run(
        ["gh", "workflow", "run", "Docker Image CI/CD", "--repo", repo],
        check=True,
    )
    print("Triggered Docker Image CI/CD workflow (build + deploy to Oracle)")


def main():
    print(f"Opening browser for Spotify authorization:\n{authorize_url}\n")
    webbrowser.open(authorize_url)

    server = HTTPServer(("127.0.0.1", 8000), CallbackHandler)
    server.auth_code = None
    server.auth_error = None
    server.handle_request()  # blocks until the one callback request arrives

    if server.auth_error:
        raise SystemExit(f"Spotify returned an error: {server.auth_error}")
    if not server.auth_code:
        raise SystemExit("No authorization code received.")

    token_resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": server.auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    token_resp.raise_for_status()
    tokens = token_resp.json()

    refresh_token = tokens["refresh_token"]
    print("\nAccess token: ", tokens["access_token"])
    print("Refresh token:", refresh_token)

    update_dotenv(refresh_token)

    answer = input("\nPush this token to the GitHub secret and redeploy prod now? [y/N] ")
    if answer.strip().lower() == "y":
        update_github_secret_and_redeploy(refresh_token)
    else:
        print("Skipped. Re-run manually with:")
        print('  gh secret set SPOTIFY_REFRESH_TOKEN --repo <owner>/<repo>')
        print('  gh workflow run "Docker Image CI/CD" --repo <owner>/<repo>')


if __name__ == "__main__":
    main()

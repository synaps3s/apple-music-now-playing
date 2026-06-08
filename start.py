#!/usr/bin/env python3
"""
Starts the FastAPI server and a Cloudflare quick tunnel, then updates
the GitHub profile README with the new tunnel URL.

Can be run directly or managed via the included systemd user service.
"""
import subprocess
import re
import sys
import signal
import threading
import time
import requests
import base64
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import GITHUB_TOKEN, GITHUB_REPO, SERVER_PORT


def update_readme(tunnel_url: str):
    """
    Replace the Now Playing badge URL in the GitHub README.

    Cloudflare quick tunnels generate a new hostname on every startup,
    so the README is updated automatically each time the server starts.
    The README must contain at least one line matching:

        ![Now Playing](https://...)

    If no such line is found, the correct placeholder is printed so you
    can add it manually -- after that, future startups handle it automatically.
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/README.md",
        headers=headers,
    )
    if r.status_code != 200:
        print(f"Could not fetch README: {r.status_code} {r.text}")
        return

    data    = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    sha     = data["sha"]

    badge_url   = f"{tunnel_url}/now-playing.svg"
    new_content, n = re.subn(
        r"!\[Now Playing\]\(https://[^\)]+\)",
        f"![Now Playing]({badge_url})",
        content,
    )

    if n == 0:
        print("Placeholder not found in README.")
        print(f"Add this line once, then restart: ![Now Playing]({badge_url})")
        return

    encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
    r = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/README.md",
        headers=headers,
        json={
            "message": "chore: update music widget url",
            "content": encoded,
            "sha":     sha,
        },
    )

    if r.status_code in (200, 201):
        print(f"README updated -> {badge_url}")
    else:
        print(f"Could not update README: {r.status_code} {r.text}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processes  = []

    print("Starting FastAPI server...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app",
         "--host", "0.0.0.0", "--port", str(SERVER_PORT)],
        cwd=script_dir,
    )
    processes.append(server_proc)
    time.sleep(2)
    print(f"Server listening on port {SERVER_PORT}")

    print("Starting Cloudflare tunnel...")
    tunnel_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"localhost:{SERVER_PORT}"],
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
    )
    processes.append(tunnel_proc)

    # The public URL is printed to stderr once the tunnel is established
    url_found = False
    for line in iter(tunnel_proc.stderr.readline, b""):
        decoded = line.decode("utf-8", errors="ignore")
        match   = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", decoded)
        if match:
            tunnel_url = match.group(0)
            print(f"Tunnel active: {tunnel_url}")
            update_readme(tunnel_url)
            url_found = True
            break

    if not url_found:
        print("Could not read tunnel URL from cloudflared output.")

    # Drain stderr so the pipe buffer never fills and blocks cloudflared
    threading.Thread(
        target=lambda: [_ for _ in iter(tunnel_proc.stderr.readline, b"")],
        daemon=True,
    ).start()

    def shutdown(sig, frame):
        print("\nShutting down...")
        for p in processes:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("All services running. Press Ctrl+C to stop.")
    tunnel_proc.wait()


if __name__ == "__main__":
    main()

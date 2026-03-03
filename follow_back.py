#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Iterable, Iterator, List, Optional

import requests

API_BASE = "https://api.github.com"


def require_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token or not token.strip():
        raise SystemExit(
            "Missing GITHUB_TOKEN env var.\n"
            "Windows PowerShell:\n"
            '  $env:GITHUB_TOKEN="YOUR_TOKEN"\n'
            "macOS/Linux:\n"
            '  export GITHUB_TOKEN="YOUR_TOKEN"\n'
        )
    return token.strip()


def make_session(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "follow-back-script",
        }
    )
    return s


def parse_next_link(link_header: Optional[str]) -> Optional[str]:
    """
    Parse GitHub-style Link header and return URL for rel="next" if present.
    """
    if not link_header:
        return None
    parts = [p.strip() for p in link_header.split(",")]
    for p in parts:
        if 'rel="next"' in p:
            start = p.find("<") + 1
            end = p.find(">")
            if start > 0 and end > start:
                return p[start:end]
    return None


def iter_followers(session: requests.Session, per_page: int = 100) -> Iterator[str]:
    """
    Yield follower usernames (logins). Uses GET /user/followers with pagination.
    """
    url = f"{API_BASE}/user/followers?per_page={per_page}"
    while url:
        resp = session.get(url)
        resp.raise_for_status()
        data = resp.json()
        for item in data:
            login = item.get("login")
            if login:
                yield login
        url = parse_next_link(resp.headers.get("Link"))


def check_following(session: requests.Session, username: str) -> bool:
    url = f"{API_BASE}/user/following/{username}"
    resp = session.get(url)
    if resp.status_code == 204:
        return True
    if resp.status_code == 404:
        return False
    resp.raise_for_status()
    return False


def follow_user(session: requests.Session, username: str) -> None:
    url = f"{API_BASE}/user/following/{username}"
    resp = session.put(url)

    if resp.status_code == 204:
        print(f"✅ Followed: {username}")
        return
    if resp.status_code == 304:
        print(f"↪️  Already following: {username}")
        return

    try:
        detail = resp.json()
    except Exception:
        detail = resp.text.strip()

    raise RuntimeError(f"Failed to follow '{username}' (HTTP {resp.status_code}). Response: {detail}")


def main(argv: Iterable[str]) -> int:
    parser = argparse.ArgumentParser(description="Follow back everyone who follows you on GitHub.")
    parser.add_argument("--only-missing", action="store_true", help="Only follow users you are not already following.")
    parser.add_argument("--check", action="store_true", help="Verify follow state before/after (extra API calls).")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to sleep between follow requests.")
    parser.add_argument("--limit", type=int, default=0, help="Max number of followers to process (0 = no limit).")
    args = parser.parse_args(list(argv))

    token = require_token()
    session = make_session(token)

    processed = 0
    followed = 0
    skipped = 0

    try:
        for login in iter_followers(session):
            if args.limit and processed >= args.limit:
                break

            processed += 1

            if args.only_missing:
                already = check_following(session, login)
                if already:
                    skipped += 1
                    if args.check:
                        print(f"↪️  Skip (already following): {login}")
                    continue

            follow_user(session, login)
            followed += 1

            if args.check:
                ok = check_following(session, login)
                print(f"   🔎 verify: {'following' if ok else 'NOT following'}")

            if args.sleep:
                time.sleep(args.sleep)

    except requests.HTTPError as e:
        print(f"❌ HTTP error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    print(f"\nDone. processed={processed}, followed={followed}, skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

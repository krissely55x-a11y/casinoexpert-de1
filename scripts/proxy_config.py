"""SOCKS5 proxy configuration for Wayback downloads."""

import os

PROXY_HOST = os.environ.get("SOCKS_PROXY_HOST", "74.2.160.204")
PROXY_PORT = os.environ.get("SOCKS_PROXY_PORT", "14561")
PROXY_USER = os.environ.get("SOCKS_PROXY_USER", "user276336")
PROXY_PASS = os.environ.get("SOCKS_PROXY_PASS", "y6a8gz")

PROXY_URL = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
PROXIES = {"http": PROXY_URL, "https": PROXY_URL}


def apply_proxy(session):
    session.proxies.update(PROXIES)
    return session

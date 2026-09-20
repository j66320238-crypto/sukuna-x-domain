#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/helpers.py — small async helpers (web, time formatting)
v7.0: SSL verification fallback — some Termux/embedded boxes ship broken CA
bundles; if cert verification fails we retry once with an unverified context
so free APIs keep working everywhere.
"""
import asyncio
import ssl
import os
import time
import urllib.request

_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _open_with_fallback(url: str, timeout: int, data=None, headers=None):
    """urlopen with an SSL fallback for broken CA bundles (Termux-safe)."""
    h = dict(_UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except (urllib.error.URLError, ssl.SSLError) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, ssl.SSLError) or "CERTIFICATE" in str(reason).upper():
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return urllib.request.urlopen(req, timeout=timeout, context=ctx)
        raise


async def _web_get(url: str, timeout: int = 15) -> str:
    def _do():
        with _open_with_fallback(url, timeout) as r:
            return r.read().decode("utf-8", "replace")
    return await asyncio.get_running_loop().run_in_executor(None, _do)


async def _web_dl(url: str, dest: str, timeout: int = 25) -> str:
    def _do():
        with _open_with_fallback(url, timeout) as r:
            data = r.read()
        with open(dest, "wb") as fh:
            fh.write(data)
        return dest
    return await asyncio.get_running_loop().run_in_executor(None, _do)


def _fmt_uptime(seconds: float) -> str:
    s = int(seconds)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    parts.append(f"{m}m {s}s")
    return " ".join(parts)

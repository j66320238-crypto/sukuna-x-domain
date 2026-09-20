#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/helpers.py — small async helpers (web, time formatting)
"""
import asyncio
import os
import time
import urllib.request


async def _web_get(url: str, timeout: int = 15) -> str:
    def _do():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    return await asyncio.get_running_loop().run_in_executor(None, _do)


async def _web_dl(url: str, dest: str, timeout: int = 25) -> str:
    def _do():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
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

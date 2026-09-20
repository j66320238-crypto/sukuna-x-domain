#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/banner.py — SUKUNA-X DOMAIN v7.0 banner (Termux-safe ASCII, tagra look)
Uses only ASCII-safe chars so it never breaks into dotted squares on any terminal.
"""
import datetime
import platform
import sys

from .config import BOT_VERSION

_BANNER = r"""
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃                                                                ┃
  ┃    ____  _   _ _  __ _   _    _          __  __               ┃
  ┃   / ___|| | | | |/ /| |  / \  | |         \ \/ /               ┃
  ┃   \___ \| | | | ' / | | / _ \ | |  _____   \  /                ┃
  ┃    ___) | |_| | . \| |/ ___ \| | |_____|  /  \                ┃
  ┃   |____/ \___/|_|\_\_/_/   \_\_\/       /_/\_\               ┃
  ┃                                                                ┃
  ┃    ____   ___  __  __    _    ___ _   _                       ┃
  ┃   |  _ \ / _ \|  \/  |  / \  |_ _| \ | |                      ┃
  ┃   | | | | | | | |\/| | / _ \  | ||  \| |                      ┃
  ┃   | |_| | |_| | |  | |/ ___ \ | || |\  |                      ┃
  ┃   |____/ \___/|_|  |_/_/   \_\___|_| \_|                      ┃
  ┃                                                                ┃
  ┃   ⚡  v{ver} • PHANTOM EDITION • {plugins} plugins loading...   ┃
  ┃   ────────────────────────────────────────────────────        ┃
  ┃   🕒 Booted : {ts}
  ┃   🐍 Python : {py}   📡 Telethon : {tl}   Prefix : .
  ┃   🛡️  Shield : {shield}
  ┃                                                                ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""

# ANSI colors — only when attached to a real terminal (never breaks logs/pipes)
class C:
    R = "\033[91m"   # red (sukuna)
    G = "\033[92m"   # green
    Y = "\033[93m"   # yellow
    B = "\033[94m"   # blue
    M = "\033[95m"   # magenta
    C = "\033[96m"   # cyan
    W = "\033[97m"   # white bold
    D = "\033[90m"   # dim
    X = "\033[0m"    # reset


def _colorize(text: str) -> str:
    """Light color pass over the banner (only on real TTYs)."""
    if not sys.stdout.isatty():
        return text
    out = []
    for i, line in enumerate(text.splitlines(True)):
        if "⚡" in line or "SUKUNA" in line.upper():
            out.append(C.R + line.rstrip("\n") + C.X + "\n" if line.endswith("\n") else C.R + line + C.X)
        elif line.strip().startswith("┏") or line.strip().startswith("┗"):
            out.append(C.M + line.rstrip("\n") + C.X + "\n" if line.endswith("\n") else C.M + line + C.X)
        elif line.strip().startswith("┃"):
            out.append(C.C + line.rstrip("\n") + C.X + "\n" if line.endswith("\n") else C.C + line + C.X)
        else:
            out.append(line)
    return "".join(out)


def print_banner() -> None:
    from .safety import safety_line
    try:
        from telethon import __version__ as telethon_version
    except ImportError:
        telethon_version = "?"
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    shield = safety_line()
    print(_colorize(_BANNER.format(
        ver=BOT_VERSION, ts=ts, shield=shield,
        py=platform.python_version(),
        tl=telethon_version,
        plugins="27",
    )))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/banner.py — SUKUNA-X DOMAIN banner (fixed, Termux-safe, tagra)
Uses only ASCII safe chars: _ / \\ | - etc, so it never breaks into dotted squares.
"""
import datetime
import platform

from .config import BOT_VERSION

# ── SAFE ASCII ART (no █, ▀, ▄ — only _ / \ | which render everywhere) ──
# SUKUNA-X in slant-ish style, DOMAIN below — clean, bold, tagra
_BANNER = r"""
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃                                                              ┃
  ┃    ____  _   _ _  __ _   _    _          __  __              ┃
  ┃   / ___|| | | | |/ /| |  / \  | |         \ \/ /             ┃
  ┃   \___ \| | | | ' / | | / _ \ | |  _____   \  /              ┃
  ┃    ___) | |_| | . \| |/ ___ \| | |_____|  /  \               ┃
  ┃   |____/ \___/|_|\_\_|_/_/   \_\____/    /_/\_\              ┃
  ┃                                                              ┃
  ┃    ____   ___  __  __    _    ___ _   _                      ┃
  ┃   |  _ \ / _ \|  \/  |  / \  |_ _| \ | |                     ┃
  ┃   | | | | | | | |\/| | / _ \  | ||  \| |                     ┃
  ┃   | |_| | |_| | |  | |/ ___ \ | || |\  |                     ┃
  ┃   |____/ \___/|_|  |_/_/   \_\___|_| \_|                     ┃
  ┃                                                              ┃
  ┃   ⚡ SUKUNA-X DOMAIN • v{ver} • Farmer Edition ⚡              ┃
  ┃   ──────────────────────────────────────────────             ┃
  ┃   Booted : {ts}                                              ┃
  ┃   Python : {py}  •  Telethon {tl}  •  Prefix: .               ┃
  ┃   Shield : {shield}                                          ┃
  ┃                                                              ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""


def print_banner() -> None:
    from .safety import safety_line
    try:
        from telethon import __version__ as telethon_version
    except ImportError:
        telethon_version = "?"
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    shield = safety_line()
    print(_BANNER.format(
        ver=BOT_VERSION, ts=ts, shield=shield,
        py=platform.python_version(),
        tl=telethon_version,
    ))

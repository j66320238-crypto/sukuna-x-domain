#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/decorators.py — flood-safe wrapper (v7.2 upgraded)

Improvements over the old version:
  • retry cap (5) — pehle infinite loop tha, ab kabhi hang nahi hoga
  • big-flood guard — 120s+ ka FloodWait = instant paranoid mode (ID safe)
  • 900s+ flood pe graceful bail (bot ko hamesha ke liye block nahi)
  • CancelledError hamesha pass-through (.stop support clean)
"""
import asyncio
import logging
from functools import wraps

log = logging.getLogger("userbot")

try:
    from telethon.errors import FloodWaitError
except ImportError:
    FloodWaitError = Exception

FLOOD_MAX_RETRIES = 5      # attempts before graceful give-up
FLOOD_BAIL_SECONDS = 900   # 15min+ wait = bail (kuch gadbad hai, ruk jao)


def flood_safe(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from .safety import note_flood
        try:
            from .safety import big_flood_guard
        except ImportError:          # older core? guard optional hai
            big_flood_guard = None
        retries = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except FloodWaitError as e:
                secs = int(getattr(e, "seconds", 0) or 0)
                note_flood(secs)
                retries += 1
                # 🚨 bada flood → turant paranoid brake (raksha autopilot)
                if big_flood_guard is not None and secs >= 120:
                    big_flood_guard(secs)
                # bahut bada wait ya bahut zyada retries → graceful exit
                if secs > FLOOD_BAIL_SECONDS or retries > FLOOD_MAX_RETRIES:
                    log.warning(
                        "🛡 flood_safe[%s]: bailing after %d flood(s), "
                        "last wait %ds — ID safe rakhne ke liye skip.",
                        func.__name__, retries, secs)
                    return None
                log.warning(
                    "FloodWait in %s — sleeping %ds (retry %d/%d)…",
                    func.__name__, secs, retries, FLOOD_MAX_RETRIES)
                await asyncio.sleep(secs + 1)
            except asyncio.CancelledError:
                log.info("Task %s cancelled via .stop", func.__name__)
                raise
            except Exception as e:
                log.error("[flood_safe] %s failed: %s", func.__name__, e,
                          exc_info=True)
                return None
    return wrapper

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/decorators.py — flood-safe wrapper
"""
import asyncio
import logging
from functools import wraps

log = logging.getLogger("userbot")

try:
    from telethon.errors import FloodWaitError
except ImportError:
    FloodWaitError = Exception


def flood_safe(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from .safety import note_flood
        while True:
            try:
                return await func(*args, **kwargs)
            except FloodWaitError as e:
                note_flood(getattr(e, "seconds", 0))
                log.warning("FloodWait in %s — sleeping %ds…", func.__name__, getattr(e, "seconds", 0))
                await asyncio.sleep(getattr(e, "seconds", 0) + 1)
            except asyncio.CancelledError:
                log.info("Task %s cancelled via .stop", func.__name__)
                raise
            except Exception as e:
                log.error("[flood_safe] %s failed: %s", func.__name__, e, exc_info=True)
                return None
    return wrapper

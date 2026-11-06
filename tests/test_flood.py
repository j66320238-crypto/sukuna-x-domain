#!/usr/bin/env python3
"""v7.2 floodwait protection tests — retry cap, storm, big-flood guard.

NOTE: retry-cap test me 6×30s FloodWait sleeps hote hai (~2.5 min).
Speed ke liye FLOOD secs = 1s wala test rakha gaya hai — logic same rehta hai.

Usage:  python3 tests/test_flood.py   (ya  pytest tests/test_flood.py)
"""
import asyncio
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import telethon.errors as te  # noqa: E402
from core.decorators import flood_safe  # noqa: E402
from core import safety  # noqa: E402


def _reset_storm():
    safety.STORM_UNTIL = 0.0
    safety._STORM_PREV_PROFILE = None
    safety.SAFETY["profile"] = "normal"
    safety.SAFETY["mult"] = 1.0
    safety._FLOOD_TIMES.clear()


async def test_retry_cap():
    """Hamesha-fail flood function → 5 retries ke baad graceful None."""
    _reset_storm()
    calls = {"n": 0}

    @flood_safe
    async def always_flood():
        calls["n"] += 1
        raise te.FloodWaitError(request=None, capture=1)

    r = await asyncio.wait_for(always_flood(), timeout=60)
    assert calls["n"] == 6, calls["n"]      # 1 + 5 retries
    assert r is None                        # graceful, no crash
    print(f"  ✓ retry-cap: {calls['n']} attempts → graceful None (infinite loop khatam)")


async def test_normal_pass_through():
    @flood_safe
    async def fine():
        return "ok"
    assert await fine() == "ok"
    print("  ✓ normal calls pass through untouched")


async def test_big_flood_guard():
    _reset_storm()
    safety.big_flood_guard(300)
    assert safety.SAFETY["profile"] == "paranoid"
    assert safety.storm_active()
    left = safety.storm_left()
    assert 590 <= left <= 610, left          # 300×2 = 600s
    assert safety.SAFETY["mult"] >= 2.5
    # guard active storm me no-op karta hai (double-brake nahi)
    safety.big_flood_guard(600)
    assert safety.storm_left() <= left + 5
    print(f"  ✓ big-flood guard: instant paranoid ×{safety.SAFETY['mult']} slow, "
          f"{safety.storm_left()}s cooldown, no-op while active")
    _reset_storm()


def main():
    print("── v7.2 floodwait protection ──")
    asyncio.run(test_normal_pass_through())
    asyncio.run(test_retry_cap())
    asyncio.run(test_big_flood_guard())
    _reset_storm()
    print("\nALL FLOOD TESTS PASSED ✅")


if __name__ == "__main__":
    main()

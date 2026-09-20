#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/safety.py — 5-layer anti-ban / anti-rate-limit engine
Layer 1 — minimum gap
Layer 2 — sliding window (global per minute)
Layer 3 — per-chat limiter
Layer 4 — human breather
Layer 5 — adaptive backoff + warm-up
"""
import asyncio
import json
import os
import random
import time
from collections import deque

from .config import (
    SAFE_MODE_DEFAULT, SAFE_SEND_GAP, SAFE_EDIT_GAP, SAFE_LOOP_DELAY,
    SAFE_ANIM_DELAY, SAFE_BURST_CAP, SAFETY_PROFILES, WARMUP_HOURS,
    HARD_HOUR_CAP, HARD_DAY_CAP, STORM_FLOODS, STORM_WINDOW, STORM_COOLDOWN,
)
from .store import DATA_DIR, SAFETY_FILE, load_store
from .state import START_TIME

MIN_SEND_GAP = SAFE_SEND_GAP
MIN_EDIT_GAP = SAFE_EDIT_GAP
MIN_LOOP_DELAY = SAFE_LOOP_DELAY
MIN_ANIM_DELAY = SAFE_ANIM_DELAY
FLOOD_MULT_MAX = 8.0

SAFETY = {
    "safe_mode": SAFE_MODE_DEFAULT,
    "sends": 0,
    "edits": 0,
    "floods": 0,
    "last_flood": 0.0,
    "mult": 1.0,
    "last_send": 0.0,
    "last_edit": 0.0,
    "first_seen": 0.0,
    "profile": "normal",
    "breathers": 0,
    "blocked_waits": 0.0,
}

_SEND_WINDOW: deque = deque(maxlen=400)
_CHAT_WINDOW: dict = {}
_CHAT_LAST: dict = {}
_SENDS_SINCE_BREATHER = 0

# ── v7.1 BAN-PROOF SHIELD state ─────────────────────────────────────────
_FLOOD_TIMES: deque = deque(maxlen=60)   # timestamps of recent FloodWaits
_HOUR_WINDOW: deque = deque(maxlen=HARD_HOUR_CAP + 200)
_DAY_WINDOW: deque = deque(maxlen=HARD_DAY_CAP + 500)
STORM_UNTIL: float = 0.0                 # monotonic ts until paranoid cooldown
_STORM_PREV_PROFILE = None               # profile to restore after cooldown
RAKSHA = True                            # master ban-protection autopilot
import logging as _lg
_log = _lg.getLogger("userbot")


def _safety_load() -> None:
    global RAKSHA
    try:
        with open(SAFETY_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data.get("safe_mode"), bool):
            SAFETY["safe_mode"] = data["safe_mode"]
        if isinstance(data.get("first_seen"), (int, float)):
            SAFETY["first_seen"] = float(data["first_seen"])
        if data.get("profile") in SAFETY_PROFILES:
            SAFETY["profile"] = data["profile"]
        if isinstance(data.get("raksha"), bool):
            RAKSHA = data["raksha"]
    except Exception:
        pass


def _safety_save() -> None:
    try:
        with open(SAFETY_FILE, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "safe_mode": SAFETY["safe_mode"],
                    "first_seen": SAFETY["first_seen"],
                    "profile": SAFETY.get("profile", "normal"),
                    "raksha": RAKSHA,
                },
                fh,
            )
    except OSError:
        pass


# ── v7.1 BAN-PROOF SHIELD API ───────────────────────────────────────────
def raksha_on() -> bool:
    return bool(RAKSHA)


def raksha_set(on: bool) -> None:
    global RAKSHA
    RAKSHA = bool(on)
    _safety_save()


def _storm_check(now: float) -> None:
    """Auto-paranoid cooldown when FloodWaits cluster (ban-storm autopilot)."""
    global STORM_UNTIL, _STORM_PREV_PROFILE
    recent = [t for t in _FLOOD_TIMES if now - t < STORM_WINDOW]
    if RAKSHA and len(recent) >= STORM_FLOODS and now > STORM_UNTIL:
        STORM_UNTIL = now + STORM_COOLDOWN
        _STORM_PREV_PROFILE = SAFETY.get("profile", "normal")
        SAFETY["profile"] = "paranoid"
        SAFETY["mult"] = max(SAFETY["mult"], 3.0)
        _log.warning("🚨 FLOOD STORM detected (%d FloodWaits) → paranoid "
                     "cooldown %ds. ID protection autopilot engaged.",
                     len(recent), STORM_COOLDOWN)


def storm_active() -> bool:
    """True while ban-storm cooldown is running (auto restores after)."""
    global STORM_UNTIL, _STORM_PREV_PROFILE
    now = time.time()
    if STORM_UNTIL and now >= STORM_UNTIL:
        if _STORM_PREV_PROFILE:
            SAFETY["profile"] = _STORM_PREV_PROFILE
            _STORM_PREV_PROFILE = None
            _log.info("🛡️ Storm cooldown over — profile restored to %s",
                      SAFETY["profile"])
        STORM_UNTIL = 0.0
        return False
    return now < STORM_UNTIL


def storm_left() -> int:
    return max(0, int(STORM_UNTIL - time.time()))


def hour_sends() -> int:
    cut = time.monotonic() - 3600
    while _HOUR_WINDOW and _HOUR_WINDOW[0] < cut:
        _HOUR_WINDOW.popleft()
    return len(_HOUR_WINDOW)


def day_sends() -> int:
    cut = time.monotonic() - 86400
    while _DAY_WINDOW and _DAY_WINDOW[0] < cut:
        _DAY_WINDOW.popleft()
    return len(_DAY_WINDOW)


_safety_load()
if not SAFETY["first_seen"]:
    SAFETY["first_seen"] = time.time()
    _safety_save()


def _decay_mult() -> None:
    if SAFETY["mult"] > 1.0 and (time.time() - SAFETY["last_flood"]) > 180:
        SAFETY["mult"] = max(1.0, SAFETY["mult"] * 0.85)


def _profile() -> dict:
    return SAFETY_PROFILES.get(SAFETY.get("profile", "normal"), SAFETY_PROFILES["normal"])


def anim_floor() -> float:
    return _profile()["anim_delay"]


def note_flood(seconds: int = 0) -> None:
    SAFETY["floods"] += 1
    now = time.time()
    SAFETY["last_flood"] = now
    SAFETY["mult"] = min(FLOOD_MULT_MAX, max(1.5, SAFETY["mult"] * 1.5))
    _FLOOD_TIMES.append(now)
    _storm_check(now)


def warmup_active() -> bool:
    first = SAFETY.get("first_seen") or 0
    return bool(first) and (time.time() - first) < WARMUP_HOURS * 3600


def warmup_left() -> str:
    if not warmup_active():
        return "done"
    left = WARMUP_HOURS * 3600 - (time.time() - SAFETY["first_seen"])
    h, m = divmod(int(left // 60), 60)
    return f"{h}h {m}m left"


def _effective(kind: str) -> dict:
    if not SAFETY["safe_mode"]:
        return {"gap": 0.0, "edit_gap": 0.0, "per_min": 0, "chat_gap": 0.0, "chat_per_min": 0}
    prof = _profile()
    warm = 1.5 if warmup_active() else 1.0
    if kind == "edit":
        return {"gap": prof["edit_gap"] * warm, "edit_gap": prof["edit_gap"] * warm,
                "per_min": 0, "chat_gap": 0.0, "chat_per_min": 0}
    return {
        "gap": prof["gap"] * warm,
        "edit_gap": prof["edit_gap"] * warm,
        "per_min": int(prof["per_min"] / (1.4 if warmup_active() else 1.0)),
        "chat_gap": prof["chat_gap"] * warm,
        "chat_per_min": int(prof["chat_per_min"] / (1.4 if warmup_active() else 1.0)),
    }


async def throttle(kind: str = "send", chat_id=None) -> None:
    global _SENDS_SINCE_BREATHER
    _decay_mult()
    if not SAFETY["safe_mode"]:
        SAFETY["sends" if kind != "edit" else "edits"] += 1
        return

    lim = _effective(kind)
    now = time.monotonic()
    waited = 0.0
    storm_mult = 2.0 if storm_active() else 1.0   # extra caution in storm

    # 🚨 v7.1 hard hourly/daily caps — brake hard before Telegram flags you
    if RAKSHA and kind != "edit":
        cut_h = now - 3600
        while _HOUR_WINDOW and _HOUR_WINDOW[0] < cut_h:
            _HOUR_WINDOW.popleft()
        cut_d = now - 86400
        while _DAY_WINDOW and _DAY_WINDOW[0] < cut_d:
            _DAY_WINDOW.popleft()
        if len(_HOUR_WINDOW) >= HARD_HOUR_CAP or len(_DAY_WINDOW) >= HARD_DAY_CAP:
            pause = random.uniform(45.0, 90.0)
            SAFETY["breathers"] += 1
            SAFETY["blocked_waits"] += pause
            _log.warning("🛡️ Hard cap reached (%d/h or %d/day) — braking %.0fs",
                         len(_HOUR_WINDOW), len(_DAY_WINDOW), pause)
            await asyncio.sleep(pause)
            waited += pause

    if kind == "edit":
        need = lim["edit_gap"] * SAFETY["mult"] - (now - SAFETY["last_edit"])
        if need > 0:
            await asyncio.sleep(need)
            waited += need
        SAFETY["last_edit"] = time.monotonic()
        SAFETY["edits"] += 1
        SAFETY["blocked_waits"] += waited
        return

    if chat_id is not None:
        last = _CHAT_LAST.get(chat_id, 0.0)
        need = lim["chat_gap"] - (now - last)
        if need > 0:
            await asyncio.sleep(need)
            waited += need
        w = _CHAT_WINDOW.setdefault(chat_id, deque(maxlen=200))
        cut = time.monotonic() - 60
        while w and w[0] < cut:
            w.popleft()
        if lim["chat_per_min"] and len(w) >= lim["chat_per_min"]:
            need = 60 - (time.monotonic() - w[0]) + 0.05
            if need > 0:
                await asyncio.sleep(need)
                waited += need
            cut = time.monotonic() - 60
            while w and w[0] < cut:
                w.popleft()
        w.append(time.monotonic())
        _CHAT_LAST[chat_id] = time.monotonic()

    need = lim["gap"] * storm_mult - (time.monotonic() - SAFETY["last_send"])
    if need > 0:
        await asyncio.sleep(need)
        waited += need

    cut = time.monotonic() - 60
    while _SEND_WINDOW and _SEND_WINDOW[0] < cut:
        _SEND_WINDOW.popleft()
    per_min = int(lim["per_min"] / storm_mult) if lim["per_min"] else 0
    if per_min and len(_SEND_WINDOW) >= per_min:
        need = 60 - (time.monotonic() - _SEND_WINDOW[0]) + 0.05
        if need > 0:
            await asyncio.sleep(need)
            waited += need
        cut = time.monotonic() - 60
        while _SEND_WINDOW and _SEND_WINDOW[0] < cut:
            _SEND_WINDOW.popleft()
    _SEND_WINDOW.append(time.monotonic())
    _HOUR_WINDOW.append(time.monotonic())
    _DAY_WINDOW.append(time.monotonic())

    _SENDS_SINCE_BREATHER += 1
    breath_every = _profile()["breather_every"]
    if breath_every and _SENDS_SINCE_BREATHER >= breath_every:
        _SENDS_SINCE_BREATHER = 0
        SAFETY["breathers"] += 1
        pause = random.uniform(3.0, 7.0)
        await asyncio.sleep(pause)
        waited += pause

    SAFETY["last_send"] = time.monotonic()
    SAFETY["sends"] += 1
    SAFETY["blocked_waits"] += waited


async def throttle_chat(chat_id) -> None:
    await throttle("send", chat_id=chat_id)


def rate_used() -> dict:
    cut = time.monotonic() - 60
    while _SEND_WINDOW and _SEND_WINDOW[0] < cut:
        _SEND_WINDOW.popleft()
    lim = _effective("send")
    per_min = lim["per_min"] or 10 ** 9
    return {
        "used": len(_SEND_WINDOW),
        "limit": lim["per_min"],
        "pct": round(100 * len(_SEND_WINDOW) / per_min, 1) if lim["per_min"] else 0.0,
    }


async def safe_sleep(sec: float, floor: float = None) -> None:
    _decay_mult()
    if floor is None:
        floor = _profile()["loop_delay"] if SAFETY["safe_mode"] else 0.0
    sec = max(float(sec or 0.0), floor) * SAFETY["mult"]
    if SAFETY["safe_mode"] and sec > 0:
        sec = sec * random.uniform(0.85, 1.25)
    if sec > 0:
        await asyncio.sleep(sec)


def safe_cap(count: int, hard: int = SAFE_BURST_CAP) -> int:
    try:
        count = int(count)
    except (TypeError, ValueError):
        return count
    if count <= 0:
        return count
    if SAFETY["safe_mode"]:
        if warmup_active():
            hard = max(20, int(hard * 0.6))
        if count > hard:
            return hard
    return count


def safe_mode_on() -> bool:
    return bool(SAFETY["safe_mode"])


def safety_line() -> str:
    if not safe_mode_on():
        return "⚠️ OFF (no protection)"
    bits = ["🛡️ ON"]
    if storm_active():
        bits.append(f"🚨 storm-cooldown {storm_left() // 60}m")
    if warmup_active():
        bits.append(f"warm-up {warmup_left()}")
    if SAFETY["mult"] > 1.0:
        bits.append(f"slow ×{SAFETY['mult']:.2f}")
    return " · ".join(bits)

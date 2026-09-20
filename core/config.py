#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/config.py — SUKUNA-X DOMAIN constants & user-editable config
"""
# ★★★  CONFIG — PUT YOUR API ID / HASH HERE  ★★★
# https://my.telegram.org → API development tools → Create app
API_ID = 0                      # ← your API ID here (number, no quotes)
API_HASH = ""                   # ← your API HASH here (inside quotes)
SESSION_STRING = ""             # ← optional, usually leave empty
PHONE = ""                      # ← optional, e.g. "+919876543210"
SESSION_NAME = "sukuna"

# 🛡️ Safe mode defaults
SAFE_MODE_DEFAULT = True
SAFE_SEND_GAP = 0.40
SAFE_EDIT_GAP = 0.35
SAFE_LOOP_DELAY = 0.45
SAFE_ANIM_DELAY = 0.30
SAFE_BURST_CAP = 100
SAFE_PER_MINUTE = 18
SAFE_CHAT_PER_MINUTE = 15
SAFE_CHAT_GAP = 1.0
SAFE_BREATHER_EVERY = 15
WARMUP_HOURS = 48

# 🚨 v7.1 BAN-PROOF SHIELD — hard caps & flood-storm autopilot
HARD_HOUR_CAP = 150        # max sends per rolling hour (human-like ceiling)
HARD_DAY_CAP = 900         # max sends per rolling 24h
STORM_FLOODS = 3           # FloodWaits in window = storm
STORM_WINDOW = 600         # 10 min window for storm detection
STORM_COOLDOWN = 1800      # 30 min paranoid cooldown after a storm

BOT_VERSION = "7.0.0"

SAFETY_PROFILES = {
    "paranoid": dict(gap=0.80, edit_gap=0.60, per_min=12, chat_per_min=8,
                     chat_gap=1.6, breather_every=10, loop_delay=0.70, anim_delay=0.45),
    "normal":   dict(gap=SAFE_SEND_GAP, edit_gap=SAFE_EDIT_GAP, per_min=SAFE_PER_MINUTE,
                     chat_per_min=SAFE_CHAT_PER_MINUTE, chat_gap=SAFE_CHAT_GAP,
                     breather_every=SAFE_BREATHER_EVERY, loop_delay=SAFE_LOOP_DELAY,
                     anim_delay=SAFE_ANIM_DELAY),
    "fast":     dict(gap=0.25, edit_gap=0.20, per_min=25, chat_per_min=20,
                     chat_gap=0.6, breather_every=25, loop_delay=0.30, anim_delay=0.22),
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/state.py — global runtime state (shared across engine & plugins)
"""
import time

START_TIME = time.time()

# Every background task (spam/raid/animation/tag/farmer) is tracked here
# so `.stop` / `.tasks` can see / kill it.
stop_processes: dict = {}

# {module_name: {"description": str, "commands": [(cmd, help), ...]}}
command_registry: dict = {}

# {plugin_name: load_time_ms} — filled by the loader, shown by .plist / .stats
PLUGIN_LOAD_TIMES: dict = {}

# owner user id (cached after login) — used by interactive menus
OWNER_ID: int = 0

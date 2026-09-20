#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/store.py — tiny JSON stores (sukuna_data/*.json)
"""
import json
import os

# Folder for small JSON stores used by sections (filters/notes/welcome/…)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
# Fallback: if run from core/__init__.py location, DATA_DIR is ../data, else ./sukuna_data
# Keep both for backward compat
_alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sukuna_data")
if not os.path.isdir(DATA_DIR):
    # if old layout exists, use it
    if os.path.isdir(_alt):
        DATA_DIR = _alt
    else:
        # default to sukuna_data next to project root
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sukuna_data")
        # if that doesn't exist, try ../data
        if not os.path.exists(DATA_DIR):
            DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Safety file lives next to store (project root)
SAFETY_FILE = os.path.join(os.path.dirname(DATA_DIR), "safety_data.json")
# Also try old location: core/safety_data.json
_old_safety = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safety_data.json")
if not os.path.exists(SAFETY_FILE) and os.path.exists(_old_safety):
    SAFETY_FILE = _old_safety

try:
    os.makedirs(DATA_DIR, exist_ok=True)
except OSError:
    pass


def load_store(name: str, default=None):
    """Read DATA_DIR/<name>.json"""
    try:
        with open(os.path.join(DATA_DIR, f"{name}.json"), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {} if default is None else default


def save_store(name: str, data) -> bool:
    """Write DATA_DIR/<name>.json (atomic-ish, never throws)."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = os.path.join(DATA_DIR, f"{name}.json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, os.path.join(DATA_DIR, f"{name}.json"))
        return True
    except Exception:
        return False

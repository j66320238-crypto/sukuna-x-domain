#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/__init__.py — SUKUNA-X DOMAIN engine (well-structured edition)

This package is the heart of the bot. Every plugin does `from core import *`
and gets EVERYTHING: safety engine, stores, accounts, helpers, Telethon, etc.

Structure:
  config.py    → constants & BOT_VERSION
  state.py     → global runtime state (START_TIME, stop_processes, command_registry)
  store.py     → DATA_DIR + load_store/save_store
  safety.py    → 5-layer anti-ban engine
  accounts.py  → multi-account + interactive setup
  helpers.py   → _web_get, _web_dl, _fmt_uptime
  decorators.py→ flood_safe
  banner.py    → print_banner

Adding a new core module? Import it here and it auto-exports to plugins.
"""
# ── stdlib (so plugins can use them without importing) ──────────────────
import ast
import asyncio
import base64
import datetime
import getpass
import html
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import math
import operator
import os
import platform
import random
import re
import shutil
import signal
import sys
import textwrap
import time
import urllib.parse
import urllib.request
from collections import deque
from functools import wraps
from urllib.parse import quote_plus  # noqa: F401 (used by .google)

# ── Telethon (single import point) ───────────────────────────────────────
try:
    from telethon import TelegramClient, events
    from telethon import __version__ as telethon_version
    from telethon.errors import (
        FloodWaitError,
        UserAdminInvalidError,
        ChatAdminRequiredError,
        SessionPasswordNeededError,
        MessageNotModifiedError,
        YouBlockedUserError,
        ChatWriteForbiddenError,
    )
    from telethon.sessions import StringSession
    from telethon.tl.types import InputMediaDice
    from telethon.tl.functions.account import UpdateProfileRequest
    from telethon.tl.functions.channels import (
        EditBannedRequest,
        EditAdminRequest,
        InviteToChannelRequest,
        JoinChannelRequest,
        LeaveChannelRequest,
    )
    from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
    from telethon.tl.functions.messages import (
        EditChatDefaultBannedRightsRequest,
        EditChatAboutRequest,
        UpdatePinnedMessageRequest,
        GetCommonChatsRequest,
        ExportChatInviteRequest,
        ImportChatInviteRequest,
    )
    from telethon.tl.functions.photos import UploadProfilePhotoRequest
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.tl.types import (
        ChatBannedRights,
        ChatAdminRights,
        ChannelParticipantAdmin,
        ChannelParticipantCreator,
        ChannelParticipantsAdmins,
        ChannelParticipantsBots,
        MessageMediaPhoto,
        MessageMediaDocument,
        InputDocument,
        DocumentAttributeSticker,
        DocumentAttributeFilename,
        DocumentAttributeAudio,
        DocumentAttributeVideo,
        DocumentAttributeAnimated,
    )
except ImportError:
    print(
        "\n⛔  Telethon is NOT installed — that's why nothing runs.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  Run this once, then start the bot again:\n\n"
        "      pip install telethon tgcrypto pillow\n"
        "      python userbot.py\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    sys.exit(1)

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# ── core submodules ──────────────────────────────────────────────────────
from .config import (
    API_ID, API_HASH, SESSION_STRING, PHONE, SESSION_NAME,
    SAFE_MODE_DEFAULT, SAFE_SEND_GAP, SAFE_EDIT_GAP, SAFE_LOOP_DELAY,
    SAFE_ANIM_DELAY, SAFE_BURST_CAP, SAFE_PER_MINUTE, SAFE_CHAT_PER_MINUTE,
    SAFE_CHAT_GAP, SAFE_BREATHER_EVERY, WARMUP_HOURS, BOT_VERSION,
    SAFETY_PROFILES,
)
from .state import START_TIME, stop_processes, command_registry
from .store import DATA_DIR, SAFETY_FILE, load_store, save_store
from .safety import (
    SAFETY, _SEND_WINDOW, _CHAT_WINDOW, _CHAT_LAST, _SENDS_SINCE_BREATHER,
    MIN_SEND_GAP, MIN_EDIT_GAP, MIN_LOOP_DELAY, MIN_ANIM_DELAY, FLOOD_MULT_MAX,
    _safety_load, _safety_save, _decay_mult, _profile, anim_floor,
    note_flood, warmup_active, warmup_left, _effective,
    throttle, throttle_chat, rate_used, safe_sleep, safe_cap,
    safe_mode_on, safety_line,
)
from .accounts import ACCOUNT, _safe_name, _acc_cfg_load, _acc_cfg_save, resolve_credentials
from .helpers import _web_get, _web_dl, _fmt_uptime
from .decorators import flood_safe
from .banner import _BANNER, print_banner

# ── logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s │ %(levelname)-7s │ %(name)-18s │ %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("userbot")
# silence telethon update spam (Got difference...)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("telethon.client.updates").setLevel(logging.WARNING)

# ── export everything (so `from core import *` works) ───────────────────
__all__ = [n for n in globals() if not n.startswith("__")]

#!/usr/bin/env python3
"""Offline command test harness — runs every major handler against a fake
Telegram client so regressions are caught without a live session.

Usage:  python3 tests/test_commands.py
"""
import asyncio
import os
import re
import sys
import importlib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from telethon import events  # noqa: E402
from telethon.tl.types import DocumentAttributeCustomEmoji  # noqa: E402

import core  # noqa: E402
from core import command_registry  # noqa: E402
from core.ui import register_builtin_commands  # noqa: E402


# ── fakes ────────────────────────────────────────────────────────────────
class FakeSession:
    dc_id = 2


class FakeMe:
    first_name, last_name, username, id = "Test", "User", "test_user", 12345


class FakeDoc:
    def __init__(self, doc_id, alt, free=True):
        self.id = doc_id
        self.attributes = [DocumentAttributeCustomEmoji(alt=alt, free=free)]


class FakeMsg:
    def __init__(self, mid):
        self.id = mid


class FakeChat:
    title = "Test Chat"
    first_name = "Test Chat"


class FakeClient:
    def __init__(self):
        self.handlers = []
        self.stop_processes = {}
        self.flood_safe = lambda f: f
        self.session = FakeSession()
        self._mid = 900

    def on(self, ev):
        def deco(fn):
            self.handlers.append((ev, fn))
            return fn
        return deco

    def add_event_handler(self, fn, ev):
        self.handlers.append((ev, fn))

    async def __call__(self, req):
        name = req.__class__.__name__
        if name == "SearchCustomEmojiRequest":
            emo = req.emoticon
            return type("EmojiList", (), {"documents": [FakeDoc(700 + ord(emo[-1]), emo, True)]})()
        if name == "DeletePhotosRequest":
            return []
        return object()

    async def get_me(self):
        return FakeMe()

    async def get_profile_photos(self, *a, **k):
        return []

    async def send_message(self, *a, **k):
        self._mid += 1
        return FakeMsg(self._mid)

    async def send_file(self, *a, **k):
        self._mid += 1
        return FakeMsg(self._mid)

    async def download_media(self, *a, **k):
        return None

    async def upload_file(self, *a, **k):
        return object()


class FakeEvent:
    _seq = 1000

    def __init__(self, text):
        FakeEvent._seq += 1
        self.id = FakeEvent._seq
        self.text = text
        self.chat_id = 5
        self.media = None
        self.fwd_from = None
        self.via_bot = None
        self.entities = None
        self.reply_to_msg_id = None
        self.is_reply = False
        self.pattern_match = None
        self.edits = []
        self.deleted = False

    async def edit(self, text, **kw):
        self.edits.append((text, kw))
        return self

    async def delete(self):
        self.deleted = True

    async def get_input_chat(self):
        return 5

    async def get_chat(self):
        return FakeChat()

    async def get_reply_message(self):
        return None


# ── load everything ──────────────────────────────────────────────────────
CLIENT = FakeClient()
register_builtin_commands(CLIENT)
for name in sorted(f[:-3] for f in os.listdir(os.path.join(BASE, "plugins"))
                   if f.endswith(".py") and not f.startswith("_")):
    mod = importlib.import_module(f"plugins.{name}")
    reg = meta = None
    for attr in sorted(dir(mod)):
        obj = getattr(mod, attr)
        if reg is None and attr.startswith("register") and callable(obj):
            reg = obj
        if meta is None and attr.startswith("COMMANDS") and isinstance(obj, dict):
            meta = obj
    reg(CLIENT)
    command_registry[name] = meta or {"description": name, "commands": []}

# ── commands to exercise (offline-safe paths) ───────────────────────────
CMDS = [
    ".help", ".h", ".help 2", ".help dp", ".help zzz_nothing", ".help clone",
    ".menu", ".cmds", ".cmds 3", ".plist", ".pstats", ".stats", ".alive",
    ".tasks", ".stop", ".ping", ".uptime", ".sysinfo", ".calc 6*7",
    ".google cats", ".time", ".random 9", ".reverse hello", ".count hi there",
    ".gc", ".speed", ".rps rock", ".rps patthar", ".scratch",
    ".dplist", ".dpstatus", ".dptime 30", ".adddp", ".getdp 1", ".setdp 1",
    ".nextdp", ".deldp all", ".undp", ".curdp",
    ".pestatus", ".pereset", ".premiumsticker on", ".premiumsticker status",
    ".petest", ".premiumsticker off", ".pemoji hello 🙂",
    ".pblist", ".pbdel nope", ".pbsave", ".pbload nope",
    ".anims", ".limits", ".antiban", ".safemode on", ".safemode normal",
    ".raksha status", ".warmup", ".mock hello", ".shrug", ".lenny",
    ".8ball will it work", ".choose a | b", ".roll", ".flip hi", ".shout yo",
    ".json", ".getid", ".stopautodp",
]


async def run(cmd: str):
    for ev, fn in CLIENT.handlers:
        if not isinstance(ev, events.NewMessage):
            continue
        pat = getattr(ev, "pattern", None)
        if not pat:
            continue
        m = pat(cmd) if callable(pat) else re.match(pat, cmd)
        if not m:
            continue
        e = FakeEvent(cmd)
        e.pattern_match = m
        await fn(e)
        return True
    return False


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ok = fail = nomatch = 0
    for cmd in CMDS:
        try:
            matched = loop.run_until_complete(run(cmd))
        except Exception as exc:
            print(f"  ✗ CRASH  {cmd!r}: {exc!r}")
            fail += 1
            continue
        if not matched:
            print(f"  ? no-handler  {cmd!r}")
            nomatch += 1
            continue
        ok += 1
    print(f"\nRESULT: {ok} passed · {fail} crashed · {nomatch} unmatched "
          f"(of {len(CMDS)})")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

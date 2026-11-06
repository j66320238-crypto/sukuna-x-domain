#!/usr/bin/env python3
"""Focused tests for the fixed features: .raid, .sg cleaning, .rclone, autodp state."""
import asyncio
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from telethon import events  # noqa: E402

import core  # noqa: E402
from plugins.raid import (  # noqa: E402
    _build_raid_message, _load_raid_text, _has_saved_raid_text,
    _save_raid_text, _delete_raid_text, RAID_DATA_FILE, register_raid,
)
from plugins.info import _clean_history_text  # noqa: E402


def test_raid_message_builder():
    # default format: "<name> <text> <mention>"
    msg = _build_raid_message("kya kar rhe ho", 123, "mintu")
    assert msg == 'mintu kya kar rhe ho <a href="tg://user?id=123">mintu</a>', msg
    print("  ✓ default format: mintu kya kar rhe ho <mention>")

    # template {name} only
    msg = _build_raid_message("kya kar rhe ho {name}", 123, "mintu")
    assert msg == 'kya kar rhe ho mintu', msg
    print("  ✓ template {name}")

    # template {tag} / {mention}
    msg = _build_raid_message("{name} oye {tag}", 123, "mintu")
    assert msg == 'mintu oye <a href="tg://user?id=123">mintu</a>', msg
    msg = _build_raid_message("hi {mention}", 123, "mintu")
    assert msg == 'hi <a href="tg://user?id=123">mintu</a>', msg
    print("  ✓ templates {tag}/{mention}")

    # html escaping safety
    msg = _build_raid_message("<b>bold</b> & more", 123, "A<b>&")
    assert "&lt;b&gt;bold&lt;/b&gt; &amp; more" in msg
    print("  ✓ HTML escaping")

    # default text fallback + persistence (restore original file after)
    orig = None
    if os.path.exists(RAID_DATA_FILE):
        with open(RAID_DATA_FILE, "r", encoding="utf-8") as fh:
            orig = fh.read()
        os.remove(RAID_DATA_FILE)
    try:
        assert _load_raid_text() == "kya kar rhe ho"
        assert not _has_saved_raid_text()
        _save_raid_text("oye {name}")
        assert _has_saved_raid_text()
        assert _load_raid_text() == "oye {name}"
        _delete_raid_text()
    finally:
        if orig is not None:
            with open(RAID_DATA_FILE, "w", encoding="utf-8") as fh:
                fh.write(orig)
        else:
            _save_raid_text("kya kar rhe ho")
    print("  ✓ raid text persistence + default fallback (file restored)")


def test_sg_cleaner():
    raw = (
        "🔎 History of [Mintu](tg://user?id=1)\n"
        "\n"
        "First Name:\n"
        "1. Mintu (2023-01-01)\n"
        "2. Mintu Kumar (2024-05-11)\n"
        "\n"
        "🤖 @SangMata_BOT\n"
        "Powered by SangMata Forward Bot\n"
        "[SangMata Bot](t.me/SangMata_BOT)\n"
        "Join @SangMataForwardBot\n"
    )
    cleaned = _clean_history_text(raw)
    low = cleaned.lower()
    assert "sangmata" not in low, cleaned
    assert "powered by" not in low
    assert "t.me/" not in cleaned
    assert "Mintu Kumar (2024-05-11)" in cleaned
    assert "History of Mintu" in cleaned  # md link → label only
    print("  ✓ branding stripped, data kept:")
    print("    ── " + cleaned.replace("\n", "\n    ── "))


class FakeUser:
    def __init__(self, uid, first, last=None, bot=False):
        self.id = uid
        self.first_name = first
        self.last_name = last
        self.bot = bot


class FakeClient:
    def __init__(self):
        self.handlers = []
        self.stop_processes = {}
        self.flood_safe = lambda f: f
        self.sent = []

    def on(self, ev):
        def deco(fn):
            self.handlers.append((ev, fn))
            return fn
        return deco

    def add_event_handler(self, fn, ev):
        self.handlers.append((ev, fn))

    async def __call__(self, req):
        return object()  # raw TL requests (UpdateProfileRequest etc.)

    async def send_message(self, chat, text, **kw):
        self.sent.append((chat, text, kw))

    async def get_entity(self, x):
        return FakeUser(123, "mintu")

    async def get_input_entity(self, x):
        return x

    async def iter_participants(self, chat, limit=200):
        for u in (FakeUser(1, "Mintu"), FakeUser(2, "Raju"),
                  FakeUser(3, "BotGuy", bot=True), FakeUser(123, "me")):
            yield u

    async def get_me(self):
        return FakeUser(123, "me")


class FakeReplyMsg:
    async def get_input_sender(self):
        return "peer"


class FakeEvent:
    _seq = 1

    def __init__(self, text, with_reply=False):
        FakeEvent._seq += 1
        self.id = FakeEvent._seq
        self.text = text
        self.chat_id = 55
        self._with_reply = with_reply
        self.edits = []

    async def edit(self, text, **kw):
        self.edits.append(text)

    async def get_input_chat(self):
        return 55

    async def get_reply_message(self):
        return FakeReplyMsg() if self._with_reply else None


async def test_raid_and_rclone_handlers():
    c = FakeClient()
    register_raid(c)

    # find the .raid handler
    import re as _re
    raid_fn = None
    for ev, fn in c.handlers:
        pat = getattr(ev, "pattern", None)
        if not pat:
            continue
        try:
            m = pat(".raid 3") if callable(pat) else _re.match(pat, ".raid 3")
        except Exception:
            continue
        if m and m.group(0).startswith(".raid"):
            raid_fn = fn
    assert raid_fn, "raid handler not found"
    m = _re.match(r"^\.raid\s*(\d+)?\s*$", ".raid 3")
    e = FakeEvent(".raid 3", with_reply=True)
    e.pattern_match = m
    await raid_fn(e)
    # raid loop is background-paced (safe_sleep ≥0.45s per message)
    for _ in range(40):
        await asyncio.sleep(0.25)
        if len(c.sent) >= 3:
            break
    sent = [t for ch, t, kw in c.sent]
    assert any("kya kar rhe ho" in t and "mintu" in t for t in sent), sent
    print(f"  ✓ .raid 3 → {len(sent)} messages sent, first: {sent[0][:60]!r}")

    # ---- .rclone ----
    import importlib
    prof = importlib.import_module("plugins.profile")
    pc = FakeClient()
    prof.register_profile(pc)
    rclone_fn = None
    for ev, fn in pc.handlers:
        pat = getattr(ev, "pattern", None)
        if not pat:
            continue
        try:
            m = pat(".rclone") if callable(pat) else _re.match(pat, ".rclone")
        except Exception:
            continue
        if m and m.group(0).startswith(".rclone"):
            rclone_fn = fn
    assert rclone_fn, "rclone handler not found"
    m = _re.match(r"^\.rclone(?:\s+(full|f|all))?\s*$", ".rclone")
    e = FakeEvent(".rclone")
    e.pattern_match = m
    # patch internals used by _clone_profile
    async def fake_full(client, target):
        return FakeUser(1, "Mintu"), type("F", (), {"about": "bio"})()
    async def fake_dl(client, entity, dest, limit=1):
        return []
    prof._get_user_full = fake_full
    prof._download_all_pfps = fake_dl
    await rclone_fn(e)
    assert any("Random target" in t for t in e.edits), e.edits
    assert any("clone done" in t.lower() or "cloned" in t.lower() for t in e.edits), e.edits
    print(f"  ✓ .rclone → edits: {[x[:40] for x in e.edits]}")

    # ---- autodp state flag (restore original state after) ----
    from plugins.dp import _dp_load_state, _dp_save_state
    orig_state = _dp_load_state()
    try:
        st = dict(orig_state)
        st["autodp_on"] = True
        st["interval_min"] = 30
        _dp_save_state(st)
        assert _dp_load_state().get("autodp_on") is True
        print("  ✓ autodp persistent state (autodp_on) round-trips")
    finally:
        _dp_save_state(orig_state)


def main():
    print("── raid message builder ──")
    test_raid_message_builder()
    print("── .sg cleaner ──")
    test_sg_cleaner()
    print("── live handler sim ──")
    asyncio.get_event_loop().run_until_complete(test_raid_and_rclone_handlers())
    print("\nALL FOCUSED TESTS PASSED ✅")


if __name__ == "__main__":
    main()

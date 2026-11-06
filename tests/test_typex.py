#!/usr/bin/env python3
"""TYPE-X tests — styles, control commands, auto-mode guards, persistence.

Usage:  python3 tests/test_typex.py   (ya  pytest tests/test_typex.py)
"""
import asyncio
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import plugins.fun as fun  # noqa: E402
from plugins.fun import (  # noqa: E402
    _tx_frames, _tx_steps, _tx_animate, _tx_load, _tx_save,
    _TX_STATE, _TX_STYLES, _TX_MAX_CHARS, _TX_FILE,
)

TYPE_PATTERN = re.compile(r"^\.type(?:\s+([\s\S]+))?$")
SAMPLE = "Hello Sukuna X"


class FakeClient:
    def __init__(self):
        self.handlers = []
        self.stop_processes = {}
        self.flood_safe = lambda f: f
        self._mid = 500

    def on(self, ev):
        def deco(fn):
            self.handlers.append((ev, fn))
            return fn
        return deco

    async def send_message(self, chat, text, **kw):
        self._mid += 1
        return type("M", (), {"id": self._mid})()


class FakeEvent:
    def __init__(self, text, mid=1, media=False, entities=None):
        self.id = mid
        self.text = text
        self.media = media
        self.entities = entities
        self.fwd_from = None
        self.via_bot = None
        self.buttons = None
        self.edits = []

    async def edit(self, text, **kw):
        self.edits.append((text, kw))


def _find_handler(client, name):
    for _ev, fn in client.handlers:
        if fn.__name__ == name:
            return fn
    return None


def test_all_styles_valid():
    for style in _TX_STYLES:
        frames = _tx_frames(SAMPLE, style)
        assert frames, style
        assert frames[-1] == SAMPLE, (style, frames[-1])
        assert len(frames) <= 48, (style, len(frames))
        for a, b in zip(frames, frames[1:]):
            assert a != b, (style, "duplicate consecutive frames")
    print(f"  ✓ all {len(_TX_STYLES)} styles: frames valid, last frame == original")


def test_long_text_capped():
    for style in _TX_STYLES:
        frames = _tx_frames("x" * _TX_MAX_CHARS, style)
        assert len(frames) <= 48, (style, len(frames))
        assert frames[-1] == "x" * _TX_MAX_CHARS
    assert _tx_steps(300) == 13      # 300/24 = 12.5 → 13 chars/frame
    assert _tx_steps(10) == 1
    print("  ✓ 300-char text: frame cap respected, steps math correct")


def test_wave_has_bold():
    frames = _tx_frames("wave", "wave")
    assert any("**" in f for f in frames)
    assert frames[-1] == "wave"
    print("  ✓ wave style: bold wave frames generated")


def test_random_style_resolves():
    for _ in range(10):
        frames = _tx_frames(SAMPLE, "random")
        assert frames[-1] == SAMPLE
    print("  ✓ random style: always resolves to a valid style")


def test_persistence_roundtrip():
    orig = dict(_TX_STATE)
    try:
        _TX_STATE.update({"on": True, "style": "glitch", "speed": 0.3})
        _tx_save()
        _TX_STATE.update({"on": False, "style": "classic", "speed": 0.15})
        _tx_load()
        assert _TX_STATE["on"] is True
        assert _TX_STATE["style"] == "glitch"
        assert abs(_TX_STATE["speed"] - 0.3) < 1e-9
    finally:
        _TX_STATE.update(orig)
        _tx_save()
    print("  ✓ typex.json persistence round-trip (restart-proof)")


async def test_control_commands():
    c = FakeClient()
    fun.register_fun(c)
    h = _find_handler(c, "_type")
    assert h, ".type handler registered nahi hua"

    async def run(arg):
        e = FakeEvent(f".type {arg}" if arg else ".type")
        m = TYPE_PATTERN.match(e.text)
        assert m, e.text
        e.pattern_match = m
        await h(e)
        return e

    # on
    e = await run("on")
    assert _TX_STATE["on"] is True
    assert any("TYPE-X: ON" in t for t, _ in e.edits)
    # off (".type of" typo alias bhi)
    for word in ("off", "of"):
        e = await run(word)
        assert _TX_STATE["on"] is False
        assert any("OFF" in t for t, _ in e.edits)
    # style set
    e = await run("glitch")
    assert _TX_STATE["style"] == "glitch"
    assert any("glitch" in t for t, _ in e.edits)
    # speed set + clamp
    e = await run("speed 0.4")
    assert abs(_TX_STATE["speed"] - 0.4) < 1e-9
    await run("speed 99")          # clamp to 1.0
    assert abs(_TX_STATE["speed"] - 1.0) < 1e-9
    # styles gallery
    e = await run("styles")
    assert any("TYPE-X STYLES" in t for t, _ in e.edits)
    # status
    e = await run("status")
    assert any("TYPE-X STATUS" in t for t, _ in e.edits)
    # no-arg help
    e = await run("")
    assert any("TYPE-X SYSTEM" in t for t, _ in e.edits)
    print("  ✓ .type on/off/of/style/speed/styles/status/help — sab ok")


async def test_one_shot_animation():
    c = FakeClient()
    fun.register_fun(c)
    h = _find_handler(c, "_type")
    e = FakeEvent(".type kya kar rhe ho")
    e.pattern_match = TYPE_PATTERN.match(e.text)
    _TX_STATE["on"] = False
    _TX_STATE["style"] = "classic"
    await h(e)
    texts = [t for t, _ in e.edits]
    assert len(texts) >= 3, texts                     # multiple frames
    assert texts[0].endswith("▌") or "▌" in texts[0]  # typewriter cursor
    # final edit must restore the exact text (md parse for one-shot)
    final_t, final_kw = e.edits[-1]
    assert final_t == "kya kar rhe ho"
    assert final_kw.get("parse_mode", "md") == "md"
    print(f"  ✓ one-shot .type <text>: {len(texts)} frames, final == original")


async def test_auto_mode():
    c = FakeClient()
    fun.register_fun(c)
    auto = _find_handler(c, "_type_auto")
    assert auto, "auto handler registered nahi hua"

    # bot-sent marking patch laga?
    assert getattr(c, "_tx_patched", False), "send_message patch missing"

    # ON karo
    _TX_STATE["on"] = True
    _TX_STATE["style"] = "classic"
    _TX_STATE["speed"] = 0.05

    # 1) normal plain message → animate
    fun._TX_LAST_AUTO = 0.0
    e = FakeEvent("hello doston kaise ho", mid=101)
    await auto(e)
    assert len(e.edits) >= 3, e.edits
    fin_t, fin_kw = e.edits[-1]
    assert fin_t == "hello doston kaise ho"
    assert fin_kw.get("parse_mode") is None          # plain restore (auto mode)
    print(f"  ✓ auto-mode: plain message animated ({len(e.edits)} edits), final exact")

    # 2) command messages skip
    for txt in (".help", "/start", "!bang", "#tag"):
        fun._TX_LAST_AUTO = 0.0
        e2 = FakeEvent(txt, mid=102)
        await auto(e2)
        assert not e2.edits, (txt, e2.edits)
    print("  ✓ auto-mode: ./!/# commands skipped")

    # 3) media / entities skip
    fun._TX_LAST_AUTO = 0.0
    e3 = FakeEvent("photo text", mid=103, media=True)
    await auto(e3)
    assert not e3.edits
    fun._TX_LAST_AUTO = 0.0
    e4 = FakeEvent("link wala", mid=104, entities=["url"])
    await auto(e4)
    assert not e4.edits
    print("  ✓ auto-mode: media / entity messages skipped")

    # 4) bot-sent (client.send_message) skip — raid/spam protection
    fun._TX_LAST_AUTO = 0.0
    sent = await c.send_message(55, "bot ka bheja message")
    e5 = FakeEvent("bot ka bheja message", mid=sent.id)
    await auto(e5)
    assert not e5.edits
    print("  ✓ auto-mode: bot-sent messages (raid/spam/echo) NEVER animated")

    # 4b) event.respond()/reply() — Telethon internally client.send_message
    #     hi call karta hai → wahi patched → auto-mode inhe bhi skip karega
    class _RespEvent:
        def __init__(self, client):
            self._client = client

        async def respond(self, text):
            return await self._client.send_message("chat", text)

    fun._TX_LAST_AUTO = 0.0
    re_ = _RespEvent(c)
    sent2 = await re_.respond("antipm ka auto-reply message")
    assert sent2.id in fun._TX_BOT_SENT, "respond() message marked nahi hua!"
    e5b = FakeEvent("antipm ka auto-reply message", mid=sent2.id)
    await auto(e5b)
    assert not e5b.edits
    print("  ✓ auto-mode: event.respond()/reply() messages bhi never animated")

    # 5) OFF state → kuch nahi hota
    _TX_STATE["on"] = False
    fun._TX_LAST_AUTO = 0.0
    e6 = FakeEvent("normal message", mid=105)
    await auto(e6)
    assert not e6.edits
    print("  ✓ auto-mode: OFF me zero edits")

    _TX_STATE["on"] = False
    _tx_save()


async def test_animate_flood_fail_safe():
    """edit hamesha fail ho → 3 fails me break, infinite loop nahi."""
    class BombEvent:
        id = 900
        edits = []

        async def edit(self, *a, **kw):
            raise RuntimeError("edit blocked")

    _TX_STATE["speed"] = 0.05
    done = await asyncio.wait_for(
        _tx_animate(BombEvent(), "test flood safety", "classic"), timeout=30)
    assert done in (True, False)   # no exception, no hang
    print("  ✓ _tx_animate: 3-fail break, kabhi hang nahi")


def main():
    print("── TYPE-X style engine ──")
    test_all_styles_valid()
    test_long_text_capped()
    test_wave_has_bold()
    test_random_style_resolves()
    test_persistence_roundtrip()
    print("── TYPE-X commands (fake client) ──")
    asyncio.run(test_control_commands())
    asyncio.run(test_one_shot_animation())
    asyncio.run(test_auto_mode())
    asyncio.run(test_animate_flood_fail_safe())
    print("\nALL TYPE-X TESTS PASSED ✅")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Simulate the .sg flow with a fake conversation to verify the copy-delivery fix."""
import asyncio
import os
import sys
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from telethon import events  # noqa: E402


class FakeUser:
    id = 777
    first_name = "Mintu"
    last_name = None
    username = "mintu_x"
    title = None


class FakeMsg:
    _seq = 0
    def __init__(self, text=None, media=None):
        FakeMsg._seq += 1
        self.id = FakeMsg._seq
        self.message = text
        self.media = media
    async def edit(self, text, **kw):
        self.edited = text
        print(f"    [status→] {text[:60]}")
        return self
    async def delete(self):
        self.deleted = True
        return True


class FakeConv:
    """Mimics telethon conversation — replies queued after each send."""
    def __init__(self, script):
        self.script = list(script)   # list of lists (replies per send)
        self.sent = []
    async def __aenter__(self):
        return self
    async def __aexit__(self, *a):
        return False
    async def send_message(self, text):
        self.sent.append(text)
        self.pending = list(self.script.pop(0)) if self.script else []
    async def get_response(self, timeout=None):
        await asyncio.sleep(0.01)
        if not self.pending:
            raise asyncio.TimeoutError()
        return self.pending.pop(0)


class FakeClient:
    def __init__(self, script):
        self.conv = FakeConv(script)
        self.handlers = []
        self.stop_processes = {}
        self.flood_safe = lambda f: f
        self.sent = []
        self.entity = FakeUser()

    def on(self, ev):
        def deco(fn):
            self.handlers.append((ev, fn))
            return fn
        return deco
    def add_event_handler(self, fn, ev):
        self.handlers.append((ev, fn))
    async def get_entity(self, x):
        return self.entity if x != "@SangMata_BOT" else "bot-entity"
    def conversation(self, entity, timeout=None):
        return self.conv
    async def send_message(self, chat, text, **kw):
        self.sent.append((chat, text))
        print(f"    [deliver→chat {chat}] {text[:90]!r}")
    async def send_file(self, chat, file, caption=None):
        self.sent.append((chat, f"<media:{caption}>"))
        print(f"    [deliver-media→chat {chat}] caption={caption!r}")


class FakeReplyMsg:
    async def get_input_sender(self):
        return "peer-target"


class FakeEvent:
    id = 42
    chat_id = 55
    is_reply = True
    async def get_input_chat(self):
        return 55
    async def get_reply_message(self):
        return FakeReplyMsg()
    async def reply(self, text="", **kw):
        m = FakeMsg()
        print(f"    [status←] {text[:60]}")
        return m


def find_handler(client, cmd):
    for ev, fn in client.handlers:
        pat = getattr(ev, "pattern", None)
        if not pat:
            continue
        try:
            m = pat(cmd) if callable(pat) else re.match(pat, cmd)
        except Exception:
            continue
        if m:
            return fn
    return None


async def main():
    import plugins.info as info

    # SangMata-style replies: first a "please wait" msg, then real data,
    # then a second data message (username history) + branding lines
    script = [[
        FakeMsg("⚠️ Please wait a second..."),
        FakeMsg(
            "🔎 History of [Mintu](tg://user?id=777)\n\n"
            "First Name:\n"
            "1. Mintu (2023-01-01)\n"
            "2. Mintu Bhai (2024-02-02)\n\n"
            "🤖 @SangMata_BOT | Powered by SangMata Forward Bot"),
        FakeMsg(
            "Username History:\n"
            "1. @mintu_king (2023-03-03)\n\n"
            "[SangMata](t.me/SangMata_BOT)"),
    ]]

    client = FakeClient(script)
    info.register_info(client)
    sg = find_handler(client, ".sg")
    assert sg, ".sg handler not registered"

    print("── .sg simulation ──")
    await sg(FakeEvent())

    assert len(client.conv.sent) >= 1 and client.conv.sent[0] == "777", client.conv.sent
    print(f"  ✓ query sent inside conversation: {client.conv.sent}")

    deliveries = [t for _, t in client.sent]
    assert deliveries, "nothing delivered to the chat!"
    out = "\n".join(deliveries).lower()
    assert "sangmata" not in out, out
    assert "powered by" not in out
    assert "mintu bhai (2024-02-02)" in out
    assert "@mintu_king (2023-03-03)" in out
    assert "name history" in out
    print("  ✓ history copied & delivered as OWN message (no source branding)")
    print("\n.SG SIMULATION PASSED ✅")


if __name__ == "__main__":
    asyncio.run(main())

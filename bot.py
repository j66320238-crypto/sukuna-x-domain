#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  🤖 SUKUNA-X DOMAIN TEST BOT MODE                                           ║
╠══════════════════════════════════════════════════════════════════════╣
║  Test commands on your OWN bot (from @BotFather) instead of your     ║
║  main account — so testing never touches your real ID.               ║
║                                                                      ║
║      python bot.py                     (asks for token)              ║
║      BOT_TOKEN="123:abc" python bot.py                             ║
╚══════════════════════════════════════════════════════════════════════╝

Commands (owner-only):
  /start /ping /alive     basics
  .spamb <n> <text>       text spam in the current chat (max 50/burst)
  .sspam <n>              reply to a sticker → re-send it n times
  .stop                   cancel loops

⚠️  Use ONLY in your own test chats/groups. Spam outside your own
   spaces can get the bot banned — that's the point of testing here.
"""
import asyncio, os, sys

try:
    from telethon import TelegramClient, events
    from telethon.errors import FloodWaitError
except ImportError:
    print("❌ Telethon missing → pip install telethon tgcrypto")
    sys.exit(1)

from core import (resolve_credentials, throttle, safe_sleep, note_flood,
                  safety_line, _fmt_uptime, BOT_VERSION, log, stop_processes,
                  DATA_DIR)

START_TIME = __import__("time").time()
MAX_BURST = 50          # hard cap per command — never more
OWNER_ID = None         # set at startup; only this user can drive the bot


def _owner_only(event):
    return OWNER_ID is not None and event.sender_id == OWNER_ID


async def main():
    global OWNER_ID
    print("\n⚡ SUKUNA-X DOMAIN TEST BOT MODE v" + BOT_VERSION)
    print("─" * 56)
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        token = input("🤖 Bot token (from @BotFather): ").strip()
    if not token or ":" not in token:
        print("❌ Invalid bot token.")
        sys.exit(1)
    api_id, api_hash, acc_name, _phone = resolve_credentials()

    client = TelegramClient(os.path.join(DATA_DIR, "sukuna_testbot"), api_id, api_hash)
    await client.start(bot_token=token)
    me = await client.get_me()
    print(f"✅ Connected as @{me.username} (bot id {me.id})")
    own = os.environ.get("OWNER_ID", "").strip()
    if own.isdigit():
        OWNER_ID = int(own)
    else:
        raw = input("👑 Your Telegram user-ID (owner-only control, 0 = anyone): ").strip()
        OWNER_ID = int(raw) if raw.isdigit() else 0
    print("🛡  Anti-ban engine active:", safety_line())

    @client.on(events.NewMessage(pattern=r"^/start$"))
    async def _start(event):
        await event.reply(
            "⚡ **SUKUNA-X DOMAIN TEST BOT** online!\n"
            "`/ping` `/alive` · `.spamb <n> <text>` · `.sspam <n>` (reply to sticker)")

    @client.on(events.NewMessage(pattern=r"^/ping$"))
    async def _ping(event):
        if not _owner_only(event):
            return
        t0 = __import__("time").time()
        msg = await event.reply("pong")
        await msg.edit(f"🏓 Pong! `{(__import__('time').time()-t0)*1000:.0f} ms`")

    @client.on(events.NewMessage(pattern=r"^/alive$"))
    async def _alive(event):
        if not _owner_only(event):
            return
        await event.reply(
            "✦ ━━━〔 🤖 SUKUNA-X DOMAIN TEST BOT 〕━━━ ✦\n"
            f"┃ 💚 Online · v`{BOT_VERSION}`\n"
            f"┃ ⏱ Uptime: `{_fmt_uptime(__import__('time').time() - START_TIME)}`\n"
            f"┃ 🛡 {safety_line()}\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦")

    @client.on(events.NewMessage(pattern=r"^\.spamb\s+(\d+)\s+([\s\S]+)$"))
    async def _spamb(event):
        if not _owner_only(event):
            return
        n = min(int(event.pattern_match.group(1)), MAX_BURST)
        text = event.pattern_match.group(2)
        await event.reply(f"📨 Test-spamming `{n}` messages (capped at {MAX_BURST})…")
        key = f"botspam_{event.id}"
        async def _run():
            sent = 0
            try:
                for i in range(n):
                    await throttle("send", chat_id=event.chat_id)
                    await client.send_message(event.chat_id, f"{text}  `[{i+1}/{n}]`")
                    sent += 1
                    await safe_sleep(0.5)
            except asyncio.CancelledError:
                raise
            except FloodWaitError as e:
                note_flood(e.seconds)
                log.warning("bot spam hit FloodWait %ss", e.seconds)
            except Exception as e:
                log.error("bot spam error: %s", e)
            finally:
                stop_processes.pop(key, None)
            try:
                await client.send_message(event.chat_id, f"✅ Test spam done: {sent}/{n}")
            except Exception:
                pass
        stop_processes[key] = asyncio.ensure_future(_run())

    @client.on(events.NewMessage(pattern=r"^\.sspam\s+(\d+)$"))
    async def _sspam(event):
        if not _owner_only(event):
            return
        reply = await event.get_reply_message()
        if reply is None or not reply.file:
            return await event.reply("↩️ Reply to a sticker/photo with `.sspam <n>`.")
        n = min(int(event.pattern_match.group(1)), MAX_BURST)
        await event.reply(f"🩸 Test-spamming that sticker `{n}` times…")
        sent = 0
        try:
            for i in range(n):
                await throttle("send", chat_id=event.chat_id)
                await client.send_file(event.chat_id, reply.file,
                                       caption=f"`[{i+1}/{n}]`" if i == n - 1 else None)
                sent += 1
                await safe_sleep(0.5)
        except FloodWaitError as e:
            note_flood(e.seconds)
        except Exception as e:
            log.error("sticker spam error: %s", e)
        await event.reply(f"✅ Sticker test done: {sent}/{n}")

    @client.on(events.NewMessage(pattern=r"^\.stop$"))
    async def _stop(event):
        if not _owner_only(event):
            return
        killed = 0
        for k, t in list(stop_processes.items()):
            if not t.done():
                t.cancel()
                killed += 1
            stop_processes.pop(k, None)
        await event.reply(f"⏹ Stopped {killed} task(s).")

    print("🚀 Test bot running… Ctrl+C to stop.")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test bot stopped cleanly.")

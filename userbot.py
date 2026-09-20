#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
userbot.py — SUKUNA-X DOMAIN entry point (well-structured edition)

This file is ONLY the bootstrapper:
  1. Loads core engine
  2. Connects to Telegram
  3. Auto-discovers plugins/ and registers them
  4. Runs forever

All features live in plugins/ — drop a new .py there and it auto-loads.
Core engine lives in core/ — split into config, safety, store, accounts, etc.
Easy to update: `git pull` + `bash start.sh` or `.update` inside Telegram.
"""
import asyncio
import os
import sys
import platform
import signal
from logging.handlers import RotatingFileHandler

# ── core engine (well-structured) ────────────────────────────────────────
import core
from core import (
    BOT_VERSION, SESSION_NAME, SESSION_STRING, ACCOUNT,
    DATA_DIR, SAFETY, START_TIME,
    print_banner, resolve_credentials, safety_line,
    _fmt_uptime, stop_processes, command_registry,
    log, _safety_save,
)
from core.ui import register_builtin_commands, _total_commands
from core.client import _step, _shutdown_panel, _run_forever, _interactive_login

from telethon import TelegramClient
from telethon.sessions import StringSession

# ── plugin loader (auto-discovers every plugins/*.py) ────────────────────
def register_all(client) -> int:
    """🔌 PLUGIN LOADER — import every plugins/*.py, run its register_*(), harvest COMMANDS_*"""
    import importlib
    base = os.path.dirname(os.path.abspath(__file__))
    plugin_dir = os.path.join(base, "plugins")
    names = sorted(f[:-3] for f in os.listdir(plugin_dir)
                   if f.endswith(".py") and not f.startswith("_"))
    loaded = 0
    for name in names:
        try:
            mod = importlib.import_module(f"plugins.{name}")
        except Exception as e:
            log.error("  ✗  Plugin %s failed to import: %s", name, e, exc_info=True)
            print(f"   ✗  Plugin {name}: import failed (see log)")
            continue
        reg = meta = None
        for attr in sorted(dir(mod)):
            obj = getattr(mod, attr)
            if reg is None and attr.startswith("register") and callable(obj):
                reg = obj
            if meta is None and attr.startswith("COMMANDS") and isinstance(obj, dict):
                meta = obj
        if reg is None:
            continue
        try:
            reg(client)
            command_registry[name] = meta or {"description": name, "commands": []}
            loaded += 1
            log.info("  ✓  Loaded plugin: %s", name)
        except Exception as e:
            log.error("  ✗  Plugin %s failed: %s", name, e, exc_info=True)
            print(f"   ✗  Plugin {name}: register failed (see log)")
    return loaded


# ── main ─────────────────────────────────────────────────────────────────
async def main() -> None:
    print_banner()
    TOTAL_STEPS = 5
    print("   ⚙️  Starting up…")

    _step(1, TOTAL_STEPS,
          f"Python {platform.python_version()} · Telethon {core.telethon_version}"
          + ("  ·  Pillow ✔" if core._HAS_PIL else "  ·  Pillow ✖ (image tools off)"))
    if sys.version_info < (3, 8):
        print("   ✖  Python 3.8+ is required.")
        sys.exit(1)

    try:
        api_id, api_hash, acc_name, acc_phone = resolve_credentials()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled. Bye!")
        sys.exit(1)

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        fh = RotatingFileHandler(os.path.join(DATA_DIR, "userbot.log"),
                                 maxBytes=2_000_000, backupCount=2, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
        log.addHandler(fh)
    except Exception:
        pass
    try:
        asyncio.get_running_loop().set_exception_handler(
            lambda loop, ctx: log.error("Unhandled async error: %s",
                                        ctx.get("exception") or ctx.get("message")))
    except Exception:
        pass
    who = f"account '{acc_name}'" if ACCOUNT else "built-in API_ID/API_HASH"
    _step(2, TOTAL_STEPS, f"Credentials ready ({who})" +
          (f" · phone {acc_phone}" if acc_phone else ""))

    use_string_session = bool(SESSION_STRING and SESSION_STRING.strip())
    if use_string_session:
        try:
            session_obj = StringSession(SESSION_STRING.strip())
            print("   ℹ️  Using SESSION_STRING (no file session needed).")
        except ValueError:
            log.critical("SESSION_STRING is invalid (not a valid Telethon string).")
            sys.exit(1)
    else:
        session_obj = acc_name if ACCOUNT else SESSION_NAME

    client = TelegramClient(
        session=session_obj,
        api_id=api_id,
        api_hash=api_hash,
        device_model="SukunaX-Domain",
        system_version=BOT_VERSION,
        app_version=f"Sukuna-X Domain {BOT_VERSION}",
        lang_code="en",
        system_lang_code="en",
        connection_retries=None,
        retry_delay=1,
        request_retries=5,
        flood_sleep_threshold=60,
    )
    try:
        client.parse_mode = "md"
    except Exception:
        pass

    client.stop_processes = stop_processes
    client.flood_safe = core.flood_safe
    client.command_registry = command_registry
    client._logger = log

    log.info("Connecting to Telegram…")
    try:
        await client.connect()
    except Exception as e:
        print("   ✖  Connect failed.\n")
        log.critical("Connect failed: %s", e)
        print(
            "⛔  Could not connect to Telegram. Check:\n"
            "   • Internet / VPN is working\n"
            "   • API_ID / API_HASH are correct (https://my.telegram.org)\n"
            "   • Your system clock is accurate\n"
        )
        sys.exit(1)
    _step(3, TOTAL_STEPS, "Connected to Telegram servers")

    if not await client.is_user_authorized():
        if use_string_session:
            log.critical("SESSION_STRING is not authorised — regenerate it or leave it empty.")
            await client.disconnect()
            sys.exit(1)
        ok = await _interactive_login(client)
        if not ok or not await client.is_user_authorized():
            log.critical("Login failed — shutting down.")
            await client.disconnect()
            sys.exit(1)
        log.info("✅  Logged in! Session saved in '%s.session' — keep the file safe.",
                 session_obj)

    me = await client.get_me()
    log.info("✅  Logged in as: %s (@%s)  │  ID: %s",
             me.first_name, me.username or "n/a", me.id)

    register_builtin_commands(client)
    count = register_all(client)
    total_handlers = len(getattr(client, "_event_builders", []) or [])
    cmds = _total_commands()
    _step(4, TOTAL_STEPS,
          f"Registered {count} plugins · {total_handlers} handlers · {cmds} commands")
    if count < 23 or total_handlers < 290:
        log.warning("Self-check looks low — some plugins may have failed (scroll up for ✗).")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, AttributeError, RuntimeError):
            try:
                signal.signal(sig, lambda *_: stop_event.set())
            except Exception:
                pass

    try:
        await client.send_message(
            "me",
            "✦ ━━━━━〔 ⚡ SUKUNA-X DOMAIN 〕━━━━━ ✦\n"
            f"┃ 💚 **Userbot Online!** `v{BOT_VERSION}`\n"
            f"┃ 👤 {me.first_name} (@{me.username or 'n/a'})\\n"
            f"┃ 🧩 Plugins: `{count}`  ·  ⌨️ Commands: `{cmds}`\n"
            f"┃ 🛡️ Shield: {safety_line()}\n"
            "┃ 📖 Commands: `.help`\n"
            "┃ 🎮 Farmer: `.mhelp`\n"
            "┃ 🎬 Animations: `.anims`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )
    except Exception as e:
        log.warning("Could not send Saved Messages note: %s", e)
    _step(5, TOTAL_STEPS, "Online card sent to Saved Messages")

    log.info("🚀  SUKUNA-X DOMAIN is ONLINE!   (Ctrl+C to stop)")

    reason = "unknown"
    runner = asyncio.create_task(_run_forever(client, stop_event))
    waiter = asyncio.create_task(stop_event.wait())
    try:
        await asyncio.wait({runner, waiter}, return_when=asyncio.FIRST_COMPLETED)
        reason = "stopped by signal (Ctrl+C / kill)" if stop_event.is_set() \
            else "Telegram connection closed"
    except KeyboardInterrupt:
        reason = "Ctrl+C"
    finally:
        stop_event.set()
        stopped = 0
        for name, task in list(stop_processes.items()):
            if not task.done():
                task.cancel()
                stopped += 1
        stop_processes.clear()
        for t in (runner, waiter):
            if not t.done():
                t.cancel()
        await asyncio.sleep(0.3)
        try:
            await client.disconnect()
        except Exception:
            pass
        _safety_save()
        log.debug("stopped %d background task(s)", stopped)
        _shutdown_panel(me, reason)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔  Stopped (Ctrl+C). Session saved — next run is instant. 👋")
    except Exception as exc:
        log.critical("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)

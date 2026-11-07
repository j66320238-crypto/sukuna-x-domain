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
import fcntl               # v7.4.2: instance-lock (double-start guard)
import logging          # v7.2 fix: pehle yahan import nahi tha → file-log silently kaam nahi karta tha
import os
import sys
import time
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
from core import state as _core_state
from core import accounts as _accounts_mod   # v7.4.2: LIVE ACCOUNT (stale-import fix)
from core.ui import register_builtin_commands, _total_commands
from core.client import _step, _shutdown_panel, _run_forever, _interactive_login

from telethon import TelegramClient
from telethon import events as _tg_events          # v7.7.1: update-stream healer
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
    total = len(names)
    print(f"\n   🔌 Loading {total} plugins…")
    for idx, name in enumerate(names, 1):
        t0 = time.time()
        try:
            mod = importlib.import_module(f"plugins.{name}")
        except Exception as e:
            log.error("  ✗  Plugin %s failed to import: %s", name, e, exc_info=True)
            print(f"   [{idx}/{total}] ✗  {name} — import failed (see log)")
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
            ms = (time.time() - t0) * 1000
            core.state.PLUGIN_LOAD_TIMES[name] = ms
            log.info("  ✓  Loaded plugin: %s (%.0fms)", name, ms)
            print(f"   [{idx}/{total}] ✓  {name:<14} ({ms:.0f}ms)")
        except Exception as e:
            log.error("  ✗  Plugin %s failed: %s", name, e, exc_info=True)
            print(f"   [{idx}/{total}] ✗  {name} — register failed (see log)")
    return loaded


# ── main ─────────────────────────────────────────────────────────────────
def _acquire_instance_lock():
    """v7.4.2 — DOUBLE-START GUARD.

    Problem: agar do userbot instances ek hi session file par chalein toh
    (a) 'database is locked' errors aate hain
    (b) session ki entity-cache CORRUPT ho jaati hai → edits galat chat par
        jaate hain ('message id invalid') → commands chupchap fail
    Ab: ek hi instance chalega — doosra turant clear message ke saath exit.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        fh = open(os.path.join(DATA_DIR, "sukuna.lock"), "w")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError):
            fh.close()
            return None
        fh.write(str(os.getpid()))
        fh.flush()
        return fh                     # fd open rakho — process exit par lock release
    except Exception:
        return None                   # lock lag nahi paya (FS support?) — warn bhi mat


async def main() -> None:
    _lock_fh = _acquire_instance_lock()
    if _lock_fh is None:
        print(
            "\n⛔  SUKUNA-X DOMAIN IS ALREADY RUNNING (another instance holds the lock).\n"
            "   ──────────────────────────────────────────────\n"
            "   • Only ONE instance per account is allowed —\n"
            "     two instances = session corruption + 'database is locked'.\n"
            "   • Check status:   ps aux | grep userbot\n"
            "   • Stop it:        bash sukuna_stop.sh\n"
            "   • Then start:     screen -dmS sukuna bash sukuna_run.sh\n"
        )
        log.critical("Double-start BLOCKED by instance lock (pid %s)", os.getpid())
        sys.exit(77)                  # supervisor isko 60s backoff samajhta hai

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

    # 🤖 v7.3 BotController: bot sessions ke liye resolved creds share karo
    _core_state.ACTIVE_API_ID = api_id or 0
    _core_state.ACTIVE_API_HASH = api_hash or ""

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
    # v7.4.2 FIX: pehle `ACCOUNT` by-value import hota tha jo hamesha None
    # reh jata tha (resolve_credentials ke baad bhi) → session hamesha
    # SESSION_NAME hi banta tha. Ab LIVE module attribute dekha jata hai.
    _live_account = getattr(_accounts_mod, "ACCOUNT", None)
    who = f"account '{acc_name}'" if _live_account else "built-in API_ID/API_HASH"
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
        session_obj = acc_name if _live_account else SESSION_NAME

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
        # 🛡 v7.2: 60 → 20 — chhote floods Telethon khud sambhalta hai,
        # bade floods (20s+) ab raise hote hain → hamara engine unhe pakadta
        # hai (note_flood + storm detect + adaptive backoff). Zyada protection.
        flood_sleep_threshold=20,
    )
    try:
        client.parse_mode = "md"
    except Exception:
        pass

    # 🩺 v7.7.1: fetch updates missed during connection hiccups — without
    # this, a routing hiccup can leave own messages unprocessed forever.
    try:
        client.catch_up = True
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
    _core_state.OWNER_ID = me.id
    log.info("✅  Logged in as: %s (@%s)  │  ID: %s",
             me.first_name, me.username or "n/a", me.id)

    register_builtin_commands(client)
    count = register_all(client)
    total_handlers = len(getattr(client, "_event_builders", []) or [])
    cmds = _total_commands()
    _step(4, TOTAL_STEPS,
          f"Registered {count} plugins · {total_handlers} handlers · {cmds} commands")

    # ── v7.7.1 UPDATE-STREAM SELF-HEALER ─────────────────────────────────
    # An unclean kill (kill -9) or a server-side update-routing hiccup can
    # leave this connection update-dead (commands sent but never processed)
    # while RPCs still work. Detection = TWOFOLD:
    #   (a) total dispatch silence > 5 min, or
    #   (b) Telethon logs ≥4 "Timeout waiting for updates expired" inside
    #       5 min while <2 updates actually dispatched (half-dead stream:
    #       some diffs arrive but own messages never come back).
    # Cure = reconnect (fresh getState re-binds the update stream).
    _upd_state = {"ts": time.time(), "timeouts": [], "dispatched": 0,
                  "last_heal": 0.0}

    async def _upd_touch(event):
        _upd_state["ts"] = time.time()
        _upd_state["dispatched"] += 1

    client.add_event_handler(_upd_touch, _tg_events.NewMessage())

    class _UpdateTimeoutCounter(logging.Handler):
        def emit(self, record):
            try:
                if "Timeout waiting for updates" in record.getMessage():
                    _upd_state["timeouts"].append(time.time())
            except Exception:
                pass

    _timeout_counter = _UpdateTimeoutCounter()
    logging.getLogger("telethon.client.updates").addHandler(_timeout_counter)

    async def _updates_healer():
        while True:
            await asyncio.sleep(75)
            try:
                now = time.time()
                # (a) total silence
                silent = now - _upd_state["ts"]
                # (b) timeout cluster with barely any dispatches
                _upd_state["timeouts"] = [t for t in _upd_state["timeouts"]
                                          if now - t < 300]
                n_timeouts = len(_upd_state["timeouts"])
                dead = silent > 300 or (n_timeouts >= 4
                                        and now - _upd_state["ts"] > 120)
                if not dead or now - _upd_state["last_heal"] < 240:
                    continue
                _upd_state["last_heal"] = now
                log.warning("🩺 update stream looks dead (silent %ds, "
                            "%d update-timeouts) — self-healing reconnect…",
                            int(silent), n_timeouts)
                await client.disconnect()
                await client.connect()
                _upd_state["ts"] = time.time()
                _upd_state["timeouts"].clear()
                me2 = await client.get_me()
                log.warning("🩺 update-stream heal done — reconnected as %s "
                            "(%s)", me2.first_name, me2.id)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("🩺 updates healer: %r", e)

    # keep a strong reference — unreferenced asyncio tasks get garbage-collected!
    _core_state.BG_TASKS.append(asyncio.create_task(_updates_healer()))

    expected_plugins = len([f for f in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins"))
                            if f.endswith(".py") and not f.startswith("_")])
    if count < expected_plugins:
        log.warning("Self-check: %d/%d plugins loaded — some failed (scroll up for ✗).",
                    count, expected_plugins)

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
            f"┃ 💚 **Userbot Online!** `v{BOT_VERSION}` PHANTOM\n"
            f"┃ 👤 {me.first_name} (@{me.username or 'n/a'})\n"
            f"┃ 🧩 Plugins: `{count}`  ·  ⌨️ Commands: `{cmds}`\n"
            f"┃ 🛡️ Shield: {safety_line()}\n"
            "┃ 📖 Menu: `.help` · 🕹 `.menu` · 🎬 `.anims`\n"
            "┃ 📜 `.plist` · 📊 `.stats` · 🎮 `.mhelp`\n"
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

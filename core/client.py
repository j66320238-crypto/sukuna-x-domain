#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/client.py — startup helpers & interactive login
"""
import asyncio
import getpass
import os
import sys
import time

from .helpers import _fmt_uptime
from .safety import SAFETY
from .state import START_TIME
from .store import DATA_DIR
from .config import PHONE

import logging
log = logging.getLogger("userbot")


def _step(n: int, total: int, text: str, ok: bool = True) -> None:
    mark = "✔" if ok else "✖"
    print(f"   [{n}/{total}] {mark}  {text}")


def _shutdown_panel(me, reason: str) -> None:
    uptime = _fmt_uptime(time.time() - START_TIME)
    name = getattr(me, "first_name", "user") if me else "user"
    print(
        "\n✦ ───────────────────────────────────────────────────────── ✦\n"
        "   ⏹  SUKUNA-X DOMAIN IS SHUTTING DOWN\n"
        f"   ✦  User   : {name}\n"
        f"   ✦  Reason : {reason}\n"
        f"   ✦  Uptime : {uptime}\n"
        f"   ✦  Sends  : {SAFETY['sends']}   ·  Edits: {SAFETY['edits']}   ·  "
        f"FloodWaits: {SAFETY['floods']}\n"
        "   ✦  Session saved — next start is instant ⚡\n"
        "✦ ───────────────────────────────────────────────────────── ✦\n"
    )


async def _run_forever(client, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await client.run_until_disconnected()
            if stop_event.is_set():
                return
            break
        except ConnectionError as exc:
            log.warning("Connection dropped (%s) — reconnecting…", exc)
            await asyncio.sleep(3)
            try:
                await client.connect()
            except Exception as retry_exc:
                log.error("Reconnect failed: %s", retry_exc)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            raise


async def _interactive_login(client) -> bool:
    from telethon.errors import (
        PhoneCodeInvalidError,
        PhoneCodeExpiredError,
        PhoneNumberInvalidError,
        PhoneNumberBannedError,
        FloodWaitError as _FWE,
        SessionPasswordNeededError,
    )

    print("\n🔐  First-time login — one time only (the session is saved after).")
    phone = (PHONE or "").strip()
    if not phone:
        try:
            phone = input("📱  Phone number with country code (e.g. +919876543210): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n⛔  Login cancelled.")
            return False
    if not phone:
        print("⛔  Phone number can't be empty — run the bot again.")
        return False

    try:
        await client.send_code_request(phone)
        print("   ✔  OTP sent to your Telegram app (or SMS).")
    except PhoneNumberInvalidError:
        print("⛔  That phone number looks wrong. Use the +countrycode format.")
        return False
    except PhoneNumberBannedError:
        print("⛔  This number is banned by Telegram — use another account.")
        return False
    except _FWE as exc:
        print(f"⛔  Telegram asked to wait {exc.seconds}s before trying again.")
        return False
    except Exception as exc:
        print(f"⛔  Could not send OTP: {exc}")
        return False

    for attempt in range(1, 4):
        try:
            code = input(f"💬  Enter the OTP code (attempt {attempt}/3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n⛔  Login cancelled.")
            return False
        if not code:
            continue
        try:
            await client.sign_in(phone, code)
            print("   ✔  Logged in!")
            return True
        except PhoneCodeInvalidError:
            print("   ✖  Wrong code — check the Telegram message again.")
        except PhoneCodeExpiredError:
            print("   ↻  Code expired — sending a fresh one…")
            try:
                await client.send_code_request(phone)
            except Exception as exc:
                print(f"   ✖  Could not resend: {exc}")
        except SessionPasswordNeededError:
            for pw_try in range(1, 4):
                try:
                    pw = getpass.getpass(
                        f"🔑  Two-step verification password (attempt {pw_try}/3): "
                    )
                except (EOFError, KeyboardInterrupt):
                    print("\n⛔  Login cancelled.")
                    return False
                try:
                    await client.sign_in(password=pw)
                    print("   ✔  Logged in with 2FA!")
                    return True
                except Exception as exc:
                    print(f"   ✖  Wrong password or error: {exc}")
            return False
        except _FWE as exc:
            print(f"   ⏳  Too many tries — waiting {exc.seconds}s…")
            await asyncio.sleep(exc.seconds + 1)
        except Exception as exc:
            print(f"   ✖  Login failed: {exc}")
    print("⛔  Too many wrong attempts. Run the bot again.")
    return False

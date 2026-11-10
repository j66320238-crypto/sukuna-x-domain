# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: SPAM  (ported from worker_bot/modules/spam.py)
############################################################################

# worker_bot/modules/spam.py
# Spam & Sticker module for the Telegram Userbot.
# Loaded dynamically by userbot.py via register(client).


# ─── Paths ──────────────────────────────────────────────────────────────────
GSPAM_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "gspam_data.json"
)

# ─── JSON Helpers ───────────────────────────────────────────────────────────

def _save_gspam(doc):
    """Persist a sticker Document's id / access_hash / file_reference to JSON."""
    try:
        file_ref = (
            base64.b64encode(doc.file_reference).decode("utf-8")
            if doc.file_reference
            else ""
        )
        payload = {
            "id": str(doc.id),
            "access_hash": str(doc.access_hash),
            "file_reference": file_ref,
        }
        with open(GSPAM_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        return True
    except Exception:
        return False


def _load_gspam():
    """Return an ``InputDocument`` from the JSON file, or ``None``."""
    try:
        with open(GSPAM_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        file_ref = (
            base64.b64decode(data["file_reference"])
            if data.get("file_reference")
            else b""
        )
        return InputDocument(
            id=int(data["id"]),
            access_hash=int(data["access_hash"]),
            file_reference=file_ref,
        )
    except Exception:
        return None


def _clear_gspam():
    """Delete the gspam JSON file."""
    try:
        if os.path.exists(GSPAM_FILE):
            os.remove(GSPAM_FILE)
    except Exception:
        pass


# ─── Module Entry Point ─────────────────────────────────────────────────────

def register_spam(client):
    """Register all spam & sticker handlers on *client*."""

    # ── Background task helpers ──────────────────────────────────────────

    async def _text_spam_task(event, chat, count, text, delay, label):
        """Send *text* to *chat* *count* times with *delay* seconds between."""
        key = f"spam_{event.id}"
        count = safe_cap(count)  # 🛡️ burst cap in safe mode
        sent = 0
        try:
            for _ in range(count):
                try:
                    await client.send_message(chat, text, link_preview=False)
                    sent += 1
                except FloodWaitError as fw:
                    note_flood(fw.seconds)  # 🛡️ auto slow-down
                    await asyncio.sleep(fw.seconds + 1)
                    try:
                        await client.send_message(chat, text, link_preview=False)
                        sent += 1
                    except Exception:
                        continue
                except asyncio.CancelledError:
                    raise
                except Exception:
                    continue

                await safe_sleep(delay)  # 🛡️ anti-ban pacing

            try:
                await event.reply(
                    f"✅ **{label}** finished — {sent}/{count} messages sent."
                )
            except Exception:
                pass
        except asyncio.CancelledError:
            try:
                await event.reply(
                    f"⛔ **{label}** stopped — {sent}/{count} messages sent."
                )
            except Exception:
                pass
            raise
        finally:
            client.stop_processes.pop(key, None)

    # ─────────────────────────────────────────────────────────────────────

    async def _sticker_spam_task(event, chat, count, sticker_doc, label):
        """Send *sticker_doc* (InputDocument) to *chat* *count* times."""
        key = f"spam_{event.id}"
        count = safe_cap(count)  # 🛡️ burst cap in safe mode
        sent = 0
        try:
            for _ in range(count):
                try:
                    await client.send_file(chat, sticker_doc)
                    sent += 1
                except FloodWaitError as fw:
                    note_flood(fw.seconds)  # 🛡️ auto slow-down
                    await asyncio.sleep(fw.seconds + 1)
                    try:
                        await client.send_file(chat, sticker_doc)
                        sent += 1
                    except Exception:
                        continue
                except asyncio.CancelledError:
                    raise
                except Exception:
                    continue

                await safe_sleep(0.05)  # 🛡️ anti-ban pacing
                if sent % 25 == 0:
                    await asyncio.sleep(0)

            try:
                await event.reply(
                    f"✅ **{label}** finished — {sent}/{count} stickers sent."
                )
            except Exception:
                pass
        except asyncio.CancelledError:
            try:
                await event.reply(
                    f"⛔ **{label}** stopped — {sent}/{count} stickers sent."
                )
            except Exception:
                pass
            raise
        finally:
            client.stop_processes.pop(key, None)

    # ─────────────────────────────────────────────────────────────────────

    async def _dm_spam_task(event, target, count, text, delay):
        """Send *text* to a user's DM *count* times."""
        key = f"spam_{event.id}"
        count = safe_cap(count)  # 🛡️ burst cap in safe mode
        sent = 0
        try:
            for _ in range(count):
                try:
                    await client.send_message(target, text, link_preview=False)
                    sent += 1
                except FloodWaitError as fw:
                    note_flood(fw.seconds)  # 🛡️ auto slow-down
                    await asyncio.sleep(fw.seconds + 1)
                    try:
                        await client.send_message(target, text, link_preview=False)
                        sent += 1
                    except Exception:
                        continue
                except asyncio.CancelledError:
                    raise
                except Exception:
                    continue

                await safe_sleep(delay)  # 🛡️ anti-ban pacing

            try:
                await event.reply(
                    f"✅ **dmspam** finished — {sent}/{count} messages sent."
                )
            except Exception:
                pass
        except asyncio.CancelledError:
            try:
                await event.reply(
                    f"⛔ **dmspam** stopped — {sent}/{count} messages sent."
                )
            except Exception:
                pass
            raise
        finally:
            client.stop_processes.pop(key, None)

    # ── Parsing helper ───────────────────────────────────────────────────

    def _parse_count_text(args, usage):
        """Return (count, text, error_message)."""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return None, None, usage
        try:
            count = int(parts[0])
        except ValueError:
            return None, None, "❌ **Count** must be an integer."
        if count <= 0:
            return None, None, "❌ **Count** must be a positive integer."
        return count, parts[1], None

    # ── v7.12 REPLY-REPEAT engine ────────────────────────────────────────

    def _parse_repeat_args(args, default_interval):
        """Reply mode: `.spam 10 .1` → (count, interval, err).
        Interval float allowed — 0 / 0.1 / 0.5 / 1 sab chalta hai."""
        parts = (args or "").split()
        if not parts:
            return None, None, ("❌ Count do — e.g. `.spam 10 .1` "
                                "(reply par)")
        try:
            count = int(parts[0])
        except ValueError:
            return None, None, ("❌ Count integer hona chahiye — "
                                "`.spam 10 .1`")
        if count <= 0:
            return None, None, "❌ Count positive hona chahiye."
        interval = default_interval
        if len(parts) >= 2:
            try:
                interval = float(parts[1])
            except ValueError:
                return None, None, ("❌ Interval number hona chahiye — "
                                    "`.spam 10 .1`")
        if interval < 0:
            interval = 0.0
        return count, interval, None

    async def _repeat_reply_task(event, chat, reply, count, interval, label):
        """v7.12: REPLIED content ko repeat karo — sticker / text / photo /
        video / GIF / voice / audio / document SAB. Direct media-reference
        send (same file, no forward) + FloodWait-safe pacing."""
        key = f"spam_{event.id}"
        count = safe_cap(count)  # 🛡 burst cap in safe mode
        media = getattr(reply, "media", None)
        raw = (getattr(reply, "raw_text", "") or "").strip()
        is_stic = bool(getattr(reply, "sticker", None))
        cap = None if (is_stic or not raw) else raw
        kind = ("sticker" if is_stic else
                ("media" if media is not None else
                 ("text" if raw else "empty")))
        sent = 0
        try:
            if kind == "empty":
                await event.reply("❌ Replied message me kuch repeat karne "
                                  "ko nahi hai.")
                return
            for _ in range(count):
                try:
                    if media is not None:
                        await client.send_file(chat, media, caption=cap)
                    else:
                        await client.send_message(chat, raw,
                                                  link_preview=False)
                    sent += 1
                except FloodWaitError as fw:
                    note_flood(fw.seconds)  # 🛡 auto slow-down
                    await asyncio.sleep(fw.seconds + 1)
                    try:
                        if media is not None:
                            await client.send_file(chat, media, caption=cap)
                        else:
                            await client.send_message(chat, raw,
                                                      link_preview=False)
                        sent += 1
                    except Exception:
                        pass
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass
                if sent and sent % 10 == 0:
                    await asyncio.sleep(0)   # event-loop breath
                await safe_sleep(interval)   # 🛡 anti-ban pacing
            try:
                await event.reply(
                    f"✅ **{label} repeat** finished — {sent}/{count} {kind} "
                    "sent.")
            except Exception:
                pass
        except asyncio.CancelledError:
            try:
                await event.reply(
                    f"⛔ **{label} repeat** stopped — {sent}/{count} sent.")
            except Exception:
                pass
            raise
        finally:
            client.stop_processes.pop(key, None)

    # ── .spam  (1 s delay) ───────────────────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.spam(?:\s|$)"))
    @client.flood_safe
    async def spam_handler(event):
        args = event.raw_text[len(".spam"):].strip()
        # ── v7.12 REPLY-REPEAT: `.spam 10 .1` reply par → replied content
        #    (sticker/text/photo/GIF/video/voice sab) count baar repeat ──
        reply = await event.get_reply_message()
        if reply is not None and (getattr(reply, "media", None) is not None
                                  or (getattr(reply, "raw_text", "") or "").strip()):
            count, interval, err = _parse_repeat_args(args, 1.0)
            if err:
                await event.reply(err)
                return
            chat = await event.get_input_chat()
            task = asyncio.create_task(
                _repeat_reply_task(event, chat, reply, count, interval,
                                   "spam"))
            client.stop_processes[f"spam_{event.id}"] = task
            return
        if not args:
            await event.reply("Usage: `.spam <count> <text>`")
            return
        count, text, err = _parse_count_text(args, "Usage: `.spam <count> <text>`")
        if err:
            await event.reply(err)
            return
        chat = await event.get_input_chat()
        task = asyncio.create_task(
            _text_spam_task(event, chat, count, text, 1.0, "spam")
        )
        client.stop_processes[f"spam_{event.id}"] = task

    # ── .uspam  (no delay) ───────────────────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.uspam(?:\s|$)"))
    @client.flood_safe
    async def uspam_handler(event):
        args = event.raw_text[len(".uspam"):].strip()
        # v7.12 REPLY-REPEAT (no delay)
        reply = await event.get_reply_message()
        if reply is not None and (getattr(reply, "media", None) is not None
                                  or (getattr(reply, "raw_text", "") or "").strip()):
            count, interval, err = _parse_repeat_args(args, 0.0)
            if err:
                await event.reply(err)
                return
            chat = await event.get_input_chat()
            task = asyncio.create_task(
                _repeat_reply_task(event, chat, reply, count, interval,
                                   "uspam"))
            client.stop_processes[f"spam_{event.id}"] = task
            return
        if not args:
            await event.reply("Usage: `.uspam <count> <text>`")
            return
        count, text, err = _parse_count_text(args, "Usage: `.uspam <count> <text>`")
        if err:
            await event.reply(err)
            return
        chat = await event.get_input_chat()
        task = asyncio.create_task(
            _text_spam_task(event, chat, count, text, 0.0, "uspam")
        )
        client.stop_processes[f"spam_{event.id}"] = task

    # ── .fastspam  (0.1 s delay) ─────────────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fastspam(?:\s|$)"))
    @client.flood_safe
    async def fastspam_handler(event):
        args = event.raw_text[len(".fastspam"):].strip()
        # v7.12 REPLY-REPEAT (0.1s default)
        reply = await event.get_reply_message()
        if reply is not None and (getattr(reply, "media", None) is not None
                                  or (getattr(reply, "raw_text", "") or "").strip()):
            count, interval, err = _parse_repeat_args(args, 0.1)
            if err:
                await event.reply(err)
                return
            chat = await event.get_input_chat()
            task = asyncio.create_task(
                _repeat_reply_task(event, chat, reply, count, interval,
                                   "fastspam"))
            client.stop_processes[f"spam_{event.id}"] = task
            return
        if not args:
            await event.reply("Usage: `.fastspam <count> <text>`")
            return
        count, text, err = _parse_count_text(args, "Usage: `.fastspam <count> <text>`")
        if err:
            await event.reply(err)
            return
        chat = await event.get_input_chat()
        task = asyncio.create_task(
            _text_spam_task(event, chat, count, text, 0.1, "fastspam")
        )
        client.stop_processes[f"spam_{event.id}"] = task

    # ── .delayspam  (custom delay) ───────────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.delayspam(?:\s|$)"))
    @client.flood_safe
    async def delayspam_handler(event):
        args = event.raw_text[len(".delayspam"):].strip()
        # v7.12 REPLY-REPEAT (custom delay): `.delayspam 10 0.3` reply par
        reply = await event.get_reply_message()
        if reply is not None and (getattr(reply, "media", None) is not None
                                  or (getattr(reply, "raw_text", "") or "").strip()):
            count, interval, err = _parse_repeat_args(args, 0.5)
            if err:
                await event.reply(err)
                return
            chat = await event.get_input_chat()
            task = asyncio.create_task(
                _repeat_reply_task(event, chat, reply, count, interval,
                                   "delayspam"))
            client.stop_processes[f"spam_{event.id}"] = task
            return
        if not args:
            await event.reply("Usage: `.delayspam <count> <seconds> <text>`")
            return
        parts = args.split(maxsplit=2)
        if len(parts) < 3:
            await event.reply("Usage: `.delayspam <count> <seconds> <text>`")
            return
        try:
            count = int(parts[0])
            delay = float(parts[1])
        except ValueError:
            await event.reply("❌ **Count** and **seconds** must be numbers.")
            return
        if count <= 0:
            await event.reply("❌ **Count** must be a positive integer.")
            return
        if delay < 0:
            await event.reply("❌ **Delay** cannot be negative.")
            return
        text = parts[2]
        chat = await event.get_input_chat()
        task = asyncio.create_task(
            _text_spam_task(event, chat, count, text, delay, "delayspam")
        )
        client.stop_processes[f"spam_{event.id}"] = task

    # ── .dmspam  (DM spam) ───────────────────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dmspam(?:\s|$)"))
    @client.flood_safe
    async def dmspam_handler(event):
        args = event.raw_text[len(".dmspam"):].strip()
        if not args:
            await event.reply("Usage: `.dmspam <count> <username> <text>`")
            return
        parts = args.split(maxsplit=2)
        if len(parts) < 3:
            await event.reply("Usage: `.dmspam <count> <username> <text>`")
            return
        try:
            count = int(parts[0])
        except ValueError:
            await event.reply("❌ **Count** must be an integer.")
            return
        if count <= 0:
            await event.reply("❌ **Count** must be a positive integer.")
            return
        username = parts[1].lstrip("@")
        text = parts[2]

        # ── Resolve the target entity to avoid Peer ID errors ──
        try:
            target = await client.get_input_entity(username)
        except Exception as exc:
            await event.reply(f"❌ Failed to resolve `{username}`:\n`{exc}`")
            return

        task = asyncio.create_task(_dm_spam_task(event, target, count, text, 1.0))
        client.stop_processes[f"spam_{event.id}"] = task

    # ── .mspam  (reply to a sticker) ─────────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mspam(?:\s|$)"))
    @client.flood_safe
    async def mspam_handler(event):
        args = event.raw_text[len(".mspam"):].strip()
        if not args:
            await event.reply("Usage: `.mspam <count>`  (reply to a sticker)")
            return
        try:
            count = int(args.split()[0])
        except ValueError:
            await event.reply("❌ **Count** must be an integer.")
            return
        if count <= 0:
            await event.reply("❌ **Count** must be a positive integer.")
            return

        reply = await event.get_reply_message()
        if not reply:
            await event.reply("❌ Please reply to a sticker.")
            return
        if not reply.sticker:
            await event.reply("❌ The replied message is not a sticker.")
            return

        doc = reply.media.document
        sticker_input = InputDocument(
            id=doc.id,
            access_hash=doc.access_hash,
            file_reference=doc.file_reference,
        )
        chat = await event.get_input_chat()
        task = asyncio.create_task(
            _sticker_spam_task(event, chat, count, sticker_input, "mspam")
        )
        client.stop_processes[f"spam_{event.id}"] = task

    # ── .gspam  (globally saved sticker) ─────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.gspam(?:\s|$)"))
    @client.flood_safe
    async def gspam_handler(event):
        args = event.raw_text[len(".gspam"):].strip()
        if not args:
            await event.reply("Usage: `.gspam <count>`")
            return
        try:
            count = int(args.split()[0])
        except ValueError:
            await event.reply("❌ **Count** must be an integer.")
            return
        if count <= 0:
            await event.reply("❌ **Count** must be a positive integer.")
            return

        sticker_input = _load_gspam()
        if not sticker_input:
            await event.reply(
                "❌ No global sticker is set.\n"
                "Use `.setgspam` (reply to a sticker) to set one."
            )
            return

        chat = await event.get_input_chat()
        task = asyncio.create_task(
            _sticker_spam_task(event, chat, count, sticker_input, "gspam")
        )
        client.stop_processes[f"spam_{event.id}"] = task

    # ── .setgspam  (save a sticker) ──────────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setgspam(?:\s|$)"))
    @client.flood_safe
    async def setgspam_handler(event):
        reply = await event.get_reply_message()
        if not reply:
            await event.reply("❌ Please reply to a sticker to save it.")
            return
        if not reply.sticker:
            await event.reply("❌ The replied message is not a sticker.")
            return

        doc = reply.media.document
        if _save_gspam(doc):
            await event.reply(
                f"✅ **Global sticker saved.**\n"
                f"📄 Document ID: `{doc.id}`\n"
                f"🔑 Access Hash: `{doc.access_hash}`"
            )
        else:
            await event.reply("❌ Failed to save the global sticker.")

    # ── .listgspam  (view saved sticker) ─────────────────────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.listgspam(?:\s|$)"))
    @client.flood_safe
    async def listgspam_handler(event):
        sticker_input = _load_gspam()
        if not sticker_input:
            await event.reply(
                "📭 No global sticker is currently set.\n"
                "Use `.setgspam` (reply to a sticker) to set one."
            )
            return
        await event.reply(
            f"📌 **Saved Global Sticker**\n"
            f"📄 Document ID: `{sticker_input.id}`\n"
            f"🔑 Access Hash: `{sticker_input.access_hash}`"
        )

    # ── .clrgspam  /  .delgspam  (delete saved sticker) ──────────────────

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.clrgspam(?:\s|$)"))
    @client.flood_safe
    async def clrgspam_handler(event):
        _clear_gspam()
        await event.reply("🗑️ Global sticker has been **cleared**.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.delgspam(?:\s|$)"))
    @client.flood_safe
    async def delgspam_handler(event):
        _clear_gspam()
        await event.reply("🗑️ Global sticker has been **deleted**.")
COMMANDS_SPAM = {
    "description": "Spam & Stickers",
    "commands": [
        (".spam <n> <text>", "spam text (1s delay)"),
        (".spam <n> [sec] (reply)", "⚡ v7.12 — reply sticker/photo/GIF/text → wahi content <n> baar repeat (interval float, 0.1 ok)"),
        (".fastspam <n> [sec] (reply)", "repeat replied content fast (0.1s default)"),
        (".uspam <n> [sec] (reply)", "repeat replied content no-delay"),
        (".delayspam <n> <sec> (reply)", "repeat replied content custom delay"),
        (".delayspam <n> <sec> <text>", "custom delay text spam"),
        (".dmspam <n> @user <text>", "spam user DM"),
        (".mspam <n>", "spam replied sticker"),
        (".setgspam", "save global sticker"),
        (".gspam <n>", "spam saved sticker"),
        (".listgspam / .clrgspam", "view/clear saved sticker"),
    ],
}

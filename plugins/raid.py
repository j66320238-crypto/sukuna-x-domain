# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: RAID  (ported from worker_bot/modules/raid.py)
############################################################################

# worker_bot/modules/raid.py
"""
Raid module for the Telegram Userbot.
Dynamically loaded by userbot.py via ``register(client)``.

Raid message format (v2):
    • Default  : "<name> <saved text> <mention>"
                 e.g. saved "kya kar rhe ho" + target "Mintu"
                      → "Mintu kya kar rhe ho Mintu"
    • Template : if saved text contains {name} / {mention} / {tag},
                 it is used as a template:
                 .setraid kya kar rhe ho {name}   → "kya kar rhe ho Mintu"
                 .setraid {name} kya kar rhe ho {tag} → "Mintu kya kar rhe ho Mintu"
    • Fallback : no .setraid needed — default text "kya kar rhe ho" is used.
"""


# ─── Module-level constants & state ───────────────────────────────────────

RAID_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "raid_data.json",
)

# Default raid text — .raid works even if nothing was saved via .setraid
DEFAULT_RAID_TEXT = "kya kar rhe ho"

# In-memory store of user IDs with active reply-raid.
active_reply_raids = []


# ─── File I/O helpers ─────────────────────────────────────────────────────

def _load_raid_text():
    """Return saved raid text or the default one."""
    if os.path.exists(RAID_DATA_FILE):
        try:
            with open(RAID_DATA_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            text = data.get("raid_text")
            if text and str(text).strip():
                return str(text).strip()
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_RAID_TEXT


def _has_saved_raid_text():
    """True only if the user saved a custom raid text via .setraid."""
    if not os.path.exists(RAID_DATA_FILE):
        return False
    try:
        with open(RAID_DATA_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return bool(data.get("raid_text"))
    except (json.JSONDecodeError, OSError):
        return False


def _save_raid_text(text):
    """Persist raid text.  Return ``True`` on success."""
    try:
        with open(RAID_DATA_FILE, "w", encoding="utf-8") as fh:
            json.dump({"raid_text": text}, fh, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def _delete_raid_text():
    """Remove the raid-data file.  Return ``True`` on success."""
    if not os.path.exists(RAID_DATA_FILE):
        return True
    try:
        os.remove(RAID_DATA_FILE)
        return True
    except OSError:
        return False


def _escape_html(text):
    """Escape HTML special characters for safe display inside ``<code>``."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def _build_mention(user_id, display_name):
    """Build an HTML ``<a>`` mention tag."""
    name = _escape_html(display_name or "User")
    return f'<a href="tg://user?id={user_id}">{name}</a>'


# ─── Raid message builder ────────────────────────────────────────────────

def _build_raid_message(text, user_id, display_name):
    """Build the final raid message (HTML).

    • saved text has {name}/{mention}/{tag} → use it as a template
    • otherwise → "<name> <text> <mention>"  (e.g. "Mintu kya kar rhe ho Mintu")
    """
    name = (display_name or "User").strip() or "User"
    safe_name = _escape_html(name)
    mention = _build_mention(user_id, name)
    safe_text = _escape_html(text.strip()) if text else _escape_html(DEFAULT_RAID_TEXT)

    if any(ph in text for ph in ("{name}", "{mention}", "{tag}")):
        msg = (
            text.replace("{name}", safe_name)
                .replace("{tag}", mention)
                .replace("{mention}", mention)
        )
        return msg
    # default style: "Mintu kya kar rhe ho Mintu"
    return f"{safe_name} {safe_text} {mention}"


# ─── Module entry-point ───────────────────────────────────────────────────

def register_raid(client):
    """Register all raid commands on the given Telethon client."""

    # ── .setraid <text> ──────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setraid\s+([\s\S]+)$"))
    @client.flood_safe
    async def setraid_handler(event):
        """Save custom raid text to raid_data.json."""
        text = event.pattern_match.group(1).strip()
        if not text:
            await event.edit(
                "<b>Usage:</b> <code>.setraid &lt;text&gt;</code>",
                parse_mode="html",
            )
            return
        if _save_raid_text(text):
            await event.edit(
                "✅ <b>Raid text saved.</b>\n\n"
                f"<code>{_escape_html(text)}</code>\n\n"
                "💡 Use <code>{name}</code> for plain name and "
                "<code>{tag}</code>/<code>{mention}</code> for mention in the text.\n"
                "Without them: <code>name + text + mention</code> format is used.",
                parse_mode="html",
            )
        else:
            await event.edit(
                "❌ <b>Failed to save raid text.</b>",
                parse_mode="html",
            )

    # ── .listraid ────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.listraid$"))
    @client.flood_safe
    async def listraid_handler(event):
        """Display the currently saved raid text."""
        if _has_saved_raid_text():
            safe = _escape_html(_load_raid_text())
            await event.edit(
                "📝 <b>Current Raid Text:</b>\n\n<code>"
                + safe +
                "</code>\n\n💡 <code>{name}</code> = plain name · "
                "<code>{tag}</code> = mention · no placeholders → "
                "<code>name + text + mention</code>",
                parse_mode="html",
            )
        else:
            await event.edit(
                "ℹ️ <b>No custom raid text saved — using default:</b>\n\n"
                f"<code>{DEFAULT_RAID_TEXT}</code>\n\n"
                "Use <code>.setraid &lt;text&gt;</code> to save your own.",
                parse_mode="html",
            )

    # ── .delraid / .clrraid ──────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:delraid|clrraid)\s*$"))
    @client.flood_safe
    async def delraid_handler(event):
        """Delete the saved raid text."""
        if _delete_raid_text():
            await event.edit(
                "✅ <b>Raid text deleted.</b> Default text will be used now.",
                parse_mode="html",
            )
        else:
            await event.edit("❌ <b>Failed to delete raid text.</b>", parse_mode="html")

    # ── .raid <count> ────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.raid\s*(\d+)?\s*$"))
    @client.flood_safe
    async def raid_handler(event):
        """Raid the replied user with the saved text."""
        # ── Raid text (default fallback, never blocks a raid) ────────────
        text = _load_raid_text()

        # ── Parse count ──────────────────────────────────────────────────
        count_str = event.pattern_match.group(1)
        try:
            count = int(count_str) if count_str else 10
        except ValueError:
            count = 10
        if count <= 0:
            await event.edit(
                "❌ <b>Count must be a positive integer.</b>",
                parse_mode="html",
            )
            return
        if count > 500:
            await event.edit(
                "❌ <b>Maximum count is 500.</b>",
                parse_mode="html",
            )
            return
        count = safe_cap(count)  # 🛡️ burst cap in safe mode

        # ── Resolve target user ──────────────────────────────────────────
        target = await event.get_reply_message()
        if not target:
            await event.edit(
                "❌ <b>Reply to a user to raid them.</b>",
                parse_mode="html",
            )
            return
        # FIX: Message objects have no get_input_entity() in Telethon.
        try:
            target_entity = await target.get_input_sender()
        except Exception:
            await event.edit(
                "❌ <b>Could not resolve target user.</b>",
                parse_mode="html",
            )
            return

        # ── Resolve chat (avoid Peer ID errors) ──────────────────────────
        try:
            chat = await event.get_input_chat()
        except Exception:
            await event.edit(
                "❌ <b>Could not resolve chat.</b>",
                parse_mode="html",
            )
            return

        # ── Fetch user details for mention ───────────────────────────────
        try:
            user_obj = await client.get_entity(target_entity)
            user_id = user_obj.id
            display_name = (
                getattr(user_obj, "first_name", None)
                or getattr(user_obj, "title", None)
                or "User"
            )
        except Exception:
            await event.edit(
                "❌ <b>Could not fetch target user details.</b>",
                parse_mode="html",
            )
            return

        # ── Build raid message: "<name> <text> <mention>" ────────────────
        raid_msg = _build_raid_message(text, user_id, display_name)

        await event.edit(
            f"💥 <b>Raid started</b> on "
            f'<a href="tg://user?id={user_id}">{_escape_html(display_name)}</a> '
            f"| Count: <b>{count}</b>",
            parse_mode="html",
        )

        # ── Background raid loop ─────────────────────────────────────────
        async def _raid_loop():
            try:
                for _ in range(count):
                    try:
                        await client.send_message(
                            chat, raid_msg, parse_mode="html"
                        )
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)  # 🛡️ auto slow-down
                        await asyncio.sleep(fw.seconds + 1)
                        try:
                            await client.send_message(
                                chat, raid_msg, parse_mode="html"
                            )
                        except Exception:
                            pass
                    except Exception:
                        await asyncio.sleep(0.5)
                    # Small delay between messages to ease rate-limit pressure
                    await safe_sleep(0.3)  # 🛡️ anti-ban pacing
            except asyncio.CancelledError:
                raise
            finally:
                client.stop_processes.pop(f"raid_{event.id}", None)

        task = asyncio.create_task(_raid_loop())
        client.stop_processes[f"raid_{event.id}"] = task

    # ── .drraid  (activate reply-raid) ───────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.drraid\s*$"))
    @client.flood_safe
    async def drraid_handler(event):
        """Activate reply-raid on the replied user."""
        text = _load_raid_text()

        target = await event.get_reply_message()
        if not target:
            await event.edit(
                "❌ <b>Reply to a user to enable reply-raid.</b>",
                parse_mode="html",
            )
            return
        # FIX: Message objects have no get_input_entity() in Telethon.
        try:
            target_entity = await target.get_input_sender()
        except Exception:
            await event.edit(
                "❌ <b>Could not resolve target user.</b>",
                parse_mode="html",
            )
            return

        try:
            user_obj = await client.get_entity(target_entity)
            user_id = user_obj.id
            display_name = (
                getattr(user_obj, "first_name", None)
                or getattr(user_obj, "title", None)
                or "User"
            )
        except Exception:
            await event.edit(
                "❌ <b>Could not fetch target user details.</b>",
                parse_mode="html",
            )
            return

        if user_id in active_reply_raids:
            await event.edit(
                "⚠️ <b>Reply-raid is already active on this user.</b>",
                parse_mode="html",
            )
            return

        active_reply_raids.append(user_id)
        await event.edit(
            f"✅ <b>Reply-raid activated</b> on "
            f'<a href="tg://user?id={user_id}">{_escape_html(display_name)}</a>.\n'
            "Every message they send will be replied to with the raid text.",
            parse_mode="html",
        )

    # ── .stopraid  (deactivate reply-raid) ───────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stopraid\s*$"))
    @client.flood_safe
    async def stopraid_handler(event):
        """Deactivate reply-raid on the replied user (or all if no reply)."""
        target = await event.get_reply_message()
        if not target:
            # No reply → clear every active reply-raid
            if active_reply_raids:
                cleared = len(active_reply_raids)
                active_reply_raids.clear()
                await event.edit(
                    f"✅ <b>Cleared {cleared} active reply-raid(s).</b>",
                    parse_mode="html",
                )
            else:
                await event.edit(
                    "❌ <b>No reply-raid is currently active.</b>",
                    parse_mode="html",
                )
            return

        # FIX: Message objects have no get_input_entity() in Telethon.
        try:
            target_entity = await target.get_input_sender()
        except Exception:
            await event.edit(
                "❌ <b>Could not resolve target user.</b>",
                parse_mode="html",
            )
            return

        try:
            user_obj = await client.get_entity(target_entity)
            user_id = user_obj.id
        except Exception:
            await event.edit(
                "❌ <b>Could not fetch target user details.</b>",
                parse_mode="html",
            )
            return

        if user_id in active_reply_raids:
            active_reply_raids.remove(user_id)
            await event.edit(
                f"✅ <b>Reply-raid stopped</b> on user <code>{user_id}</code>.",
                parse_mode="html",
            )
        else:
            await event.edit(
                "⚠️ <b>Reply-raid was not active on this user.</b>",
                parse_mode="html",
            )

    # ── Reply-raid listener (fires on every incoming message) ────────────
    @client.on(events.NewMessage(incoming=True))
    async def reply_raid_listener(event):
        """Reply with raid text whenever a reply-raid target sends a message."""
        if not active_reply_raids:
            return
        sender_id = event.sender_id
        if sender_id is None or sender_id not in active_reply_raids:
            return

        text = _load_raid_text()

        try:
            sender = await event.get_sender()
            display_name = (
                getattr(sender, "first_name", None)
                or getattr(sender, "title", None)
                or "User"
            )
        except Exception:
            display_name = "User"

        raid_msg = _build_raid_message(text, sender_id, display_name)

        try:
            await event.reply(raid_msg, parse_mode="html")
        except FloodWaitError as fw:
            note_flood(fw.seconds)  # 🛡️ auto slow-down
            await asyncio.sleep(fw.seconds + 1)
            try:
                await event.reply(raid_msg, parse_mode="html")
            except Exception:
                pass
        except Exception:
            pass
COMMANDS_RAID = {
    "description": "Raid Tools",
    "commands": [
        (".raid [n]", "raid replied user — saved text + name (mintu kya kar rhe ho mintu style)"),
        (".setraid <text>", "save raid text ({name} / {tag} placeholders optional)"),
        (".listraid", "view saved raid text"),
        (".delraid / .clrraid", "delete raid text (default text used)"),
        (".drraid", "auto-reply raid on user"),
        (".stopraid", "stop reply-raids"),
    ],
}

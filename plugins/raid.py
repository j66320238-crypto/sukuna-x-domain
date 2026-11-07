# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: RAID v3 — CLEAN REWRITE
############################################################################
"""
Raid v3 — the old error-prone commands (.drraid + its listener) were REMOVED.
Reply-raid is now handled by BotController's `.rrt` / `.rrtb`
(better: saved slots rotation + bots support + `.stoprrt`).

Raid message format:
    • Default  : "<name> <saved text> <mention>"
                 e.g. saved "hi" + target "Mintu"
                      → "Mintu hi Mintu"
    • Template : if the saved text contains {name} / {mention} / {tag} it is
                 used as a template:
                 .setraid what's up {name} → "what's up Mintu"
    • Fallback : works even without .setraid — default text is used.

Commands (user version — bots are handled by BotController's .raidb):
    .raid [n] [gap] [text]   raid — saved slots rotate + reply → victim
    .setraid <text>          raid text save ({name}/{tag} placeholders)
    .listraid                view saved text
    .delraid/.clrraid        delete saved text
Raid message slots (.saverm) are managed by BotController
(`plugins/botcontroller.py`) — `.raid` rotates them (1st → 2nd → 3rd…).
Stop: `.stop` (all) · `.stopraid` / `.raidstop` (raid+RRT) — in BotController.
"""

# ─── Module-level constants & state ───────────────────────────────────────

RAID_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "raid_data.json",
)

# Default raid text — .raid works even if nothing was saved via .setraid
DEFAULT_RAID_TEXT = "hi"


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


# ─── v7.3: .saverm slots — .raid inhe rotate karta hai ─────────────────────
# (slots BotController me .saverm se bhar te hain — same store)

def _load_raid_messages():
    """`.saverm` se saved raid-message slots (list)."""
    try:
        d = load_store("raid_messages")
        if isinstance(d, dict):
            msgs = d.get("messages")
            if isinstance(msgs, list):
                return [str(m) for m in msgs if str(m).strip()]
    except Exception:
        pass
    return []


# ─── HTML helpers ─────────────────────────────────────────────────────────

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
    • otherwise → "<name> <text> <mention>"  (e.g. "Mintu hi Mintu")
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
    # default style: "Mintu hi Mintu"
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

    # ── .raid <count> [gap] [text] ──────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.raid(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def raid_handler(event):
        """Raid v3 — reply OPTIONAL + custom text + saved slots rotation.

        Formats:
          .raid               → 10 msgs from saved slots (run .saverm first)
          .raid 20            → 20 messages
          .raid 20 .5 hello   → 20 messages, 0.5s gap, custom text
          reply + .raid 20    → target gets REPLY + TAG on every message
          text placeholders: {name} / {tag} / {mention}
        """
        # ── Raid text (default fallback, never blocks a raid) ────────────
        text = _load_raid_text()

        # ── Parse <count> [gap] [text] (gap float — ".1" = 0.1s) ─────────
        raw_arg = (event.pattern_match.group(1) or "").strip()
        count = 10
        gap = 0.3
        custom_text = None
        if raw_arg:
            parts = raw_arg.split(maxsplit=2)
            if parts[0].isdigit():
                count = int(parts[0])
                rest = parts[1:]
                if rest:
                    try:
                        gap = float(rest[0])
                        custom_text = (rest[1].strip() or None) if len(rest) > 1 else None
                    except ValueError:
                        gap = 0.3
                        custom_text = " ".join(rest).strip() or None
            else:
                custom_text = raw_arg
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
        gap = max(0.0, min(gap, 60.0))
        count = safe_cap(count)  # 🛡️ burst cap in safe mode

        # ── Resolve target user (reply OPTIONAL) ─────────────────────────
        user_id = None
        display_name = None
        reply_to_id = None
        try:
            target = await event.get_reply_message()
        except Exception:
            target = None
        if target:
            try:
                target_entity = await target.get_input_sender()
                user_obj = await client.get_entity(target_entity)
                user_id = user_obj.id
                display_name = (
                    getattr(user_obj, "first_name", None)
                    or getattr(user_obj, "title", None)
                    or "User"
                )
            except Exception:
                user_id = None
                display_name = None
            # reply + tag BOTH: every raid message replies to the target
            reply_to_id = (getattr(event, "reply_to_msg_id", None)
                            or getattr(target, "id", None))

        # ── Resolve chat (avoid Peer ID errors) ──────────────────────────
        try:
            chat = await event.get_input_chat()
        except Exception:
            await event.edit(
                "❌ <b>Could not resolve chat.</b>",
                parse_mode="html",
            )
            return

        # 🤖 .saverm slots — raid inhe rotate karta hai (1st → 2nd → 3rd…)
        saved_msgs = _load_raid_messages()

        # ── Usage card (jab koi content nahi) ──────
        if user_id is None and custom_text is None and not saved_msgs:
            await event.edit(
                "💥 <b>RAID — Usage:</b>\n"
                "┃ <code>.raid</code> — use saved messages (add via <code>.saverm</code>)\n"
                "┃ <code>.raid 20</code> — 20 times\n"
                "┃ <code>.raid 20 .5 hello</code> — custom text, 0.5s gap\n"
                "┃ reply + <code>.raid 20</code> — target gets reply + tag both\n"
                "┃ placeholders in text: <code>{name}</code> <code>{tag}</code>\n"
                "┃ <code>.raidb 10 .1</code> — BOT raid: 10x, 0.1s gap\n"
                "┃ <code>.rr</code> — reply-raid toggle · <code>.stopraid</code> — stop",
                parse_mode="html",
            )
            return

        # ── Start card ──────
        if user_id is not None:
            whom = f'<a href="tg://user?id={user_id}">{_escape_html(display_name)}</a>'
        else:
            whom = "<b>chat</b>"
        slot_note = f" | slots: <b>{len(saved_msgs)}</b>" if (saved_msgs and custom_text is None) else ""
        mode_note = " | mode: <b>reply + tag</b>" if user_id is not None else ""
        await event.edit(
            f"💥 <b>Raid started</b> on {whom} | Count: <b>{count}</b>"
            f"{slot_note}{mode_note} | gap: <b>{gap}s</b>",
            parse_mode="html",
        )

        # ── Background raid loop ─────────────────────────────────────────
        async def _raid_loop():
            try:
                for i in range(count):
                    # saved slots rotate — har message agli slot se
                    if custom_text is not None:
                        raw = custom_text
                    elif saved_msgs:
                        raw = saved_msgs[i % len(saved_msgs)]
                    else:
                        raw = text
                    if user_id is not None:
                        raid_msg_i = _build_raid_message(raw, user_id, display_name)
                    else:
                        raid_msg_i = _escape_html(raw)
                    try:
                        await client.send_message(
                            chat, raid_msg_i, parse_mode="html",
                            reply_to=reply_to_id,
                        )
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)  # 🛡️ auto slow-down
                        await asyncio.sleep(fw.seconds + 1)
                        try:
                            await client.send_message(
                                chat, raid_msg_i, parse_mode="html",
                                reply_to=reply_to_id,
                            )
                        except Exception:
                            pass
                    except Exception:
                        await asyncio.sleep(0.5)
                    # gap between messages (user-controlled, 0 allowed)
                    if gap > 0:
                        await safe_sleep(gap, floor=0.0)  # 🛡️ pacing
                    else:
                        await asyncio.sleep(0)
            except asyncio.CancelledError:
                raise
            finally:
                client.stop_processes.pop(f"raid_{event.id}", None)

        task = asyncio.create_task(_raid_loop())
        client.stop_processes[f"raid_{event.id}"] = task


COMMANDS_RAID = {
    "description": "Raid Tools",
    "commands": [
        (".raid [n] [gap] [text]", "raid — reply optional (reply+tag), saved slots rotate"),
        (".setraid <text>", "save raid text ({name} / {tag} placeholders optional)"),
        (".listraid", "view saved raid text"),
        (".delraid / .clrraid", "delete raid text (default text is used)"),
        (".saverm <text>", "save a raid message slot — 1st, 2nd, 3rd… (BotController)"),
        (".listrm / .delrm <n> / .delallrm", "slots list / delete (auto-shift) / delete all"),
        (".rr / .rrt", "reply-raid TOGGLE — every message the target sends gets a saved slot as reply (userbot)"),
        (".rrb / .rrtb [slots]", "reply-raid via BOTS — bots send the saved messages (toggle)"),
        (".raidb [slots] <n> [gap] [txt]", "BOT raid — `.raidb 10 .1` = 10x @ 0.1s gap; reply+tag (BotController)"),
        (".stopraid / .raidstop / .raidbstop / .stopraidb", "raid stop commands (BotController)"),
        (".stoprrt / .stoprr", "stop all reply-raid (user + bots)"),
    ],
}

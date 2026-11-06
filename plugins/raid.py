# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: RAID v3 — CLEAN REWRITE
############################################################################
"""
Raid v3 — purane error-wale commands (.drraid + uska listener) HATA diye
gaye hain. Reply-raid ab BotController ka `.rrt` / `.rrtb` karta hai
(better: saved slots rotation + bots support + `.stoprrt`).

Raid message format:
    • Default  : "<name> <saved text> <mention>"
                 e.g. saved "kya kar rhe ho" + target "Mintu"
                      → "Mintu kya kar rhe ho Mintu"
    • Template : saved text me {name} / {mention} / {tag} ho to template:
                 .setraid kya kar rhe ho {name} → "kya kar rhe ho Mintu"
    • Fallback : .setraid ki bina bhi chalega — default "kya kar rhe ho"

Commands (user version — bots ke liye BotController me .raidb hai):
    .raid [n] [text]    raid — saved slots rotate + reply → victim
    .setraid <text>     raid text save ({name}/{tag} placeholders)
    .listraid           saved text dekho
    .delraid/.clrraid   saved text delete
Raid messages (.saverm slots) BotController (`plugins/botcontroller.py`)
manage karta hai — `.raid` inhe rotate karta hai (1st → 2nd → 3rd…).
Stop: `.stop` (sab) · `.stopraid` / `.raidstop` (raid+RRT) — BotController me.
"""

# ─── Module-level constants & state ───────────────────────────────────────

RAID_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "raid_data.json",
)

# Default raid text — .raid works even if nothing was saved via .setraid
DEFAULT_RAID_TEXT = "kya kar rhe ho"


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

    # ── .raid <count> [text] ────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.raid(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def raid_handler(event):
        """Raid v3 — reply OPTIONAL + custom text + saved slots rotation.

        Formats:
          .raid               → 10 msgs, saved slots ya raid text (chat raid)
          .raid 20            → 20 msgs
          .raid 20 hello yaar  → 20 msgs custom text se
          reply + .raid 20    → victim ke naam+mention ke saath
        """
        # ── Raid text (default fallback, never blocks a raid) ────────────
        text = _load_raid_text()

        # ── Parse count ──────────────────────────────────────────────────
        raw_arg = (event.pattern_match.group(1) or "").strip()
        count = 10
        custom_text = None
        if raw_arg:
            parts = raw_arg.split(maxsplit=1)
            if parts[0].isdigit():
                count = int(parts[0])
                custom_text = parts[1].strip() if len(parts) > 1 else None
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
        count = safe_cap(count)  # 🛡️ burst cap in safe mode

        # ── Resolve target user (reply OPTIONAL) ─────────────────────────
        user_id = None
        display_name = None
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
                "┃ <code>.raid</code> — saved messages se (pehle <code>.saverm</code> karo)\n"
                "┃ <code>.raid 20</code> — 20 baar\n"
                "┃ <code>.raid 20 hello</code> — apne text se\n"
                "┃ reply karke <code>.raid 20</code> — us user ka naam+mention lagega\n"
                "┃ text me <code>{name}</code> <code>{tag}</code> use kar sakte ho\n"
                "┃ <code>.raidb</code> — BOTS se raid (BotController)\n"
                "┃ <code>.rrt</code> — reply-raid turbo · <code>.stopraid</code> — stop",
                parse_mode="html",
            )
            return

        # ── Start card ──────
        if user_id is not None:
            whom = f'<a href="tg://user?id={user_id}">{_escape_html(display_name)}</a>'
        else:
            whom = "<b>chat</b>"
        slot_note = f" | slots: <b>{len(saved_msgs)}</b>" if (saved_msgs and custom_text is None) else ""
        await event.edit(
            f"💥 <b>Raid started</b> on {whom} | Count: <b>{count}</b>{slot_note}",
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
                            chat, raid_msg_i, parse_mode="html"
                        )
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)  # 🛡️ auto slow-down
                        await asyncio.sleep(fw.seconds + 1)
                        try:
                            await client.send_message(
                                chat, raid_msg_i, parse_mode="html"
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


COMMANDS_RAID = {
    "description": "Raid Tools",
    "commands": [
        (".raid [n] [text]", "raid — reply optional, saved slots rotate (saverm wale 1st/2nd/3rd…)"),
        (".setraid <text>", "save raid text ({name} / {tag} placeholders optional)"),
        (".listraid", "view saved raid text"),
        (".delraid / .clrraid", "delete raid text (default text used)"),
        (".saverm <text>", "raid message slot save — 1st, 2nd, 3rd… (BotController)"),
        (".listrm / .delrm <n> / .delallrm", "saved slots list / delete (auto-shift) / sab delete"),
        (".rrt / .rrtb", "reply-raid turbo — user + bots (BotController)"),
        (".stopraid / .raidstop / .raidbstop / .stopraidb", "raid stop commands (BotController)"),
    ],
}

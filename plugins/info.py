# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: INFO  (ported from worker_bot/modules/info.py)
############################################################################

# worker_bot/modules/info.py
"""
Info Module — User information, name history, and related utilities.

Commands:
    .id           — Basic user info (ID, name, username, premium).
    .info         — Detailed user info (bio, flags, DC, common chats count).
    .sg           — Name & username history (alias: .namehistory).
    .namehistory  — Alias for .sg.
    .common       — Common chats with the replied user.
    .pfp / .pp    — Fetch and send the replied user's profile photo.
    .uname        — Just the username (or "no username").
    .dc           — Data-centre info of the replied user.
    .me           — Full info about *yourself*.

Designed to be loaded dynamically by ``userbot.py``.
"""



# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────

def _safe(obj, attr, default=None):
    """Buller-proof ``getattr``."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


_DC_LOCATIONS = {
    1: "Miami, USA",
    2: "Amsterdam, Netherlands",
    3: "Miami, USA",
    4: "Amsterdam, Netherlands",
    5: "Singapore",
}


def _format_card(user, full_user=None, detailed=False):
    """Build a nicely-formatted info card string."""

    user_id   = user.id
    fname     = user.first_name or "—"
    lname     = user.last_name  or "—"
    username  = f"@{user.username}" if user.username else "—"
    mention   = f"[{fname or 'User'}](tg://user?id={user_id})"

    is_premium    = _safe(user, "premium", False) or _safe(user, "is_premium", False)
    is_bot        = _safe(user, "bot", False)
    is_verified   = _safe(user, "verified", False)
    is_restricted = _safe(user, "restricted", False)
    is_scam       = _safe(user, "scam", False)
    is_fake       = _safe(user, "fake", False)
    is_support    = _safe(user, "support", False)

    lines = [
        "┌──────────────────────────┐",
        "│   👤  USER INFORMATION   │",
        "└──────────────────────────┘",
        "",
        f"🆔  **ID**         : `{user_id}`",
        f"👤  **First Name** : {fname}",
        f"👥  **Last Name**  : {lname}",
        f"📛  **Username**   : {username}",
        f"🔗  **Mention**    : {mention}",
        f"⭐  **Premium**    : {'✅ Yes' if is_premium else '❌ No'}",
    ]

    if detailed:
        lines += [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"🤖  **Bot**        : {'✅' if is_bot else '❌'}",
            f"✔️  **Verified**   : {'✅' if is_verified else '❌'}",
            f"🚫  **Restricted** : {'⚠️ Yes' if is_restricted else '✅ No'}",
            f"🎭  **Scam**       : {'⚠️ Yes' if is_scam else '✅ No'}",
            f"👻  **Fake**       : {'⚠️ Yes' if is_fake else '✅ No'}",
            f"🛠️  **Support**    : {'✅' if is_support else '❌'}",
        ]

        if full_user:
            about = _safe(full_user, "about", None) or "—"
            lines.append(f"📝  **Bio**        : {about}")

            common_count = _safe(full_user, "common_chats_count", 0)
            lines.append(f"💬  **Common Chats**: {common_count}")

            has_photo = bool(_safe(full_user, "profile_photo", None))
            lines.append(f"🖼️  **Photo**      : {'✅' if has_photo else '❌'}")

            calls_ok  = _safe(full_user, "phone_calls_available", False)
            calls_priv = _safe(full_user, "phone_calls_private", False)
            lines.append(f"📞  **Calls OK**   : {'✅' if calls_ok else '❌'}")
            lines.append(f"🔒  **Calls Priv** : {'✅' if calls_priv else '❌'}")

            settings = _safe(full_user, "settings", None)
            if settings:
                auto_arch = _safe(settings, "auto_archived", False)
                lines.append(f"🗄️  **Auto-Archive**: {'✅' if auto_arch else '❌'}")

        # DC
        photo = _safe(user, "photo", None)
        dc_id = _safe(photo, "dc_id", None) if photo else None
        if dc_id:
            loc = _DC_LOCATIONS.get(dc_id, "Unknown")
            lines.append(f"🌍  **DC**         : `{dc_id}` ({loc})")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


async def _resolve_target(event):
    """Return ``(target_input_entity, reply_msg)`` or ``(None, None)``.

    FIX: ``Message`` objects have no ``get_input_entity()`` method in
    Telethon — that call always raised AttributeError and made every
    command reply "Reply to a user's message first".  The correct
    method is ``get_input_sender()``.
    """
    reply = await event.get_reply_message()
    if not reply:
        return None, None
    try:
        target = await reply.get_input_sender()
    except Exception:
        return None, reply
    return target, reply


async def _fetch_full_user(client, target):
    """Best-effort ``GetFullUserRequest`` — never raises."""
    try:
        result = await client(GetFullUserRequest(target))
        return result.full_user if result else None
    except FloodWaitError as fe:
        await asyncio.sleep(fe.seconds + 1)
        try:
            result = await client(GetFullUserRequest(target))
            return result.full_user if result else None
        except Exception:
            return None
    except Exception:
        return None


# ── .sg internals (lookup bot is internal — NEVER shown in chat) ────────
_SG_BOT = "@SangMata_BOT"

_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HTML_LINK_RE = re.compile(r'<a\s+href="[^"]+">([^<]+)</a>')
# branding / promo lines that get stripped from the raw result
_BRAND_LINE_PAT = re.compile(
    r"(?i)(sang[\s_-]?mata|forward[\s_-]?bot|powered\s+by|t\.me/\S+)"
)


def _clean_history_text(text):
    """Strip bot branding / promo links from raw history text.

    Keeps the actual data (names, usernames, dates), removes lines that
    reveal which service the data came from.
    """
    if not text:
        return ""
    out = []
    for line in text.splitlines():
        line = _MD_LINK_RE.sub(r"\1", line)          # [x](url) → x
        line = _HTML_LINK_RE.sub(r"\1", line)        # <a>x</a> → x
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue
        if _BRAND_LINE_PAT.search(stripped):
            continue  # drop branding / promo lines
        out.append(stripped)
    # collapse consecutive blank lines
    cleaned = []
    for ln in out:
        if ln == "" and (not cleaned or cleaned[-1] == ""):
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).strip()


# module-level busy flag so two .sg queries don't fight over the conversation
_sg_busy = {"on": False}

# transient "please wait" notices that should NOT be delivered as history
_WAIT_NOTICE_RE = re.compile(
    r"(?i)(please\s+wait|wait\s+a\s+(second|moment|bit|sec)|processing|"
    r"loading|sabar|tunggu|moment\s please)"
)


def _is_wait_notice(text):
    """True for short single-line 'please wait' pings (not real data)."""
    t = (text or "").strip()
    if not t or "\n" in t or len(t) > 90:
        return False
    return bool(_WAIT_NOTICE_RE.search(t))


# ──────────────────────────────────────────────────────────────
#  Register
# ──────────────────────────────────────────────────────────────

def register_info(client):
    """Register every command exposed by this module."""

    # ── .id ────────────────────────────────────────────────
    @client.flood_safe
    async def _id_handler(event):
        try:
            chat = await event.get_input_chat()
            target, reply = await _resolve_target(event)
            if not target:
                await event.reply("❌ **Reply to a user's message first.**")
                return

            try:
                user = await client.get_entity(target)
            except Exception as e:
                await event.reply(f"❌ **Could not fetch user:**\n`{e}`")
                return

            await event.reply(_format_card(user, detailed=False),
                              link_preview=False)
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ── .info ──────────────────────────────────────────────
    @client.flood_safe
    async def _info_handler(event):
        try:
            chat = await event.get_input_chat()
            target, reply = await _resolve_target(event)
            if not target:
                await event.reply("❌ **Reply to a user's message first.**")
                return

            try:
                user = await client.get_entity(target)
            except Exception as e:
                await event.reply(f"❌ **Could not fetch user:**\n`{e}`")
                return

            full_user = await _fetch_full_user(client, target)
            await event.reply(_format_card(user, full_user, detailed=True),
                              link_preview=False)
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ── .sg  /  .namehistory ──────────────────────────────
    @client.flood_safe
    async def _sg_handler(event):
        status_msg = None
        try:
            chat = await event.get_input_chat()
            target, reply = await _resolve_target(event)
            if not target:
                await event.reply("❌ **Reply to a user's message first.**")
                return

            try:
                user = await client.get_entity(target)
                user_id = str(user.id)
                display = getattr(user, "first_name", None) \
                    or getattr(user, "title", None) or "User"
            except Exception as e:
                await event.reply(f"❌ **Could not fetch user:**\n`{e}`")
                return

            if _sg_busy["on"]:
                await event.reply(
                    "⏳ **A query is already running — wait a moment and try again.**")
                return
            _sg_busy["on"] = True

            try:
                status_msg = await event.reply("🔍 **Checking name history …**")

                # resolve the internal lookup service (never shown in chat)
                try:
                    sg_entity = await client.get_entity(_SG_BOT)
                except Exception:
                    sg_entity = _SG_BOT

                texts = []
                media_msgs = []

                async def _collect(conv, first_timeout=14, more_timeout=3.5,
                                   max_msgs=8):
                    """Collect every reply message (text + media)."""
                    got_texts, got_media = [], []
                    timeout = first_timeout
                    while len(got_texts) + len(got_media) < max_msgs:
                        try:
                            resp = await conv.get_response(timeout=timeout)
                        except asyncio.TimeoutError:
                            break
                        timeout = more_timeout
                        if resp is None:
                            continue
                        body = (resp.message or "").strip()
                        if _is_wait_notice(body):
                            continue  # transient "please wait" ping — skip
                        if resp.media is not None and not body:
                            got_media.append(resp)
                        elif body:
                            got_texts.append(body)
                    return got_texts, got_media

                try:
                    # FIX: enter the conversation FIRST, then send the query —
                    # the old code sent the ID before listening, so fast replies
                    # were missed and never copied back to the chat.
                    async with client.conversation(sg_entity, timeout=60) as conv:
                        await conv.send_message(user_id)
                        texts, media_msgs = await _collect(conv)

                        joined = "\n".join(texts).lower()
                        needs_start = (
                            ("/start" in joined and "history" not in joined
                             and "name" not in joined
                             and "username" not in joined)
                            or (not texts and not media_msgs)
                        )
                        if needs_start:
                            # service wants /start first → do it & retry once
                            try:
                                await conv.send_message("/start")
                                await asyncio.sleep(2.0)
                                await conv.send_message(user_id)
                                texts, media_msgs = await _collect(conv)
                            except Exception:
                                pass
                except YouBlockedUserError:
                    await status_msg.edit(
                        "❌ **History service is blocked — unblock it and try again.**")
                    return
                except asyncio.TimeoutError:
                    await status_msg.edit(
                        "⏰ **History service timed out — try again in a bit.**")
                    return
                except Exception:
                    await status_msg.edit(
                        "❌ **Could not reach the history service — try again in a bit.**")
                    return

                # ── "no records" style replies ──────────────────────────
                joined = "\n".join(texts).lower()
                if texts and any(
                        k in joined for k in
                        ("no records", "not found", "tidak ditemukan",
                         "no data", "doesn't have")):
                    await status_msg.edit(
                        f"❓ **No history records found for** {display}.")
                    return
                if not texts and not media_msgs:
                    await status_msg.edit(
                        "⏰ **History service timeout — thodi der baad try karo.**")
                    return

                # ── deliver as OUR OWN copied message (no source shown) ──
                header = (
                    f"📜 **Name History** — "
                    f"[{display}](tg://user?id={user.id})\n"
                    f"🆔 `{user.id}`"
                )
                cleaned = [c for c in (_clean_history_text(t) for t in texts)
                           if c.strip()]
                try:
                    await status_msg.delete()
                except Exception:
                    pass
                delivered = False
                if cleaned:
                    body = "\n\n".join(cleaned)[:3500]
                    try:
                        await throttle("send")
                        await client.send_message(
                            chat, f"{header}\n\n{body}", link_preview=False)
                        delivered = True
                    except Exception:
                        pass
                for m in media_msgs[:3]:
                    try:
                        await throttle("send")
                        await client.send_file(
                            chat, m,
                            caption=header if not delivered else None)
                        delivered = True
                    except Exception:
                        pass
                if not delivered:
                    await event.reply(
                        "❌ **History fetch failed — thodi der baad try karo.**")
            finally:
                _sg_busy["on"] = False
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                if status_msg:
                    await status_msg.edit(f"❌ **Unexpected error:**\n`{e}`")
                else:
                    await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ── .common ────────────────────────────────────────────
    @client.flood_safe
    async def _common_handler(event):
        try:
            chat = await event.get_input_chat()
            target, reply = await _resolve_target(event)
            if not target:
                await event.reply("❌ **Reply to a user's message first.**")
                return

            try:
                user = await client.get_entity(target)
            except Exception as e:
                await event.reply(f"❌ **Could not fetch user:**\n`{e}`")
                return

            status_msg = await event.reply("⏳ **Fetching common chats …**")

            try:
                result = await client(
                    GetCommonChatsRequest(user.id, max_id=0, limit=100)
                )
                chats = result.chats if result else []

                if not chats:
                    await status_msg.edit(
                        f"🤷 **No common chats with** `{user.id}`."
                    )
                    return

                lines = [f"💬 **Common Chats with** `{user.id}`", ""]
                for c in chats[:30]:
                    title = _safe(c, "title", "Untitled")
                    cid   = _safe(c, "id", 0)
                    lines.append(f"• **{title}**  (`{cid}`)")

                if len(chats) > 30:
                    lines.append(f"\n_…and {len(chats) - 30} more._")

                await status_msg.edit("\n".join(lines), link_preview=False)
            except Exception as e:
                await status_msg.edit(
                    f"❌ **Failed to fetch common chats:**\n`{e}`"
                )
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ── .pfp / .pp ─────────────────────────────────────────
    @client.flood_safe
    async def _pfp_handler(event):
        try:
            chat = await event.get_input_chat()
            target, reply = await _resolve_target(event)
            if not target:
                await event.reply("❌ **Reply to a user's message first.**")
                return

            try:
                user = await client.get_entity(target)
            except Exception as e:
                await event.reply(f"❌ **Could not fetch user:**\n`{e}`")
                return

            try:
                photos = await client.get_profile_photos(user)
            except Exception as e:
                await event.reply(f"❌ **Cannot fetch photos:**\n`{e}`")
                return

            if not photos:
                await event.reply("❌ **This user has no profile photo.**")
                return

            await event.reply(file=photos[0])
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ── .uname ─────────────────────────────────────────────
    @client.flood_safe
    async def _uname_handler(event):
        try:
            chat = await event.get_input_chat()
            target, reply = await _resolve_target(event)
            if not target:
                await event.reply("❌ **Reply to a user's message first.**")
                return

            try:
                user = await client.get_entity(target)
            except Exception as e:
                await event.reply(f"❌ **Could not fetch user:**\n`{e}`")
                return

            if user.username:
                await event.reply(
                    f"📛 **Username:** @{user.username}\n🆔 **ID:** `{user.id}`"
                )
            else:
                await event.reply(
                    f"❌ **No username set.**\n🆔 **ID:** `{user.id}`"
                )
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ── .dc ────────────────────────────────────────────────
    @client.flood_safe
    async def _dc_handler(event):
        try:
            chat = await event.get_input_chat()
            target, reply = await _resolve_target(event)
            if not target:
                await event.reply("❌ **Reply to a user's message first.**")
                return

            try:
                user = await client.get_entity(target)
            except Exception as e:
                await event.reply(f"❌ **Could not fetch user:**\n`{e}`")
                return

            photo = _safe(user, "photo", None)
            dc_id = _safe(photo, "dc_id", None) if photo else None

            if dc_id:
                loc = _DC_LOCATIONS.get(dc_id, "Unknown")
                await event.reply(
                    "🌍 **Data-Centre Info**\n\n"
                    f"🆔 **User ID** : `{user.id}`\n"
                    f"🖥️ **DC ID**   : `{dc_id}`\n"
                    f"📍 **Location**: {loc}",
                    link_preview=False,
                )
            else:
                await event.reply(
                    f"❌ **No DC info available.**\n🆔 **ID:** `{user.id}`"
                )
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ── .me ────────────────────────────────────────────────
    @client.flood_safe
    async def _me_handler(event):
        try:
            chat = await event.get_input_chat()
            me = await client.get_me()
            full_user = await _fetch_full_user(client, "me")
            await event.reply(_format_card(me, full_user, detailed=True),
                              link_preview=False)
        except FloodWaitError as fe:
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            try:
                await event.reply(f"❌ **Unexpected error:**\n`{e}`")
            except Exception:
                pass

    # ───────────────────────────────────────────────────────
    #  Wire-up
    # ───────────────────────────────────────────────────────
    _PAT = {
        _id_handler:     [r"^\.id$",          r"^\.id\s"],
        _info_handler:   [r"^\.info$",        r"^\.info\s"],
        _sg_handler:     [r"^\.sg$",          r"^\.sg\s",
                          r"^\.namehistory$", r"^\.namehistory\s"],
        _common_handler: [r"^\.common$",      r"^\.common\s"],
        _pfp_handler:    [r"^\.pfp$",         r"^\.pfp\s",
                          r"^\.pp$",          r"^\.pp\s"],
        _uname_handler:  [r"^\.uname$",       r"^\.uname\s"],
        _dc_handler:     [r"^\.dc$",          r"^\.dc\s"],
        _me_handler:     [r"^\.me$",          r"^\.me\s"],
    }

    for handler, patterns in _PAT.items():
        for pat in patterns:
            client.add_event_handler(
                handler,
                events.NewMessage(pattern=pat, outgoing=True),
            )

    # Log
    try:
        client._logger.info(  # type: ignore[attr-defined]
            "[info] Registered %d commands.", len(_PAT)
        )
    except Exception:
        pass
COMMANDS_INFO = {
    "description": "User Info & Lookup",
    "commands": [
        (".id", "quick user card (reply)"),
        (".info", "detailed user card (reply)"),
        (".sg / .namehistory", "name & username history (reply)"),
        (".common", "common chats (reply)"),
        (".pfp / .pp", "send profile photo (reply)"),
        (".uname", "just the username (reply)"),
        (".dc", "user's data-centre (reply)"),
        (".me", "full info about yourself"),
    ],
}

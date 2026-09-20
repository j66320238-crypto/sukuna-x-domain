# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
# SECTION: EVENTS — welcome / goodbye messages + word blacklist
#   .welcome  .setwelcome  .goodbye  .setgoodbye
#   .blacklist add/del/list/on/off
# Works when your account is an admin in the group (it then sees the joins).
# ============================================================================
COMMANDS_EVENTS = {
    "description": "Welcome · Goodbye · Blacklist (8)",
    "commands": [
        (".welcome on|off", "greet new members of this group"),
        (".setwelcome <text>", "custom welcome text ({mention} {chat} {count})"),
        (".goodbye on|off", "farewell message when someone leaves"),
        (".setgoodbye <text>", "custom goodbye text"),
        (".blacklist on|off", "auto-delete banned words here"),
        (".blacklist add <words>", "add words (space separated)"),
        (".blacklist del <word>", "remove a word"),
        (".blacklist list", "show banned words"),
    ],
}

_EV_STORE = load_store("events", {})
_EV_STORE.setdefault("welcome", {})
_EV_STORE.setdefault("goodbye", {})
_EV_STORE.setdefault("blacklist", {})

_DEF_WELCOME = (
    "✦ Welcome, {mention}! 🎉\n"
    "┃ You joined **{chat}**\n"
    "┃ Member count: `{count}`  ·  Enjoy your stay! 💜"
)
_DEF_GOODBYE = "👋 **{name}** left the chat. We'll miss you!"


def _ev_key(chat_id) -> str:
    return str(chat_id)


async def _mention_html(client, user) -> str:
    name = " ".join(
        x for x in [getattr(user, "first_name", "") or "", getattr(user, "last_name", "") or ""]
        if x
    ).strip() or "User"
    return f'<a href="tg://user?id={getattr(user, "id", 0)}">{html.escape(name)}</a>'


async def _fill_template(template: str, mention: str, name: str, chat_title: str, count) -> str:
    return (template
            .replace("{mention}", mention)
            .replace("{name}", html.escape(name or "User"))
            .replace("{chat}", html.escape(chat_title or "the group"))
            .replace("{count}", str(count)))


def register_events(client):
    """Welcome / goodbye / blacklist."""

    # ================== CONFIG COMMANDS ==================

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.welcome(?:\s+(on|off))?$"))
    @client.flood_safe
    async def _welcome_toggle(event):
        if event.is_private:
            return await event.edit("❌ Use `.welcome` inside a group.")
        key = _ev_key(event.chat_id)
        arg = (event.pattern_match.group(1) or "").lower()
        cfg = _EV_STORE["welcome"].setdefault(key, {"on": False, "text": _DEF_WELCOME})
        if arg == "on":
            cfg["on"] = True
        elif arg == "off":
            cfg["on"] = False
        else:
            arg = "on" if cfg["on"] else "off"
        save_store("events", _EV_STORE)
        await event.edit(
            "✦ ━━━〔 👋 WELCOME 〕━━━ ✦\n"
            f"┃ Status : **{arg.upper()}**\n"
            f"┃ Text   : {cfg.get('text', _DEF_WELCOME)[:140]}\n"
            "┃ Tips   : `{mention}` `{chat}` `{count}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setwelcome\s+([\s\S]+)$"))
    @client.flood_safe
    async def _set_welcome(event):
        key = _ev_key(event.chat_id)
        cfg = _EV_STORE["welcome"].setdefault(key, {"on": False, "text": _DEF_WELCOME})
        cfg["text"] = event.pattern_match.group(1).strip()[:600]
        save_store("events", _EV_STORE)
        await event.edit(
            "✦ ━━━〔 ✅ WELCOME TEXT SET 〕━━━ ✦\n"
            f"┃ {cfg['text'][:200]}\n"
            "┃ ℹ️ Turn on with `.welcome on`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.goodbye(?:\s+(on|off))?$"))
    @client.flood_safe
    async def _goodbye_toggle(event):
        if event.is_private:
            return await event.edit("❌ Use `.goodbye` inside a group.")
        key = _ev_key(event.chat_id)
        arg = (event.pattern_match.group(1) or "").lower()
        cfg = _EV_STORE["goodbye"].setdefault(key, {"on": False, "text": _DEF_GOODBYE})
        if arg == "on":
            cfg["on"] = True
        elif arg == "off":
            cfg["on"] = False
        else:
            arg = "on" if cfg["on"] else "off"
        save_store("events", _EV_STORE)
        await event.edit(
            "✦ ━━━〔 👋 GOODBYE 〕━━━ ✦\n"
            f"┃ Status : **{arg.upper()}**\n"
            f"┃ Text   : {cfg.get('text', _DEF_GOODBYE)[:140]}\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setgoodbye\s+([\s\S]+)$"))
    @client.flood_safe
    async def _set_goodbye(event):
        key = _ev_key(event.chat_id)
        cfg = _EV_STORE["goodbye"].setdefault(key, {"on": False, "text": _DEF_GOODBYE})
        cfg["text"] = event.pattern_match.group(1).strip()[:600]
        save_store("events", _EV_STORE)
        await event.edit(
            "✦ ━━━〔 ✅ GOODBYE TEXT SET 〕━━━ ✦\n"
            f"┃ {cfg['text'][:200]}\n"
            "┃ ℹ️ Turn on with `.goodbye on`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.blacklist(?:\s+(.*))?$"))
    @client.flood_safe
    async def _blacklist(event):
        if event.is_private:
            return await event.edit("❌ Use `.blacklist` inside a group.")
        key = _ev_key(event.chat_id)
        cfg = _EV_STORE["blacklist"].setdefault(key, {"on": False, "words": []})
        raw = (event.pattern_match.group(1) or "").strip()
        parts = raw.split(None, 1)
        sub = parts[0].lower() if parts else "list"
        rest = parts[1].strip() if len(parts) > 1 else ""

        if sub == "add":
            if not rest:
                return await event.edit("❌ Usage: `.blacklist add word1 word2`")
            new_words = [w.lower()[:40] for w in rest.split() if w.strip()]
            for w in new_words:
                if w not in cfg["words"]:
                    cfg["words"].append(w)
            cfg["on"] = True
            save_store("events", _EV_STORE)
            return await event.edit(
                f"🚫 Added **{len(new_words)}** word(s). Blacklist is **ON**.\n"
                f"┃ Words: `{'`, `'.join(cfg['words'][:20])}`"
            )
        if sub == "del":
            if not rest:
                return await event.edit("❌ Usage: `.blacklist del word`")
            for w in rest.split():
                if w.lower() in cfg["words"]:
                    cfg["words"].remove(w.lower())
            save_store("events", _EV_STORE)
            return await event.edit(f"✅ Removed. Words now: `{len(cfg['words'])}`")
        if sub == "on":
            cfg["on"] = True
            save_store("events", _EV_STORE)
            return await event.edit("🚫 **Blacklist ON** — banned words get deleted.")
        if sub == "off":
            cfg["on"] = False
            save_store("events", _EV_STORE)
            return await event.edit("✅ **Blacklist OFF**")
        if sub == "clear":
            cfg["words"].clear()
            save_store("events", _EV_STORE)
            return await event.edit("🗑️ All banned words cleared.")
        # default → list
        if not cfg["words"]:
            return await event.edit("📭 Blacklist is empty.\n💡 `.blacklist add spam ads`")
        await event.edit(
            "✦ ━━━〔 🚫 BLACKLIST 〕━━━ ✦\n"
            f"┃ Status : **{'ON' if cfg['on'] else 'OFF'}**\n"
            f"┃ Words  : `{'`, `'.join(cfg['words'][:40])}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    # ================== JOIN / LEAVE LISTENER ==================

    @client.on(events.ChatAction(func=lambda e: (
        e.user_joined or e.user_added or e.user_left or e.user_kicked
    )))
    async def _welcome_watcher(event):
        try:
            key = _ev_key(event.chat_id)
            joined = bool(event.user_joined or event.user_added)
            cfg = _EV_STORE["welcome" if joined else "goodbye"].get(key)
            if not cfg or not cfg.get("on"):
                return
            users = []
            if event.user_joined or event.user_left or event.user_kicked:
                u = await event.get_user()
                users = [u] if u else []
            else:  # someone added others
                users = await event.get_users()
                users = [u for u in users if not getattr(u, "bot", False)]
            if not users:
                return
            chat = await event.get_chat()
            title = getattr(chat, "title", None) or "the group"
            count = getattr(chat, "participants_count", None) or "?"
            for user in users[:5]:
                mention = await _mention_html(client, user)
                name = getattr(user, "first_name", "") or "User"
                text = await _fill_template(cfg.get("text") or (
                    _DEF_WELCOME if joined else _DEF_GOODBYE
                ), mention, name, title, count)
                await throttle_chat(event.chat_id)
                await client.send_message(
                    event.chat_id, text, parse_mode="html", link_preview=False
                )
        except Exception as exc:
            log.debug("welcome/goodbye listener: %s", exc)

    # ================== BLACKLIST LISTENER ==================

    @client.on(events.NewMessage(incoming=True))
    async def _blacklist_watcher(event):
        try:
            if event.is_private:
                return
            cfg = _EV_STORE["blacklist"].get(_ev_key(event.chat_id))
            if not cfg or not cfg.get("on") or not cfg["words"]:
                return
            text = (event.raw_text or "").lower()
            if not text:
                return
            for word in cfg["words"]:
                if word in text:
                    await event.delete()
                    log.info("Blacklist: deleted message with “%s”", word)
                    return
        except Exception:
            pass

    log.info("Event commands: welcome, goodbye, blacklist")

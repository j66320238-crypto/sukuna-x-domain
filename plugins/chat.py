# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
# SECTION: CHAT — auto-filters, saved notes (snips) & sed text fixing
#   .filter  .stopfilter  .filters  .delallfilters
#   .savenote  .note  .notes  .delnote  .delallnotes
#   .sed / s/old/new/
# Inspired by Ultroid "filters" + CatUserbot "snips" + classic sed plugin.
# ============================================================================
COMMANDS_CHAT = {
    "description": "Chat Filters & Notes (10)",
    "commands": [
        (".filter <word>", "reply to a msg → auto-reply when <word> appears"),
        (".stopfilter <word>", "remove one filter in this chat"),
        (".filters", "list filters of this chat"),
        (".delallfilters", "delete ALL filters of this chat"),
        (".savenote <name>", "reply to a msg → save it as a note"),
        (".note <name>", "send a saved note"),
        (".notes", "list saved notes here"),
        (".delnote <name>", "delete one note"),
        (".delallnotes", "delete all notes here"),
        (".sed s/old/new/", "reply → fix a typo in your own message"),
    ],
}

_CHAT_STORE = load_store("chat", {})
_CHAT_STORE.setdefault("filters", {})
_CHAT_STORE.setdefault("notes", {})


def _chat_key(chat_id) -> str:
    return str(chat_id)


def register_chat(client):
    """Per-chat filters + notes + sed."""

    # ================== FILTERS ==================

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.filter\s+([\s\S]+)$"))
    @client.flood_safe
    async def _filter_add(event):
        if not event.is_reply:
            return await event.edit("❌ Reply to the message I should send back.")
        keyword = event.pattern_match.group(1).strip()
        if not keyword:
            return await event.edit("❌ Usage: `.filter <word>` (as a reply)")
        replied = await event.get_reply_message()
        body = (replied.raw_text or "").strip()
        if not body:
            return await event.edit(
                "❌ The replied message has no text — filters store text only.\n"
                "💡 For pictures/videos use `.save` (Saved Messages)."
            )
        key = _chat_key(event.chat_id)
        _CHAT_STORE["filters"].setdefault(key, {})[keyword.lower()] = {
            "word": keyword,
            "text": body,
        }
        save_store("chat", _CHAT_STORE)
        await event.edit(
            "✦ ━━━〔 🎯 FILTER SAVED 〕━━━ ✦\n"
            f"┃ 🔑 Trigger : `{keyword}`\n"
            f"┃ 💬 Reply   : {body[:120]}\n"
            "┃ ℹ️ Works in this chat only.\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stopfilter\s+([\s\S]+)$"))
    @client.flood_safe
    async def _filter_del(event):
        keyword = event.pattern_match.group(1).strip().lower()
        key = _chat_key(event.chat_id)
        bucket = _CHAT_STORE["filters"].get(key, {})
        if keyword not in bucket:
            return await event.edit(f"⚠️ No filter named `{keyword}` in this chat.")
        bucket.pop(keyword, None)
        save_store("chat", _CHAT_STORE)
        await event.edit(f"🗑️ Filter `{keyword}` removed.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.filters$"))
    @client.flood_safe
    async def _filters_list(event):
        bucket = _CHAT_STORE["filters"].get(_chat_key(event.chat_id), {})
        if not bucket:
            return await event.edit("📭 No filters in this chat yet.\n💡 `.filter <word>` (as reply)")
        lines = ["✦ ━━━〔 🎯 FILTERS 〕━━━ ✦"]
        for item in bucket.values():
            lines.append(f"┃ • `{item['word']}` → {item['text'][:60]}")
        lines.append("✦ ━━━━━━━━━━━━━━━━━━━━━ ✦")
        lines.append("_Remove:_ `.stopfilter <word>` · _Clear all:_ `.delallfilters`")
        await event.edit("\n".join(lines), link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.delallfilters$"))
    @client.flood_safe
    async def _filters_clear(event):
        key = _chat_key(event.chat_id)
        n = len(_CHAT_STORE["filters"].get(key, {}))
        _CHAT_STORE["filters"].pop(key, None)
        save_store("chat", _CHAT_STORE)
        await event.edit(f"🗑️ Removed **{n}** filter(s) from this chat.")

    # ================== NOTES (snips) ==================

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.savenote\s+(\S+)$"))
    @client.flood_safe
    async def _note_add(event):
        if not event.is_reply:
            return await event.edit("❌ Reply to the message you want to save.")
        name = event.pattern_match.group(1).strip().lower()[:32]
        replied = await event.get_reply_message()
        body = (replied.raw_text or "").strip()
        if not body:
            return await event.edit(
                "❌ Only text notes are supported (no text in that message).\n"
                "💡 Media? Use `.save` → goes to Saved Messages."
            )
        _CHAT_STORE["notes"].setdefault(_chat_key(event.chat_id), {})[name] = body
        save_store("chat", _CHAT_STORE)
        await event.edit(
            f"✦ ━━━〔 📝 NOTE SAVED 〕━━━ ✦\n"
            f"┃ 🏷 Name : `{name}`\n"
            f"┃ 💬 {body[:150]}\n"
            f"┃ ℹ️ Send it: `.note {name}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.note\s+(\S+)$"))
    @client.flood_safe
    async def _note_send(event):
        name = event.pattern_match.group(1).strip().lower()
        body = _CHAT_STORE["notes"].get(_chat_key(event.chat_id), {}).get(name)
        if body is None:
            return await event.edit(f"⚠️ No note named `{name}` here.\n💡 `.notes` to list.")
        await event.delete()
        await throttle_chat(event.chat_id)
        await client.send_message(
            await event.get_input_chat(), body, reply_to=event.reply_to_msg_id,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.notes$"))
    @client.flood_safe
    async def _notes_list(event):
        bucket = _CHAT_STORE["notes"].get(_chat_key(event.chat_id), {})
        if not bucket:
            return await event.edit("📭 No notes here yet.\n💡 Reply + `.savenote <name>`")
        lines = ["✦ ━━━〔 📝 SAVED NOTES 〕━━━ ✦"]
        for name, body in bucket.items():
            lines.append(f"┃ • `{name}` — {body[:50]}")
        lines.append("✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦")
        await event.edit("\n".join(lines), link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.delnote\s+(\S+)$"))
    @client.flood_safe
    async def _note_del(event):
        name = event.pattern_match.group(1).strip().lower()
        bucket = _CHAT_STORE["notes"].get(_chat_key(event.chat_id), {})
        if name not in bucket:
            return await event.edit(f"⚠️ No note named `{name}`.")
        bucket.pop(name, None)
        save_store("chat", _CHAT_STORE)
        await event.edit(f"🗑️ Note `{name}` deleted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.delallnotes$"))
    @client.flood_safe
    async def _notes_clear(event):
        key = _chat_key(event.chat_id)
        n = len(_CHAT_STORE["notes"].get(key, {}))
        _CHAT_STORE["notes"].pop(key, None)
        save_store("chat", _CHAT_STORE)
        await event.edit(f"🗑️ Removed **{n}** note(s) from this chat.")

    # ================== AUTO-REPLY LISTENER ==================

    @client.on(events.NewMessage(incoming=True))
    async def _filter_listener(event):
        try:
            text = (event.raw_text or "").lower()
            if not text:
                return
            bucket = _CHAT_STORE["filters"].get(_chat_key(event.chat_id))
            if not bucket:
                return
            for key, item in bucket.items():
                if key in text:
                    await throttle_chat(event.chat_id)
                    await event.reply(item["text"])
                    return
        except Exception:
            pass

    # ================== SED (fix your own typo) ==================

    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^(?:\.sed\s+)?s/([^/\n]+)/([^/\n]*)/?$"))
    @client.flood_safe
    async def _sed(event):
        old, new = event.pattern_match.group(1), event.pattern_match.group(2)
        if not event.is_reply:
            return await event.edit(
                "❌ Reply to your message with `s/old/new/`\n"
                "💡 Example: `s/teh/the/`"
            )
        target = await event.get_reply_message()
        if not target.out:
            return await event.edit("❌ I can only fix **your own** messages.")
        body = target.raw_text or ""
        if old not in body:
            return await event.edit(f"⚠️ `{old}` not found in that message.")
        fixed = body.replace(old, new, 1)
        await client.edit_message(target.chat_id, target.id, fixed)
        await event.delete()

    log.info("Chat commands: filters, notes, sed")

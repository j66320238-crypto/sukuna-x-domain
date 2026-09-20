# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: CHAT UTILITIES  (v5.3 — ported from Ultroid extra.py)
#  .del .copy .edit .reply — fast message utilities
#  NOTE: no imports here — everything comes from the header.
# ============================================================================


def register_util(client):

    # ---- .del — delete the replied message (or yourself) -------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.del$"))
    @client.flood_safe
    async def _del(event):
        reply = await event.get_reply_message()
        if reply is not None:
            try:
                await reply.delete()
            except Exception:
                pass
        try:
            await event.delete()
        except Exception:
            pass

    # ---- .copy — duplicate the replied message right below it --------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.copy$"))
    @client.flood_safe
    async def _copy(event):
        reply = await event.get_reply_message()
        if reply is None:
            return await event.edit("↩️ Reply to any message with `.copy`.")
        await throttle("send")
        try:
            await reply.reply(reply)
        except Exception as e:
            return await event.edit(f"⚠️ Couldn't copy: `{e}`")
        try:
            await event.delete()
        except Exception:
            pass

    # ---- .edit <text> — edit your previous message (or the replied one) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.edit(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _edit(event):
        new_text = (event.pattern_match.group(1) or "").strip()
        if not new_text:
            return await event.edit("✏️ Usage: `.edit <new text>` (reply to your own message, or it edits your previous one).")
        reply = await event.get_reply_message()
        if reply is not None and getattr(reply, "out", False) and reply.text:
            try:
                await throttle("edit")
                await client.edit_message(event.chat_id, reply.id, new_text)
                await event.delete()
            except Exception as e:
                await event.edit(f"⚠️ Can't edit that message: `{e}`")
            return
        # no reply → edit YOUR previous message
        found = None
        try:
            i = 0
            async for msg in client.iter_messages(event.chat_id, from_user="me", limit=3):
                i += 1
                if i == 2:
                    found = msg
                    break
        except Exception:
            pass
        if found is None:
            return await event.edit("⚠️ No previous message found to edit.")
        try:
            await throttle("edit")
            await client.edit_message(event.chat_id, found.id, new_text)
            await event.delete()
        except Exception as e:
            await event.edit(f"⚠️ Couldn't edit: `{e}`")

    # ---- .reply — send your previous message again as a reply --------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.reply$"))
    @client.flood_safe
    async def _reply_again(event):
        if not event.reply_to_msg_id:
            try:
                await event.delete()
            except Exception:
                pass
            return
        prev = None
        try:
            msgs = await client.get_messages(event.chat_id, limit=1, max_id=event.id)
            if msgs:
                prev = msgs[0]
        except Exception:
            pass
        if prev is None:
            return await event.edit("⚠️ No previous message found to reply with.")
        await throttle("send")
        try:
            await client.send_message(event.chat_id, prev, reply_to=event.reply_to_msg_id)
            await client.delete_messages(event.chat_id, [event.id, prev.id])
        except Exception as e:
            await event.edit(f"⚠️ Couldn't re-reply: `{e}`")


COMMANDS_UTIL = {
    "description": "Chat utilities",
    "commands": [
        (".del", "delete replied message (or yourself)"),
        (".copy", "duplicate the replied message below it"),
        (".edit <text>", "edit your previous/replied message"),
        (".reply", "send your previous message as a reply"),
    ],
}

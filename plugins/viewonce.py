# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: VIEW-ONCE SAVER — 👁 v7.7 (photos + videos, DEFAULT ON)
############################################################################
"""
ViewOnce Saver — self-destructing (view-once / "tap to view") media never
disappears anymore. When someone sends you a view-once PHOTO or VIDEO:

  1. the media is downloaded instantly (before Telegram destroys it)
  2. a normal, permanent copy is sent to your SAVED MESSAGES ("me")
  3. caption shows who sent it, in which chat, and when

Commands:
  .viewonce            status card
  .viewonce on / off   toggle (DEFAULT ON, persists across restarts)
  .vos last            re-send the last saved media in the current chat
  .vos clear           clear the local saved-file cache

Notes:
  • Works for photos AND videos (video was broken in old builds — fixed).
  • Albums: every view-once item of an album is saved individually.
  • Files are cached in data/viewonce/ (oldest deleted beyond 60 MB).
  • Fully FloodWait-safe; failures never crash the client.
"""

_VO_STORE = "viewonce"
_VO_DIR = os.path.join(DATA_DIR, "viewonce")
_VO_MAX_BYTES = 60 * 1024 * 1024          # 60 MB local cache cap
try:
    os.makedirs(_VO_DIR, exist_ok=True)
except Exception:
    pass

_VO_STATE = {"on": True}                  # runtime flag (default ON)
_VO_SEEN = set()                          # message ids already handled
_VO_SEEN_CAP = 800
_VO_LAST = {"path": None, "kind": None, "from": None}   # for .vos last


def _vo_load():
    try:
        d = load_store(_VO_STORE)
        if isinstance(d, dict):
            _VO_STATE["on"] = bool(d.get("on", True))
    except Exception:
        _VO_STATE["on"] = True


def _vo_save():
    try:
        return save_store(_VO_STORE, {"on": bool(_VO_STATE["on"])})
    except Exception:
        return False


def _vo_cache_trim():
    """Keep the cache dir under the size cap — delete oldest files first."""
    try:
        files = []
        total = 0
        for fn in os.listdir(_VO_DIR):
            fp = os.path.join(_VO_DIR, fn)
            if os.path.isfile(fp):
                try:
                    st = os.stat(fp)
                    files.append((st.st_mtime, st.st_size, fp))
                    total += st.st_size
                except OSError:
                    pass
        if total <= _VO_MAX_BYTES:
            return
        files.sort()
        for _mt, _sz, fp in files:
            if total <= _VO_MAX_BYTES:
                break
            try:
                total -= os.path.getsize(fp)
                os.remove(fp)
            except OSError:
                pass
    except Exception:
        pass


def _vo_is_viewonce(media) -> bool:
    """True when the message carries self-destructing (view-once) media."""
    if media is None:
        return False
    ttl = getattr(media, "ttl_seconds", None)
    return bool(ttl) and int(ttl) > 0


def _vo_kind(msg) -> str:
    try:
        from telethon.tl.types import MessageMediaPhoto
        if isinstance(msg.media, MessageMediaPhoto):
            return "photo"
        doc = getattr(msg.media, "document", None)
        if doc is not None:
            mime = (getattr(doc, "mime_type", "") or "").lower()
            if mime.startswith("video"):
                return "video"
            if mime.startswith("image"):
                return "photo"
            if any(getattr(a, "round_message", False) for a in
                   (getattr(doc, "attributes", None) or [])):
                return "video message"
            return "document"
    except Exception:
        pass
    return "media"


def _vo_register_plugins_meta():
    pass


def register_viewonce(client):
    """ViewOnce saver — intercept + download + re-save TTL media."""
    from telethon import events as _ev

    _vo_load()
    log.info("[viewonce] 👁 saver ready — %s (photos + videos)",
             "ON" if _VO_STATE["on"] else "OFF")

    # ── incoming view-once media → download → saved messages ────────────
    @client.on(_ev.NewMessage(incoming=True))
    async def _viewonce_listener(event):
        if not _VO_STATE["on"]:
            return
        msg = event.message
        if msg is None or not _vo_is_viewonce(getattr(msg, "media", None)):
            return
        if msg.id in _VO_SEEN:
            return
        _VO_SEEN.add(msg.id)
        if len(_VO_SEEN) > _VO_SEEN_CAP:
            _VO_SEEN.clear()
        kind = _vo_kind(msg)
        sender_name = "Unknown"
        sender_id = event.sender_id or 0
        chat_name = "this chat"
        try:
            sender = await event.get_sender()
            sender_name = (getattr(sender, "first_name", None)
                           or getattr(sender, "title", None) or "Unknown")
        except Exception:
            pass
        try:
            chat = await event.get_chat()
            chat_name = (getattr(chat, "title", None)
                         or getattr(chat, "first_name", None) or "this chat")
        except Exception:
            pass

        stamp = time.strftime("%Y%m%d-%H%M%S")
        base = os.path.join(_VO_DIR, f"vo_{stamp}_{msg.id}")
        path = None
        try:
            path = await client.download_media(msg, file=base)
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 1)
            try:
                path = await client.download_media(msg, file=base)
            except Exception:
                path = None
        except Exception as e:
            log.warning("[viewonce] download fail: %s: %s",
                        type(e).__name__, str(e)[:80])
            path = None
        if not path or not os.path.exists(path):
            log.warning("[viewonce] media expired before download (%s)", kind)
            return

        cap = (
            "👁 **View-once SAVED** (permanent copy)\n"
            f"┃ 🎞 Type: `{kind}`\n"
            f"┃ 👤 From: **{sender_name}** (`{sender_id}`)\n"
            f"┃ 💬 Chat: `{chat_name}`\n"
            f"┃ 🕒 {time.strftime('%d %b %Y %H:%M:%S')}\n"
            "┃ ♻️ `.vos last` — view it again anywhere"
        )
        try:
            await throttle("send")
            if kind == "photo":
                await client.send_file("me", path, caption=cap,
                                       force_document=False, link_preview=False)
            else:
                # video / video-message / document — keep it playable
                await client.send_file("me", path, caption=cap,
                                       force_document=False,
                                       supports_streaming=True,
                                       link_preview=False)
            _VO_LAST["path"] = path
            _VO_LAST["kind"] = kind
            _VO_LAST["from"] = sender_name
            _vo_cache_trim()
            log.info("[viewonce] 👁 saved %s from %s (%s)", kind,
                     sender_name, chat_name)
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 1)
            try:
                await client.send_file("me", path, caption=cap,
                                       force_document=False,
                                       supports_streaming=True)
                _VO_LAST["path"] = path
                _VO_LAST["kind"] = kind
                _VO_LAST["from"] = sender_name
            except Exception as e2:
                log.warning("[viewonce] re-send fail: %s: %s",
                            type(e2).__name__, str(e2)[:80])
        except Exception as e:
            log.warning("[viewonce] send-to-saved fail: %s: %s",
                        type(e).__name__, str(e)[:80])

    # ── .viewonce on/off/status ─────────────────────────────────────────
    @client.on(_ev.NewMessage(outgoing=True,
                              pattern=r"^\.viewonce(?:\s+(on|off|status))?\s*$"))
    @client.flood_safe
    async def _viewonce_toggle(event):
        mode = (event.pattern_match.group(1) or "").lower()
        if mode in ("on", "enable"):
            _VO_STATE["on"] = True
            _vo_save()
            return await event.edit(
                "👁 **ViewOnce Saver: 🟢 ON**\n"
                "┃ every view-once **photo AND video** you receive is\n"
                "┃ auto-saved as a permanent copy in Saved Messages\n"
                "┃ off: `.viewonce off`")
        if mode in ("off", "disable"):
            _VO_STATE["on"] = False
            _vo_save()
            return await event.edit(
                "👁 **ViewOnce Saver: 🔴 OFF**\n"
                "┃ view-once media will self-destruct normally again\n"
                "┃ on: `.viewonce on`")
        return await event.edit(
            "✦ ━━〔 👁 **VIEW-ONCE SAVER** 〕━━ ✦\n"
            f"┃ Status : {'🟢 ON (default)' if _VO_STATE['on'] else '🔴 OFF'}\n"
            "┃ Saves  : photos ✔ · videos ✔ · video messages ✔\n"
            "┃ Target : 📥 Saved Messages (permanent copy)\n"
            "┃ ♻️ `.vos last` — re-send the last saved item here\n"
            "✦ ━━━━━━━━━━━━━━━━━━ ✦\n"
            "📖 `.viewonce on/off` — toggle (persists across restarts)",
            link_preview=False)

    # ── .vos last / .vos clear ───────────────────────────────────────────
    @client.on(_ev.NewMessage(outgoing=True,
                              pattern=r"^\.vos\s*(last|clear)?\s*$"))
    @client.flood_safe
    async def _vos_last(event):
        arg = (event.pattern_match.group(1) or "").lower()
        if arg == "clear":
            removed = 0
            for fn in os.listdir(_VO_DIR):
                fp = os.path.join(_VO_DIR, fn)
                try:
                    if os.path.isfile(fp):
                        os.remove(fp)
                        removed += 1
                except OSError:
                    pass
            _VO_LAST["path"] = None
            return await event.edit(f"🧹 ViewOnce cache cleared — `{removed}` file(s).")
        path = _VO_LAST.get("path")
        if not path or not os.path.exists(path):
            return await event.edit(
                "ℹ️ Nothing saved yet.\n"
                "┃ view-once media you receive is saved automatically\n"
                "┃ (check `.viewonce` — the saver is ON by default)")
        try:
            await throttle("send")
            await client.send_file(event.chat_id, path,
                                   caption=(f"👁 **Last view-once** "
                                            f"({_VO_LAST.get('kind') or 'media'}) — "
                                            f"from {_VO_LAST.get('from') or 'Unknown'}"),
                                   force_document=False,
                                   supports_streaming=True,
                                   reply_to=event.reply_to_msg_id)
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 1)
            try:
                await client.send_file(event.chat_id, path,
                                       force_document=False,
                                       supports_streaming=True)
            except Exception:
                pass
        except Exception as e:
            await event.edit(f"❌ Could not re-send: `{str(e)[:80]}`")


COMMANDS_VIEWONCE = {
    "description": "👁 ViewOnce Saver — self-destructing media, saved forever",
    "commands": [
        (".viewonce on/off", "view-once saver — photos AND videos land in Saved Messages (DEFAULT ON)"),
        (".viewonce", "saver status card"),
        (".vos last", "re-send the last saved view-once media here"),
        (".vos clear", "clear the local view-once file cache"),
    ],
}

# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: STICKERS — steal any sticker/photo into YOUR own pack
#  Uses the official @Stickers conversation flow (/addsticker → /newpack
#  → /publish), same as popular kang bots. No imports needed except `re`.
#  Inserted by assemble.py — do NOT run standalone.
# ============================================================================
import re


def _sticker_kind(reply):
    """Return 'static' | 'anim' | 'video' | 'photo' | None."""
    if getattr(reply, "sticker", None) and reply.document:
        mime = (reply.document.mime_type or "").lower()
        if mime == "application/x-tgs":
            return "anim"
        if mime == "video/webm":
            return "video"
        if mime.startswith("image/"):
            return "static"
        return None
    if getattr(reply, "photo", None):
        return "photo"
    doc = getattr(reply, "document", None)
    if doc and (doc.mime_type or "").lower().startswith("image/"):
        return "photo"
    return None


def _sticker_emoji(reply):
    doc = getattr(reply, "document", None)
    if doc:
        for attr in getattr(doc, "attributes", []) or []:
            if isinstance(attr, DocumentAttributeSticker):
                return getattr(attr, "alt", None) or None
    return None


def _pack_names(me, kind, vol):
    uname = re.sub(r"[^a-z0-9_]", "", (me.username or f"user{me.id}").lower())[:20]
    uname = uname or f"user{me.id}"
    suffix = {"static": "", "photo": "", "anim": "_anim", "video": "_vid"}[kind]
    short = f"px{me.id}{suffix}_by_{uname}"
    if vol > 1:
        short = f"px{me.id}{suffix}v{vol}_by_{uname}"
    title = f"{me.first_name}'s Phantom Pack"
    if kind in ("anim", "video"):
        title += f" ({kind})"
    if vol > 1:
        title += f" Vol.{vol}"
    return short, title


def register_stickers(client):
    """`.steal` / `.kang` / `.stickerinfo` / `.getsticker`."""

    async def _ask(conv, text=None, file=None):
        if file:
            await conv.send_file(file, force_document=True)
        else:
            await conv.send_message(text)
        try:
            await client.send_read_acknowledge(conv.chat_id)
        except Exception:
            pass
        resp = await conv.get_response(timeout=40)
        try:
            await client.send_read_acknowledge(conv.chat_id)
        except Exception:
            pass
        return resp

    async def _steal_flow(conv, path, kind, emoji, me):
        """Talk to @Stickers. Returns (ok: bool, pack_or_error: str)."""
        newcmd = {"static": "/newpack", "photo": "/newpack",
                  "anim": "/newanimated", "video": "/newvideo"}[kind]
        for vol in range(1, 4):
            packname, title = _pack_names(me, kind, vol)
            r = await _ask(conv, "/addsticker")
            r = await _ask(conv, packname)
            low = (r.text or "").lower()

            if "invalid" in low or "not found" in low or "does not exist" in low:
                # ---- pack doesn't exist → create it ----
                await _ask(conv, "/cancel")
                r = await _ask(conv, newcmd)
                r = await _ask(conv, title)
                r = await _ask(conv, file=path)
                low = (r.text or "").lower()
                if "emoji" not in low:
                    if any(w in low for w in ("invalid", "error", "can't",
                                              "cannot", "dimensions", "wrong",
                                              "failed")):
                        await _ask(conv, "/cancel")
                        return False, (r.text or "Unknown error")[:300]
                r = await _ask(conv, emoji)
                r = await _ask(conv, "/publish")
                low = (r.text or "").lower()
                if kind in ("static", "photo") and (
                        "icon" in low or "skip" in low or "128" in low):
                    r = await _ask(conv, "/skip")
                r = await _ask(conv, packname)
                low = (r.text or "").lower()
                if ("congratulations" in low or "successfully" in low
                        or "addstickers" in low or packname in low):
                    return True, packname
                await _ask(conv, "/cancel")
                return False, (r.text or "Publish failed")[:300]

            if "120" in low or "50" in low or "full" in low:
                # ---- pack full → try next volume ----
                await _ask(conv, "/cancel")
                continue

            # ---- pack exists → add sticker ----
            r = await _ask(conv, file=path)
            low = (r.text or "").lower()
            if "120" in low or "50" in low or "full" in low:
                await _ask(conv, "/cancel")
                continue
            if "emoji" not in low and any(w in low for w in (
                    "invalid", "error", "can't", "cannot", "failed")):
                await _ask(conv, "/cancel")
                return False, (r.text or "Unknown error")[:300]
            r = await _ask(conv, emoji)
            r = await _ask(conv, "/done")
            return True, packname

        return False, "Tried 3 pack volumes — all full. Delete one via @Stickers."

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:steal|kang)(?:\s+(.*))?$"))
    @client.flood_safe
    async def _steal(event):
        arg = (event.pattern_match.group(1) or "").strip()
        reply = await event.get_reply_message()
        kind = _sticker_kind(reply) if reply else None
        if not kind:
            return await event.edit(
                "🖼️ **Sticker Stealer**\n\n"
                "Reply to any sticker / photo / image with:\n"
                "• `.steal` — keep original emoji\n"
                "• `.steal 😎` — use your own emoji\n\n"
                "_It gets added to YOUR pack, auto-created on first use._"
            )
        emoji = arg.split()[0] if arg else (_sticker_emoji(reply) or "⭐")

        if kind in ("static", "photo") and not _HAS_PIL:
            return await event.edit(
                "🖼️ Static stickers need image resizing.\n"
                "Run `pip install pillow`, then `.restart`."
            )

        await event.edit("📥 Downloading…")
        ext = {"static": "png", "photo": "png",
               "anim": "tgs", "video": "webm"}[kind]
        path = f"steal_{event.id}.{ext}"
        try:
            downloaded = await client.download_media(reply, file=path)
            if not downloaded or not os.path.exists(path):
                return await event.edit("❌ Download failed. Try again.")

            if kind in ("static", "photo"):
                await event.edit("🎨 Resizing to 512px…")
                try:
                    im = Image.open(path)
                    w, h = im.size
                    if w < 512 and h < 512:
                        # upscale small images so one side hits 512
                        if w >= h:
                            scale = 512 / max(w, 1)
                            im = im.resize((512, math.floor(h * scale)))
                        else:
                            scale = 512 / max(h, 1)
                            im = im.resize((math.floor(w * scale), 512))
                    else:
                        im.thumbnail((512, 512))
                    if im.mode not in ("RGBA", "LA"):
                        im = im.convert("RGBA")
                    im.save(path, "PNG")
                except Exception as e:
                    return await event.edit(f"❌ Image convert failed: `{e}`")

            me = await client.get_me()
            await event.edit("💬 Talking to @Stickers… _(takes ~10 sec)_")

            async def _run():
                async with client.conversation("@Stickers", timeout=60) as conv:
                    return await _steal_flow(conv, path, kind, emoji, me)

            try:
                ok, result = await _run()
            except YouBlockedUserError:
                try:
                    await client(UnblockRequest(await client.get_entity("@Stickers")))
                    ok, result = await _run()
                except Exception as e:
                    return await event.edit(f"❌ @Stickers is blocked & unblock failed: `{e}`")
            except asyncio.TimeoutError:
                return await event.edit("⏰ @Stickers took too long. Try again later.")

            if ok:
                _, title = _pack_names(me, kind, 1)
                await event.edit(
                    f"✅ **Sticker stolen!** {emoji}\n\n"
                    f"📦 Pack: [{title}](https://t.me/addstickers/{result})\n"
                    f"🔗 `https://t.me/addstickers/{result}`",
                    link_preview=False,
                )
            else:
                await event.edit(f"❌ **Steal failed.**\n@Stickers said:\n`{result}`")
        finally:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stickerinfo$"))
    @client.flood_safe
    async def _stickerinfo(event):
        reply = await event.get_reply_message()
        if not reply or not getattr(reply, "sticker", None):
            return await event.edit("❌ Reply to a sticker with `.stickerinfo`.")
        doc = reply.document
        mime = (doc.mime_type or "").lower()
        kind = ("🎞 Animated" if mime == "application/x-tgs"
                else "🎥 Video" if mime == "video/webm" else "🖼 Static")
        emoji, short, fname, w, h = "—", None, "—", "?", "?"
        for attr in getattr(doc, "attributes", []) or []:
            if isinstance(attr, DocumentAttributeSticker):
                emoji = getattr(attr, "alt", None) or "—"
                ss = getattr(attr, "stickerset", None)
                if ss is not None:
                    short = getattr(ss, "short_name", None)
            elif isinstance(attr, DocumentAttributeFilename):
                fname = attr.file_name
            elif type(attr).__name__ == "DocumentAttributeImageSize":
                w, h = attr.w, attr.h
        title, count = None, None
        if short:
            try:
                from telethon.tl.functions.messages import GetStickerSet
                from telethon.tl.types import InputStickerSetShortName
                res = await client(GetStickerSet(
                    stickerset=InputStickerSetShortName(short_name=short), hash=0))
                title = res.set.title
                count = res.set.count
            except Exception:
                pass
        kb = (doc.size or 0) / 1024
        lines = [
            "✦ ━━━〔 🖼 STICKER INFO 〕━━━ ✦",
            f"┃ {kind}",
            f"┃ {emoji} Emoji : {emoji}",
            f"┃ 🆔 Doc ID : `{doc.id}`",
            f"┃ 📐 Size   : `{w}x{h}` · `{kb:.1f} KB`",
            f"┃ 📄 File   : `{fname}`",
        ]
        if short:
            lines.append(f"┃ 📦 Pack   : [{title or short}](https://t.me/addstickers/{short})")
            if count:
                lines.append(f"┃ 🔢 In pack: `{count}` stickers")
            lines.append(f"┃ 🔗 `https://t.me/addstickers/{short}`")
        else:
            lines.append("┃ 📦 Pack   : _custom / unknown_")
        lines.append("✦ ━━━━━━━━━━━━━━━━━━━━━ ✦")
        lines.append("_Steal it with `.steal` (reply)._")
        await event.edit("\n".join(lines), link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.getsticker$"))
    @client.flood_safe
    async def _getsticker(event):
        reply = await event.get_reply_message()
        if not reply or not getattr(reply, "sticker", None):
            return await event.edit("❌ Reply to a sticker with `.getsticker`.")
        await event.edit("📥 Downloading sticker…")
        path = f"gsticker_{event.id}"
        try:
            downloaded = await client.download_media(reply, file=path)
            if not downloaded or not os.path.exists(downloaded):
                return await event.edit("❌ Download failed.")
            # convert static webp → png for easy reuse
            if downloaded.lower().endswith(".webp") and _HAS_PIL:
                try:
                    png = downloaded + ".png"
                    Image.open(downloaded).convert("RGBA").save(png, "PNG")
                    try:
                        os.remove(downloaded)
                    except OSError:
                        pass
                    downloaded = png
                except Exception:
                    pass
            await client.send_file(
                await event.get_input_chat(), downloaded,
                caption="🖼 Here is your sticker file",
                reply_to=event.id,
            )
            await event.delete()
        finally:
            for p in (path, path + ".png"):
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except OSError:
                    pass


COMMANDS_STICKERS = {
    "description": "Sticker Tools",
    "commands": [
        (".steal [emoji] / .kang", "steal replied sticker/photo to YOUR pack"),
        (".stickerinfo", "pack + emoji + size of replied sticker"),
        (".getsticker", "download replied sticker as a file"),
    ],
}

# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
# SECTION: MEDIA — quote sticker, file info, voice→audio & image tools
#   .q/.quotly  .fileinfo  .toaudio
#   .blur  .mirror  .rotate  .gray  .invert  .circle
# Image tools need: pip install pillow
# ============================================================================
COMMANDS_MEDIA = {
    "description": "Media & Image Tools (9)",
    "commands": [
        (".q (reply)", "turn a message into a quote card image"),
        (".fileinfo (reply)", "details of any replied file/media"),
        (".toaudio (reply)", "voice note / video → audio file"),
        (".blur [n]", "blur the replied image (default 8)"),
        (".mirror", "mirror the replied image"),
        (".rotate [deg]", "rotate the replied image"),
        (".gray", "black & white image"),
        (".invert", "negative / inverted colours"),
        (".circle", "round sticker from the image"),
    ],
}

_MD_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def _md_font(size: int):
    """Best available TrueType font, else PIL's tiny default."""
    for path in _MD_FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _md_open(data: bytes):
    return Image.open(io.BytesIO(data))


async def _md_media_bytes(event, msg=None) -> bytes:
    """Download the replied (or given) message's media into memory."""
    target = msg or await event.get_reply_message()
    if target is None or target.media is None:
        return b""
    data = await event.client.download_media(target, file=bytes)
    return data or b""


async def _md_send(event, img, caption: str = "", document: bool = False) -> None:
    """Send a PIL image back to the chat."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "sukuna.png"
    await throttle_chat(event.chat_id)
    await event.client.send_file(
        await event.get_input_chat(), buf, caption=caption or None,
        reply_to=event.reply_to_msg_id or event.id, force_document=document,
    )


def register_media(client):
    """Quote cards + file/media utilities."""

    # ================== QUOTE STICKER ==================

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:q|quotly)$"))
    @client.flood_safe
    async def _quotly(event):
        if not event.is_reply:
            return await event.edit("❌ Reply to a message: `.q`")
        if not _HAS_PIL:
            return await event.edit(
                "❌ Pillow is not installed.\n"
                "💡 Run: `pip install pillow` then restart the bot."
            )
        await event.edit("🎨 Painting your quote…")
        msg = await event.get_reply_message()
        text = (msg.raw_text or "").strip()[:900]
        if not text:
            text = "📎 (media message)"
        # sender name
        try:
            sender = await msg.get_sender()
            name = " ".join(
                x for x in [getattr(sender, "first_name", "") or "",
                            getattr(sender, "last_name", "") or ""] if x
            ).strip()
            if not name:
                name = getattr(sender, "title", None) or "Unknown"
            avatar_bytes = b""
            try:
                avatar_bytes = await client.download_profile_photo(
                    getattr(sender, "id", None), file=bytes
                ) or b""
            except Exception:
                avatar_bytes = b""
        except Exception:
            name, avatar_bytes = "Unknown", b""

        W, PAD = 720, 36
        f_name = _md_font(34)
        f_text = _md_font(30)
        f_tag = _md_font(22)
        wrap_at = 34
        lines = []
        for raw_line in text.split("\n"):
            lines.extend(textwrap.wrap(raw_line, wrap_at) or [""])
        lines = lines[:18]
        line_h = 46
        H = PAD * 2 + 120 + line_h * len(lines) + 40

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # rounded dark card
        draw.rounded_rectangle([(0, 0), (W - 1, H - 1)], radius=34,
                               fill=(24, 26, 42, 255), outline=(88, 101, 242, 255), width=3)
        # accent bar
        draw.rounded_rectangle([(0, 0), (14, H - 1)], radius=7, fill=(88, 101, 242, 255))

        # avatar
        ax, ay, asz = PAD + 14, PAD, 96
        avatar = None
        if avatar_bytes:
            try:
                avatar = _md_open(avatar_bytes).convert("RGBA")
            except Exception:
                avatar = None
        if avatar is None:
            avatar = Image.new("RGBA", (asz, asz), (120, 90, 240, 255))
            d0 = ImageDraw.Draw(avatar)
            d0.text((asz // 2, asz // 2), (name or "?")[:1].upper(),
                    font=_md_font(46), fill=(255, 255, 255, 255), anchor="mm")
        avatar = ImageOps.fit(avatar, (asz, asz), Image.LANCZOS)
        mask = Image.new("L", (asz * 4, asz * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, asz * 4, asz * 4), fill=255)
        mask = mask.resize((asz, asz), Image.LANCZOS)
        img.paste(avatar, (ax, ay), mask)
        draw = ImageDraw.Draw(img)

        # name + verified-ish dot
        draw.text((ax + asz + 22, ay + 12), name[:28], font=f_name,
                  fill=(255, 255, 255, 255))
        draw.text((ax + asz + 22, ay + 56), "SUKUNA-X QUOTE", font=f_tag,
                  fill=(140, 150, 255, 255))

        # text
        y = ay + asz + 34
        for line in lines:
            draw.text((PAD + 26, y), line, font=f_text, fill=(228, 231, 255, 255))
            y += line_h

        # watermark
        draw.text((W - PAD - 6, H - PAD + 2), "⚡ SUKUNA-X", font=f_tag,
                  fill=(110, 118, 200, 255), anchor="rs")
        await _md_send(event, img.convert("RGB"), caption="🎨 Quote card")
        try:
            await event.delete()
        except Exception:
            pass

    # ================== FILE INFO ==================

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fileinfo$"))
    @client.flood_safe
    async def _fileinfo(event):
        if not event.is_reply:
            return await event.edit("❌ Reply to a file/media: `.fileinfo`")
        msg = await event.get_reply_message()
        if msg.media is None:
            return await event.edit("❌ That message has no media/file.")
        rows = [
            "✦ ━━━〔 📄 FILE INFO 〕━━━ ✦",
            f"┃ 🆔 Message : `{msg.id}`",
        ]
        doc = getattr(msg, "document", None)
        photo = getattr(msg, "photo", None)
        if photo is not None:
            rows.append("┃ 🖼 Type    : Photo")
        if doc is not None:
            size = getattr(doc, "size", 0) or 0
            rows.append(f"┃ 🗂 Type    : `{getattr(doc, 'mime_type', 'unknown')}`")
            rows.append(f"┃ 📦 Size    : `{size / 1048576:.2f} MB` ({size} bytes)")
            for attr in getattr(doc, "attributes", []):
                cls = attr.__class__.__name__
                if cls == "DocumentAttributeFilename":
                    rows.append(f"┃ 🏷 Name    : `{attr.file_name}`")
                elif cls == "DocumentAttributeSticker":
                    rows.append(f"┃ 🩹 Sticker : emoji `{getattr(attr, 'alt', '-')}`")
                elif cls == "DocumentAttributeAudio":
                    rows.append(f"┃ 🎵 Audio   : `{getattr(attr, 'title', '-')}` "
                                f"({getattr(attr, 'duration', 0)}s)")
                elif cls == "DocumentAttributeVideo":
                    rows.append(
                        f"┃ 🎬 Video   : `{getattr(attr, 'w', 0)}×{getattr(attr, 'h', 0)}` "
                        f"({getattr(attr, 'duration', 0)}s)"
                    )
            if any(a.__class__.__name__ == "DocumentAttributeAnimated"
                   for a in getattr(doc, "attributes", [])):
                rows.append("┃ ✨ Animated : yes (GIF)")
        if msg.date:
            rows.append(f"┃ 🕐 Date    : `{msg.date:%Y-%m-%d %H:%M:%S}`")
        rows.append("✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦")
        await event.edit("\n".join(rows), link_preview=False)

    # ================== VOICE / VIDEO → AUDIO ==================

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.toaudio(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _toaudio(event):
        if not event.is_reply:
            return await event.edit("❌ Reply to a voice note / video: `.toaudio`")
        msg = await event.get_reply_message()
        if msg.media is None:
            return await event.edit("❌ No media in the replied message.")
        title = (event.pattern_match.group(1) or "SUKUNA-X audio").strip()[:64]
        await event.edit("🎧 Converting to audio…")
        path = None
        try:
            path = await client.download_media(msg)
            if not path:
                return await event.edit("❌ Download failed.")
            duration = 0
            voice = False
            doc = getattr(msg, "document", None)
            if doc is not None:
                for attr in getattr(doc, "attributes", []):
                    if attr.__class__.__name__ == "DocumentAttributeAudio":
                        duration = getattr(attr, "duration", 0) or 0
                        voice = bool(getattr(attr, "voice", False))
            await throttle_chat(event.chat_id)
            await client.send_file(
                await event.get_input_chat(), path,
                attributes=[DocumentAttributeAudio(
                    duration=int(duration or 0), title=title,
                    performer="SUKUNA-X", voice=False,
                )],
                force_document=False,
                reply_to=event.reply_to_msg_id or event.id,
            )
            await event.delete()
        except Exception as exc:
            await event.edit(f"❌ Failed: `{exc}`")
        finally:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    # ================== IMAGE TOOLS ==================

    async def _image_op(event, label, worker, document=False):
        if not _HAS_PIL:
            return await event.edit(
                "❌ Pillow is not installed.\n💡 Run: `pip install pillow` and restart."
            )
        if not event.is_reply:
            return await event.edit(f"❌ Reply to an image: `. {label}`".replace(". ", "."))
        await event.edit(f"🖼 Applying **{label}**…")
        try:
            data = await _md_media_bytes(event)
            if not data:
                return await event.edit("❌ Could not download that media.")
            img = _md_open(data)
            out = worker(img)
            await _md_send(event, out, caption=f"🖼 {label} · ⚡ SUKUNA-X", document=document)
            try:
                await event.delete()
            except Exception:
                pass
        except Exception as exc:
            await event.edit(f"❌ Image error: `{exc}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.blur(?:\s+(\d+))?$"))
    @client.flood_safe
    async def _blur(event):
        radius = int(event.pattern_match.group(1) or 8)
        radius = max(1, min(40, radius))
        await _image_op(
            event, f"blur {radius}",
            lambda im: im.convert("RGB").filter(ImageFilter.GaussianBlur(radius)),
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mirror$"))
    @client.flood_safe
    async def _mirror(event):
        await _image_op(event, "mirror", lambda im: ImageOps.mirror(im.convert("RGB")))

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rotate(?:\s+(\d+))?$"))
    @client.flood_safe
    async def _rotate(event):
        deg = int(event.pattern_match.group(1) or 90) % 360
        await _image_op(event, f"rotate {deg}°",
                        lambda im: im.convert("RGB").rotate(-deg, expand=True))

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.gray$"))
    @client.flood_safe
    async def _gray(event):
        await _image_op(event, "grayscale", lambda im: im.convert("L").convert("RGB"))

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.invert$"))
    @client.flood_safe
    async def _invert(event):
        await _image_op(event, "invert", lambda im: ImageOps.invert(im.convert("RGB")))

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.circle$"))
    @client.flood_safe
    async def _circle(event):
        def _round(im):
            im = im.convert("RGBA")
            side = min(im.size)
            im = ImageOps.fit(im, (side, side), Image.LANCZOS)
            mask = Image.new("L", (side * 4, side * 4), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, side * 4, side * 4), fill=255)
            mask = mask.resize((side, side), Image.LANCZOS)
            out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            out.paste(im, (0, 0), mask)
            return out
        await _image_op(event, "circle sticker", _round, document=True)

    log.info("Media commands: quotly, fileinfo, toaudio, image tools")

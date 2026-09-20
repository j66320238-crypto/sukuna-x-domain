# ── SUKUNA-X DOMAIN v7.0 plugin ──────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: PREMEMOJI — ✨ PREMIUM EMOJI SYSTEM (OkEmojiBot killer edition)
#  Normal emojis → **animated premium emojis**, apne hi account se —
#  koi "via @bot" tag NAHI, bilkul clean message.
#
#   .premiumsticker on      → AUTO mode: every message gets premium emojis
#   .premiumsticker off     → disable auto mode
#   .premiumsticker <text>  → one-time premium emoji message
#   .pemoji <text>          → alias (one-time)
#   .pestatus               → status + cached emoji count
#
#  Tech: Telegram custom-emoji documents (SearchCustomEmoji RPC) +
#  MessageEntityCustomEmoji entities. IDs cached forever in disk.
#  Flood-safe: delete+resend me throttle, FloodWait auto-sleep.
# ============================================================================

from telethon.tl.functions.messages import SearchCustomEmojiRequest
from telethon.tl.types import MessageEntityCustomEmoji

_PE_FILE = os.path.join(DATA_DIR, "prememoji.json")
_PE_STATE = {"on": False}
_PE_MAP = {}            # emoji → document_id
_PE_SKIP = set()        # message ids we already premium-ified (no loops)
_PE_LAST_AUTO = 0.0     # cooldown between auto conversions (anti-conflict)

# common emojis incl. ZWJ sequences, variation selectors, flags, hearts…
_EMOJI_CORE = (
    "[\U0001F1E6-\U0001F1FF]{2}"
    "|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF\u2700-\u27BF\u2190-\u21FF\u2B00-\u2BFF\u2300-\u23FF"
    "\u2049\u203C\u00A9\u00AE\u2122]"
    "[\uFE0F]?(?:\u200D[\U0001F300-\U0001FAFF][\uFE0F]?)*"
    "|[\u2764\u270C\u270B\u270A\u270D\u261D\u263A\u2639\u2620\u270C][\uFE0F]?"
)
EMOJI_RE = re.compile(_EMOJI_CORE)


def _pe_load():
    global _PE_STATE, _PE_MAP
    try:
        with open(_PE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            _PE_STATE = {"on": bool(data.get("on"))}
            _PE_MAP = {k: int(v) for k, v in (data.get("map") or {}).items()}
    except Exception:
        pass


def _pe_save():
    try:
        with open(_PE_FILE, "w", encoding="utf-8") as fh:
            json.dump({"on": _PE_STATE["on"], "map": _PE_MAP}, fh, ensure_ascii=False)
    except OSError:
        pass


_pe_load()


def _u16(s: str) -> int:
    """Telegram offsets are UTF-16 code units."""
    return sum(2 if ord(c) > 0xFFFF else 1 for c in s)


async def _pe_resolve(client, emojis) -> dict:
    """emoji → document_id, cache-first. Returns dict (may be partial)."""
    out, missing = {}, []
    for e in emojis:
        if e in _PE_MAP:
            out[e] = _PE_MAP[e]
        else:
            missing.append(e)
    if not missing:
        return out
    for e in missing[:6]:  # limit RPC per message (flood-safe)
        try:
            res = await client(SearchCustomEmojiRequest(emoticon=e, hash=0))
            docs = getattr(res, "documents", None) or []
            best_free, best_any = None, None
            for d in docs:
                for attr in (getattr(d, "attributes", None) or []):
                    if attr.__class__.__name__ == "DocumentAttributeCustomEmoji" \
                            and getattr(attr, "alt", "") == e:
                        # prefer FREE documents — they render for every
                        # account (non-premium included); no black dots.
                        if getattr(attr, "free", False) and best_free is None:
                            best_free = d.id
                        if best_any is None:
                            best_any = d.id
            doc_id = best_free or best_any or (docs[0].id if docs else None)
            if doc_id:
                _PE_MAP[e] = doc_id
                out[e] = doc_id
        except Exception as exc:
            log.debug("[prememoji] resolve %r failed: %s", e, exc)
    _pe_save()
    return out


def _pe_build_entities(text: str, mapping: dict):
    """Build MessageEntityCustomEmoji list with correct UTF-16 offsets."""
    ents = []
    for m in EMOJI_RE.finditer(text):
        emo = m.group(0)
        doc = mapping.get(emo)
        if not doc:
            continue
        ents.append(MessageEntityCustomEmoji(
            offset=_u16(text[:m.start()]),
            length=_u16(emo),
            document_id=doc))
    ents.sort(key=lambda e: e.offset)
    return ents


async def _pe_send_premium(client, event, text: str, reply_to=None) -> bool:
    """Delete original & resend with premium emojis. Returns True if done."""
    emojis = list({m.group(0) for m in EMOJI_RE.finditer(text)})
    if not emojis:
        return False
    mapping = await _pe_resolve(client, emojis)
    ents = _pe_build_entities(text, mapping)
    if not ents:
        return False
    await throttle("send")
    try:
        await event.delete()
    except Exception:
        pass
    msg = await client.send_message(
        await event.get_input_chat(), text,
        entities=ents, reply_to=reply_to)
    _PE_SKIP.add(msg.id)
    if len(_PE_SKIP) > 200:
        _PE_SKIP.clear()
    return True


def register_prememoji(client):
    """Premium emoji auto-system."""

    # ---- auto mode: outgoing messages ----
    @client.on(events.NewMessage(outgoing=True))
    async def _pe_auto(event):
        global _PE_LAST_AUTO
        try:
            if not _PE_STATE["on"]:
                return
            if storm_active():      # 🚨 during a ban-storm, skip — ID safe
                return
            if event.id in _PE_SKIP:
                return
            now = time.time()
            if now - _PE_LAST_AUTO < 1.5:   # anti-conflict cooldown
                return
            text = event.text or ""
            if not text or text.startswith(".") or text.startswith("/"):
                return
            if not EMOJI_RE.search(text):
                return
            # only auto-convert plain user messages (no media, no fwd)
            if event.media or event.fwd_from or event.via_bot:
                return
            # already has custom-emoji entities? leave it alone (no fights)
            for ent in (event.entities or []):
                if ent.__class__.__name__ == "MessageEntityCustomEmoji":
                    return
            ok = await _pe_send_premium(client, event, text, reply_to=event.reply_to_msg_id)
            if ok:
                _PE_LAST_AUTO = now
                log.info("[prememoji] auto-converted msg %s", event.id)
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(min(fw.seconds, 30) + 1)
        except Exception as exc:
            log.debug("[prememoji] auto failed: %s", exc)

    # ---- .premiumsticker / .pemon / .pemoji ----
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.(?:premiumsticker|pemon|pemoji)(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _pe_cmd(event):
        arg = (event.pattern_match.group(1) or "").strip()

        # control words
        if not arg or arg.lower() in ("on", "off", "status"):
            if arg.lower() == "on":
                _PE_STATE["on"] = True
                _pe_save()
                return await event.edit(
                    "✦ ━━━〔 ✨ PREMIUM EMOJI: ON 〕━━━ ✦\n"
                    "✅ Now **every message** you send gets its emojis converted to\n"
                    "   premium/animated ones — from your own account, NO bot tag 👑\n\n"
                    "💡 `.premiumsticker off` to disable • `.pestatus` info",
                    link_preview=False)
            if arg.lower() == "off":
                _PE_STATE["on"] = False
                _pe_save()
                return await event.edit(
                    "⏹ Premium emoji AUTO mode **OFF**.\n"
                    "💡 One-time use: `.pemoji hello 🙂`", link_preview=False)
            return await event.edit(
                f"✨ Premium emoji mode: {'🟢 **ON**' if _PE_STATE['on'] else ' OFF'}\n"
                f"📦 Cached emojis: `{len(_PE_MAP)}`\n"
                f"💡 `.premiumsticker on` • `.pemoji <text>`", link_preview=False)

        # one-shot premium message
        if not EMOJI_RE.search(arg):
            return await event.edit("❌ No emoji in the text — e.g. `.pemoji hello 🙂😂❤️`")
        ok = await _pe_send_premium(client, event, arg, reply_to=event.reply_to_msg_id)
        if not ok:
            await event.edit(
                "⚠️ These emojis have no premium documents (your account may be limited).\n"
                "💡 Try simple emojis: 🙂 😂 ❤️ 🔥")

    # ---- .petest : verify premium rendering on this account ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.petest$"))
    @client.flood_safe
    async def _pe_test(event):
        sample = "Sukuna-X premium test 🙂 😂 ❤️ 🔥 😎 🎉"
        await event.edit("✨ Testing premium emoji rendering…")
        ok = await _pe_send_premium(client, event, sample, reply_to=None)
        if not ok:
            await event.edit(
                "❌ Could not convert the test emojis.\n"
                "💡 Run `.pereset` once, then try again. If it still fails, "
                "this account cannot send custom emojis (Telegram restriction).")

    # ---- .pereset : clear cached emoji documents ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pereset$"))
    @client.flood_safe
    async def _pe_reset(event):
        _PE_MAP.clear()
        _pe_save()
        await event.edit("🧹 Emoji document cache cleared — fresh documents "
                         "will be fetched on next use. Try `.petest`.")

    # ---- .pestatus ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pestatus$"))
    @client.flood_safe
    async def _pe_status(event):
        sample = list(_PE_MAP.items())[:8]
        sample_txt = " ".join(e for e, _ in sample) or "—"
        await event.edit(
            "✦ ━━━〔  PREMIUM EMOJI STATUS 〕━━━ ✦\n"
            f"┃  Mode  : {'ON — auto convert active' if _PE_STATE['on'] else 'OFF'}\n"
            f"┃ 📦 Cache : `{len(_PE_MAP)}` emoji documents (permanent)\n"
            f"┃  Sample: {sample_txt}\n"
            f"┃ 🛡 Flood-safe delete+resend\n"
            "┃ 💡 `.premiumsticker on/off` toggle",
            link_preview=False)


COMMANDS_PREMEMOJI = {
    "description": "Premium Emojis",
    "type": "Fun",
    "commands": [
        (".premiumsticker on|off", "AUTO premium emoji mode (no bot tag)"),
        (".premiumsticker <text>", "one-time premium emoji message"),
        (".pemoji <text>", "alias — one-time convert"),
        (".petest", "test premium rendering on this account"),
        (".pereset", "clear cached emoji documents"),
        (".pestatus", "mode + cached emoji documents"),
    ],
}

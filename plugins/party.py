# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: PARTY & GAMES  (v5.2 — researched from Ultroid / CatUserbot)
#  .scam       → fake chat actions ("typing…", "recording video…")   [Ultroid]
#  .rdice/.dart/.basket/.football/.slot/.bowl → rigged Telegram dice  [CatUserbot]
#  .fancy      → text in fancy unicode fonts                          [Ultroid]
#  NOTE: no imports here — everything comes from the header.
# ============================================================================

try:
    from telethon.tl.types import InputMediaDice as _DiceMedia
except Exception:  # pragma: no cover
    _DiceMedia = None

# ---------------------------------------------------------------------------
#  Fake chat actions (.scam)
# ---------------------------------------------------------------------------
_SCAM_ACTIONS = {
    "typing":    "typing",
    "contact":   "contact",
    "game":      "game",
    "location":  "location",
    "sticker":   "sticker",
    "voice":     "record-voice",
    "round":     "record-round",
    "video":     "record-video",
    "photo":     "upload-photo",
    "document":  "upload-document",
    "music":     "upload-audio",
    "audio":     "upload-audio",
}

_SCAM_LABEL = {
    "typing": "typing a message ✍️", "contact": "choosing a contact 📇",
    "game": "playing a game 🎮", "location": "choosing a location 📍",
    "sticker": "choosing a sticker 🩹", "voice": "recording a voice note 🎙️",
    "round": "recording a video message 📹", "video": "recording a video 🎥",
    "photo": "uploading a photo 🖼️", "document": "uploading a file 📄",
    "music": "uploading music 🎵", "audio": "uploading music 🎵",
}


def register_party(client):

    # ---- .scam <action> [seconds] -----------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.(?:scam|fake)\s+(\w+)(?:\s+(\d+))?$"))
    @client.flood_safe
    async def _scam(event):
        act = (event.pattern_match.group(1) or "").lower()
        secs = int(event.pattern_match.group(2) or 30)
        if act not in _SCAM_ACTIONS:
            opts = " · ".join(f"`{a}`" for a in
                              ("typing", "contact", "game", "location", "sticker",
                               "voice", "round", "video", "photo", "document", "music"))
            return await event.edit(
                "✦ ━━━〔 🎭 FAKE ACTIONS 〕━━━ ✦\n"
                "┃ usage: `.scam <action> [seconds]`\n"
                f"┃ actions: {opts}\n"
                "┃ example: `.scam typing 60`\n"
                "✦ ━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        secs = max(3, min(secs, 3600))
        task_key = f"scam_{event.id}"
        old = client.stop_processes.get(task_key)
        if old is not None and not old.done():
            old.cancel()

        async def _pretend():
            try:
                async with client.action(event.chat_id, _SCAM_ACTIONS[act]):
                    end = time.time() + secs
                    while time.time() < end:
                        await asyncio.sleep(1)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
            finally:
                client.stop_processes.pop(task_key, None)

        client.stop_processes[task_key] = asyncio.ensure_future(_pretend())
        await event.edit(
            f"🎭 Now {_SCAM_LABEL[act]} for **{secs}s**…\n"
            "⏹️ Cancel anytime with `.stop`",
            link_preview=False,
        )

    # ---- rigged Telegram dice ----------------------------------------------
    async def _rigged(event, emoji, target, max_tries, label, hi):
        if _DiceMedia is None:
            return await event.edit("⚠️ Your Telethon is too old for dice media — run `pip install -U telethon`.")
        if target is not None and not (1 <= target <= hi):
            return await event.edit(f"⚠️ `{label}` target must be between **1** and **{hi}**.")
        if target is None:
            target = random.randint(1, hi)
        await event.edit(f"🎲 Rigging the {label}… I want a **{target}** 🤫")
        last = None
        for _try in range(min(max_tries, SAFE_BURST_CAP)):
            await throttle("send")
            if last is not None:
                try:
                    await last.delete()
                except Exception:
                    pass
            try:
                last = await client.send_file(
                    event.chat_id, _DiceMedia(emoticon=emoji),
                    reply_to=event.reply_to_msg_id,
                )
            except FloodWaitError as e:
                note_flood(e.seconds)
                await asyncio.sleep(e.seconds + 1)
                continue
            except Exception:
                break
            await asyncio.sleep(2.8)  # let Telegram animate the roll
            try:
                val = last.media.value
            except Exception:
                val = None
            if val == target:
                try:
                    await event.delete()
                except Exception:
                    pass
                return
        try:
            await event.edit(f"😅 Couldn't rig a **{target}** — kept the last roll instead.")
        except Exception:
            pass

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rdice\s*(\d+)?$"))
    @client.flood_safe
    async def _rdice(event):
        t = event.pattern_match.group(1)
        await _rigged(event, "🎲", int(t) if t else None, 14, "dice", 6)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dart\s*(\d+)?$"))
    @client.flood_safe
    async def _dart(event):
        t = event.pattern_match.group(1)
        await _rigged(event, "🎯", int(t) if t else None, 14, "dart", 6)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.basket\s*(\d+)?$"))
    @client.flood_safe
    async def _basket(event):
        t = event.pattern_match.group(1)
        await _rigged(event, "🏀", int(t) if t else None, 12, "basketball", 5)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.football\s*(\d+)?$"))
    @client.flood_safe
    async def _football(event):
        t = event.pattern_match.group(1)
        await _rigged(event, "⚽", int(t) if t else None, 12, "football", 5)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.bowl\s*(\d+)?$"))
    @client.flood_safe
    async def _bowl(event):
        t = event.pattern_match.group(1)
        await _rigged(event, "🎳", int(t) if t else None, 14, "bowling", 6)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.slotwin\s*(\d+)?$"))
    @client.flood_safe
    async def _slotwin(event):
        t = event.pattern_match.group(1)
        await _rigged(event, "🎰", int(t) if t else None, 20, "slot machine", 64)

    # ---- fancy fonts ---------------------------------------------------------
    # Unicode mathematical-letter ranges (same trick as Ultroid/CatUserbot fontgen)
    _FANCY_EXC = {
        "script":      {"B": "ℬ", "E": "ℰ", "F": "ℱ", "H": "ℋ", "I": "ℐ", "L": "ℒ",
                        "M": "ℳ", "R": "ℛ", "e": "ℯ", "g": "ℊ", "o": "ℴ"},
        "fraktur":     {"C": "ℭ", "H": "ℌ", "I": "ℑ", "R": "ℜ", "Z": "ℨ"},
        "doublestruck": {"C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ", "Q": "ℚ",
                         "R": "ℝ", "Z": "ℤ"},
    }

    def _fancy_style(name, up, lo, dig=None, exc_key=None):
        table = {}
        exc = _FANCY_EXC.get(exc_key, {}) if exc_key else {}
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            table[ord(ch)] = exc.get(ch, chr(up + i))
        for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
            table[ord(ch)] = exc.get(ch, chr(lo + i))
        if dig is not None:
            for i, ch in enumerate("0123456789"):
                table[ord(ch)] = chr(dig + i)
        return (name, table)

    _FANCY_STYLES = [
        _fancy_style("𝐁𝐨𝐥𝐝", 0x1D400, 0x1D41A, 0x1D7CE),
        _fancy_style("𝘐𝘵𝘢𝘭𝘪𝘤", 0x1D434, 0x1D44E),
        _fancy_style("𝑩𝒐𝒍𝒅 𝑰𝒕𝒂𝒍𝒊𝒄", 0x1D468, 0x1D482),
        _fancy_style("𝒮𝒸𝓇𝒾𝓅𝓉", 0x1D49C, 0x1D4B6, exc_key="script"),
        _fancy_style("𝕱𝖗𝖆𝖐𝖙𝖚𝖗", 0x1D504, 0x1D51E, exc_key="fraktur"),
        _fancy_style("𝔻𝕠𝕦𝕓𝕝𝕖-𝕤𝕥𝕣𝕦𝕔𝕜", 0x1D538, 0x1D552, 0x1D7D8, "doublestruck"),
        _fancy_style("𝙼𝚘𝚗𝚘𝚜𝚙𝚊𝚌𝚎", 0x1D670, 0x1D68A, 0x1D7F6),
        _fancy_style("𝗦𝗮𝗻𝘀 𝗕𝗼𝗹𝗱", 0x1D5D4, 0x1D5EE, 0x1D7EC),
        _fancy_style("Ⓑⓤⓑⓑⓛⓔ", 0x24B6, 0x24D0),
        _fancy_style("Ｓｑｕａｒｅ", 0xFF21, 0xFF41, 0xFF10),
        _fancy_style("𝚂𝚖𝚊𝚕𝚕𝚌𝚊𝚙𝚜", 0x1D00, 0x0061),
    ]
    # Small caps: map a-z to small-cap glyphs (A-Z stay normal)
    _SMALL = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
    _sm_table = {ord(c): _SMALL[i] for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}
    _FANCY_STYLES[-1] = ("ꜱᴍᴀʟʟᴄᴀᴘꜱ", _sm_table)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fancy(?:\s+(\d+)\s+([\s\S]+)|\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _fancy(event):
        num = event.pattern_match.group(1)
        styled = event.pattern_match.group(2)
        plain = event.pattern_match.group(3)
        if not num and not plain:
            lines = ["✦ ━━━〔 🖋 FANCY FONTS 〕━━━ ✦",
                     "┃ usage: `.fancy <n> <text>` or `.fancy <text>`"]
            for i, (nm, tbl) in enumerate(_FANCY_STYLES, 1):
                sample = "Phantom".translate(tbl)
                lines.append(f"┃ `{i:2}` {nm} → {sample}")
            lines.append("✦ ━━━━━━━━━━━━━━━━━━ ✦")
            return await event.edit("\n".join(lines), link_preview=False)
        text = styled if styled else plain
        if num:
            idx = int(num)
            if not (1 <= idx <= len(_FANCY_STYLES)):
                return await event.edit(f"⚠️ Style number must be 1–{len(_FANCY_STYLES)} (see `.fancy`).")
            nm, tbl = _FANCY_STYLES[idx - 1]
            return await event.edit(f"{nm}:\n`{text.translate(tbl)}`", link_preview=False)
        out = ["✦ ━━━〔 🖋 FANCY 〕━━━ ✦"]
        for nm, tbl in _FANCY_STYLES:
            out.append(f"┃ {text.translate(tbl)}")
        out.append("✦ ━━━━━━━━━━━━━━━━━━ ✦")
        await event.edit("\n".join(out), link_preview=False)


COMMANDS_PARTY = {
    "description": "Party & games — fake actions, rigged dice, fancy fonts",
    "commands": [
        (".scam <action> [secs]", 'fake "typing…" status (11 actions)'),
        (".rdice [1-6]", "rigged Telegram dice 🎲"),
        (".dart [1-6] / .basket [1-5]", "rigged darts 🎯 / basketball 🏀"),
        (".football [1-5] / .bowl [1-6]", "rigged football ⚽ / bowling 🎳"),
        (".slotwin [1-64]", "rigged slot machine 🎰"),
        (".fancy [n] <text>", "fancy Unicode fonts (11 styles)"),
    ],
}

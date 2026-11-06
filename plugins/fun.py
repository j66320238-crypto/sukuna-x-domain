# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: FUN — text fun, games & web toys (no API keys needed)
#  NOTE: no imports here — everything comes from the header.
#  Inserted by assemble.py — do NOT run standalone.
# ============================================================================

_FLIP_TABLE = str.maketrans({
    "a": "ɐ", "b": "q", "c": "ɔ", "d": "p", "e": "ǝ", "f": "ɟ", "g": "ƃ",
    "h": "ɥ", "i": "ı", "j": "ɾ", "k": "ʞ", "l": "l", "m": "ɯ", "n": "u",
    "o": "o", "p": "d", "q": "b", "r": "ɹ", "s": "s", "t": "ʇ", "u": "n",
    "v": "ʌ", "w": "ʍ", "x": "x", "y": "ʎ", "z": "z",
    "A": "∀", "B": "ᗺ", "C": "Ɔ", "D": "ᗡ", "E": "Ǝ", "F": "Ⅎ", "G": "⅁",
    "H": "H", "I": "I", "J": "ᒿ", "K": "⋊", "L": "˥", "M": "W", "N": "N",
    "O": "O", "P": "Ԁ", "Q": "Ό", "R": "ᴚ", "S": "S", "T": "⊥", "U": "∩",
    "V": "Λ", "W": "M", "X": "X", "Y": "⅄", "Z": "Z",
    "0": "0", "1": "Ɩ", "2": "ᘔ", "3": "Ɛ", "4": "߈", "5": "ϛ",
    "6": "9", "7": "ㄥ", "8": "8", "9": "6",
    ".": "˙", ",": "'", "?": "¿", "!": "¡", "'": ",",
    '"': "„", "(": ")", ")": "(", "[": "]", "]": "[",
})

_8BALL = [
    "Yes, definitely. 🎱", "It is certain. ✅", "Without a doubt. 💯",
    "Yes! 🎉", "Most likely. 👍", "Outlook good. 🌤️",
    "Signs point to yes. 🔮", "Ask again later. 🕰️",
    "Better not tell you now. 🤫", "Cannot predict now. 🌫️",
    "Don't count on it. 🚫", "My reply is no. ❌",
    "Outlook not so good. 🌧️", "Very doubtful. 🤨",
    "Yes — in another universe. 🌌", "Absolutely NOT. 🙅",
    "Maybe… flip a coin. 🪙", "The stars say yes. ✨",
    "The stars say no. 🌑", "Do it! No fear. 💪",
]


# ============================================================================
#  TYPE-X ⌨️ — auto typewriter system
#  .type on          → ab HAR message automatic typewriter animation me jayega
#  .type off         → auto mode band (".type of" bhi chalega)
#  .type styles      → saare styles ki gallery
#  .type <style>     → style set karo (classic wave glitch scramble matrix
#                      pulse fire hearts zoom eraser reverse random)
#  .type speed 0.2   → frame speed set (0.05–1.0s)
#  .type status      → mode / style / speed card
#  .type <text>      → one-shot animation (purana behaviour, ab styles ke saath)
#  Flood-safe: edit throttle + jitter + frame cap + storm guard + single-lock
# ============================================================================

_TX_FILE = os.path.join(DATA_DIR, "typex.json")
_TX_STATE = {"on": False, "style": "classic", "speed": 0.15}
_TX_BUSY = set()        # message ids being animated (loop guard)
_TX_BOT_SENT = set()    # ids sent via client.send_message → auto-mode skip
_TX_LOCK = None         # single-animation lock (no edit storms)
_TX_LAST_AUTO = 0.0     # cooldown between auto animations

_TX_STYLES = ("classic", "wave", "glitch", "scramble", "matrix", "pulse",
              "fire", "hearts", "zoom", "eraser", "reverse", "random")
_TX_CURSORS = {
    "pulse": ("💓", "❤️", "💗", "💖"),
    "fire": ("🔥", "✨", "💥", "💨"),
    "hearts": ("❤️", "💖", "💘", "💕"),
}
_GLITCH_CHARS = "░▒▓█▓▒░▒▓"
_SCRAMBLE_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"
_TX_MAX_CHARS = 300     # isse lambe messages auto-animate nahi hote
_TX_MAX_FRAMES = 24     # per-message frame cap (flood-safe)
_TX_STYLE_HINTS = {
    "classic":  "classi typewriter cursor ▌",
    "wave":     "bold wave char-by-char",
    "glitch":   "░▒▓ glitch blocks resolve hote hain",
    "scramble": "random letters decode ho ke text bante hain",
    "matrix":   "binary bits ke saath type",
    "pulse":    "💓 heartbeat cursor",
    "fire":     "🔥 fire cursor",
    "hearts":   "❤️ love cursor",
    "zoom":     "letters spacing se zoom-in hote hain",
    "eraser":   "type → erase → retype story",
    "reverse":  "ulta type phir snap flip",
    "random":   "har message naya style 🎲",
}


def _tx_lock():
    global _TX_LOCK
    if _TX_LOCK is None:
        _TX_LOCK = asyncio.Lock()
    return _TX_LOCK


def _tx_load():
    global _TX_STATE
    try:
        with open(_TX_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            _TX_STATE["on"] = bool(data.get("on", False))
            if data.get("style") in _TX_STYLES:
                _TX_STATE["style"] = data["style"]
            try:
                _TX_STATE["speed"] = min(1.0, max(0.05, float(data.get("speed", 0.15))))
            except (TypeError, ValueError):
                pass
    except Exception:
        pass


def _tx_save():
    try:
        with open(_TX_FILE, "w", encoding="utf-8") as fh:
            json.dump(_TX_STATE, fh)
    except OSError:
        pass


_tx_load()


def _tx_steps(n: int) -> int:
    """chars-per-frame so total frames stay under the flood-safe cap."""
    if n <= 0:
        return 1
    return max(1, math.ceil(n / _TX_MAX_FRAMES))


def _tx_frames(text: str, style: str = None) -> list:
    """Build typewriter frames for a style. Last frame == original text."""
    style = (style or _TX_STATE.get("style") or "classic").lower()
    if style == "random":
        style = random.choice([s for s in _TX_STYLES if s != "random"])
    if style not in _TX_STYLES:
        style = "classic"
    n = len(text)
    if n <= 1:
        return [text]
    step = _tx_steps(n)
    frames = []

    if style == "classic":
        frames = [text[:i] + "▌" for i in range(1, n + 1, step)]

    elif style == "wave":
        for i in range(1, n + 1, step):
            head, tail = text[:i - 1], text[i - 1]
            if tail.isalnum():
                frames.append(f"{head}**{tail}**")
            else:
                frames.append(f"{head}{tail}")

    elif style == "glitch":
        frames.append("".join(random.choice(_GLITCH_CHARS)
                              for _ in range(min(n, 12))))
        for i in range(1, n + 1, step):
            rest = min(n - i, 14)
            tail = "".join(random.choice(_GLITCH_CHARS) for _ in range(max(rest, 0)))
            frames.append(text[:i] + tail)

    elif style == "scramble":
        for i in range(1, n + 1, step):
            pad = "".join(random.choice(_SCRAMBLE_CHARS) for _ in range(n - i))
            frames.append(text[:i] + pad)

    elif style == "matrix":
        for i in range(1, n + 1, step):
            bits = "".join(random.choice("01") for _ in range(4))
            frames.append(text[:i] + "▌" + bits)

    elif style in _TX_CURSORS:
        cyc = _TX_CURSORS[style]
        for j, i in enumerate(range(1, n + 1, step)):
            frames.append(text[:i] + cyc[j % len(cyc)])

    elif style == "zoom":
        frames.append(" ".join(list(text)))
        g = n
        while g > 1:
            g = max(1, g // 2)
            frames.append(" ".join(text[k:k + g] for k in range(0, n, g)))

    elif style == "eraser":
        full = [text[:i] for i in range(1, n + 1, step)]
        cut = max(1, int(n * 0.6))
        back = [text[:i] for i in range(cut, 0, -(step * 2))]
        redo = [text[:i] for i in range(1, n + 1, step * 2)]
        frames = full + back + redo

    elif style == "reverse":
        for i in range(1, n + 1, step):
            frames.append(text[:i][::-1])

    # dedupe consecutive + cap + guarantee the exact original as final frame
    out = []
    for f in frames:
        if not out or f != out[-1]:
            out.append(f)
    out = out[:_TX_MAX_FRAMES * 2]
    if not out or out[-1] != text:
        out.append(text)
    return out


async def _tx_animate(msg, text: str, style: str = None,
                      speed: float = None, plain: bool = False) -> bool:
    """Play typewriter frames on an existing message (flood-safe).

    plain=True → final edit raw text with NO entities (auto-mode: message
    bilkul waise hi dikhta hai jaise user ne type kiya tha).
    """
    frames = _tx_frames(text, style)
    if len(frames) < 2:
        return False
    speed = float(speed if speed is not None else _TX_STATE.get("speed", 0.15))
    floor = anim_floor() if safe_mode_on() else 0.05
    delay = max(speed, floor)
    last = None
    fails = 0
    for frame in frames:
        if frame == last:
            continue
        try:
            await throttle("edit")
            await msg.edit(frame, link_preview=False)
            last = frame
            fails = 0
        except MessageNotModifiedError:
            pass
        except FloodWaitError as e:
            note_flood(e.seconds)
            await asyncio.sleep(min(int(e.seconds or 0), 60) + 1)
            try:
                await throttle("edit")
                await msg.edit(frame, link_preview=False)
                last = frame
            except Exception:
                fails += 1
        except asyncio.CancelledError:
            raise
        except Exception:
            fails += 1
        if fails >= 3:
            break
        await safe_sleep(delay + random.uniform(0, 0.05), floor=0.0)
    # final frame — user ka exact original text
    if last != text:
        try:
            await throttle("edit")
            await msg.edit(text, link_preview=False,
                           parse_mode=None if plain else "md")
        except Exception:
            pass
    return True


def register_fun(client):
    """Fun text, games and web toys."""

    # ── mark bot-sent messages so TYPE-X auto-mode never animates them ────
    if not getattr(client, "_tx_patched", False):
        _orig_send = client.send_message

        async def _tx_marked_send(*args, **kwargs):
            msg = await _orig_send(*args, **kwargs)
            try:
                _TX_BOT_SENT.add(getattr(msg, "id", 0))
                if len(_TX_BOT_SENT) > 800:
                    _TX_BOT_SENT.clear()
            except Exception:
                pass
            return msg

        try:
            client.send_message = _tx_marked_send
            client._tx_patched = True
        except Exception:
            pass

    # ── TYPE-X auto mode: har outgoing plain message typewriter me ─────────
    @client.on(events.NewMessage(outgoing=True))
    async def _type_auto(event):
        global _TX_LAST_AUTO
        try:
            if not _TX_STATE["on"]:
                return
            text = (event.text or "").strip()
            if not text or text[0] in "./!#":
                return
            if len(text) < 2 or len(text) > _TX_MAX_CHARS:
                return
            if event.media or event.fwd_from or event.via_bot \
                    or getattr(event, "buttons", None):
                return
            if event.entities:
                return
            if event.id in _TX_BUSY or event.id in _TX_BOT_SENT:
                return
            if storm_active():       # 🚨 ban-storm → ID protection first
                return
            now = time.time()
            if now - _TX_LAST_AUTO < 1.5:
                return
            # premium-emoji auto mode ON + emoji text? → unko karne do
            try:
                from plugins.prememoji import _PE_STATE, EMOJI_RE
                if _PE_STATE.get("on") and EMOJI_RE.search(text):
                    return
            except Exception:
                pass
            lock = _tx_lock()
            if lock.locked():
                return               # ek waqt me ek animation — no edit storm
            async with lock:
                _TX_LAST_AUTO = time.time()
                _TX_BUSY.add(event.id)
                if len(_TX_BUSY) > 300:
                    _TX_BUSY.clear()
                try:
                    await _tx_animate(event, text, plain=True)
                finally:
                    _TX_BUSY.discard(event.id)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass

    # ---- .mock ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mock\s+(.+)$"))
    @client.flood_safe
    async def _mock(event):
        text = event.pattern_match.group(1).strip()
        out = "".join(c.upper() if i % 2 == 0 else c.lower()
                      for i, c in enumerate(text))
        await event.edit(f"🥴 {out}")

    # ---- .shout ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.shout\s+(.+)$"))
    @client.flood_safe
    async def _shout(event):
        text = event.pattern_match.group(1).strip()[:30]
        if not text:
            return await event.edit("❌ Usage: `.shout <text>`")
        lines = [" ".join(list(text))]
        for i, ch in enumerate(text[1:], 1):
            lines.append(" " * (i * 2) + ch + " " * (len(text) - 1 - i) * 0 + " " + ch)
        await event.edit("📢\n" + "\n".join(lines))

    # ---- faces ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.shrug(?:\s+(.*))?$"))
    @client.flood_safe
    async def _shrug(event):
        arg = (event.pattern_match.group(1) or "").strip()
        face = "¯\\_(ツ)_/¯"
        await event.edit(f"{arg} {face}".strip())

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.lenny$"))
    @client.flood_safe
    async def _lenny(event):
        await event.edit("( ͡° ͜ʖ ͡°)")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tableflip(?:\s+(.*))?$"))
    @client.flood_safe
    async def _tableflip(event):
        arg = (event.pattern_match.group(1) or "").strip()
        await event.edit(f"{arg} (╯°□°）╯︵ ┻━┻".strip())

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.unflip(?:\s+(.*))?$"))
    @client.flood_safe
    async def _unflip(event):
        arg = (event.pattern_match.group(1) or "").strip()
        await event.edit(f"{arg} ┬─┬ ノ( ゜-゜ノ)".strip())

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.flip\s+(.+)$"))
    @client.flood_safe
    async def _flip(event):
        text = event.pattern_match.group(1).strip()
        await event.edit(f"🙃 {text[::-1].translate(_FLIP_TABLE)}")

    # ---- .8ball ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.8ball\s+(.+)$"))
    @client.flood_safe
    async def _8ball(event):
        q = event.pattern_match.group(1).strip()
        await event.edit(f"🎱 **Q:** {q}\n**A:** {random.choice(_8BALL)}")

    # ---- .choose ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.choose\s+(.+)$"))
    @client.flood_safe
    async def _choose(event):
        raw = event.pattern_match.group(1).strip()
        opts = [o.strip() for o in raw.split("|")] if "|" in raw else \
               [o.strip() for o in raw.split(",")]
        opts = [o for o in opts if o]
        if len(opts) < 2:
            return await event.edit("❌ Usage: `.choose apple | banana | mango`")
        await event.edit(f"🎯 I choose: **{random.choice(opts)}**")

    # ---- .roll ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.roll(?:\s+(\d{1,3}d\d{1,3}|\d{1,4}))?$"))
    @client.flood_safe
    async def _roll(event):
        arg = (event.pattern_match.group(1) or "").strip().lower()
        if not arg:
            return await event.edit(f"🎲 You rolled: **{random.randint(1, 6)}**")
        if "d" in arg:
            n, sides = arg.split("d")
            n, sides = max(1, min(int(n or 1), 20)), max(2, min(int(sides), 1000))
            rolls = [random.randint(1, sides) for _ in range(n)]
            total = sum(rolls)
            detail = " + ".join(str(r) for r in rolls)
            return await event.edit(f"🎲 `{arg}` → {detail} = **{total}**")
        top = max(2, min(int(arg), 1000000))
        await event.edit(f"🎲 You rolled: **{random.randint(1, top)}** _(1–{top})_")

    # ---- .echo / .say ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:echo|say)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _echo(event):
        text = event.pattern_match.group(1).strip()
        await throttle("send")
        await event.delete()
        await client.send_message(await event.get_input_chat(), text)

    # ---- .type — TYPE-X master command (on/off/styles/speed/status/text) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.type(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _type(event):
        arg = (event.pattern_match.group(1) or "").strip()
        low = arg.lower()

        if not arg:
            return await event.edit(
                "✦ ━━━〔 ⌨️ **TYPE-X SYSTEM** 〕━━━ ✦\n"
                "┃ `.type on` — har message auto animation me\n"
                "┃ `.type off` — auto mode band\n"
                "┃ `.type styles` — 12 animation styles\n"
                "┃ `.type <style>` — style set (`.type glitch`)\n"
                "┃ `.type speed 0.2` — frame speed (0.05–1.0s)\n"
                "┃ `.type status` — mode/style/speed card\n"
                "┃ `.type <text>` — one-shot animation\n"
                "✦ ━━━━━━━━━━━━━━━━━━ ✦\n"
                "_🛡 Flood-safe: frame cap + throttle + storm guard_",
                link_preview=False)

        if low in ("on", "enable"):
            _TX_STATE["on"] = True
            _tx_save()
            return await event.edit(
                "✦ ━━━〔 ⌨️ **TYPE-X: ON** 〕━━━ ✦\n"
                "✅ Ab tumhara **har message** automatic typewriter animation\n"
                "   me jayega — jaise `.type` hota hai, bas auto!\n\n"
                f"🎬 Style: **{_TX_STATE['style']}** · ⚡ Speed: `{_TX_STATE['speed']}s`\n"
                "💡 `.type styles` — 12 styles · `.type off` — band karo\n"
                "_🛡 Storm/flood me auto-skip (ID safe)_",
                link_preview=False)

        if low in ("off", "disable", "of"):
            _TX_STATE["on"] = False
            _tx_save()
            return await event.edit(
                "⏹ **TYPE-X auto mode OFF** — messages ab normal jayenge.\n"
                "💡 `.type on` — dobara chalu · `.type <text>` — one-shot",
                link_preview=False)

        if low in ("status", "info"):
            return await event.edit(
                "✦ ━━━〔 ⌨️ **TYPE-X STATUS** 〕━━━ ✦\n"
                f"┃ Mode  : {'🟢 ON — har message animated' if _TX_STATE['on'] else '⛔ OFF'}\n"
                f"┃ Style : **{_TX_STATE['style']}**\n"
                f"┃ Speed : `{_TX_STATE['speed']}s` per frame\n"
                f"┃ Frames: ≤{_TX_MAX_FRAMES * 2}/message (flood-safe cap)\n"
                f"┃ Saved : restart ke baad bhi yaad ✅\n"
                "✦ ━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)

        if low in ("styles", "list"):
            style_list = "\n".join(
                f"┃ `{s:<10}` {_TX_STYLE_HINTS[s]}" for s in _TX_STYLES)
            return await event.edit(
                f"✦ ━━━〔 ⌨️ **TYPE-X STYLES ({len(_TX_STYLES)})** 〕━━━ ✦\n"
                f"{style_list}\n"
                "✦ ━━━━━━━━━━━━━━━━━━ ✦\n"
                "💡 `.type glitch` — set karo · `.type on` — auto mode\n"
                "_`random` = har message naya style_",
                link_preview=False)

        if low.split()[0] in ("speed", "spd") and len(low.split()) == 2:
            try:
                v = min(1.0, max(0.05, float(low.split()[1])))
            except ValueError:
                v = None
            if v is not None:
                _TX_STATE["speed"] = v
                _tx_save()
                return await event.edit(
                    f"⚡ TYPE-X speed set: **{v}s** per frame "
                    f"({'tez 🚀' if v <= 0.1 else 'smooth 🙂'})\n"
                    "_Range 0.05–1.0 · `.type speed 0.2`_",
                    link_preview=False)

        if low in _TX_STYLES:
            _TX_STATE["style"] = low
            _tx_save()
            return await event.edit(
                f"🎬 TYPE-X style set: **{low}** {_TX_STYLE_HINTS[low]}\n"
                f"⚡ Speed: `{_TX_STATE['speed']}s` · Mode: "
                f"{'🟢 ON' if _TX_STATE['on'] else '⛔ OFF'}\n"
                "_`.type on` se auto mode chalu karo_",
                link_preview=False)

        # ---- one-shot animation (purana behaviour — ab styles ke saath) ----
        text = arg[:_TX_MAX_CHARS]
        await _tx_animate(event, text)

    # ---- .joke ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.joke$"))
    @client.flood_safe
    async def _joke(event):
        await event.edit("🔍 Finding a joke…")
        try:
            data = json.loads(await _web_get("https://official-joke-api.appspot.com/random_joke"))
            await event.edit(f"😂 **{data['setup']}**\n\n_{data['punchline']}_")
        except Exception:
            await event.edit("❌ Couldn't fetch a joke. Try again later.")

    # ---- .quote ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.quote$"))
    @client.flood_safe
    async def _quote(event):
        await event.edit("🔍 Finding a quote…")
        try:
            data = json.loads(await _web_get("https://dummyjson.com/quotes/random"))
            await event.edit(f"💬 _“{data['quote']}”_\n\n— **{data['author']}**")
        except Exception:
            await event.edit("❌ Couldn't fetch a quote. Try again later.")

    # ---- .ud ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ud\s+(.+)$"))
    @client.flood_safe
    async def _ud(event):
        word = event.pattern_match.group(1).strip()[:60]
        await event.edit(f"🔍 Looking up **{word}**…")
        try:
            url = ("https://api.urbandictionary.com/v0/define?term="
                   + quote_plus(word))
            data = json.loads(await _web_get(url))
            entries = data.get("list") or []
            if not entries:
                return await event.edit(f"❌ No definition for **{word}**.")
            top = entries[0]
            defi = (top.get("definition") or "—").strip()[:900]
            ex = (top.get("example") or "").strip()[:400]
            ups = top.get("thumbs_up", 0)
            text = f"📖 **{word}**  (👍 {ups})\n\n{defi}"
            if ex:
                text += f"\n\n_Example:_ {ex}"
            await event.edit(text, link_preview=False)
        except Exception:
            await event.edit("❌ Couldn't fetch the definition. Try again later.")

    # ---- .meme ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.meme$"))
    @client.flood_safe
    async def _meme(event):
        await event.edit("🔍 Finding a meme…")
        dest = f"web_{event.id}.jpg"
        try:
            data = json.loads(await _web_get("https://meme-api.com/gimme"))
            url = data.get("url")
            if not url:
                return await event.edit("❌ No meme right now. Try again.")
            await _web_dl(url, dest)
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), dest,
                caption=f"🤣 **{data.get('title', 'meme')}**\n👍 {data.get('ups', '?')} ups",
                reply_to=event.id,
            )
            await event.delete()
        except Exception:
            try:
                await event.edit("❌ Couldn't fetch a meme. Try again later.")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .dog ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dog$"))
    @client.flood_safe
    async def _dog(event):
        await event.edit("🔍 Finding a doggo…")
        dest = f"web_{event.id}.jpg"
        try:
            data = json.loads(await _web_get("https://dog.ceo/api/breeds/image/random"))
            url = data.get("message")
            if not url:
                return await event.edit("❌ No doggo right now. Try again.")
            await _web_dl(url, dest)
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), dest,
                caption="🐶 Woof!", reply_to=event.id,
            )
            await event.delete()
        except Exception:
            try:
                await event.edit("❌ Couldn't fetch a dog. Try again later.")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .cat ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.cat$"))
    @client.flood_safe
    async def _cat(event):
        await event.edit("🔍 Finding a cat…")
        dest = f"web_{event.id}.jpg"
        try:
            data = json.loads(await _web_get("https://api.thecatapi.com/v1/images/search"))
            url = (data[0] or {}).get("url") if data else None
            if not url:
                return await event.edit("❌ No cat right now. Try again.")
            await _web_dl(url, dest)
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), dest,
                caption="🐱 Meow!", reply_to=event.id,
            )
            await event.delete()
        except Exception:
            try:
                await event.edit("❌ Couldn't fetch a cat. Try again later.")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass


COMMANDS_FUN = {
    "description": "Fun & Games",
    "commands": [
        (".mock <text>", "sPoNgE tExT"),
        (".shout <text>", "big vertical text"),
        (".shrug [.lenny .tableflip .unflip]", "classic text faces"),
        (".flip <text>", "upside-down text"),
        (".8ball <question>", "magic 8-ball answers"),
        (".choose a | b | c", "random picker"),
        (".roll [N|XdY]", "dice roller"),
        (".echo / .say <text>", "repeat text (deletes command)"),
        (".type on / .type off", "AUTO typewriter mode — har message animated"),
        (".type styles / <style>", "12 styles: glitch wave matrix scramble…"),
        (".type speed 0.2 / status", "frame speed / TYPE-X status card"),
        (".type <text>", "one-shot typewriter (current style me)"),
        (".joke .quote .ud <word>", "joke / quote / urban dictionary"),
        (".meme .dog .cat", "random meme / dog / cat pics"),
    ],
}

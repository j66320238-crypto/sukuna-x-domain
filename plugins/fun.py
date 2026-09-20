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


def register_fun(client):
    """Fun text, games and web toys."""

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

    # ---- .type ----  (self-contained typewriter — no cross-plugin dependency)
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.type\s+([\s\S]+)$"))
    @client.flood_safe
    async def _type(event):
        text = event.pattern_match.group(1).strip()[:200]
        if not text:
            return await event.edit("❌ Usage: `.type <text>`")
        frames = [text[:i] + "▌" for i in range(1, len(text) + 1)] + [text]
        last = None
        for frame in frames:
            if frame == last:
                continue
            try:
                await throttle("edit")
                await event.edit(frame)
                last = frame
            except MessageNotModifiedError:
                pass
            except FloodWaitError as e:
                note_flood(e.seconds)
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                break
            await safe_sleep(0.12, floor=0.0)

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
        (".type <text>", "typewriter effect with your text"),
        (".joke .quote .ud <word>", "joke / quote / urban dictionary"),
        (".meme .dog .cat", "random meme / dog / cat pics"),
    ],
}

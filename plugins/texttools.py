# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: TEXT TOOLS  (v5.3 — classic transforms from popular userbots)
#  .clap .vapor .str .zal .owo .lfy
#  NOTE: no imports here — everything comes from the header.
# ============================================================================

# Zalgo combining marks (up/down/mid) — kept SHORT so Telegram renders it fine
_ZAL_UP = "\u030d\u030e\u0304\u0305\u033f\u0311\u0306\u0310\u0352\u0357\u0351\u0307\u0308\u030a\u0342\u0343\u0344\u034a\u034b\u034c\u0303\u0302\u030c\u0350\u0300\u0301\u030b\u030f\u0312\u0313\u0314\u033d\u0309\u0363\u0364\u0365\u0366\u0367\u0368\u0369\u036a\u036b\u036c\u036d\u036e\u036f\u033e\u035b\u0346\u031a"
_ZAL_DOWN = "\u0316\u0317\u0318\u0319\u031c\u031d\u031e\u031f\u0320\u0324\u0325\u0326\u0329\u032a\u032b\u032c\u032d\u032e\u032f\u0330\u0331\u0332\u0333\u0339\u033a\u033b\u033c\u0345\u0347\u0348\u0349\u034d\u034e\u0353\u0354\u0355\u0356\u0359\u035a\u0323"
_ZAL_MID = "\u0315\u031b\u0340\u0341\u0358\u0321\u0322\u0327\u0328\u0334\u0335\u0336\u034f\u035c\u035d\u035e\u035f\u0360\u0362\u0338\u0337\u0361"


def _zalgify(text: str, intensity: int = 3) -> str:
    out = []
    for ch in text:
        if ch.isspace():
            out.append(ch)
            continue
        out.append(ch)
        for _ in range(random.randint(1, max(1, intensity))):
            out.append(random.choice(_ZAL_UP + _ZAL_DOWN + _ZAL_MID))
    return "".join(out)


_VAPOR_MAP = str.maketrans(
    "".join(chr(c) for c in range(0x21, 0x7F)),
    "".join(chr(c + 0xFEE0) for c in range(0x21, 0x7F)),
)
_VAPOR_MAP[ord(" ")] = "\u3000"


def register_texttools(client):

    # ---- .clap — 👏 between words -------------------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.clap(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _clap(event):
        text = event.pattern_match.group(1)
        if not text and event.is_reply:
            r = await event.get_reply_message()
            text = r.text if r else None
        if not text:
            return await event.edit("👏 Usage: `.clap <text>` or reply to a message.")
        await event.edit("👏 " + " 👏 ".join(text.split()) + " 👏", link_preview=False)

    # ---- .vapor — ｖａｐｏｒｗａｖｅ fullwidth ---------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.vapor(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _vapor(event):
        text = event.pattern_match.group(1)
        if not text and event.is_reply:
            r = await event.get_reply_message()
            text = r.text if r else None
        if not text:
            return await event.edit("🌫 Usage: `.vapor <text>` or reply to a message.")
        await event.edit(text.translate(_VAPOR_MAP), link_preview=False)

    # ---- .str — streeeeetched text ------------------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.str(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _stretch(event):
        text = event.pattern_match.group(1)
        if not text and event.is_reply:
            r = await event.get_reply_message()
            text = r.text if r else None
        if not text:
            return await event.edit("〰 Usage: `.str <text>` or reply to a message.")
        out = []
        for ch in text:
            out.append(ch)
            if ch.lower() in "aeiou":
                out.append(ch * random.randint(2, 4))
        await event.edit("".join(out), link_preview=False)

    # ---- .zal — z̴a̶l̷g̸o̷ chaos text -----------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.zal(?:\s+(\d+))?(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _zalgo(event):
        level = event.pattern_match.group(1)
        text = event.pattern_match.group(2)
        if not text and event.is_reply:
            r = await event.get_reply_message()
            text = r.text if r else None
        if not text:
            return await event.edit(
                "👹 Usage: `.zal <text>` or `.zal <level 1-5> <text>` or reply to a message.")
        lvl = int(level) if level else 3
        lvl = max(1, min(lvl, 5))
        await event.edit(_zalgify(text, lvl), link_preview=False)

    # ---- .owo — owofy --------------------------------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.owo(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _owo(event):
        text = event.pattern_match.group(1)
        if not text and event.is_reply:
            r = await event.get_reply_message()
            text = r.text if r else None
        if not text:
            return await event.edit("🐱 Usage: `.owo <text>` or reply to a message.")
        faces = ["(・`ω´・)", ";;w;;", "owo", "UwU", ">w<", "^w^"]
        t = re.sub(r"[rl]", "w", text)
        t = re.sub(r"[RL]", "W", t)
        t = re.sub(r"n([aeiou])", r"ny\1", t)
        t = re.sub(r"N([aeiou])", r"Ny\1", t)
        t = re.sub(r"ove", "uv", t)
        t += " " + random.choice(faces)
        await event.edit(t, link_preview=False)

    # ---- .lfy — Let Me Google That For You ----------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.lfy\s+([\s\S]+)$"))
    @client.flood_safe
    async def _lfy(event):
        q = event.pattern_match.group(1).strip()
        url = "https://lmgtfy.app/?q=" + quote_plus(q)
        await event.edit(
            f"🔎 Here you go, I googled it for you:\n[{q}]({url})",
            link_preview=False,
        )


COMMANDS_TEXTTOOLS = {
    "description": "Text transforms",
    "commands": [
        (".clap [text|reply]", "👏 clap 👏 between 👏 words"),
        (".vapor [text|reply]", "ｆｕｌｌｗｉｄｅ ｖａｐｏｒｗａｖｅ"),
        (".str [text|reply]", "streeeeetch the vowels"),
        (".zal [1-5] [text|reply]", "z̷a̶l̸g̷o̴ chaos text"),
        (".owo [text|reply]", "owo-ify your text UwU"),
        (".lfy <query>", "Let Me Google That For You link"),
    ],
}

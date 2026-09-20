# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine


# ============================================================================
# SECTION: EXTRA — 🌟 Extra Addons (Ultroid/CatUserbot inspired, SUKUNA-X edition)
# 20+ new commands: figlet, imdb, anime, waifu, pokedex, truth/dare,
# morse, wiki, covid, fakeid, qrcode, carbon color, insta, ytdl info, etc.
# All use SUKUNA-X safety engine, no crashes.
# ============================================================================

# ---- morse tables ----
_MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/', '.': '.-.-.-', ',': '--..--',
    '?': '..--..', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
}
_RMORSE = {v: k for k, v in _MORSE.items()}

# ---- small helpers ----
def _figlet_simple(text: str) -> str:
    """Very small figlet fallback if pyfiglet not installed — uses block."""
    try:
        import pyfiglet
        return pyfiglet.figlet_format(text, font="small")[:3800]
    except Exception:
        # fallback: big letters with box
        t = text[:20]
        top = " ".join(f" {c} " for c in t)
        mid = " ".join(f"[{c}]" for c in t)
        return f"```\n{top}\n{mid}\n{top}\n```"


def register_extra(client: TelegramClient) -> None:

    # ---- .figlet ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.figlet(?:\s+([\s\S]+))?$"))
    async def _figlet(event):
        txt = (event.pattern_match.group(1) or "").strip()
        if not txt:
            return await event.edit("✏️ `.figlet <text>` — fancy ASCII art.")
        art = _figlet_simple(txt)
        await event.edit(f"**{txt}**\n{art}", link_preview=False)

    # ---- .imdb ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.imdb(?:\s+([\s\S]+))?$"))
    async def _imdb(event):
        q = (event.pattern_match.group(1) or "").strip()
        if not q:
            return await event.edit("🎬 `.imdb <movie name>`")
        await event.edit(f"🔍 Searching IMDb for `{q}`…")
        try:
            # use OMDB-free style via web search? use _web_get to imdb search
            url = f"https://www.imdb.com/find/?q={urllib.parse.quote_plus(q)}"
            html = await _web_get(url)
            # crude parse first result title
            m = re.search(r'<a[^>]+href="/title/tt\d+[^"]*"[^>]*>([^<]+)</a>', html)
            title = m.group(1).strip() if m else q
            await event.edit(
                f"✦ ━━━〔 🎬 IMDb 〕━━━ ✦\n"
                f"┃ 🔎 Query: `{q}`\n"
                f"┃ 🎞 Title: **{title}**\n"
                f"┃ 🔗 https://www.imdb.com/find/?q={urllib.parse.quote_plus(q)}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)
        except Exception as e:
            await event.edit(f"❌ IMDb error: `{e}`")

    # ---- .anime ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.anime(?:\s+([\s\S]+))?$"))
    async def _anime(event):
        q = (event.pattern_match.group(1) or "").strip()
        if not q:
            return await event.edit("🍥 `.anime <name>` — search AniList.")
        await event.edit(f"🔍 Searching anime `{q}`…")
        try:
            # AniList GraphQL via _web_get not ideal (POST needed) — fallback to web
            url = f"https://anilist.co/search/anime?search={urllib.parse.quote_plus(q)}"
            await event.edit(
                f"✦ ━━━〔 🍥 ANIME 〕━━━ ✦\n"
                f"┃ 🔎 `{q}`\n"
                f"┃ 🔗 {url}\n"
                "┃ Tip: open link for details, trailers, scores.\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)
        except Exception as e:
            await event.edit(f"❌ Anime error: `{e}`")

    # ---- .waifu ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.waifu$"))
    async def _waifu(event):
        await event.edit("🌸 Fetching waifu…")
        try:
            j = await _web_get("https://api.waifu.pics/sfw/waifu")
            data = json.loads(j)
            url = data.get("url")
            if url:
                await client.send_file(event.chat_id, url, caption="🌸 Waifu for you — SUKUNA-X DOMAIN")
                await event.delete()
            else:
                await event.edit("❌ No waifu found.")
        except Exception as e:
            await event.edit(f"❌ Waifu error: `{e}`")

    # ---- .pokedex ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pokedex(?:\s+(\S+))?$"))
    async def _pokedex(event):
        name = (event.pattern_match.group(1) or "").strip().lower()
        if not name:
            return await event.edit("🔴 `.pokedex <pokemon>` — e.g. `.pokedex pikachu`")
        await event.edit(f"🔍 Pokédex: `{name}`…")
        try:
            j = await _web_get(f"https://pokeapi.co/api/v2/pokemon/{urllib.parse.quote_plus(name)}")
            d = json.loads(j)
            types = ", ".join(t["type"]["name"] for t in d.get("types", []))
            await event.edit(
                f"✦ ━━━〔 🔴 POKEDEX 〕━━━ ✦\n"
                f"┃ 👾 {d.get('name','?').title()}  •  ID `{d.get('id','?')}`\n"
                f"┃ 📏 Height `{d.get('height')}` • Weight `{d.get('weight')}`\n"
                f"┃ 🧬 Types: `{types}`\n"
                f"┃ ⚔️ Base XP: `{d.get('base_experience','?')}`\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)
        except Exception as e:
            await event.edit(f"❌ Pokédex: `{name}` not found. ({e})")

    # ---- .truth / .dare ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.truth$"))
    async def _truth(event):
        try:
            j = await _web_get("https://api.truthordarebot.xyz/v1/truth")
            d = json.loads(j)
            q = d.get("question", "Tell a secret 😏")
            await event.edit(f"✦ ━━━〔 😏 TRUTH 〕━━━ ✦\n┃ {q}\n✦ ━━━━━━━━━━━━━━━━━━━━━ ✦")
        except Exception:
            qs = ["What is your biggest fear?", "Who is your crush?", "Tell your darkest secret 👀",
                  "Have you ever cheated?", "What is your worst habit?"]
            await event.edit(f"😏 **TRUTH:** {random.choice(qs)}")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dare$"))
    async def _dare(event):
        try:
            j = await _web_get("https://api.truthordarebot.xyz/v1/dare")
            d = json.loads(j)
            q = d.get("question", "Do 10 pushups 💪")
            await event.edit(f"✦ ━━━〔 😈 DARE 〕━━━ ✦\n┃ {q}\n✦ ━━━━━━━━━━━━━━━━━━━━━ ✦")
        except Exception:
            qs = ["Send a voice note singing 🎤", "Change your DP for 1 hour", "Do 20 pushups 💪",
                  "Text your crush 'I like you' 😂", "Dance for 30 seconds in group call"]
            await event.edit(f"😈 **DARE:** {random.choice(qs)}")

    # ---- .morse / .demorse ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.morse(?:\s+([\s\S]+))?$"))
    async def _morse(event):
        txt = (event.pattern_match.group(1) or "").strip().upper()
        if not txt:
            return await event.edit("📻 `.morse <text>` — text to morse.")
        out = " ".join(_MORSE.get(c, "?") for c in txt)
        await event.edit(f"📻 **MORSE:**\n`{out[:3800]}`", link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.demorse(?:\s+([\s\S]+))?$"))
    async def _demorse(event):
        code = (event.pattern_match.group(1) or "").strip()
        if not code:
            return await event.edit("📻 `.demorse <... --- ...>` — morse to text.")
        out = "".join(_RMORSE.get(c, "?") for c in code.split())
        await event.edit(f"📻 **TEXT:** `{out[:3800]}`", link_preview=False)

    # ---- .wiki ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.wiki(?:\s+([\s\S]+))?$"))
    async def _wiki(event):
        q = (event.pattern_match.group(1) or "").strip()
        if not q:
            return await event.edit("📚 `.wiki <query>` — Wikipedia summary.")
        await event.edit(f"📚 Wiki: `{q}`…")
        try:
            j = await _web_get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote_plus(q)}")
            d = json.loads(j)
            title = d.get("title", q)
            extract = d.get("extract", "No summary.")[:900]
            url = d.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{q}")
            await event.edit(
                f"✦ ━━━〔 📚 WIKI — {title} 〕━━━ ✦\n"
                f"┃ {extract}\n"
                f"┃ 🔗 {url}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)
        except Exception as e:
            await event.edit(f"❌ Wiki error: `{e}`")

    # ---- .covid ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.covid(?:\s+(\S+))?$"))
    async def _covid(event):
        country = (event.pattern_match.group(1) or "world").strip()
        await event.edit(f"🦠 COVID stats: `{country}`…")
        try:
            if country.lower() in ("world", "global", "all"):
                j = await _web_get("https://disease.sh/v3/covid-19/all")
            else:
                j = await _web_get(f"https://disease.sh/v3/covid-19/countries/{urllib.parse.quote_plus(country)}")
            d = json.loads(j)
            await event.edit(
                f"✦ ━━━〔 🦠 COVID — {d.get('country','World')} 〕━━━ ✦\n"
                f"┃ 😷 Cases: `{d.get('cases','?'):,}`\n"
                f"┃ 💀 Deaths: `{d.get('deaths','?'):,}`\n"
                f"┃ 💚 Recovered: `{d.get('recovered','?'):,}`\n"
                f"┃ 🧪 Active: `{d.get('active','?'):,}`\n"
                f"┃ 📅 Updated: {datetime.datetime.fromtimestamp(d.get('updated',0)/1000).strftime('%Y-%m-%d %H:%M') if d.get('updated') else '?'}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)
        except Exception as e:
            await event.edit(f"❌ COVID error: `{e}` — try `.covid india` / `.covid world`")

    # ---- .fakeid ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fakeid$"))
    async def _fakeid(event):
        names = ["Aarav Sharma", "Vivaan Patel", "Aditya Singh", "Sai Kumar", "Arjun Reddy",
                 "Ananya Gupta", "Diya Verma", "Ishita Rao", "Sneha Mehta", "Priya Nair"]
        cities = ["Mumbai", "Delhi", "Patna", "Bangalore", "Hyderabad", "Kolkata", "Pune", "Jaipur"]
        await event.edit(
            "✦ ━━━〔 🪪 FAKE ID 〕━━━ ✦\n"
            f"┃ 👤 Name: `{random.choice(names)}`\n"
            f"┃ 🎂 Age: `{random.randint(18,35)}`\n"
            f"┃ 📍 City: `{random.choice(cities)}`\n"
            f"┃ 📧 Email: `{''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))}@gmail.com`\n"
            f"┃ 📱 Phone: `+91{random.randint(7000000000,9999999999)}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .qrcode ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.qrcode(?:\s+([\s\S]+))?$"))
    async def _qrcode(event):
        txt = (event.pattern_match.group(1) or "").strip()
        if not txt:
            return await event.edit("🔳 `.qrcode <text>` — generate QR.")
        await event.edit("🔳 Generating QR…")
        try:
            url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={urllib.parse.quote_plus(txt)}"
            path = os.path.join(DATA_DIR, f"qr_{int(time.time())}.png")
            await _web_dl(url, path)
            await client.send_file(event.chat_id, path, caption=f"🔳 QR for: `{txt[:100]}`")
            await event.delete()
            try: os.remove(path)
            except Exception: pass
        except Exception as e:
            await event.edit(f"❌ QR error: `{e}`")

    # ---- .ccarbon (color carbon) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ccarbon(?:\s+([\s\S]+))?$"))
    async def _ccarbon(event):
        code = event.pattern_match.group(1)
        if not code:
            r = await event.get_reply_message()
            code = getattr(r, "text", None) or getattr(r, "message", None) if r else None
        if not code:
            return await event.edit("🎨 `.ccarbon <code>` or reply to code — color carbon.")
        await event.edit("🎨 Making color carbon…")
        try:
            # use carbonara API
            colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F"]
            theme = random.choice(["dracula", "material", "monokai", "nord", "one-dark"])
            # fallback: use normal carbon via plugins/tools if exists
            # here we just send text as file with caption
            await event.edit(
                f"✦ ━━━〔 🎨 CARBON 〕━━━ ✦\n"
                f"┃ Theme: `{theme}` • Color: `{random.choice(colors)}`\n"
                f"┃ Code: {len(code)} chars\n"
                "┃ Use `.carbon <code>` for image.\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)
        except Exception as e:
            await event.edit(f"❌ Carbon error: `{e}`")

    # ---- .insta ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.insta(?:\s+(\S+))?$"))
    async def _insta(event):
        url = (event.pattern_match.group(1) or "").strip()
        if not url or "instagram.com" not in url:
            return await event.edit("📸 `.insta <instagram url>` — download info.")
        await event.edit(
            f"✦ ━━━〔 📸 INSTA 〕━━━ ✦\n"
            f"┃ 🔗 {url}\n"
            f"┃ 💡 Tip: Use @SaveAsBot or https://igram.world for full download.\n"
            f"┃ SUKUNA-X will auto-download in future updates.\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .ytdl info ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ytdl(?:\s+(\S+))?$"))
    async def _ytdl(event):
        url = (event.pattern_match.group(1) or "").strip()
        if not url:
            return await event.edit("▶️ `.ytdl <youtube url>` — get video info.")
        await event.edit(
            f"✦ ━━━〔 ▶️ YTDL 〕━━━ ✦\n"
            f"┃ 🔗 {url}\n"
            f"┃ 📥 Use `.song` / `.vsong` to download, or @YTAudioBot\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .autobio (fake, safe) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.autobio(?:\s+(on|off))?$"))
    async def _autobio(event):
        arg = (event.pattern_match.group(1) or "").lower()
        if arg not in ("on", "off"):
            return await event.edit("🔄 `.autobio on|off` — auto bio with time (safe, local).")
        save_store("autobio", {"on": arg == "on"})
        if arg == "on":
            await event.edit("🔄 Auto-bio ON — will update bio every 60s with time. `.autobio off` to stop.")
            async def _loop():
                while load_store("autobio").get("on"):
                    try:
                        t = datetime.datetime.now().strftime("%H:%M")
                        await client(UpdateProfileRequest(about=f"⚡ SUKUNA-X DOMAIN • {t} • Farmer ON"))
                    except Exception:
                        pass
                    await asyncio.sleep(60)
            stop_processes["autobio"] = asyncio.ensure_future(_loop())
        else:
            t = stop_processes.pop("autobio", None)
            if t and not t.done():
                t.cancel()
            await event.edit("⏹ Auto-bio OFF.")

    # ---- .accounts — list saved accounts (Telegram) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.accounts$"))
    async def _accounts(event):
        cfg = load_store("accounts") or {}
        accs = cfg.get("accounts", [])
        if not accs:
            return await event.edit("📭 No saved accounts — add via terminal at startup.")
        last = cfg.get("last_used", "—")
        lines = ["✦ ━━━〔 👥 SAVED ACCOUNTS 〕━━━ ✦"]
        for i, a in enumerate(accs, 1):
            sess = "✅" if os.path.exists(os.path.join(DATA_DIR, f"{a.get('name')}.session")) or os.path.exists(f"{a.get('name')}.session") else "❌"
            mark = " ← last" if a.get("name") == last else ""
            lines.append(f"┃ {i}. `{a.get('name')}` • {a.get('phone','—')} • api_id `{a.get('api_id')}` • {sess}{mark}")
        lines.append(f"┃ Last used: `{last}`")
        lines.append("┃ Manage at startup: [N] new, [D] delete, or set SUKUNA_ACCOUNT env")
        lines.append("✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦")
        await event.edit("\n".join(lines), link_preview=False)

    log.info("Extra registered: 15+ addon commands (figlet, imdb, anime, waifu, pokedex, truth/dare, morse, wiki, covid, fakeid, qrcode, ccarbon, insta, ytdl, autobio, accounts)")


COMMANDS_EXTRA = {
    "description": "Extra Addons",
    "commands": [
        (".figlet <text>", "fancy ASCII art"),
        (".imdb <movie>", "IMDb search"),
        (".anime <name>", "anime search (AniList)"),
        (".waifu", "random waifu image"),
        (".pokedex <name>", "pokemon info"),
        (".truth", "random truth question"),
        (".dare", "random dare"),
        (".morse <text>", "text → morse"),
        (".demorse <code>", "morse → text"),
        (".wiki <query>", "Wikipedia summary"),
        (".covid [country]", "COVID stats"),
        (".fakeid", "fake identity generator"),
        (".qrcode <text>", "generate QR code"),
        (".ccarbon <code>", "color carbon info"),
        (".insta <url>", "Instagram info"),
        (".ytdl <url>", "YouTube info"),
        (".autobio on|off", "auto bio with time"),
        (".accounts", "list saved accounts (startup manager)"),
    ],
}

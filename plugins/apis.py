# ── SUKUNA-X DOMAIN v7.2 plugin ─────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: APIS — 🌐 API Toolkit (13 naye commands, sab free, NO API keys)
#  Har endpoint live-tested: agify · genderize · nationalize · catfact ·
#  uselessfacts · kanye.rest · random-d.uk · coffee.alexflipnote ·
#  riddles-api · horoscope-app-api · dns.google · news RSS · NASA APOD
#  Fail-safe: har command graceful error message deta hai, kabhi crash nahi.
# ============================================================================

COMMANDS_APIS = {
    "description": "API Toolkit (13)",
    "type": "Utility",
    "commands": [
        (".age <name>", "age guess from name (census data)"),
        (".gender <name>", "gender probability for a name"),
        (".nat <name>", "top nationalities for a name"),
        (".horo <sign>", "daily horoscope (desi naam bhi: singh, mesh…)"),
        (".news [topic]", "top headlines / topic news search"),
        (".dns <domain> [type]", "DNS records lookup (A/AAAA/MX/TXT…)"),
        (".riddle", "riddle + 10s baad answer reveal"),
        (".catfact", "random cat fact 🐱"),
        (".uselessfact", "random useless fact 🤓"),
        (".kanye", "random Kanye West quote 🎤"),
        (".duck", "random duck pic 🦆"),
        (".cafe", "random coffee pic ☕"),
        (".nasa", "NASA astronomy picture of the day 🔭"),
    ],
}

# desi + western horoscope sign mapping
_HORO_SIGNS = {
    "aries": "aries", "mesha": "aries", "mesh": "aries",
    "taurus": "taurus", "vrishabha": "taurus", "bull": "taurus",
    "gemini": "gemini", "mithuna": "gemini", "mithun": "gemini",
    "cancer": "cancer", "karka": "cancer", "kark": "cancer",
    "leo": "leo", "simha": "leo", "singh": "leo",
    "virgo": "virgo", "kanya": "virgo",
    "libra": "libra", "tula": "libra",
    "scorpio": "scorpio", "vrishchika": "scorpio", "vrishchik": "scorpio",
    "sagittarius": "sagittarius", "dhanu": "sagittarius",
    "capricorn": "capricorn", "makara": "capricorn", "makar": "capricorn",
    "aquarius": "aquarius", "kumbha": "aquarius", "kumbh": "aquarius",
    "pisces": "pisces", "meena": "pisces",
}
_HORO_EMOJI = {
    "aries": "♈", "taurus": "♉", "gemini": "♊", "cancer": "♋",
    "leo": "♌", "virgo": "♍", "libra": "♎", "scorpio": "♏",
    "sagittarius": "♐", "capricorn": "♑", "aquarius": "♒", "pisces": "♓",
}

_DNS_TYPES = {1: "A", 2: "NS", 5: "CNAME", 6: "SOA", 12: "PTR",
              15: "MX", 16: "TXT", 28: "AAAA", 33: "SRV", 65: "HTTPS"}
_DNS_QUERY = {"a": 1, "aaaa": 28, "mx": 15, "txt": 16, "ns": 2,
              "cname": 5, "srv": 33, "any": 255}


def _horo_resolve(raw: str):
    """user input → (western_sign, pretty_name) — desi naam bhi chalega."""
    key = re.sub(r"[^a-z]", "", (raw or "").lower())
    return _HORO_SIGNS.get(key)


def _rss_parse(xml_text: str, limit: int = 8):
    """RSS <item> blocks → [(title, link), …] — CDATA-safe, no extra deps."""
    items = []
    for m in re.finditer(r"<item>(.*?)</item>", xml_text, re.S):
        block = m.group(1)
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
        l = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", block, re.S)
        if t:
            title = html.unescape(t.group(1).strip())
            link = (l.group(1).strip() if l else "")
            if title:
                items.append((title, link))
        if len(items) >= limit:
            break
    return items


def _dns_rows(answers: list) -> list:
    """DoH Answer[] → [(TYPE, TTL, data), …] human-readable."""
    rows = []
    for a in (answers or []):
        code = a.get("type", 0)
        rows.append((_DNS_TYPES.get(code, str(code)),
                     str(a.get("TTL", "?")), str(a.get("data", ""))))
    return rows


def register_apis(client):
    """API Toolkit — 13 free-API commands."""

    # ---- .age — agify.io ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.age\s+([\s\S]+)$"))
    @client.flood_safe
    async def _age(event):
        name = event.pattern_match.group(1).strip().split()[0][:40]
        if not name.isalpha():
            return await event.edit("❌ Naam likho: `.age michael`")
        await event.edit(f"🔍 Guessing age of **{name}**…")
        try:
            data = json.loads(await _web_get(
                "https://api.agify.io?name=" + quote_plus(name)))
            age = data.get("age")
            if age is None:
                return await event.edit(f"❌ `{name}` ke liye data nahi mila.")
            await event.edit(
                f"🎂 **{name}** ka estimated age: **{age} saal**\n"
                f"📊 Based on `{data.get('count', 0):,}` log online",
                link_preview=False)
        except Exception:
            await event.edit("❌ agify.io down hai — thodi der baad try karo.")

    # ---- .gender — genderize.io ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.gender\s+([\s\S]+)$"))
    @client.flood_safe
    async def _gender(event):
        name = event.pattern_match.group(1).strip().split()[0][:40]
        if not name.isalpha():
            return await event.edit("❌ Naam likho: `.gender michael`")
        await event.edit(f"🔍 Checking **{name}**…")
        try:
            data = json.loads(await _web_get(
                "https://api.genderize.io?name=" + quote_plus(name)))
            g = data.get("gender")
            if not g:
                return await event.edit(f"❌ `{name}` ke liye data nahi mila.")
            emoji = "👨" if g == "male" else "👩" if g == "female" else "🤷"
            await event.edit(
                f"{emoji} **{name}** → **{g.title()}** "
                f"(`{data.get('probability', 0) * 100:.0f}%` sure)\n"
                f"📊 `{data.get('count', 0):,}` records se",
                link_preview=False)
        except Exception:
            await event.edit("❌ genderize.io down hai — thodi der baad try karo.")

    # ---- .nat — nationalize.io ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.nat\s+([\s\S]+)$"))
    @client.flood_safe
    async def _nat(event):
        name = event.pattern_match.group(1).strip().split()[0][:40]
        if not name.isalpha():
            return await event.edit("❌ Naam likho: `.nat michael`")
        await event.edit(f"🌍 Checking nationalities for **{name}**…")
        try:
            data = json.loads(await _web_get(
                "https://api.nationalize.io?name=" + quote_plus(name)))
            countries = data.get("country") or []
            if not countries:
                return await event.edit(f"❌ `{name}` ke liye data nahi mila.")
            lines = [f"🌍 **{name}** ka naam in deshon me common:"]
            for c in countries[:5]:
                lines.append(f"┃ {c.get('country_id', '??')} — "
                             f"**{c.get('probability', 0) * 100:.1f}%**")
            await event.edit("\n".join(lines), link_preview=False)
        except Exception:
            await event.edit("❌ nationalize.io down hai — thodi der baad try karo.")

    # ---- .horo — daily horoscope ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.horo\s+([\s\S]+)$"))
    @client.flood_safe
    async def _horo(event):
        raw = event.pattern_match.group(1).strip()
        sign = _horo_resolve(raw)
        if not sign:
            return await event.edit(
                "❌ Sign pehchana nahi gaya.\n"
                "💬 Western: `.horo leo` — Desi: `.horo singh` / `.horo mesh`\n"
                "_Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio "
                "Sagittarius Capricorn Aquarius Pisces_",
                link_preview=False)
        await event.edit(f"{_HORO_EMOJI[sign]} Reading stars for **{sign.title()}**…")
        try:
            data = json.loads(await _web_get(
                "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/"
                "daily?sign=" + sign))
            d = data.get("data") or {}
            text = (d.get("horoscope") or "").strip()
            if not text:
                return await event.edit("❌ Aaj ka horoscope nahi mila.")
            date = d.get("date", "")
            await event.edit(
                f"{_HORO_EMOJI[sign]} **{sign.title()}** — {date}\n"
                f"{'─' * 26}\n{text[:900]}",
                link_preview=False)
        except Exception:
            await event.edit("❌ Horoscope service down — baad me try karo.")

    # ---- .news — headlines / topic search ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.news(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _news(event):
        topic = (event.pattern_match.group(1) or "").strip()
        try:
            if topic:
                url = ("https://news.google.com/rss/search?q="
                       + quote_plus(topic) + "&hl=en-IN&gl=IN&ceid=IN:en")
                await event.edit(f"📰 Searching news: **{topic}**…")
            else:
                url = "https://feeds.bbci.co.uk/news/rss.xml"
                await event.edit("📰 Fetching top headlines…")
            xml = await _web_get(url, timeout=20)
            items = _rss_parse(xml, 8)
            if not items:
                return await event.edit(
                    f"❌ News nahi mili{(' — ' + topic) if topic else ''}.")
            head = f"📰 **TOP NEWS**{' — ' + topic.title() if topic else ''}"
            lines = [head, "─" * 26]
            for i, (title, _link) in enumerate(items[:8], 1):
                lines.append(f"**{i}.** {title[:110]}")
            lines.append("─" * 26)
            lines.append("_Source: Google News / BBC · `.news <topic>` search_")
            await event.edit("\n".join(lines), link_preview=False)
        except Exception:
            await event.edit("❌ News feed down — thodi der baad try karo.")

    # ---- .dns — DNS over HTTPS (Google DoH) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dns\s+([\s\S]+)$"))
    @client.flood_safe
    async def _dns(event):
        raw = event.pattern_match.group(1).strip().split()
        if not raw:
            return await event.edit("❌ Usage: `.dns google.com` ya `.dns google.com mx`")
        domain = raw[0].lower().strip(".,")
        rtype = (raw[1].lower() if len(raw) > 1 else "a")
        code = _DNS_QUERY.get(rtype, 1)
        await event.edit(f"🌐 Resolving `{domain}` ({rtype.upper()})…")
        try:
            data = json.loads(await _web_get(
                "https://dns.google/resolve?name=" + quote_plus(domain)
                + "&type=" + str(code)))
            status = data.get("Status", -1)
            if status == 3:
                return await event.edit(f"❌ `{domain}` exist hi nahi karta (NXDOMAIN).")
            rows = _dns_rows(data.get("Answer") or [])
            if not rows:
                return await event.edit(
                    f"⚠️ `{domain}` ke liye {rtype.upper()} records nahi mile.")
            lines = [f"🌐 **DNS {rtype.upper()}** — `{data.get('Question', [{}])[0].get('name', domain)}`",
                     "─" * 26]
            for t, ttl, d in rows[:15]:
                lines.append(f"┃ `{t:<5}` `{ttl:>5}s` {d[:80]}")
            await event.edit("\n".join(lines), link_preview=False)
        except Exception:
            await event.edit("❌ DNS lookup fail — domain check karo.")

    # ---- .riddle — riddle + answer reveal ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.riddle$"))
    @client.flood_safe
    async def _riddle(event):
        await event.edit("🧠 Riddle laa raha hoon…")
        try:
            data = json.loads(await _web_get(
                "https://riddles-api.vercel.app/random"))
            riddle = (data.get("riddle") or "").strip()
            answer = (data.get("answer") or "").strip()
            if not riddle:
                return await event.edit("❌ Riddle nahi mili — baad me try karo.")
            await event.edit(
                f"🧠 **RIDDLE**\n{'─' * 26}\n{riddle[:600]}\n{'─' * 26}\n"
                "_⏳ Answer 10 second me…_", link_preview=False)
            await safe_sleep(10, floor=0.0)
            await event.edit(
                f"🧠 **RIDDLE**\n{'─' * 26}\n{riddle[:400]}\n{'─' * 26}\n"
                f"✅ **Answer:** {answer[:200]}",
                link_preview=False)
        except Exception:
            await event.edit("❌ Riddle service down — baad me try karo.")

    # ---- .catfact ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.catfact$"))
    @client.flood_safe
    async def _catfact(event):
        await event.edit("🐱 Fact laa raha hoon…")
        try:
            data = json.loads(await _web_get("https://catfact.ninja/fact"))
            fact = (data.get("fact") or "").strip()
            if not fact:
                raise RuntimeError("empty")
            await event.edit(f"🐱 **CAT FACT**\n{'─' * 26}\n{fact[:800]}",
                             link_preview=False)
        except Exception:
            await event.edit("❌ Cat facts down — baad me try karo.")

    # ---- .uselessfact / .ufact ----
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.(?:uselessfact|ufact)$"))
    @client.flood_safe
    async def _uselessfact(event):
        await event.edit("🤓 Useless fact laa raha hoon…")
        try:
            data = json.loads(await _web_get(
                "https://uselessfacts.jsph.pl/api/v2/facts/random"))
            fact = (data.get("text") or "").strip()
            if not fact:
                raise RuntimeError("empty")
            await event.edit(f"🤓 **USELESS FACT**\n{'─' * 26}\n{fact[:800]}",
                             link_preview=False)
        except Exception:
            await event.edit("❌ Fact service down — baad me try karo.")

    # ---- .kanye ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.kanye$"))
    @client.flood_safe
    async def _kanye(event):
        await event.edit("🎤 Kanye soch raha hai…")
        try:
            data = json.loads(await _web_get("https://api.kanye.rest"))
            quote = (data.get("quote") or "").strip()
            if not quote:
                raise RuntimeError("empty")
            await event.edit(f"🎤 **Kanye said:**\n_{quote[:400]}_",
                             link_preview=False)
        except Exception:
            await event.edit("❌ Kanye busy hai — baad me try karo.")

    # ---- .duck — random duck pic ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.duck$"))
    @client.flood_safe
    async def _duck(event):
        await event.edit("🦆 Duck dhundh raha hoon…")
        dest = os.path.join(DATA_DIR, f"duck_{event.id}.jpg")
        try:
            data = json.loads(await _web_get("https://random-d.uk/api/random"))
            url = data.get("url")
            if not url:
                return await event.edit("❌ Duck nahi mila.")
            await _web_dl(url, dest)
            await throttle("send")
            await client.send_file(await event.get_input_chat(), dest,
                                   caption="🦆 Quack!", reply_to=event.id)
            await event.delete()
        except Exception:
            try:
                await event.edit("❌ Duck API down — baad me try karo.")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .cafe — random coffee pic ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.cafe$"))
    @client.flood_safe
    async def _cafe(event):
        await event.edit("☕ Coffee ban rahi hai…")
        dest = os.path.join(DATA_DIR, f"cafe_{event.id}.jpg")
        try:
            data = json.loads(await _web_get(
                "https://coffee.alexflipnote.dev/random.json"))
            url = data.get("file")
            if not url:
                return await event.edit("❌ Coffee nahi mili.")
            await _web_dl(url, dest)
            await throttle("send")
            await client.send_file(await event.get_input_chat(), dest,
                                   caption="☕ Fresh brew!", reply_to=event.id)
            await event.delete()
        except Exception:
            try:
                await event.edit("❌ Coffee API down — baad me try karo.")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .nasa — astronomy picture of the day ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.nasa$"))
    @client.flood_safe
    async def _nasa(event):
        await event.edit("🔭 NASA se picture laa raha hoon…")
        try:
            data = json.loads(await _web_get(
                "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"))
            title = (data.get("title") or "Astronomy Picture").strip()
            expl = (data.get("explanation") or "").strip()[:900]
            date = data.get("date", "")
            if data.get("media_type") == "video":
                return await event.edit(
                    f"🔭 **{title}** ({date}) — _video of the day_\n"
                    f"🔗 {data.get('url', '')}", link_preview=False)
            url = data.get("hdurl") or data.get("url")
            if not url:
                raise RuntimeError("no url")
            dest = os.path.join(DATA_DIR, f"nasa_{event.id}.jpg")
            try:
                await _web_dl(url, dest, timeout=30)
                await throttle("send")
                await client.send_file(
                    await event.get_input_chat(), dest,
                    caption=f"🔭 **{title}** ({date})\n\n{expl}",
                    reply_to=event.id)
                await event.delete()
            finally:
                try:
                    if os.path.exists(dest):
                        os.remove(dest)
                except OSError:
                    pass
        except Exception:
            try:
                await event.edit(
                    "❌ NASA API busy (demo key rate-limit ho sakti hai) — "
                    "thodi der baad try karo.")
            except Exception:
                pass

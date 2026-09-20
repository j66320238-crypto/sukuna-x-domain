# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
# SECTION: NET — free web lookups (no API keys needed)
#   .wiki  .weather  .lyrics  .ipinfo  .crypto  .shorten  .unshorten  .gh
# ============================================================================
COMMANDS_NET = {
    "description": "Web Lookups (10)",
    "commands": [
        (".wiki <topic>", "Wikipedia summary"),
        (".weather [city]", "live weather (no city = your area)"),
        (".lyrics artist - title", "song lyrics"),
        (".ipinfo [ip]", "IP / ISP / country lookup"),
        (".crypto <coin>", "crypto price (BTC, ETH, …)"),
        (".currency 100 usd inr", "live currency conversion"),
        (".date [timezone]", "date & time (optional zone, e.g. Asia/Kolkata)"),
        (".shorten <url>", "make a short link"),
        (".unshorten <url>", "reveal the real link behind a short one"),
        (".gh <username>", "GitHub profile summary"),
    ],
}

_COIN_IDS = {
    "btc": "bitcoin", "eth": "ethereum", "usdt": "tether", "bnb": "binancecoin",
    "sol": "solana", "xrp": "ripple", "ada": "cardano", "doge": "dogecoin",
    "dot": "polkadot", "matic": "matic-network", "trx": "tron", "ltc": "litecoin",
    "shib": "shiba-inu", "ton": "the-open-network", "avax": "avalanche-2",
    "link": "chainlink", "atom": "cosmos", "near": "near", "etc": "ethereum-classic",
}


def _net_resolve(url: str, timeout: int = 12) -> str:
    """Follow redirects and return the final URL (executor-safe, blocking)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.geturl()


def register_net(client):
    """Free web lookups."""

    # ---- .wiki ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.wiki\s+([\s\S]+)$"))
    @client.flood_safe
    async def _wiki(event):
        query = event.pattern_match.group(1).strip()
        await event.edit("🔎 Searching Wikipedia…")
        try:
            url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
                   + urllib.parse.quote(query.replace(" ", "_")))
            data = json.loads(await _web_get(url))
            if data.get("type", "").endswith("not_found") or "extract" not in data:
                return await event.edit(f"❌ Nothing found for “{html.escape(query)}”.")
            link = (data.get("content_urls", {}).get("desktop", {}).get("page") or "")
            await event.edit(
                f"✦ ━━━〔 📚 {html.escape(data.get('title', query))} 〕━━━ ✦\n"
                f"{html.escape(data['extract'][:2200])}\n"
                + (f"\n🔗 {link}" if link else ""),
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Wikipedia error: `{exc}`")

    # ---- .weather ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.weather(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _weather(event):
        city = (event.pattern_match.group(1) or "").strip()
        await event.edit("🌤 Fetching weather…")
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
            data = json.loads(await _web_get(url))
            cur = (data.get("current_condition") or [{}])[0]
            area = (data.get("nearest_area") or [{}])[0]
            place = city or ", ".join(
                x.get("value", "") for x in area.get("areaName", []) if x.get("value")
            ) or "Your area"
            desc = (cur.get("weatherDesc") or [{}])[0].get("value", "-")
            await event.edit(
                "✦ ━━━〔 🌍 WEATHER 〕━━━ ✦\n"
                f"┃ 📍 Place    : **{html.escape(place)}**\n"
                f"┃ 🌡 Temp     : `{cur.get('temp_C', '-')}°C`  (feels `{cur.get('FeelsLikeC', '-')}°C`)\n"
                f"┃ ☁️ Condition: {html.escape(desc)}\n"
                f"┃ 💧 Humidity : `{cur.get('humidity', '-')}%`\n"
                f"┃ 🌬 Wind     : `{cur.get('windspeedKmph', '-')} km/h`\n"
                f"┃ 🔆 UV index : `{cur.get('uvIndex', '-')}`\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Weather error: `{exc}`\n💡 Try: `.weather Mumbai`")

    # ---- .lyrics ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.lyrics\s+([\s\S]+)$"))
    @client.flood_safe
    async def _lyrics(event):
        query = event.pattern_match.group(1).strip()
        if " - " not in query:
            return await event.edit(
                "❌ Format: `.lyrics <artist> - <title>`\n💡 Example: `.lyrics Arijit Singh - Kesariya`"
            )
        artist, title = [p.strip() for p in query.split(" - ", 1)]
        await event.edit("🎵 Looking for lyrics…")
        try:
            url = (f"https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/"
                   f"{urllib.parse.quote(title)}")
            data = json.loads(await _web_get(url))
            text = (data.get("lyrics") or "").strip()
            if not text:
                return await event.edit("❌ Lyrics not found for that song.")
            body = html.escape(text[:3200])
            await event.edit(
                f"✦ ━━━〔 🎵 {html.escape(title.upper())} 〕━━━ ✦\n"
                f"🎤 _{html.escape(artist)}_\n\n{body}\n\n"
                f"✦ ━━━〔 ⚡ SUKUNA-X 〕━━━ ✦",
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Lyrics error: `{exc}`")

    # ---- .ipinfo ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ipinfo(?:\s+([\d\.:a-fA-F]+))?$"))
    @client.flood_safe
    async def _ipinfo(event):
        ip = (event.pattern_match.group(1) or "").strip()
        await event.edit("🌐 Looking up IP…")
        try:
            data = json.loads(await _web_get(f"http://ip-api.com/json/{ip}"))
            if data.get("status") != "success":
                return await event.edit(f"❌ Lookup failed: {html.escape(str(data.get('message', 'unknown')))}")
            await event.edit(
                "✦ ━━━〔 🌐 IP INFO 〕━━━ ✦\n"
                f"┃ 🔢 IP      : `{html.escape(str(data.get('query')))}`\n"
                f"┃ 🏳 Country : {html.escape(str(data.get('country')))} "
                f"(`{html.escape(str(data.get('countryCode')))}`)\n"
                f"┃ 🏙 City    : {html.escape(str(data.get('city')))} · "
                f"{html.escape(str(data.get('regionName')))}\n"
                f"┃ 🛰 ISP     : {html.escape(str(data.get('isp')))} \n"
                f"┃ 🏢 Org     : {html.escape(str(data.get('org')))} \n"
                f"┃ 🕐 Timezone: `{html.escape(str(data.get('timezone')))}`\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ IP error: `{exc}`")

    # ---- .crypto ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.crypto(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _crypto(event):
        query = (event.pattern_match.group(1) or "btc").strip().lower()
        coin_id = _COIN_IDS.get(query)
        await event.edit("💹 Fetching price…")
        try:
            if not coin_id:
                found = json.loads(await _web_get(
                    f"https://api.coingecko.com/api/v3/search?query={urllib.parse.quote(query)}"
                ))
                coins = found.get("coins") or []
                if not coins:
                    return await event.edit(f"❌ Unknown coin: `{html.escape(query)}`")
                coin_id = coins[0]["id"]
            data = json.loads(await _web_get(
                "https://api.coingecko.com/api/v3/simple/price"
                f"?ids={urllib.parse.quote(coin_id)}&vs_currencies=usd,inr"
                "&include_24hr_change=true"
            ))
            info = data.get(coin_id)
            if not info:
                return await event.edit("❌ Price not available right now.")
            usd = info.get("usd", 0)
            inr = info.get("inr", 0)
            chg = info.get("usd_24h_change", 0) or 0
            arrow = "📈" if chg >= 0 else "📉"
            await event.edit(
                f"✦ ━━━〔 💹 {html.escape(coin_id.upper())} 〕━━━ ✦\n"
                f"┃ 💵 USD : `${usd:,.4f}`\n"
                f"┃ 🇮🇳 INR : `₹{inr:,.2f}`\n"
                f"┃ {arrow} 24h : `{chg:+.2f}%`\n"
                "┃ ℹ️ Source: CoinGecko\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Crypto error: `{exc}`")

    # ---- .shorten ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.shorten\s+(\S+)$"))
    @client.flood_safe
    async def _shorten(event):
        url = event.pattern_match.group(1).strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        await event.edit("🔗 Shortening…")
        try:
            short = (await _web_get(
                f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(url)}"
            )).strip()
            if not short.startswith("http"):
                return await event.edit("❌ Shortener refused that link.")
            await event.edit(
                "✦ ━━━〔 🔗 SHORT LINK 〕━━━ ✦\n"
                f"┃ 📎 Original : {html.escape(url[:80])}\n"
                f"┃ ✨ Short    : {html.escape(short)}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━ ✦",
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Shorten error: `{exc}`")

    # ---- .unshorten ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.unshorten\s+(\S+)$"))
    @client.flood_safe
    async def _unshorten(event):
        url = event.pattern_match.group(1).strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        await event.edit("🔍 Revealing the real link…")
        try:
            final = await asyncio.get_running_loop().run_in_executor(
                None, _net_resolve, url
            )
            await event.edit(
                "✦ ━━━〔 🕵️ REAL LINK 〕━━━ ✦\n"
                f"┃ 📎 Given : {html.escape(url[:90])}\n"
                f"┃ 🎯 Real  : {html.escape(final[:150])}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━ ✦",
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Could not resolve: `{exc}`")

    # ---- .gh ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.gh\s+(\S+)$"))
    @client.flood_safe
    async def _gh(event):
        user = event.pattern_match.group(1).strip().lstrip("@")
        await event.edit("🐙 Fetching GitHub profile…")
        try:
            data = json.loads(await _web_get(f"https://api.github.com/users/{urllib.parse.quote(user)}"))
            if data.get("message"):
                return await event.edit(f"❌ GitHub: {html.escape(str(data['message']))}")
            await event.edit(
                f"✦ ━━━〔 🐙 {html.escape(user)} 〕━━━ ✦\n"
                f"┃ 👤 Name    : {html.escape(str(data.get('name') or '—'))}\n"
                f"┃ 📝 Bio     : {html.escape(str(data.get('bio') or '—'))[:120]}\n"
                f"┃ 📦 Repos   : `{data.get('public_repos', 0)}`\n"
                f"┃ 👥 Followers: `{data.get('followers', 0)}`  ·  Following: `{data.get('following', 0)}`\n"
                f"┃ 📍 Location: {html.escape(str(data.get('location') or '—'))}\n"
                f"┃ 🔗 {html.escape(str(data.get('html_url') or ''))}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                parse_mode="html", link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ GitHub error: `{exc}`")

    # ---- .currency ----
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.currency\s+([\d.]+)\s+([A-Za-z]{3})\s+([A-Za-z]{3})$"))
    @client.flood_safe
    async def _currency(event):
        amt = event.pattern_match.group(1)
        frm = event.pattern_match.group(2).upper()
        to = event.pattern_match.group(3).upper()
        await event.edit(f"💱 Converting {amt} {frm} → {to}…")
        try:
            data = json.loads(await _web_get(
                f"https://open.er-api.com/v6/latest/{urllib.parse.quote(frm)}"))
            if data.get("result") != "success":
                return await event.edit("❌ Invalid base currency.")
            rates = data.get("rates", {})
            if to not in rates:
                return await event.edit(f"❌ Unknown target currency `{to}`.")
            val = float(amt) * float(rates[to])
            await event.edit(
                "✦ ━━━〔 💱 CURRENCY 〕━━━ ✦\n"
                f"┃ `{amt} {frm}` = `{val:,.2f} {to}`\n"
                f"┃ 1 {frm} = `{float(rates[to]):,.4f} {to}`\n"
                "✦ ━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        except ValueError:
            await event.edit("❌ Amount must be a number.")
        except Exception as exc:
            await event.edit(f"❌ Conversion failed: `{exc}`")

    # ---- .date ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.date(?:\s+(\S+))?$"))
    @client.flood_safe
    async def _date(event):
        tz_name = event.pattern_match.group(1)
        import datetime as _dt
        now = _dt.datetime.now()
        if tz_name:
            try:
                from zoneinfo import ZoneInfo
                now = _dt.datetime.now(ZoneInfo(tz_name))
                shown = tz_name
            except Exception:
                return await event.edit(f"❌ Unknown timezone `{tz_name}` (e.g. `Asia/Kolkata`).")
        else:
            shown = "local time"
        await event.edit(
            "✦ ━━━〔 📅 DATE & TIME 〕━━━ ✦\n"
            f"┃ 🕒 Time  : `{now.strftime('%I:%M:%S %p')}`\n"
            f"┃ 📆 Date  : `{now.strftime('%A, %d %B %Y')}`\n"
            f"┃ 🌏 Zone  : {html.escape(str(shown))}\n"
            f"┃ 🔢 ISO   : `{now.isoformat(timespec='seconds')}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    log.info("Net commands: wiki, weather, lyrics, ipinfo, crypto, shorten, unshorten, gh, currency, date")

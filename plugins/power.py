# ── SUKUNA-X DOMAIN v7.9 plugin ─────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: POWER — ⚡ Power Tools (13 naye commands, sab keyless APIs)
#  v7.9: dev / network / crypto utilities jo pehle missing the.
#  Endpoints: github api · rdap.org · thum.io · cloudflare speed test —
#  sab FREE, no API keys. Local tools: hash · b64 · uuid · epoch · lorem ·
#  colors · ssl · passgen. Fail-safe: har command graceful error, no crash.
# ============================================================================

COMMANDS_POWER = {
    "description": "Power Tools (13)",
    "type": "Utility",
    "commands": [
        (".passgen [len] [n]", "strong random passwords (default 16, max 64)"),
        (".gitrepo <user/repo>", "GitHub repo card — stars/forks/issues"),
        (".up <url>", "website status + response time"),
        (".netspeed", "real download speed test (Mbps)"),
        (".hash <text> [algo]", "md5 / sha1 / sha256 / sha512"),
        (".b64 <enc|dec> <text>", "base64 encode / decode"),
        (".uuid [n]", "UUID v4 generator (1-10)"),
        (".epoch [ts]", "unix timestamp ↔ date converter"),
        (".lorem [n]", "lorem ipsum paragraphs (1-10)"),
        (".colors <hex>", "color preview card + RGB/HSL"),
        (".ssl <domain>", "SSL certificate expiry check"),
        (".whois <domain>", "domain whois via RDAP (keyless)"),
        (".shot <url>", "website screenshot 📸"),
    ],
}

_USER_AGENT = {"User-Agent": "Mozilla/5.0 (SukunaX-Power/" + BOT_VERSION + ")"}

import colorsys  # noqa: E402 — .colors HSL conversion
import urllib.error  # noqa: E402 — HTTPError handling


def _run_blocking(fn, *a):
    return asyncio.get_running_loop().run_in_executor(None, fn, *a)


def _lorem_word(rng):
    W = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do "
         "eiusmod tempor incididunt ut labore et dolore magna aliqua enim "
         "minim veniam quis nostrud exercitation ullamco laboris nisi "
         "aliquip ex ea commodo consequat duis aute irure in reprehenderit "
         "voluptate velit esse cillum eu fugiat nulla pariatur excepteur "
         "sint occaecat cupidatat non proident sunt culpa qui officia "
         "deserunt mollit anim id est laborum").split()
    return rng.choice(W)


def _lorem_paras(n):
    rng = random.Random()
    out = []
    for _ in range(n):
        sents = []
        for _s in range(rng.randint(4, 7)):
            words = [_lorem_word(rng) for _ in range(rng.randint(8, 16))]
            s = " ".join(words)
            sents.append(s[0].upper() + s[1:] + ".")
        out.append(" ".join(sents))
    return out


def register_power(client):
    """⚡ Power Tools — v7.9."""

    # ---- .passgen [len] [n] --------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.passgen(?:\s+(\d+))?(?:\s+(\d+))?\s*$"))
    @client.flood_safe
    async def _passgen(event):
        ln = int(event.pattern_match.group(1) or 16)
        cnt = int(event.pattern_match.group(2) or 3)
        ln = max(8, min(ln, 64))
        cnt = max(1, min(cnt, 10))
        import secrets
        import string as _str
        alpha = _str.ascii_letters + _str.digits + "!@#$%^&*()-_=+?"
        lines = []
        for i in range(cnt):
            while True:
                pw = "".join(secrets.choice(alpha) for _ in range(ln))
                if (any(c.islower() for c in pw)
                        and any(c.isupper() for c in pw)
                        and any(c.isdigit() for c in pw)
                        and any(c in "!@#$%^&*()-_=+?" for c in pw)):
                    break
            lines.append(f"┃ {i + 1}. `{pw}`")
        await event.edit(
            "✦ ━━━〔 🔑 PASSWORD GENERATOR 〕━━━ ✦\n"
            f"┃ length: `{ln}` · strength: `crypto-grade`\n"
            + "\n".join(lines)
            + "\n✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .gitrepo <user/repo> -------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.gitrepo\s+([\w\-.]+)/([\w\-.]+)\s*$"))
    @client.flood_safe
    async def _gitrepo(event):
        user, repo = event.pattern_match.group(1), event.pattern_match.group(2)
        await event.edit(f"🔍 Fetching `{user}/{repo}`…", link_preview=False)

        def work():
            req = urllib.request.Request(
                f"https://api.github.com/repos/{user}/{repo}",
                headers=_USER_AGENT)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        try:
            d = await _run_blocking(work)
        except Exception as e:
            return await event.edit(
                f"❌ Repo lookup failed: `{html.escape(str(e)[:150])}`\n"
                "┃ usage: `.gitrepo user/repo`", link_preview=False)
        desc = (d.get("description") or "—")[:180]
        lic = ((d.get("license") or {}).get("spdx_id")) or "—"
        push = (d.get("pushed_at") or "—")[:10]
        lang = d.get("language") or "—"
        stars = d.get("stargazers_count", 0)
        forks = d.get("forks_count", 0)
        issues = d.get("open_issues_count", 0)
        await event.edit(
            "✦ ━━━〔 📦 GITHUB REPO 〕━━━ ✦\n"
            f"┃ 🏷 `{d.get('full_name', user + '/' + repo)}`\n"
            f"┃ 📝 {html.escape(desc)}\n"
            f"┃ ⭐ Stars : `{stars}`\n"
            f"┃ 🍴 Forks : `{forks}`\n"
            f"┃ 🐛 Issues: `{issues}`\n"
            f"┃ 🧠 Lang  : {html.escape(str(lang))}\n"
            f"┃ ⚖️ Lic   : {html.escape(str(lic))}\n"
            f"┃ 🕒 Push  : `{push}`\n"
            f"┃ 🔗 {d.get('html_url', '')}\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .up <url> -------------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.up\s+(\S+)\s*$"))
    @client.flood_safe
    async def _up(event):
        raw = event.pattern_match.group(1)
        url = raw if raw.startswith("http") else "https://" + raw
        await event.edit(f"🌐 Pinging `{html.escape(raw)}`…", link_preview=False)

        def work():
            import time as _t
            req = urllib.request.Request(url, headers=_USER_AGENT,
                                         method="GET")
            t0 = _t.time()
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    code = r.status
                    server = r.headers.get("Server", "—")
                    blob = r.read(2048)
            except urllib.error.HTTPError as e:
                code, server, blob = e.code, e.headers.get("Server", "—"), b""
            ms = int((_t.time() - t0) * 1000)
            return code, server, ms, len(blob)
        try:
            code, server, ms, blen = await _run_blocking(work)
        except Exception as e:
            return await event.edit(
                f"🔴 **DOWN / unreachable**\n┃ `{html.escape(raw)}`\n"
                f"┃ ⚠️ {html.escape(str(e)[:150])}", link_preview=False)
        ok = 200 <= code < 400
        await event.edit(
            "✦ ━━━〔 📡 SITE STATUS 〕━━━ ✦\n"
            f"┃ 🎯 `{html.escape(raw)}`\n"
            f"┃ {'🟢 UP' if ok else '🔴 DOWN'} — HTTP `{code}`\n"
            f"┃ ⏱ `{ms} ms` response time\n"
            f"┃ 🖥 Server: `{html.escape(str(server))}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .netspeed -------------------------------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.netspeed\s*$"))
    @client.flood_safe
    async def _netspeed(event):
        await event.edit("📶 Running download speed test…", link_preview=False)

        def work():
            import time as _t
            url = ("https://speed.cloudflare.com/__down?bytes="
                   + str(10 * 1024 * 1024))
            req = urllib.request.Request(url, headers=_USER_AGENT)
            t0 = _t.time()
            got = 0
            with urllib.request.urlopen(req, timeout=60) as r:
                while True:
                    chunk = r.read(262144)
                    if not chunk:
                        break
                    got += len(chunk)
            secs = max(_t.time() - t0, 0.001)
            mbps = got * 8 / secs / 1e6
            return got, secs, mbps
        try:
            got, secs, mbps = await _run_blocking(work)
        except Exception as e:
            return await event.edit(f"❌ Speed test failed: `{e}`",
                                    link_preview=False)
        bar = "█" * min(20, int(mbps / 5)) + "░" * max(0, 20 - min(20, int(mbps / 5)))
        await event.edit(
            "✦ ━━━〔 📶 NETWORK SPEED 〕━━━ ✦\n"
            f"┃ ⬇️ **{mbps:.1f} Mbps**\n"
            f"┃ {bar}\n"
            f"┃ 📦 `{got / 1048576:.1f} MB` in `{secs:.1f}s`\n"
            f"┃ 🖧 test file: cloudflare edge\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .hash <text> [algo] ---------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.hash\s+([\s\S]+?)(?:\s+(md5|sha1|sha256|sha512))?\s*$"))
    @client.flood_safe
    async def _hash(event):
        text, algo = event.pattern_match.group(1), (
            event.pattern_match.group(2) or "sha256").lower()
        import hashlib
        data = text.encode("utf-8")
        algos = ([algo] if algo in ("md5", "sha1", "sha256", "sha512")
                 else ["md5", "sha1", "sha256", "sha512"])
        lines = [f"┃ {a.upper()}: `{hashlib.new(a, data).hexdigest()}`"
                 for a in algos]
        await event.edit(
            "✦ ━━━〔 #️⃣ HASH 〕━━━ ✦\n"
            f"┃ input: `{html.escape(text[:60])}`\n" + "\n".join(lines)
            + "\n✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .b64 <enc|dec> <text> -------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.b64\s+(enc|dec)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _b64(event):
        mode, payload = event.pattern_match.group(1), event.pattern_match.group(2)
        import base64
        try:
            if mode == "enc":
                out = base64.b64encode(payload.encode("utf-8")).decode("ascii")
            else:
                pad = payload + "=" * (-len(payload) % 4)
                out = base64.b64decode(pad).decode("utf-8", "replace")
        except Exception as e:
            return await event.edit(f"❌ base64 error: `{e}`",
                                    link_preview=False)
        await event.edit(
            f"✦ ━━━〔 🔐 BASE64 {mode.upper()} 〕━━━ ✦\n"
            f"```{out[:1500]}```\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .uuid [n] -------------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.uuid(?:\s+(\d+))?\s*$"))
    @client.flood_safe
    async def _uuid(event):
        n = max(1, min(int(event.pattern_match.group(1) or 1), 10))
        import uuid as _uuid
        lines = [f"┃ `{str(_uuid.uuid4())}`" for _ in range(n)]
        await event.edit("✦ ━━━〔 🆔 UUID v4 〕━━━ ✦\n"
                         + "\n".join(lines)
                         + "\n✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                         link_preview=False)

    # ---- .epoch [ts] -----------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.epoch(?:\s+(-?\d+))?\s*$"))
    @client.flood_safe
    async def _epoch(event):
        import datetime as _dt
        ts = event.pattern_match.group(1)
        if ts:
            t = _dt.datetime.fromtimestamp(int(ts), _dt.timezone.utc)
            src = f"unix `{ts}`"
        else:
            t = _dt.datetime.now(_dt.timezone.utc)
            src = "right now"
        await event.edit(
            "✦ ━━━〔 ⏱ EPOCH TIME 〕━━━ ✦\n"
            f"┃ input : {src}\n"
            f"┃ UTC   : `{t.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"┃ IST   : `{t.astimezone(_dt.timezone(_dt.timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"┃ unix  : `{int(t.timestamp())}`\n"
            f"┃ ISO   : `{t.isoformat(timespec='seconds')}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .lorem [n] ------------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.lorem(?:\s+(\d+))?\s*$"))
    @client.flood_safe
    async def _lorem(event):
        n = max(1, min(int(event.pattern_match.group(1) or 2), 10))
        paras = _lorem_paras(n)
        body = "\n\n".join(paras)
        await event.edit("📜 **Lorem Ipsum**\n\n" + body[:3800],
                         link_preview=False)

    # ---- .colors <hex> ---------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.colors\s+#?([0-9a-fA-F]{6})\s*$"))
    @client.flood_safe
    async def _colors(event):
        hexv = event.pattern_match.group(1).lower()
        r, g, b = int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16)
        h, s_, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        l_ = (max(r, g, b) + min(r, g, b)) / 510
        info = (f"┃ RGB  : `{r}, {g}, {b}`\n"
                f"┃ HEX  : `#{hexv.upper()}`\n"
                f"┃ HSL  : `{int(h * 360)}°, {int(s_ * 100)}%, {int(l_ * 100)}%`\n"
                f"┃ HSV  : `{int(h * 360)}°, {int(v * 100)}%, {int(v * 100)}%`")
        if not _HAS_PIL:
            return await event.edit(info, link_preview=False)
        path = os.path.join(DATA_DIR, f"color_{hexv}.jpg")

        def work():
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (512, 512), (r, g, b))
            dr = ImageDraw.Draw(img)
            dr.rectangle([0, 400, 512, 512], fill=(255, 255, 255))
            dr.text((20, 430), f"#{hexv.upper()}  R{r} G{g} B{b}",
                    fill=(20, 20, 20))
            img.save(path, "JPEG", quality=88)
        await _run_blocking(work)
        await event.reply(file=path, message=f"🎨 **#{hexv.upper()}**\n{info}")
        try:
            await event.delete()
        except Exception:
            pass
        try:
            os.remove(path)
        except Exception:
            pass

    # ---- .ssl <domain> ---------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.ssl\s+([a-zA-Z0-9.\-]+)\s*$"))
    @client.flood_safe
    async def _ssl(event):
        dom = event.pattern_match.group(1)
        await event.edit(f"🔐 Checking SSL for `{dom}`…", link_preview=False)

        def work():
            import ssl as _ssl
            import socket as _socket
            import datetime as _dt
            from datetime import timezone as _tz, timedelta as _td
            ctx = _ssl.create_default_context()
            with _socket.create_connection((dom, 443), timeout=15) as sock:
                with ctx.wrap_socket(sock, server_hostname=dom) as s:
                    cert = s.getpeercert()
            nb = _dt.datetime.strptime(cert["notBefore"],
                                       "%b %d %H:%M:%S %Y %Z")
            na = _dt.datetime.strptime(cert["notAfter"],
                                       "%b %d %H:%M:%S %Y %Z")
            days = (na - _dt.datetime.now(_tz.utc).replace(tzinfo=None)
                    + _td(0)).days
            issuer = ""
            for k, v in cert.get("issuer", ()):
                if k in ("organizationName", "commonName") and not issuer:
                    issuer = v
            return nb, na, days, issuer
        try:
            nb, na, days, issuer = await _run_blocking(work)
        except Exception as e:
            return await event.edit(
                f"❌ SSL check failed for `{dom}`:\n"
                f"`{html.escape(str(e)[:150])}`", link_preview=False)
        status = ("🟢 VALID" if days > 15 else
                  ("🟠 EXPIRING SOON" if days > 0 else "🔴 EXPIRED"))
        await event.edit(
            "✦ ━━━〔 🔐 SSL CERTIFICATE 〕━━━ ✦\n"
            f"┃ 🌐 `{dom}`\n"
            f"┃ {status} — `{days} days` left\n"
            f"┃ 📅 Valid from : `{nb:%Y-%m-%d}`\n"
            f"┃ 📅 Valid till : `{na:%Y-%m-%d}`\n"
            f"┃ 🏢 Issuer     : {html.escape(issuer or '—')}\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .whois <domain> -------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.whois\s+([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\s*$"))
    @client.flood_safe
    async def _whois(event):
        dom = event.pattern_match.group(1)
        await event.edit(f"🔎 RDAP whois `{dom}`…", link_preview=False)

        def work():
            req = urllib.request.Request(
                f"https://rdap.org/domain/{dom}", headers=_USER_AGENT)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        try:
            d = await _run_blocking(work)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return await event.edit(
                    f"❌ `{dom}` — not registered / no RDAP record.",
                    link_preview=False)
            return await event.edit(f"❌ RDAP lookup failed: HTTP `{e.code}`",
                                    link_preview=False)
        except Exception as e:
            return await event.edit(f"❌ RDAP lookup failed: `{e}`",
                                    link_preview=False)
        registrar, created, updated, expires = "—", "—", "—", "—"
        for ev in d.get("events", []):
            act = ev.get("eventAction", "")
            val = (ev.get("eventDate") or "")[:10]
            if act == "registration":
                created = val
            elif act == "expiration":
                expires = val
            elif act == "last changed":
                updated = val
        for ent in d.get("entities", []):
            if "registrar" in ent.get("roles", []):
                for v in ent.get("vcardArray", [None, []])[1] or []:
                    if v and v[0] == "fn":
                        registrar = v[3]
        status = ", ".join((d.get("status") or [])[:4]) or "—"
        ns_raw = d.get("nameservers") or []
        if isinstance(ns_raw, list) and ns_raw:
            ns = ", ".join(
                (x.get("ldhName", "?") if isinstance(x, dict) else str(x))
                for x in ns_raw[:4])
        else:
            ns = "—"
        await event.edit(
            "✦ ━━━〔 🔎 DOMAIN WHOIS (RDAP) 〕━━━ ✦\n"
            f"┃ 🌐 `{dom}`\n"
            f"┃ 🏢 Registrar: {html.escape(str(registrar))}\n"
            f"┃ 📅 Created  : `{created}`\n"
            f"┃ 📅 Updated  : `{updated}`\n"
            f"┃ ⏳ Expires  : `{expires}`\n"
            f"┃ 🛡 Status  : {html.escape(str(status))}\n"
            f"┃ 🖧 NS      : `{html.escape(str(ns))}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .shot <url> -------------------------------------------------------
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.shot\s+(\S+)\s*$"))
    @client.flood_safe
    async def _shot(event):
        raw = event.pattern_match.group(1)
        url = raw if raw.startswith("http") else "https://" + raw
        await event.edit(f"📸 Capturing `{html.escape(raw)}`…",
                         link_preview=False)
        path = os.path.join(DATA_DIR, "shot_temp.jpg")

        def work():
            req = urllib.request.Request(
                "https://image.thum.io/get/width/1200/crop/900/" + url,
                headers=_USER_AGENT)
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) < 2000:
                raise RuntimeError("screenshot service returned no image")
            with open(path, "wb") as fh:
                fh.write(data)
        try:
            await _run_blocking(work)
        except Exception as e:
            return await event.edit(
                f"❌ Screenshot failed: `{html.escape(str(e)[:120])}`",
                link_preview=False)
        await event.reply(file=path, message=f"📸 `{html.escape(raw)}`")
        try:
            await event.delete()
        except Exception:
            pass
        try:
            os.remove(path)
        except Exception:
            pass

    log.info("Power commands: passgen, gitrepo, up, netspeed, hash, b64, "
             "uuid, epoch, lorem, colors, ssl, whois, shot")

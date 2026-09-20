# ── SUKUNA-X DOMAIN v7.0 plugin ──────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: WEB — 🌍 Advanced web & media tools (popular-repo inspired)
#  CatUserbot / Ultroid / Uniborg classics, rebuilt for SUKUNA-X:
#  .img .telegraph .carbon .define .pypi .yt .country .xkcd .shiba .fox
#  .json .getid — all free, no API keys.
# ============================================================================

_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

_BROWSER_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "x-requested-with": "XMLHttpRequest",
}


# ── small helpers ─────────────────────────────────────────────────────────
def _ddg_image_urls_sync(query: str, limit: int = 10):
    """DuckDuckGo image search (vqd token flow) — returns list of image URLs."""
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def _get(url, extra=None):
        h = dict(_BROWSER_UA)
        h.update(extra or {})
        req = urllib.request.Request(url, headers=h)
        return opener.open(req, timeout=25).read().decode("utf-8", "replace")

    page = _get("https://duckduckgo.com/?q=" + urllib.parse.quote(query))
    m = re.search(r'vqd=["\']?([\d-]+)', page)
    if not m:
        raise RuntimeError("image engine unavailable right now")
    vqd = m.group(1)
    js = _get(f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}"
              f"&vqd={vqd}&f=,,,,,&p=1",
              extra={"x-vqd": vqd,
                     "Referer": "https://duckduckgo.com/?q=" + urllib.parse.quote(query)})
    data = json.loads(js)
    out = []
    for r in data.get("results", []):
        u = r.get("image")
        if u and u.startswith("http"):
            out.append(u)
        if len(out) >= limit:
            break
    return out

def _telegraph_upload_sync(path: str):
    """Upload a file to telegra.ph, return full URL (blocking, run in executor)."""
    boundary = "----SukunaX" + str(random.randint(100000, 999999))
    ext = os.path.splitext(path)[1].lower()
    ctype = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".mp4": "video/mp4",
    }.get(ext, "application/octet-stream")
    with open(path, "rb") as fh:
        data = fh.read()
    fname = os.path.basename(path) or ("upload" + ext)
    head = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n").encode()
    body = head + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        "https://telegra.ph/upload", data=body,
        headers={**_UA, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=40) as r:
        resp = json.loads(r.read().decode())
    if isinstance(resp, list) and resp and resp[0].get("src"):
        return "https://telegra.ph" + resp[0]["src"]
    raise RuntimeError(str(resp)[:120])


def _jstr(s: str) -> str:
    """Decode JSON string escapes (\\u0026 etc.) safely."""
    try:
        return json.loads(f'"{s}"')
    except Exception:
        return s


def register_web(client):
    """Advanced web & media tools."""

    # ---- .img / .pic : multi-image search (DuckDuckGo engine, CatUserbot style) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:img|pic)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _img(event):
        raw = event.pattern_match.group(1).strip()
        parts = raw.rsplit(" ", 1)
        count = 3
        if len(parts) == 2 and parts[1].isdigit():
            count = max(1, min(int(parts[1]), 6))
            raw = parts[0]
        query = raw.strip()
        if not query:
            return await event.edit("❌ Usage: `.img <query> [1-6]`")
        await event.edit(f"🔍 Searching `{count}` image(s) for **{query}**…", link_preview=False)
        files = []
        try:
            urls = await asyncio.get_running_loop().run_in_executor(
                None, _ddg_image_urls_sync, query, count * 3)
            if not urls:
                return await event.edit("❌ No images found for that.")
            await event.edit(f"⬇️ Downloading {count} image(s)…", link_preview=False)
            for u in urls:
                if len(files) >= count:
                    break
                dest = os.path.join(DATA_DIR, f"img_{int(time.time()*1000)}_{len(files)}.jpg")
                try:
                    await _web_dl(u, dest, timeout=20)
                    if os.path.getsize(dest) > 500:
                        files.append(dest)
                except Exception:
                    try:
                        if os.path.exists(dest):
                            os.remove(dest)
                    except OSError:
                        pass
            if not files:
                return await event.edit("❌ Couldn't download any image (sources blocked).")
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), files,
                caption=f"🖼 **{query}** — {len(files)} image(s) ⚡ Sukuna-X",
                reply_to=event.id,
            )
            await event.delete()
        except Exception as exc:
            try:
                await event.edit(f"❌ Image search error: `{exc}`")
            except Exception:
                pass
        finally:
            for f in files:  # cleanup after album is sent
                try:
                    os.remove(f)
                except OSError:
                    pass

    # ---- .telegraph : media or text → telegra.ph link ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.telegraph$"))
    @client.flood_safe
    async def _telegraph(event):
        reply = await event.get_reply_message()
        if reply and reply.media:
            await event.edit("📤 Uploading media to Telegraph…")
            media = await client.download_media(reply, file=DATA_DIR)
            if not media:
                return await event.edit("❌ Couldn't download that media.")
            try:
                link = await asyncio.get_running_loop().run_in_executor(
                    None, _telegraph_upload_sync, media)
                await event.edit(
                    f"✦ ━━━〔 📤 TELEGRAPH 〕━━━ ✦\n🔗 {link}\n✦ ━━━━━━━━━━━━━━━━ ✦",
                    link_preview=True)
            except Exception as exc:
                await event.edit(f"❌ Telegraph error: `{exc}`")
            finally:
                try:
                    if media and os.path.exists(media):
                        os.remove(media)
                except OSError:
                    pass
            return
        text = None
        if reply and reply.text:
            text = reply.text
        if not text:
            return await event.edit("❌ Reply to **media** or **text** and run `.telegraph`.")
        await event.edit("📤 Publishing to Telegraph…")
        try:
            acc = json.loads(await _web_get(
                "https://api.telegra.ph/createAccount?short_name=SukunaX&author_name=Sukuna-X",
                timeout=20))
            token = ((acc.get("result") or {}).get("access_token"))
            if not token:
                return await event.edit("❌ Telegraph account error.")
            content = json.dumps([{"tag": "pre", "children": [text[:30000]]}])
            url = ("https://api.telegra.ph/createPage?access_token=" + token
                   + "&title=" + urllib.parse.quote("Sukuna-X Note")
                   + "&author_name=Sukuna-X&content=" + urllib.parse.quote(content))
            page = json.loads(await _web_get(url, timeout=20))
            link = ((page.get("result") or {}).get("url"))
            if not link:
                return await event.edit(f"❌ Telegraph: {str(page)[:150]}")
            await event.edit(
                f"✦ ━━━〔 📤 TELEGRAPH 〕━━━ ✦\n🔗 {link}\n✦ ━━━━━━━━━━━━━━━━ ✦",
                link_preview=True)
        except Exception as exc:
            await event.edit(f"❌ Telegraph error: `{exc}`")

    # ---- .carbon : code → beautiful image (carbonara API) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.carbon(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _carbon(event):
        code = (event.pattern_match.group(1) or "").strip()
        reply = await event.get_reply_message()
        if not code and reply and reply.text:
            code = reply.text
        if not code:
            return await event.edit("❌ Usage: `.carbon <code>` or reply to code.")
        await event.edit("🎨 Rendering carbon…")
        dest = os.path.join(DATA_DIR, f"carbon_{int(time.time())}.png")

        def _cook():
            payload = json.dumps({"code": code[:8000], "backgroundColor": "#161b22",
                                  "theme": "one-dark", "exportSize": "2x"}).encode()
            req = urllib.request.Request(
                "https://carbonara.solopov.dev/api/cook", data=payload,
                headers={**_UA, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            with open(dest, "wb") as fh:
                fh.write(data)
            return dest

        try:
            await asyncio.get_running_loop().run_in_executor(None, _cook)
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), dest,
                caption="🎨 Carbon by Sukuna-X", reply_to=event.id)
            await event.delete()
        except Exception as exc:
            await event.edit(f"❌ Carbon error: `{exc}`\n💡 The free carbon API may be down — retry later.")
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .define : dictionary (dictionaryapi.dev + DuckDuckGo fallback) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.define\s+([\s\S]+)$"))
    @client.flood_safe
    async def _define(event):
        word = event.pattern_match.group(1).strip().lower()
        await event.edit(f"📖 Defining **{word}**…")
        # source 1 — free dictionary API
        try:
            data = json.loads(await _web_get(
                "https://api.dictionaryapi.dev/api/v2/entries/en/"
                + urllib.parse.quote(word), timeout=15))
            if isinstance(data, list) and data:
                entry = data[0]
                meanings = entry.get("meanings") or [{}]
                m0 = meanings[0]
                pos = m0.get("partOfSpeech", "—")
                d0 = (m0.get("definitions") or [{}])[0]
                definition = d0.get("definition", "—")
                example = d0.get("example")
                phonetic = entry.get("phonetic") or ""
                return await event.edit(
                    f"✦ ━━━〔 📖 {html.escape(word.upper())} 〕━━━ ✦\n"
                    f"┃ 🔤 Type    : `{phonetic}`\n"
                    f"┃ 🏷 Class   : {html.escape(pos)}\n"
                    f"┃ 📝 Meaning: {html.escape(definition[:600])}\n"
                    + (f"┃ 💬 Example: _{html.escape(example[:200])}_\n" if example else "")
                    + "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                    parse_mode="html", link_preview=False)
        except Exception:
            pass
        # source 2 — DuckDuckGo instant answers
        try:
            ddg = json.loads(await _web_get(
                "https://api.duckduckgo.com/?q=" + urllib.parse.quote(word)
                + "&format=json&no_html=1&skip_disambig=1", timeout=15))
            definition = (ddg.get("Definition") or "").strip()
            if definition:
                src = ddg.get("DefinitionSource", "")
                return await event.edit(
                    f"✦ ━━━〔 📖 {html.escape(word.upper())} 〕━━━ ✦\n"
                    f"📝 {html.escape(definition[:800])}\n"
                    + (f"🔗 _via {html.escape(src)}_\n" if src else "")
                    + "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                    parse_mode="html", link_preview=False)
        except Exception:
            pass
        await event.edit(f"❌ No definition found for `{word}`. Check spelling.")

    # ---- .pypi : python package info ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pypi\s+(\S+)$"))
    @client.flood_safe
    async def _pypi(event):
        pkg = event.pattern_match.group(1).strip().lstrip("/")
        await event.edit(f"🐍 Looking up **{pkg}** on PyPI…")
        try:
            data = json.loads(await _web_get(
                f"https://pypi.org/pypi/{urllib.parse.quote(pkg)}/json", timeout=15))
            info = data.get("info") or {}
            releases = data.get("releases") or {}
            await event.edit(
                f"✦ ━━━〔 🐍 {html.escape(info.get('name', pkg))} 〕━━━ ✦\n"
                f"┃ 📦 Version : `{info.get('version', '—')}`\n"
                f"┃ 📝 Summary : {html.escape(str(info.get('summary') or '—')[:250])}\n"
                f"┃ 👤 Author  : {html.escape(str(info.get('author') or '—'))}\n"
                f"┃ 📄 License : {html.escape(str(info.get('license') or '—')[:80])}\n"
                f"┃ 🗂 Releases: `{len(releases)}`\n"
                f"┃ 🔗 {html.escape(str(info.get('package_url') or ''))}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                parse_mode="html", link_preview=False)
        except Exception as exc:
            await event.edit(f"❌ PyPI error: `{exc}`")

    # ---- .yt : YouTube search (no API key) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.yt\s+([\s\S]+)$"))
    @client.flood_safe
    async def _yt(event):
        query = event.pattern_match.group(1).strip()
        await event.edit(f"▶️ Searching YouTube for **{query}**…")
        try:
            page_html = await _web_get(
                "https://www.youtube.com/results?search_query="
                + urllib.parse.quote(query), timeout=20)
            results = re.findall(
                r'"videoRenderer":\{"videoId":"([\w-]{11})".{0,400}?"title":\{"runs":\[\{"text":"(.*?)"\}',
                page_html, re.S)
            seen, out = set(), []
            for vid, title in results:
                if vid in seen:
                    continue
                seen.add(vid)
                out.append((vid, _jstr(title)))
                if len(out) >= 6:
                    break
            if not out:
                return await event.edit("❌ No YouTube results found.")
            lines = [f"✦ ━━━〔 ▶️ YOUTUBE: {html.escape(query[:40])} 〕━━━ ✦"]
            for i, (vid, title) in enumerate(out, 1):
                lines.append(f"{i}. [{html.escape(title[:70])}](https://youtu.be/{vid})")
            lines.append("✦ ━━━━━━━━━━━━━━━━━━━━━ ✦")
            await event.edit("\n".join(lines), parse_mode="md", link_preview=False)
        except Exception as exc:
            await event.edit(f"❌ YouTube error: `{exc}`")

    # ---- .country (Wikipedia REST — restcountries API is deprecated) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.country\s+([\s\S]+)$"))
    @client.flood_safe
    async def _country(event):
        name = event.pattern_match.group(1).strip()
        await event.edit(f"🌍 Looking up **{name}**…")
        try:
            url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
                   + urllib.parse.quote(name.replace(" ", "_")))
            data = json.loads(await _web_get(url, timeout=15))
            if not data.get("extract"):
                return await event.edit(f"❌ No country info found for `{name}`.")
            thumb = (data.get("thumbnail") or {}).get("source")
            link = (data.get("content_urls", {}).get("desktop", {}).get("page") or "")
            body = (
                f"✦ ━━━〔 🌍 {html.escape(data.get('title', name))} 〕━━━ ✦\n"
                f"{html.escape(data['extract'][:900])}\n"
                + (f"🔗 {link}" if link else "")
            )
            if thumb:
                dest = os.path.join(DATA_DIR, f"country_{int(time.time())}.jpg")
                try:
                    await _web_dl(thumb, dest, timeout=20)
                    await throttle("send")
                    await client.send_file(await event.get_input_chat(), dest,
                                           caption=body, reply_to=event.id)
                    await event.delete()
                except Exception:
                    await event.edit(body, link_preview=False)
                finally:
                    try:
                        if os.path.exists(dest):
                            os.remove(dest)
                    except OSError:
                        pass
            else:
                await event.edit(body, link_preview=False)
        except Exception as exc:
            await event.edit(f"❌ Country error: `{exc}`")

    # ---- .xkcd ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.xkcd(?:\s+(\d+))?$"))
    @client.flood_safe
    async def _xkcd(event):
        num = event.pattern_match.group(1)
        await event.edit("📰 Fetching xkcd…")
        try:
            base = f"https://xkcd.com/{num}/info.0.json" if num else "https://xkcd.com/info.0.json"
            data = json.loads(await _web_get(base, timeout=15))
            await client.send_file(
                await event.get_input_chat(), data["img"],
                caption=f"📰 **xkcd #{data['num']}** — {data['title']}\n_{data['alt'][:200]}_",
                reply_to=event.id)
            await event.delete()
        except Exception as exc:
            await event.edit(f"❌ xkcd error: `{exc}`")

    # ---- .shiba : random doggo (dog.ceo — shibe API died) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.shiba$"))
    @client.flood_safe
    async def _shiba(event):
        await event.edit("🐕 Fetching a doggo…")
        dest = os.path.join(DATA_DIR, f"shiba_{int(time.time())}.jpg")
        try:
            data = json.loads(await _web_get(
                "https://dog.ceo/api/breeds/image/random", timeout=15))
            img = data.get("message")
            if not img:
                return await event.edit("❌ No doggo right now.")
            await _web_dl(img, dest, timeout=25)
            await throttle("send")
            await client.send_file(await event.get_input_chat(), dest,
                                   caption="🐕 Doggo!", reply_to=event.id)
            await event.delete()
        except Exception as exc:
            await event.edit(f"❌ Shiba error: `{exc}`")
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fox$"))
    @client.flood_safe
    async def _fox(event):
        await event.edit("🦊 Fetching a fox…")
        dest = os.path.join(DATA_DIR, f"fox_{int(time.time())}.jpg")
        try:
            data = json.loads(await _web_get("https://randomfox.ca/floof/", timeout=15))
            await _web_dl(data["image"], dest, timeout=25)
            await throttle("send")
            await client.send_file(await event.get_input_chat(), dest,
                                   caption="🦊 Floof!", reply_to=event.id)
            await event.delete()
        except Exception as exc:
            await event.edit(f"❌ Fox error: `{exc}`")
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .json : dump replied message as JSON ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.json$"))
    @client.flood_safe
    async def _json(event):
        reply = await event.get_reply_message()
        msg = reply or event
        try:
            dump = json.dumps(msg.to_dict(), indent=1, default=str, ensure_ascii=False)
        except Exception as exc:
            return await event.edit(f"❌ Can't serialize: `{exc}`")
        await event.edit(f"🧾 **JSON dump:**\n```{dump[:3600]}```", link_preview=False)

    # ---- .getid : chat / user / message ids ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.getid$"))
    @client.flood_safe
    async def _getid(event):
        chat = await event.get_chat()
        chat_id = event.chat_id
        chat_title = getattr(chat, "title", None) or getattr(chat, "first_name", "—")
        lines = [
            "✦ ━━━〔 🆔 ID CARD 〕━━━ ✦",
            f"┃ 💬 Chat    : `{chat_id}` ({html.escape(str(chat_title))})",
            f"┃ ✉️ Message : `{event.id}`",
        ]
        reply = await event.get_reply_message()
        if reply:
            sender = await reply.get_sender()
            sid = getattr(sender, "id", "—")
            sname = getattr(sender, "username", None) or getattr(sender, "first_name", "—")
            lines.append(f"┃ 👤 Replied user: `{sid}` (@{sname})")
        lines.append("✦ ━━━━━━━━━━━━━━━━━ ✦")
        await event.edit("\n".join(lines), parse_mode="html", link_preview=False)


COMMANDS_WEB = {
    "description": "Web & Media Tools",
    "commands": [
        (".img <query> [1-6]", "multi-image search (Bing)"),
        (".pic <query> [1-6]", "alias of .img"),
        (".telegraph", "reply media/text → telegra.ph link"),
        (".carbon <code>", "code → beautiful carbon image"),
        (".define <word>", "dictionary definition"),
        (".pypi <package>", "Python package info"),
        (".yt <query>", "YouTube search (top 6 results)"),
        (".country <name>", "country info card"),
        (".xkcd [num]", "random xkcd comic"),
        (".shiba .fox", "cute shibe / fox pics"),
        (".json", "dump replied message as JSON"),
        (".getid", "chat / user / message ids"),
    ],
}

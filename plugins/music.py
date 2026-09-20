# ── SUKUNA-X DOMAIN v7.0 plugin ──────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: MUSIC — 🎵 JioSaavn direct music in chat (tagra edition)
#
#   .song <name>    → best match full song (320kbps JioSaavn) sent as audio
#   .songs <name>   → top-5 result cards (title/artist/album/year)
#
#  Triple API fallback — never fails:
#   1) saavn-api.vercel.app   → full 320kbps JioSaavn stream
#   2) saavn.dev              → JioSaavn official-style API (self-hosted style)
#   3) iTunes Search API      → 30s high-quality preview (last resort)
#  Flood-safe, human delays, auto cleanup, album art as thumb.
# ============================================================================

_SAAVN_A = "https://saavn-api.vercel.app/search/songs?query={q}&limit=5"
_SAAVN_B = "https://saavn.dev/api/search/songs?query={q}&limit=5"
_ITUNES = "https://itunes.apple.com/search?term={q}&limit=5&media=music"

_MAX_SONG_BYTES = 15 * 1024 * 1024  # 15 MB cap (Telegram-friendly)


def _clean_title(t: str) -> str:
    """Strip HTML entities JioSaavn sometimes returns."""
    return html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()


async def _search_saavn_a(query: str):
    """saavn-api.vercel.app (old style) → normalized results."""
    data = json.loads(await _web_get(_SAAVN_A.format(q=urllib.parse.quote(query)), timeout=20))
    out = []
    if not isinstance(data, list):
        return out
    for r in data:
        url = r.get("url") or ""
        if not url.startswith("http"):
            continue
        out.append({
            "source": "JioSaavn 320k",
            "title": _clean_title(r.get("title")),
            "artist": _clean_title(r.get("artists") or "") or "Unknown",
            "album": _clean_title(r.get("album") or ""),
            "year": str(r.get("year") or ""),
            "duration": int(r.get("duration") or 0),
            "image": r.get("image") or "",
            "url": url,
            "ext": ".mp4",
            "preview": False,
            "link": r.get("perma_url") or "",
        })
    return out


async def _search_saavn_b(query: str):
    """saavn.dev style API → normalized results."""
    data = json.loads(await _web_get(_SAAVN_B.format(q=urllib.parse.quote(query)), timeout=20))
    out = []
    results = ((data or {}).get("data") or {}).get("results") or []
    for r in results:
        dls = r.get("downloadUrl") or []
        url = dls[-1].get("url") if dls else ""
        if not url:
            continue
        artists = ", ".join(a.get("name", "") for a in
                            ((r.get("artists") or {}).get("primary") or []))
        imgs = r.get("image") or []
        out.append({
            "source": "JioSaavn (alt)",
            "title": _clean_title(r.get("name") or r.get("title")),
            "artist": _clean_title(artists) or "Unknown",
            "album": _clean_title((r.get("album") or {}).get("name", "")
                                  if isinstance(r.get("album"), dict) else str(r.get("album") or "")),
            "year": str(r.get("year") or ""),
            "duration": int(r.get("duration") or 0),
            "image": imgs[-1].get("url") if imgs else "",
            "url": url,
            "ext": ".mp4",
            "preview": False,
            "link": r.get("url") or "",
        })
    return out


async def _search_itunes(query: str):
    """iTunes Search API → 30s previews (guaranteed fallback)."""
    data = json.loads(await _web_get(_ITUNES.format(q=urllib.parse.quote(query)), timeout=20))
    out = []
    for r in (data or {}).get("results", []):
        url = r.get("previewUrl") or ""
        if not url:
            continue
        out.append({
            "source": "iTunes preview",
            "title": r.get("trackName") or "Unknown",
            "artist": r.get("artistName") or "Unknown",
            "album": r.get("collectionName") or "",
            "year": str(r.get("releaseDate") or "")[:4],
            "duration": int((r.get("trackTimeMillis") or 0) / 1000),
            "image": r.get("artworkUrl100") or "",
            "url": url,
            "ext": ".m4a",
            "preview": True,
            "link": r.get("trackViewUrl") or "",
        })
    return out


async def _music_search(query: str):
    """Try every source in order — first one that returns songs wins."""
    errors = []
    for fn in (_search_saavn_a, _search_saavn_b, _search_itunes):
        try:
            res = await fn(query)
            if res:
                return res, None
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")
            continue
    return [], "; ".join(errors)[:200]


async def _send_song(client, event, song: dict):
    """Download song + art, send as audio with metadata, cleanup."""
    audio_path = os.path.join(DATA_DIR, f"song_{int(time.time())}{song['ext']}")
    thumb_path = os.path.join(DATA_DIR, f"thumb_{int(time.time())}.jpg")
    have_thumb = False
    try:
        await event.edit(
            f"⬇️ Downloading **{song['title'][:45]}**…\n📡 {song['source']}",
            link_preview=False)
        await _web_dl(song["url"], audio_path, timeout=90)
        size = os.path.getsize(audio_path)
        if size > _MAX_SONG_BYTES:
            return await event.edit("❌ The song is larger than 15MB — Telegram limit. Try another one.")
        if song.get("image"):
            try:
                await _web_dl(song["image"], thumb_path, timeout=20)
                have_thumb = os.path.getsize(thumb_path) > 1000
            except Exception:
                have_thumb = False
        await throttle("send")
        title = song["title"][:120]
        artist = song["artist"][:120]
        attrs = [DocumentAttributeAudio(
            duration=max(1, song.get("duration") or 1),
            title=title, performer=artist)]
        fname = re.sub(r'[\\/:*?"<>|]', "_", f"{title} - {artist}")[:90] + song["ext"]
        kwargs = dict(attributes=attrs, supports_streaming=True,
                      caption=(f"🎵 **{title}**\n🎤 {artist}"
                               + (f"\n💿 {song['album']}" if song.get("album") else "")
                               + (f" ({song['year']})" if song.get("year") else "")
                               + f"\n📡 {song['source']} • ⚡ Sukuna-X"))
        if have_thumb:
            kwargs["thumb"] = thumb_path
        await client.send_file(
            await event.get_input_chat(), audio_path,
            file_name=fname, reply_to=event.id, **kwargs)
        await event.delete()
    finally:
        for p in (audio_path, thumb_path):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass


def register_music(client):
    """JioSaavn music commands."""

    # ---- .song <name> : best match, direct audio ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:song|gaana)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _song(event):
        query = event.pattern_match.group(1).strip()
        if not query:
            return await event.edit("❌ Usage: `.song <song name>`\n💡 Example: `.song kesariya`")
        await event.edit(f"🎵 Searching **{query[:60]}**…", link_preview=False)
        results, err = await _music_search(query)
        if not results:
            return await event.edit(
                f"❌ No song found from any source.\n`{err or 'all APIs are busy'}`\n"
                "💡 Retry in 10-20 seconds.")
        try:
            await _send_song(client, event, results[0])
        except Exception as exc:
            try:
                await event.edit(f"❌ Send error: `{exc}`\n💡 Retry — network issue.")
            except Exception:
                pass

    # ---- .songs <name> : top-5 list cards ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:songs|songlist)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _songs(event):
        query = event.pattern_match.group(1).strip()
        if not query:
            return await event.edit("❌ Usage: `.songs <song name>` — top 5 results list.")
        await event.edit(f"🔎 Searching **{query[:60]}**…", link_preview=False)
        results, err = await _music_search(query)
        if not results:
            return await event.edit(f"❌ No results found.\n`{err or 'APIs busy'}`")
        src = results[0]["source"]
        lines = [f"✦ ━━━〔 🎵 RESULTS: {query[:35]} 〕━━━ ✦",
                 f"📡 Source: {src}", "─" * 26]
        for i, r in enumerate(results[:5], 1):
            dur = f"{r['duration']//60}:{r['duration']%60:02d}" if r.get("duration") else "—"
            tag = " ⚠️30s-preview" if r.get("preview") else ""
            lines.append(f"**{i}.** {r['title'][:48]}\n"
                         f"    🎤 {r['artist'][:45]} • ⏱ {dur}{tag}")
        lines += ["─" * 26,
                  "💡 `.song " + query[:40] + "` → top result direct audio",
                  f"🛡 3 API fallbacks • ⚡ Sukuna-X"]
        await event.edit("\n".join(lines)[:3900], link_preview=False)


COMMANDS_MUSIC = {
    "description": "Music (JioSaavn)",
    "type": "AI & Media",
    "commands": [
        (".song <name>", "full song direct chat me (JioSaavn 320k)"),
        (".gaana <name>", "alias of .song"),
        (".songs <name>", "top-5 results list card"),
        (".songlist <name>", "alias of .songs"),
    ],
}

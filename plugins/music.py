# ── SUKUNA-X DOMAIN v7.10 plugin ─────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine
import struct  # noqa — core doesn't export these two
import subprocess  # noqa

# ============================================================================
#  SECTION: MUSIC v2 — 🎵 FULL-SONG ENGINE ("pura song" guarantee)
#
#   .song  <name>   → FULL song audio direct chat me
#   .gaana <name>   → alias of .song
#   .songs <name>   → top-5 result card (title / artist / ⏱ duration)
#   .songlist <name>→ alias of .songs
#   .song2 <n>      → last .songs card me se Nth song seedha bhejo
#
#  ENGINE STACK (priority order):
#   1) YouTube (yt-dlp)     → FULL song, m4a ~128k — primary, tested reliable
#   2) JioSaavn (saavn APIs)→ FULL 320k stream — secondary (jab API zinda ho)
#   3) iTunes               → 30s preview — LAST RESORT, caption me saaf
#                              ⚠️ label ke saath (kabhi chhupa ke nahi)
#
#  PURA-SONG GUARANTEE (choti se choti baat):
#   • Har downloaded file ka REAL duration parse hota hai — mp4/m4a me
#     `mvhd` atom se, mp3 me frame-bitrate math se (ffmpeg ki zaroorat nahi).
#   • Agar file 45s se chhoti ya expected duration ka 55% se kam nikli →
#     wo preview hai → REJECT → agla source try hota hai.
#   • Audio message ka duration attribute ASLI (parsed) duration se set
#     hota hai — Telegram ka seek bar bilkul sahi dikhta hai.
#   • Title/artist YouTube ke messy titles se saaf kiye jaate hain
#     ("(Official Video) | 4K" jaisa kabaad hat jaata hai).
#   • Thumbnail: hqdefault ke black-bars crop karke 16:9 clean thumb.
#   • Ek waqt me sirf ek yt-dlp download (lock) — bandwidth + flood safe.
# ============================================================================

_SAAVN_A = "https://saavn-api.vercel.app/search/songs?query={q}&limit=5"
_SAAVN_B = "https://saavn.dev/api/search/songs?query={q}&limit=5"
_ITUNES = "https://itunes.apple.com/search?term={q}&limit=5&media=music"

_MAX_SONG_BYTES = 40 * 1024 * 1024   # 40MB sanity cap (userbot limit 2GB)
_MIN_FULL_DUR = 45                   # isse chhota = preview, reject
_DUR_RATIO = 0.55                    # expected ka <55% mila = preview
_YT_SEARCH_N = 8                     # kitne results search kare
_YT_MIN_DUR, _YT_MAX_DUR = 60, 900   # shorts/live/1-hour-mix skip
_YT_DL_TIMEOUT = 240                 # download budget (seconds)
_SONG2_TTL = 600                     # .song2 list 10 min valid

_ytdl_lock = asyncio.Lock()          # ek waqt me ek hi yt-dlp
_last_songs = {}                     # chat_id → (results, saved_at)


def _clean_title(t: str) -> str:
    """Strip HTML entities JioSaavn sometimes returns."""
    return html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()


def _fmt_dur(sec) -> str:
    try:
        sec = int(sec or 0)
        return f"{sec // 60}:{sec % 60:02d}"
    except Exception:
        return "—"


# ─── duration parsers (pure python — ffmpeg-free) ──────────────────────────

def _mp4_duration(path: str):
    """mvhd atom → duration in seconds (m4a/mp4)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(2 * 1024 * 1024)
        i = head.find(b"mvhd")
        if i < 0 or i + 40 > len(head):
            return None
        ver = head[i + 4]
        if ver == 1:
            ts, dur = struct.unpack(">IQ", head[i + 24:i + 36])
        else:
            ts, dur = struct.unpack(">II", head[i + 16:i + 24])
        return (dur / ts) if ts else None
    except Exception:
        return None


def _mp3_duration(path: str):
    """CBR frame-header estimate (saavn mp3 streams are CBR)."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            head = fh.read(256 * 1024)
        i = head.find(b"\xff\xfb")
        if i >= 0 and i + 4 <= len(head):
            table = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128,
                     160, 192, 224, 256, 320, 0]
            br = table[(head[i + 2] >> 4) & 0xF]
            if br:
                return size * 8 / (br * 1000)
        return size * 8 / (160 * 1000)   # fallback 160k guess
    except Exception:
        return None


def _audio_duration(path: str, ext: str):
    """Real duration of the downloaded file — the pura-song truth."""
    ext = (ext or "").lower()
    d = _mp3_duration(path) if ext == ".mp3" else _mp4_duration(path)
    if not d:
        d = _mp3_duration(path)
    return d


def _is_full_song(actual, expected) -> bool:
    """Preview hai to False — 45s floor + 55% expected rule."""
    if not actual or actual < _MIN_FULL_DUR:
        return False
    if expected and actual < expected * _DUR_RATIO:
        return False
    return True


# ─── YouTube title/artist cleanup ─────────────────────────────────────────

_YT_JUNK = re.compile(
    r"[\(\[\|]\s*(?:official\s*)?(?:music\s+)?(?:video|audio|lyrics?|"
    r"full\s+song|lyric\s+video|visualizer|hq|hd|4k|1080p|720p)\b[^\)\]]*"
    r"[\)\]]", re.I)
_YT_TRAIL = re.compile(r"\s*[|\-–]\s*(?:4k|hd|hq|1080p|720p)\s*$", re.I)


def _yt_split(title: str, uploader: str):
    """'Kesariya - Film | Ranbir | Pritam | 4K' → ('Kesariya', 'Film • Ranbir')."""
    t = _clean_title(title)
    t = _YT_JUNK.sub("", t)
    t = _YT_TRAIL.sub("", t).strip(" -|–\u2013")
    m = re.split(r"\s+[-–]\s+|\s+\|\s+", t, 1)
    if len(m) == 2 and 1 <= len(m[0].strip()) <= 70:
        song, artist = m[0].strip(), m[1].strip()
    else:
        song, artist = t, (uploader or "YouTube")
    segs = re.split(r"\s+\|\s+", artist)
    artist = " • ".join(s.strip() for s in segs[:2] if s.strip()) if len(segs) > 1 else artist
    return (song or "Unknown")[:80], (artist or "YouTube")[:80]


# ─── yt-dlp engine (module-first, subprocess fallback) ────────────────────

def _ytdl_search_sync(query: str, n: int):
    import yt_dlp   # noqa — server python me installed hai
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True,
            "skip_download": True, "socket_timeout": 15, "retries": 1}
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch{n}:{query}", download=False)
    return _ytdl_norm((info or {}).get("entries") or [])


def _ytdl_norm(entries):
    out = []
    for e in entries:
        if not e:
            continue
        vid = e.get("id") or ""
        try:
            dur = int(e.get("duration") or 0)
        except (TypeError, ValueError):
            dur = 0
        if not vid or dur < _YT_MIN_DUR or dur > _YT_MAX_DUR:
            continue    # live/shorts/1-hour mix skip
        song, artist = _yt_split(e.get("title") or "", e.get("uploader") or "")
        out.append({
            "source": "YouTube",
            "title": song, "artist": artist,
            "album": "", "year": "",
            "duration": dur,
            "image": e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "url": f"https://www.youtube.com/watch?v={vid}",
            "yt_id": vid, "ext": ".m4a",
            "preview": False,
            "link": f"https://youtu.be/{vid}",
        })
    return out


def _ytdl_search_subproc(query: str, n: int):
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings",
           "--flat-playlist",
           "--print", "%(id)s\t%(duration)s\t%(title)s\t%(uploader)s",
           f"ytsearch{n}:{query}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    entries = []
    for ln in (r.stdout or "").splitlines():
        parts = ln.split("\t")
        if len(parts) != 4:
            continue
        vid, durs, title, uploader = parts
        try:
            dur = int(float(durs)) if durs and durs not in ("NA", "None") else 0
        except ValueError:
            dur = 0
        entries.append({"id": vid, "duration": dur,
                        "title": title, "uploader": uploader})
    return _ytdl_norm(entries)


async def _yt_search(query: str, n: int = _YT_SEARCH_N):
    loop = asyncio.get_running_loop()
    try:
        async with _ytdl_lock:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _ytdl_search_sync, query, n), 120)
    except ImportError:
        pass
    except Exception:
        pass
    try:
        async with _ytdl_lock:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _ytdl_search_subproc, query, n), 120)
    except Exception:
        return []


def _ytdl_download_sync(url: str, base: str, tv: bool = False):
    import yt_dlp   # noqa
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": base + ".%(ext)s",
            "max_filesize": _MAX_SONG_BYTES,
            "socket_timeout": 20, "retries": 2, "overwrites": True}
    if tv:
        # datacenter IP soft-block ("confirm you're not a bot") ka
        # well-known bypass — TV client ko wahi m4a milte hain
        opts["extractor_args"] = {"youtube": {"player_client": ["tv"]}}
    with yt_dlp.YoutubeDL(opts) as y:
        y.extract_info(url, download=True)
    for ext in (".m4a", ".webm", ".opus", ".mp3", ".mp4", ".mkv", ".ogg"):
        p = base + ext
        if os.path.exists(p) and os.path.getsize(p) > 60_000:
            return p, ext
    return None, None


async def _yt_download(url: str, base: str):
    loop = asyncio.get_running_loop()
    async with _ytdl_lock:
        try:
            r = await asyncio.wait_for(
                loop.run_in_executor(None, _ytdl_download_sync, url, base, False),
                _YT_DL_TIMEOUT)
            if r and r[0]:
                return r
            # soft-block lagta hai → tv client se ek aur try
            return await asyncio.wait_for(
                loop.run_in_executor(None, _ytdl_download_sync, url, base, True),
                _YT_DL_TIMEOUT)
        except Exception:
            return None, None


# ─── legacy JioSaavn + iTunes sources (normalized shape) ──────────────────

async def _search_saavn_a(query: str):
    data = json.loads(await _web_get(_SAAVN_A.format(q=urllib.parse.quote(query)), timeout=10))
    out = []
    if not isinstance(data, list):
        return out
    for r in data:
        url = r.get("url") or ""
        if not url.startswith("http"):
            continue
        out.append({
            "source": "JioSaavn 320k", "yt_id": "",
            "title": _clean_title(r.get("title")),
            "artist": _clean_title(r.get("artists") or "") or "Unknown",
            "album": _clean_title(r.get("album") or ""),
            "year": str(r.get("year") or ""),
            "duration": int(r.get("duration") or 0),
            "image": r.get("image") or "",
            "url": url, "ext": ".mp4",
            "preview": False, "link": r.get("perma_url") or "",
        })
    return out


async def _search_saavn_b(query: str):
    data = json.loads(await _web_get(_SAAVN_B.format(q=urllib.parse.quote(query)), timeout=10))
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
            "source": "JioSaavn (alt)", "yt_id": "",
            "title": _clean_title(r.get("name") or r.get("title")),
            "artist": _clean_title(artists) or "Unknown",
            "album": _clean_title((r.get("album") or {}).get("name", "")
                                  if isinstance(r.get("album"), dict) else str(r.get("album") or "")),
            "year": str(r.get("year") or ""),
            "duration": int(r.get("duration") or 0),
            "image": imgs[-1].get("url") if imgs else "",
            "url": url, "ext": ".mp4",
            "preview": False, "link": r.get("url") or "",
        })
    return out


async def _search_itunes(query: str):
    data = json.loads(await _web_get(_ITUNES.format(q=urllib.parse.quote(query)), timeout=12))
    out = []
    for r in (data or {}).get("results", []):
        url = r.get("previewUrl") or ""
        if not url:
            continue
        out.append({
            "source": "iTunes", "yt_id": "",
            "title": r.get("trackName") or "Unknown",
            "artist": r.get("artistName") or "Unknown",
            "album": r.get("collectionName") or "",
            "year": str(r.get("releaseDate") or "")[:4],
            "duration": int((r.get("trackTimeMillis") or 0) / 1000),
            "image": (r.get("artworkUrl100") or "").replace("100x100", "600x600"),
            "url": url, "ext": ".m4a",
            "preview": True, "link": r.get("trackViewUrl") or "",
        })
    return out


async def _saavn_search(query: str):
    """Dono saavn APIs (jo zinda ho)."""
    for fn in (_search_saavn_a, _search_saavn_b):
        try:
            res = await fn(query)
            if res:
                return res
        except Exception:
            continue
    return []


# ─── thumbnail prep (black-bar crop) ──────────────────────────────────────

def _prep_thumb(src_path: str, dst_path: str) -> bool:
    try:
        try:
            from PIL import Image
            im = Image.open(src_path).convert("RGB")
            w, h = im.size
            th = int(w * 9 / 16)          # hqdefault 480x360 → 480x270
            if h > th + 8:
                top = (h - th) // 2
                im = im.crop((0, top, w, top + th))
            im.save(dst_path, "JPEG", quality=88)
        except ImportError:
            shutil.copyfile(src_path, dst_path)
        return os.path.getsize(dst_path) > 1000
    except Exception:
        return False


async def _status_edit(event, text: str):
    """Status update — kabhi fatal nahi (edit rights / relay quirks par
    bhi flow chalta rahe; sirf terminal ❌ message terminal hai)."""
    try:
        await event.edit(text, link_preview=False)
    except Exception:
        pass


# ─── the sender (verified duration + honest caption) ──────────────────────

async def _send_audio_file(client, event, path: str, ext: str, song: dict,
                           real_dur, preview: bool = False, thumb: str = None):
    size = os.path.getsize(path)
    title = (song.get("title") or "Unknown")[:100]
    artist = (song.get("artist") or "Unknown")[:100]
    dur = int(real_dur) if real_dur else max(1, song.get("duration") or 1)
    attrs = [DocumentAttributeAudio(
        duration=dur, title=title[:60], performer=artist[:60])]
    fname = re.sub(r'[\\/:*?"<>|]', "_", f"{title} - {artist}")[:90] + ext
    src = song.get("source") or "—"
    cap = (f"🎵 **{title}**\n🎤 {artist}"
           + (f"\n💿 {song['album']}" if song.get("album") else "")
           + (f" ({song['year']})" if song.get("year") else "")
           + f"\n⏱ {_fmt_dur(dur)} • 💾 {size / 1e6:.1f}MB • 📡 {src}")
    if preview:
        cap += "\n⚠️ **30-sec preview** — full source busy tha, thodi der me fir se `.song` try karo"
    cap += f"\n⚡ Sukuna-X v{BOT_VERSION}"
    kwargs = dict(attributes=attrs, supports_streaming=True, caption=cap)
    if thumb:
        kwargs["thumb"] = thumb
    await throttle("send")
    await client.send_file(await event.get_input_chat(), path,
                           file_name=fname, reply_to=event.id, **kwargs)
    # send ho GAYA — ab command-message delete na ho to bhi flow safe hai
    # (duplicate-send protection: delete failure → retry nahi hoga)
    try:
        await event.delete()
    except Exception:
        pass
    return True


def _cleanup(*paths):
    """Temp files hat ao (koi bhi missing ho to bhi shant)."""
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


# ─── candidate runners ────────────────────────────────────────────────────

async def _try_yt(client, event, cand: dict) -> bool:
    """YouTube candidate: download → REAL duration verify → send."""
    ts = int(time.time())
    base = os.path.join(DATA_DIR, f"yt_{ts}_{cand['yt_id'][:12]}")
    audio = None
    try:
        await _status_edit(event,
            f"⬇️ **{cand['title'][:40]}** download ho raha hai…\n"
            f"📡 YouTube • ⏱ {_fmt_dur(cand['duration'])} (pura song)")
        audio, ext = await _yt_download(cand["url"], base)
        if not audio:
            return False
        if os.path.getsize(audio) > _MAX_SONG_BYTES:
            return False
        real = _audio_duration(audio, ext)
        if not _is_full_song(real, cand.get("duration")):
            return False        # preview/short nikla → agla candidate
        thumb = os.path.join(DATA_DIR, f"yt_{ts}_t.jpg")
        have_thumb = False
        if cand.get("image"):
            try:
                await _web_dl(cand["image"], thumb + ".raw", timeout=15)
                have_thumb = _prep_thumb(thumb + ".raw", thumb)
            except Exception:
                have_thumb = False
        try:
            return await _send_audio_file(client, event, audio, ext, cand,
                                          real, preview=False,
                                          thumb=thumb if have_thumb else None)
        finally:
            _cleanup(thumb, thumb + ".raw")
    except Exception:
        return False
    finally:
        if audio:
            _cleanup(audio)
        else:
            for e2 in (".m4a", ".webm", ".opus", ".mp3", ".mp4", ".mkv", ".ogg"):
                _cleanup(base + e2)


async def _try_direct(client, event, cand: dict, preview: bool = False) -> bool:
    """Saavn/iTunes candidate: direct URL download → verify → send."""
    ts = int(time.time())
    audio = os.path.join(DATA_DIR, f"dl_{ts}{cand['ext']}")
    thumb = os.path.join(DATA_DIR, f"dl_{ts}_t.jpg")
    thumb_raw = thumb + ".raw"
    try:
        await _status_edit(event,
            f"⬇️ **{cand['title'][:40]}** download ho raha hai…\n📡 {cand['source']}"
            + ("\n⚠️ (30s preview hi milega)" if preview else ""))
        await _web_dl(cand["url"], audio, timeout=120)
        if os.path.getsize(audio) > _MAX_SONG_BYTES or os.path.getsize(audio) < 50_000:
            return False
        real = _audio_duration(audio, cand["ext"])
        if not preview and not _is_full_song(real, cand.get("duration")):
            return False        # saavn ne chhupa ke preview diya → reject
        have_thumb = False
        if cand.get("image"):
            try:
                await _web_dl(cand["image"], thumb_raw, timeout=15)
                have_thumb = _prep_thumb(thumb_raw, thumb)
            except Exception:
                have_thumb = False
        return await _send_audio_file(client, event, audio, cand["ext"], cand,
                                      real, preview=preview,
                                      thumb=thumb if have_thumb else None)
    except Exception:
        return False
    finally:
        _cleanup(audio, thumb, thumb_raw)


async def _song_flow(client, event, query: str, note=""):
    """Pura pipeline: YouTube → JioSaavn → iTunes-preview. Fail-safe."""
    await _status_edit(event, f"🔍 **{query[:50]}** dhund raha hu…{note}")

    # 1) YouTube — full song, primary
    try:
        yt = await _yt_search(query)
    except Exception:
        yt = []
    for cand in (yt or [])[:4]:
        if await _try_yt(client, event, cand):
            return True

    # 2) JioSaavn — full 320k, jab API zinda ho
    await _status_edit(event,
        f"🔁 YouTube busy — **{query[:40]}** JioSaavn pe try kar raha hu…")
    saavn = []
    try:
        saavn = await _saavn_search(query)
    except Exception:
        saavn = []
    for cand in (saavn or [])[:3]:
        if await _try_direct(client, event, cand, preview=False):
            return True

    # 3) iTunes — 30s preview, SAAF label ke saath (last resort)
    await _status_edit(event,
        f"🎧 Full source nahi mila — **{query[:40]}** ka preview bhej raha hu…")
    try:
        it = await _search_itunes(query)
    except Exception:
        it = []
    for cand in (it or [])[:2]:
        if await _try_direct(client, event, cand, preview=True):
            return True

    return await event.edit(
        f"❌ **{query[:50]}** kisi source se nahi mila.\n"
        "💡 Spelling check karo ya `artist + song name` dono likho — "
        "jaise `.song arijit singh kesariya`", link_preview=False)


def register_music(client):
    """Music commands — full-song engine v2."""

    # ---- .song <name> : FULL song, direct audio ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:song|gaana)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _song(event):
        query = event.pattern_match.group(1).strip()
        if not query:
            return await event.edit("❌ Usage: `.song <song name>`\n💡 Example: `.song kesariya`")
        await _song_flow(client, event, query)

    # ---- .songs <name> : top-5 card ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:songs|songlist)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _songs(event):
        query = event.pattern_match.group(1).strip()
        if not query:
            return await event.edit("❌ Usage: `.songs <song name>` — top 5 results list.")
        await _status_edit(event, f"🔎 **{query[:50]}** dhund raha hu…")
        results = await _yt_search(query)
        src = "YouTube (full songs)"
        if not results:
            results = await _saavn_search(query)
            src = "JioSaavn"
        if not results:
            try:
                results = await _search_itunes(query)
                src = "iTunes (previews)"
            except Exception:
                results = []
        if not results:
            return await event.edit("❌ Kuch nahi mila — spelling check karke fir try karo.")
        _last_songs[event.chat_id] = (results[:5], time.time())
        lines = [f"✦ ━━━〔 🎵 RESULTS: {query[:35]} 〕━━━ ✦",
                 f"📡 Source: {src}", "─" * 26]
        for i, r in enumerate(results[:5], 1):
            dur = _fmt_dur(r.get("duration")) if r.get("duration") else "—"
            tag = " ⚠️30s" if r.get("preview") else ""
            lines.append(f"**{i}.** {r['title'][:48]}\n"
                         f"    🎤 {r['artist'][:45]} • ⏱ {dur}{tag}")
        lines += ["─" * 26,
                  "💡 `.song2 <n>` → isi list me se Nth song seedha bhejo",
                  "💡 `.song <naam>` → top match ka pura song",
                  f"🛡 YouTube → JioSaavn → iTunes fallback • ⚡ Sukuna-X v{BOT_VERSION}"]
        # list pehle save (edit fail ho to bhi .song2 chale)
        await _status_edit(event, "\n".join(lines)[:3900])

    # ---- .song2 <n> : pick Nth from last .songs card ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.song2\s+(\d)$"))
    @client.flood_safe
    async def _song2(event):
        n = int(event.pattern_match.group(1))
        saved = _last_songs.get(event.chat_id)
        if not saved or time.time() - saved[1] > _SONG2_TTL:
            return await event.edit("❌ Is chat me koi `.songs` list recent nahi hai.\n"
                                    "💡 Pehle `.songs <naam>` chalao, phir `.song2 <n>`")
        results = saved[0]
        if not (1 <= n <= len(results)):
            return await event.edit(f"❌ Sirf 1 se {len(results)} tak valid hai.")
        cand = results[n - 1]
        if cand.get("yt_id"):
            ok = await _try_yt(client, event, cand)
        else:
            ok = await _try_direct(client, event, cand, preview=cand.get("preview", False))
        if not ok:
            try:
                await event.edit(f"❌ #{n} **{cand['title'][:40]}** nahi bhej paya — "
                                 "network/API busy. Thodi der me retry karo.",
                                 link_preview=False)
            except Exception:
                pass


COMMANDS_MUSIC = {
    "description": "Music (full-song engine: YouTube → JioSaavn → iTunes)",
    "type": "AI & Media",
    "commands": [
        (".song <name>", "PURa song direct chat me (YouTube full → JioSaavn → preview last)"),
        (".gaana <name>", "alias of .song"),
        (".songs <name>", "top-5 results card + ⏱ duration"),
        (".songlist <name>", "alias of .songs"),
        (".song2 <n>", "last .songs list me se Nth song seedha bhejo"),
    ],
}

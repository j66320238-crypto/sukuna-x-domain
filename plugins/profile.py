# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: PROFILE  v7.9 — FULL CLONE, VIDEO PFP, AUTOPFP ROTATE, NO FLOOD
#  v7.9: verified photo delete (purani photo rah jana FIX), upload-first
#  order, auto-upscale small pfps, _safe_edit statuses, channel-target
#  guard, .cleanpics command
############################################################################

PROFILES_FILE = "profiles_data.json"
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
PFP_DIR = os.path.join(DATA_DIR, "pfps")
AUTOPFP_DIR = os.path.join(DATA_DIR, "autopfp")
DEFAULT_NAME = "Userbot"

# ensure dirs
for _d in (PROFILES_DIR, PFP_DIR, AUTOPFP_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except Exception:
        pass

def _load_profiles() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_profiles(data: dict) -> bool:
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[profile] save failed: {e}")
        return False

def _is_view_once(message) -> bool:
    try:
        if message and message.media:
            if hasattr(message.media, "ttl_seconds") and message.media.ttl_seconds:
                return True
    except Exception:
        return False
    return False

# ─── v7.9 PHOTO ENGINE — listing / verified delete / purge / upscale ────
# v7.8 tak: delete photos SILENTLY fail ho sakte the (exception swallow +
# galat "success" count) aur upload pehle hota tha delete baad me — isliye
# purani photo gallery me rah jati thi / profile photoless ho jata tha.
# v7.9: verified delete (re-list kar confirm), FloodWait retry, per-photo
# fallback, aur NAYA order — pehle nayi photo, PHIR purani delete.

async def _list_own_photos(client, retries: int = 2):
    """Apne profile photos ki TRUE list (FloodWait-safe)."""
    for attempt in range(retries + 1):
        try:
            photos = await client.get_profile_photos("me")
            return list(photos or [])
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            if attempt >= retries:
                return []
            await asyncio.sleep(fw.seconds + 1)
        except Exception as e:
            print(f"[profile] list own photos failed: {e}")
            return []
    return []


async def _delete_photos_by_ids(client, ids) -> int:
    """Diye gaye photo ids delete karo — VERIFIED count return karta hai
    (delete ke baad re-list karke confirm). FloodWait sleep + retry,
    bulk fail hone par per-photo fallback."""
    from telethon.tl.functions.photos import DeletePhotosRequest
    from telethon.tl.types import InputPhoto
    ids = list(ids or [])
    if not ids:
        return 0
    photos = await _list_own_photos(client)
    by_id = {p.id: p for p in photos}
    inputs = []
    for pid in ids:
        p = by_id.get(pid)
        if p is not None and getattr(p, "access_hash", None) is not None:
            inputs.append(InputPhoto(id=p.id, access_hash=p.access_hash,
                                     file_reference=p.file_reference))
    if not inputs:
        return 0
    for _attempt in range(3):
        try:
            await client(DeletePhotosRequest(id=inputs))
            break
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 1)
        except Exception as e:
            print(f"[profile] bulk delete failed ({e}) — per-photo fallback")
            for ip in inputs:
                try:
                    await client(DeletePhotosRequest(id=[ip]))
                    await safe_sleep(0.4, floor=0.2)
                except FloodWaitError as fw2:
                    note_flood(fw2.seconds)
                    await asyncio.sleep(fw2.seconds + 1)
                    try:
                        await client(DeletePhotosRequest(id=[ip]))
                    except Exception:
                        pass
                except Exception:
                    pass
            break
    # VERIFY — kitne sach me delete hue
    try:
        remaining = {p.id for p in await _list_own_photos(client)}
    except Exception:
        remaining = set()
    return len([pid for pid in ids if pid not in remaining])


async def _current_main_photo_id(client):
    try:
        me = await client.get_me()
        return me.photo.photo_id if me.photo else None
    except Exception:
        return None


async def _purge_old_photos(client, keep_ids=None) -> int:
    """Old photos delete — current main (ya keep_ids) ko chhod kar.
    Returns verified deleted count."""
    keep = set(keep_ids or [])
    main = await _current_main_photo_id(client)
    if main is not None:
        keep.add(main)
    photos = await _list_own_photos(client)
    old = [p.id for p in photos if p.id not in keep]
    if not old:
        return 0
    return await _delete_photos_by_ids(client, old)


def _upscale_pfp_if_needed(path: str, min_side: int = 320) -> bool:
    """Chhoti photo ko Pillow se bada karo — Telegram chhoti pfp par
    'Photo is too small' de kar upload REJECT kar deta hai (v7.8 me yahi
    bug tha: purani delete ho chuki thi aur nayi set nahi hui).
    Returns True if file was modified."""
    if not path or not os.path.exists(path):
        return False
    if path.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
        return False
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
            if w >= 160 and h >= 160 and min(w, h) >= min_side:
                return False
            scale = max(min_side / w if w else 1.0,
                        min_side / h if h else 1.0, 1.0)
            nw = max(160, int(w * scale))
            nh = max(160, int(h * scale))
            im.convert("RGB").resize((nw, nh), Image.LANCZOS).save(
                path, "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"[profile] upscale skipped: {e}")
        return False


async def _safe_edit(event, text, **kw):
    """Status message HAMESHA user tak pahunche — edit fail ho (command
    message autodelete-timer ne delete kar diya / MessageIdInvalid) to
    reply() se naya message bhejo. v7.8 me yahi crash tha: clone hota
    tha par final ✅ kabhi nahi dikhta tha."""
    try:
        return await event.edit(text, **kw)
    except Exception:
        try:
            return await event.reply(text, **kw)
        except Exception:
            return None


async def _delete_all_profile_photos(client) -> int:
    """SAB apne photos delete (verified count)."""
    photos = await _list_own_photos(client)
    if not photos:
        return 0
    return await _delete_photos_by_ids(client, [p.id for p in photos])


async def _delete_n_photos(client, n: int) -> int:
    """Sabse naye n photos delete (verified count)."""
    photos = await _list_own_photos(client)
    if not photos:
        return 0
    to_del = photos[:max(1, n)]
    return await _delete_photos_by_ids(client, [p.id for p in to_del])

async def _get_user_full(client, target):
    try:
        full = await client(GetFullUserRequest(target))
        user_info = full.users[0] if full.users else None
        user_full = full.full_user
        return user_info, user_full
    except Exception as e:
        print(f"[profile] GetFullUser failed: {e}")
        return None, None

async def _download_all_pfps(client, entity, dest_dir: str, limit: int = 15):
    """Download all profile photos of entity to dest_dir. Returns list of (path, is_video)."""
    try:
        os.makedirs(dest_dir, exist_ok=True)
    except Exception:
        pass
    files = []
    try:
        photos = await client.get_profile_photos(entity, limit=limit)
    except Exception as e:
        print(f"[profile] get_profile_photos failed: {e}")
        return files
    if not photos:
        return files
    for idx, photo in enumerate(photos):
        try:
            # photo may have video - try to detect
            is_video = False
            # Telethon Photo can have video_start_ts
            if hasattr(photo, 'video_start_ts') and photo.video_start_ts is not None:
                is_video = True
            # try download
            ext = ".mp4" if is_video else ".jpg"
            fname = os.path.join(dest_dir, f"pfp_{idx:02d}{ext}")
            # download_media handles both
            dl_path = await client.download_media(photo, file=fname)
            if dl_path and os.path.exists(dl_path):
                files.append((dl_path, is_video))
            await safe_sleep(0.6, floor=0.3)  # human delay to avoid flood
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 2)
        except Exception as e:
            print(f"[profile] download pfp {idx} failed: {e}")
            continue
    return files

async def _upload_pfp_file(client, file_path: str, is_video: bool = False):
    """Upload single file as profile photo, supports video."""
    try:
        if not os.path.exists(file_path):
            return False
        # detect video by extension
        if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            is_video = True
        uploaded = await client.upload_file(file_path)
        if is_video:
            # video profile photo
            try:
                await client(UploadProfilePhotoRequest(
                    video=uploaded,
                    video_start_ts=0.0
                ))
            except Exception as e:
                # fallback: try as file if video fails (maybe not square)
                print(f"[profile] video upload failed {e}, trying as file")
                await client(UploadProfilePhotoRequest(file=uploaded))
        else:
            await client(UploadProfilePhotoRequest(file=uploaded))
        return True
    except FloodWaitError as fw:
        note_flood(fw.seconds)
        raise
    except Exception as e:
        print(f"[profile] upload pfp failed: {e}")
        return False

# ─── v7.3 PRE-CLONE BACKUP — .revert isi se "pahle jaisa" restore karta hai ──

PRECLONE_DIR = os.path.join(DATA_DIR, "pre_clone")


def _preclone_meta_path() -> str:
    return os.path.join(PRECLONE_DIR, "meta.json")


def _preclone_photo_path() -> str:
    return os.path.join(PRECLONE_DIR, "pfp.jpg")


def _load_preclone_meta():
    """Saved pre-clone state padho (dict) ya None."""
    try:
        with open(_preclone_meta_path(), "r", encoding="utf-8") as fh:
            meta = json.load(fh)
            return meta if isinstance(meta, dict) else None
    except Exception:
        return None


def _clear_preclone():
    """Restore hone ke baad backup hata do (agli clone fresh banegi)."""
    try:
        import shutil as _shutil
        _shutil.rmtree(PRECLONE_DIR, ignore_errors=True)
    except Exception:
        pass


async def _save_preclone_backup(client):
    """Clone se PEHLE original profile ka snapshot — HAR .clone par FRESH.

    v7.4.2 FIX: pehle ye backup SIRF PEHLI BAAR save hota tha aur kabhi
    overwrite nahi hota — isliye .revert purane-purane (stale) profile
    par le jaata tha (e.g. subah ka naam shaam me restore ho jata).
    Ab: .revert = "pichla undo" (last clone se pehle wala state),
    jo user ki expectation bhi hai. Fresh backup har .clone se pehle.
    """
    try:
        os.makedirs(PRECLONE_DIR, exist_ok=True)
        me = await client.get_me()
        bio = ""
        try:
            full = await client(GetFullUserRequest("me"))
            bio = getattr(full.full_user, "about", None) or ""
        except Exception:
            pass
        has_photo = False
        try:
            photos = await client.get_profile_photos("me", limit=1)
            if photos:
                p = await client.download_media(photos[0], file=_preclone_photo_path())
                has_photo = bool(p and os.path.exists(p))
        except Exception:
            pass
        meta = {
            "ts": time.time(),
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "username": me.username or "",
            "bio": bio[:250],
            "has_photo": has_photo,
        }
        with open(_preclone_meta_path(), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False)
        print("[profile] pre-clone backup saved — .revert isi ko restore karega")
    except Exception as e:
        print(f"[profile] pre-clone backup failed: {e}")


async def _clone_profile(client, event, target, full: bool = False):
    """Core clone logic. full=True => all photos/videos.

    v7.9 REWRITE ("purani photo rah jati thi" fix):
    ① channel-sender (anonymous admin) par friendly error — pehle
       yahan crash hota tha (Cannot cast InputPeerChannel).
    ② NAYA ORDER — pehle NAYI photo upload, PHIR purani delete →
       profile kabhi photoless nahi rehta aur upload fail hone par
       purani photo SAFE rehti hai.
    ③ chhoti photo auto-upscale — 'Photo is too small' reject NO MORE.
    ④ delete VERIFIED (re-list confirm) + FloodWait sleep-retry.
    ⑤ final status _safe_edit se — autodelete-timer crash NO MORE."""
    # 0) anonymous-admin / channel guard
    try:
        from telethon.tl.types import InputPeerChannel
        if isinstance(target, InputPeerChannel):
            return await _safe_edit(
                event,
                "❌ That message was sent by the **group itself** (anonymous "
                "admin / channel) — Telegram hides the real user.\n"
                "➤ Reply to a normal user message, or use `.clone @username`")
    except Exception:
        pass
    await _safe_edit(event, f"`{'🔥 Full' if full else '👤'} Cloning "
                            f"{'full profile' if full else 'profile'}...`")
    # 1) target profile PEHLE resolve (fail-fast — backup baad me save hota)
    user_info, user_full = await _get_user_full(client, target)
    if not user_info:
        return await _safe_edit(
            event, "`❌ Could not fetch user info.` "
                   "(anonymous-admin message? try `.clone @username`)")
    first_name = (user_info.first_name or "")[:64]
    last_name = (user_info.last_name or "")[:64]
    # bio limit — Premium 140, normal 70 (ABOUT_TOO_LONG se bachne ke liye)
    try:
        _me_now = await client.get_me()
        bio_limit = 140 if getattr(_me_now, "premium", False) else 70
    except Exception:
        bio_limit = 70
    bio = getattr(user_full, "about", None) or getattr(user_full, "bio", None) or ""
    bio = bio[:bio_limit]
    # 2) 🤖 pre-clone backup — .revert isi se restore karega
    await _save_preclone_backup(client)
    temp_dir = os.path.join(DATA_DIR, f"clone_temp_{event.id}")
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except Exception:
        pass
    downloaded = []
    try:
        # 3) target ki photos download
        try:
            downloaded = await _download_all_pfps(client, target, temp_dir,
                                                  limit=20 if full else 1)
        except Exception as e:
            print(f"[clone] download all failed: {e}")

        # 4) name + bio (FloodWait sleep + retry)
        name_ok = False
        await safe_sleep(0.8, floor=0.4)
        for _attempt in range(2):
            try:
                await client(UpdateProfileRequest(
                    first_name=first_name or DEFAULT_NAME,
                    last_name=last_name,
                    about=bio))
                name_ok = True
                break
            except FloodWaitError as fw:
                note_flood(fw.seconds)
                await asyncio.sleep(fw.seconds + 1)

        # 5) apni PURANI photo ids capture — uploads se PEHLE
        old_photos = await _list_own_photos(client)
        old_ids = [p.id for p in old_photos]

        # 6) NAYI photos PEHLE upload (profile photoless na ho + purani
        #    safe rahe agar upload fail ho jaye)
        success = 0
        if downloaded:
            # for full clone, upload oldest first so newest becomes main
            to_upload = list(reversed(downloaded)) if full else downloaded
            for fpath, is_vid in to_upload:
                try:
                    await safe_sleep(1.2, floor=0.6)  # human delay
                    ok = await _upload_pfp_file(client, fpath, is_video=is_vid)
                    if not ok:
                        # 'Photo is too small' → upscale → ek aur try
                        if _upscale_pfp_if_needed(fpath):
                            ok = await _upload_pfp_file(client, fpath,
                                                        is_video=is_vid)
                    if ok:
                        success += 1
                except FloodWaitError as fw:
                    await _safe_edit(event, f"`⏳ FloodWait {fw.seconds}s on "
                                            "photo upload, waiting...`")
                    await asyncio.sleep(fw.seconds + 2)
                    try:
                        if _upscale_pfp_if_needed(fpath):
                            pass  # pehle try me already try ho chuka
                        ok = await _upload_pfp_file(client, fpath,
                                                    is_video=is_vid)
                        if ok:
                            success += 1
                    except Exception:
                        continue
                except Exception as e:
                    print(f"[clone] upload failed: {e}")

        # 7) PURANI photos delete — verified (v7.9 ORDER)
        #    • nayi set hui → sirf purani wali delete (nayi safe)
        #    • target ki photo NAHI → sab delete (100% mirror)
        #    • upload FAIL → purani rahne do (photoless profile se better)
        purged = 0
        if downloaded:
            if success:
                purged = await _delete_photos_by_ids(client, old_ids)
        else:
            purged = await _delete_photos_by_ids(client, old_ids)

        # 8) verify + final status — hamesha dikhega (_safe_edit)
        now_count = len(await _list_own_photos(client))
        mark = "✓" if name_ok else "✗"
        if downloaded:
            if success:
                photo_line = f"Photos: {success}/{len(downloaded)} ✓"
            else:
                photo_line = "Photos: ⚠️ upload failed — previous DP kept"
            if purged:
                gallery_line = f"Old photos removed: {purged} ✓"
            elif not old_ids:
                gallery_line = "Old photos: none (was already clean)"
            else:
                gallery_line = "Old photos: ⚠️ could not remove — try `.cleanpics`"
            await _safe_edit(
                event,
                f"`✅ {'Full' if full else 'Main'} clone done!`\n"
                f"Name: {first_name} {last_name} {mark}\n"
                f"Bio: {bio or 'N/A'} {mark}\n"
                f"{photo_line}\n"
                f"{gallery_line}\n"
                f"Gallery now: {now_count} photo(s) — exact copy")
        else:
            await _safe_edit(
                event,
                f"`✅ Profile cloned — no DP (exact copy)`\n"
                f"Name: {first_name} {last_name} {mark}\n"
                f"Bio: {bio or 'N/A'} {mark}\n"
                f"Photos removed: {purged} · Gallery now: {now_count}")
    except FloodWaitError as e:
        await _safe_edit(event, f"`⏳ FloodWait: {e.seconds}s`")
    except Exception as e:
        await _safe_edit(event, f"`❌ Clone error: {e}`")
    finally:
        # cleanup temp
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

def register_profile(client):

    if not hasattr(client, "vo_enabled"):
        client.vo_enabled = False

    # .clone — main clone (reply to a user OR give a @username)
    @client.flood_safe
    async def clone_handler(event):
        arg = (event.pattern_match.group(1) or "").strip()
        is_full = arg.lower() in ("full", "f", "all", "fullcopy")
        target = None
        if event.is_reply:
            reply = await event.get_reply_message()
            if not reply:
                await event.edit("`➤ No replied message.`")
                return
            try:
                target = await reply.get_input_sender()
            except Exception as e:
                await event.edit(f"`➤ Failed to get target: {e}`")
                return
        elif arg and not is_full:
            # v7.6: clone by username — .clone @name / .clone t.me/name
            uname = (arg.replace("https://t.me/", "").replace("t.me/", "")
                     .lstrip("@").split("?")[0].strip())
            if not uname:
                await event.edit("`➤ Usage: reply to a user, or .clone @username`")
                return
            try:
                target = await client.get_input_entity(uname)
            except Exception as e:
                await event.edit(
                    f"`➤ Could not resolve @{uname}: {e}`\n"
                    "`   (open a chat with them once, then try again)`")
                return
        else:
            await event.edit("`➤ Reply to a user to clone, or use .clone @username. Use .fclone for full copy.`")
            return
        await _clone_profile(client, event, target, full=is_full)

    # .fclone — full clone (all photos/videos), reply OR @username
    @client.flood_safe
    async def fclone_handler(event):
        arg = (event.pattern_match.group(1) or "").strip()
        target = None
        if event.is_reply:
            reply = await event.get_reply_message()
            if not reply:
                await event.edit("`➤ No replied message.`")
                return
            try:
                target = await reply.get_input_sender()
            except Exception as e:
                await event.edit(f"`➤ Failed: {e}`")
                return
        elif arg:
            uname = (arg.replace("https://t.me/", "").replace("t.me/", "")
                     .lstrip("@").split("?")[0].strip())
            if not uname:
                await event.edit("`➤ Usage: reply to a user, or .fclone @username`")
                return
            try:
                target = await client.get_input_entity(uname)
            except Exception as e:
                await event.edit(f"`➤ Could not resolve @{uname}: {e}`")
                return
        else:
            await event.edit("`➤ Reply to a user for full clone (.fclone), or .fclone @username.`")
            return
        await _clone_profile(client, event, target, full=True)

    # .revert — PEHLE JaisA (pre-clone state restore) — v7.3 fix
    # v7.9: restore photo PEHLE upload hota hai, PHIR baaki delete — aur
    # saare status _safe_edit se (autodelete-timer crash NO MORE).
    @client.flood_safe
    async def revert_handler(event):
        meta = _load_preclone_meta()
        if not meta:
            # fallback: koi backup nahi → purana default behaviour
            await _safe_edit(event, "`➤ No pre-clone backup found — reverting to default...`")
            try:
                await client(UpdateProfileRequest(first_name=DEFAULT_NAME, last_name="", about=""))
                await safe_sleep(0.6, floor=0.3)
                await _delete_all_profile_photos(client)
                await _safe_edit(
                    event,
                    f"`✅ Reverted to {DEFAULT_NAME}`\n"
                    "⚠️ No backup existed — from now on a backup is auto-saved before every `.clone`.")
            except FloodWaitError as e:
                await _safe_edit(event, f"`⏳ FloodWait: {e.seconds}s`")
            except Exception as e:
                await _safe_edit(event, f"`❌ Revert error: {e}`")
            return
        await _safe_edit(event, "`➤ Restoring pre-clone state...`")
        try:
            first = (meta.get("first_name") or DEFAULT_NAME)[:64]
            last = (meta.get("last_name") or "")[:64]
            bio = (meta.get("bio") or "")[:70]
            await client(UpdateProfileRequest(first_name=first, last_name=last, about=bio))
            await safe_sleep(0.6, floor=0.3)
            # v7.9 ORDER: backup photo PEHLE upload (nayi = main), PHIR
            # baaki sab delete — restore fail ho to profile photoless nahi
            photo_note = "removed"
            if meta.get("has_photo") and os.path.exists(_preclone_photo_path()):
                await safe_sleep(0.8, floor=0.4)
                if await _upload_pfp_file(client, _preclone_photo_path()):
                    photo_note = "restored"
                    new_main = await _current_main_photo_id(client)
                    await _purge_old_photos(
                        client, keep_ids=[new_main] if new_main else None)
                else:
                    if _upscale_pfp_if_needed(_preclone_photo_path()):
                        if await _upload_pfp_file(client, _preclone_photo_path()):
                            photo_note = "restored"
                            new_main = await _current_main_photo_id(client)
                            await _purge_old_photos(
                                client, keep_ids=[new_main] if new_main else None)
                    else:
                        await _delete_all_profile_photos(client)
            else:
                await _delete_all_profile_photos(client)
            _clear_preclone()
            await _safe_edit(
                event,
                "`✅ Reverted to pre-clone state!`\n"
                f"Name: `{first} {last}`\n"
                f"Bio: `{bio or '—'}`\n"
                f"DP: `{photo_note}`\n"
                "💡 Your profile is back exactly how it was before.")
        except FloodWaitError as e:
            await _safe_edit(event, f"`⏳ FloodWait: {e.seconds}s`")
        except Exception as e:
            await _safe_edit(event, f"`❌ Revert error: {e}`")

    # .rclone — RANDOM CLONE: group me kisi bhi random member ka clone
    @client.flood_safe
    async def rclone_handler(event):
        arg = (event.pattern_match.group(1) or "").strip().lower()
        is_full = arg in ("full", "f", "all")

        try:
            chat = await event.get_input_chat()
        except Exception as e:
            return await event.edit(f"`➤ Failed: {e}`")

        # collect members of the group (exclude me + bots)
        try:
            me = await client.get_me()
        except Exception:
            me = None
        members = []
        try:
            async for u in client.iter_participants(chat, limit=400):
                if getattr(u, "bot", False):
                    continue
                if me is not None and u.id == me.id:
                    continue
                members.append(u)
        except Exception:
            return await event.edit(
                "`➤ .rclone works only in groups/chats — could not fetch participants.`")

        if not members:
            return await event.edit(
                "`➤ No cloneable member found in this group.`")

        victim = random.choice(members)
        disp = " ".join(x for x in (
            getattr(victim, "first_name", None),
            getattr(victim, "last_name", None)) if x).strip()
        disp = disp or str(victim.id)

        try:
            target = await client.get_input_entity(victim.id)
        except Exception:
            target = victim  # full User object also works as entity

        await event.edit(
            f"`🎲 Random target picked: {disp} — cloning...`")
        await _clone_profile(client, event, target, full=is_full)

    # .saveprofile <name> — save replied user's full profile
    @client.flood_safe
    async def saveprofile_handler(event):
        if not event.is_reply:
            await event.edit("`➤ Reply to user to save. .saveprofile <name>`")
            return
        raw = event.pattern_match.group(1) or ""
        name = raw.strip()
        if not name:
            data = _load_profiles()
            name = f"profile_{len(data)+1}"
        # sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in "_-")[:30] or "profile"
        await event.edit(f"`➤ Saving profile as '{safe_name}' (full copy)...`")
        reply = await event.get_reply_message()
        try:
            target = await reply.get_input_sender()
        except Exception as e:
            await event.edit(f"`➤ Failed: {e}`")
            return
        save_dir = os.path.join(PROFILES_DIR, safe_name)
        try:
            os.makedirs(save_dir, exist_ok=True)
        except Exception:
            pass
        photos_dir = os.path.join(save_dir, "photos")
        try:
            user_info, user_full = await _get_user_full(client, target)
            if not user_info:
                await event.edit("`❌ Could not fetch user.`")
                return
            first_name = user_info.first_name or ""
            last_name = user_info.last_name or ""
            bio = getattr(user_full, "about", None) or getattr(user_full, "bio", None) or ""
            # download all photos
            files = await _download_all_pfps(client, target, photos_dir, limit=20)
            # save metadata
            meta = {
                "first_name": first_name,
                "last_name": last_name,
                "bio": bio,
                "user_id": user_info.id,
                "username": getattr(user_info, "username", None),
                "photos": [os.path.basename(p[0]) for p in files],
                "photos_full": [p[0] for p in files],
                "count": len(files),
                "saved_at": time.time()
            }
            with open(os.path.join(save_dir, "info.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            # also save in old JSON for compatibility (first photo base64)
            photo_b64 = None
            if files:
                try:
                    with open(files[0][0], "rb") as fh:
                        photo_b64 = base64.b64encode(fh.read()).decode("utf-8")
                except Exception:
                    pass
            old_data = _load_profiles()
            old_data[safe_name] = {
                "first_name": first_name,
                "last_name": last_name,
                "bio": bio,
                "user_id": user_info.id,
                "photo": photo_b64,
                "count": len(files),
                "dir": save_dir
            }
            _save_profiles(old_data)
            await event.edit(
                f"`✅ Saved '{safe_name}'\n"
                f"Name: {first_name} {last_name}\n"
                f"Bio: {bio[:40] or 'N/A'}\n"
                f"Photos: {len(files)} saved to {photos_dir}`"
            )
        except Exception as e:
            await event.edit(f"`❌ Save error: {e}`")

    # .loadprofile <name> [full]  — load main or full
    @client.flood_safe
    async def loadprofile_handler(event):
        raw = (event.pattern_match.group(1) or "").strip()
        if not raw:
            await event.edit("`➤ Usage: .loadprofile <name> [full]  or  .floadprofile <name>`")
            return
        parts = raw.split()
        is_full = False
        name = raw
        # parse full keyword
        if "full" in [p.lower() for p in parts]:
            is_full = True
            # remove full from name
            filtered = [p for p in parts if p.lower() != "full"]
            name = " ".join(filtered).strip()
        safe_name = "".join(c for c in name if c.isalnum() or c in "_-")[:30] or name
        # try new dir first
        save_dir = os.path.join(PROFILES_DIR, safe_name)
        info_path = os.path.join(save_dir, "info.json")
        photos_dir = os.path.join(save_dir, "photos")
        await event.edit(f"`➤ Loading '{safe_name}' {'full' if is_full else 'main'}...`")
        try:
            if os.path.exists(info_path):
                with open(info_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                first_name = meta.get("first_name", "")[:64]
                last_name = meta.get("last_name", "")[:64]
                bio = meta.get("bio", "")[:70]
                await client(UpdateProfileRequest(first_name=first_name, last_name=last_name, about=bio))
                await safe_sleep(0.6, floor=0.3)
                await _delete_all_profile_photos(client)
                # collect photos
                photo_files = []
                if os.path.exists(photos_dir):
                    for fn in sorted(os.listdir(photos_dir)):
                        fp = os.path.join(photos_dir, fn)
                        if os.path.isfile(fp):
                            photo_files.append(fp)
                if not photo_files and meta.get("photos_full"):
                    photo_files = [p for p in meta["photos_full"] if os.path.exists(p)]
                # upload
                to_upload = photo_files if is_full else (photo_files[:1] if photo_files else [])
                # for full, oldest first
                if is_full:
                    to_upload = list(reversed(to_upload)) if len(to_upload)>1 else to_upload
                    # but our files are pfp_00 newest, pfp_01 older? Actually get_profile_photos returns newest first, we saved as pfp_00 newest etc. So to keep newest as main, upload oldest first.
                    # our list sorted asc is 00 newest first? Actually we saved in order idx 0 newest. So sorted will be 00,01,02... where 00 newest. To upload oldest first, reverse.
                    to_upload = list(reversed(to_upload))
                success = 0
                for fp in to_upload:
                    await safe_sleep(1.2, floor=0.6)
                    is_vid = fp.lower().endswith('.mp4')
                    try:
                        ok = await _upload_pfp_file(client, fp, is_video=is_vid)
                        if ok:
                            success += 1
                    except FloodWaitError as fw:
                        await event.edit(f"`⏳ FloodWait {fw.seconds}s, waiting...`")
                        await asyncio.sleep(fw.seconds+1)
                await event.edit(f"`✅ Loaded '{safe_name}' {'full' if is_full else 'main'} — {success} photo(s)`")
                return
            # fallback old JSON
            data = _load_profiles()
            if safe_name not in data and name in data:
                safe_name = name
            if safe_name not in data:
                await event.edit(f"`➤ No saved profile '{safe_name}'. .savedprofiles`")
                return
            prof = data[safe_name]
            await client(UpdateProfileRequest(
                first_name=prof.get("first_name","")[:64],
                last_name=prof.get("last_name","")[:64],
                about=prof.get("bio","")[:70]
            ))
            await safe_sleep(0.5, floor=0.3)
            b64 = prof.get("photo")
            if b64:
                tmp = f"profile_load_{safe_name}.jpg"
                try:
                    with open(tmp, "wb") as f:
                        f.write(base64.b64decode(b64))
                    await _delete_all_profile_photos(client)
                    await _upload_pfp_file(client, tmp, False)
                    os.remove(tmp)
                except Exception:
                    pass
            await event.edit(f"`✅ Loaded '{safe_name}' (legacy)`")
        except FloodWaitError as e:
            await event.edit(f"`⏳ FloodWait: {e.seconds}s`")
        except Exception as e:
            await event.edit(f"`❌ Load error: {e}`")

    @client.flood_safe
    async def floadprofile_handler(event):
        # alias for full load
        raw = (event.pattern_match.group(1) or "").strip()
        if not raw:
            await event.edit("`➤ Usage: .floadprofile <name>`")
            return
        # inject full
        event.pattern_match = type('obj', (object,), {'group': lambda self, n: f"{raw} full" if n==1 else None})()
        await loadprofile_handler(event)

    @client.flood_safe
    async def savedprofiles_handler(event):
        data = _load_profiles()
        # also scan PROFILES_DIR
        try:
            dirs = [d for d in os.listdir(PROFILES_DIR) if os.path.isdir(os.path.join(PROFILES_DIR, d))]
        except Exception:
            dirs = []
        if not data and not dirs:
            await event.edit("`📁 No saved profiles.`")
            return
        lines = ["**📁 Saved Profiles:**", ""]
        # from dir
        for d in sorted(dirs):
            info_p = os.path.join(PROFILES_DIR, d, "info.json")
            cnt = "?"
            name_disp = d
            if os.path.exists(info_p):
                try:
                    with open(info_p, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    fname = meta.get("first_name","")
                    lname = meta.get("last_name","")
                    cnt = meta.get("count", "?")
                    name_disp = f"{d} — {fname} {lname} ({cnt} photos)"
                except Exception:
                    pass
            lines.append(f"• `{d}` — {name_disp}")
        # legacy json not in dir
        for k in data.keys():
            if k not in dirs:
                lines.append(f"• `{k}` (legacy)")
        lines.append("")
        lines.append("`.loadprofile <name>` main • `.floadprofile <name>` / `.loadprofile <name> full` = full copy")
        await event.edit("\n".join(lines)[:3500])

    @client.flood_safe
    async def delprofile_handler(event):
        raw = (event.pattern_match.group(1) or "").strip()
        if not raw:
            await event.edit("`➤ .delprofile <name>`")
            return
        safe_name = "".join(c for c in raw if c.isalnum() or c in "_-")[:30] or raw
        # delete dir
        save_dir = os.path.join(PROFILES_DIR, safe_name)
        import shutil
        deleted = False
        if os.path.exists(save_dir):
            try:
                shutil.rmtree(save_dir, ignore_errors=True)
                deleted = True
            except Exception:
                pass
        data = _load_profiles()
        if safe_name in data:
            del data[safe_name]
            _save_profiles(data)
            deleted = True
        if raw in data and raw != safe_name:
            del data[raw]
            _save_profiles(data)
            deleted = True
        if deleted:
            await event.edit(f"`✅ Deleted profile '{safe_name}'`")
        else:
            await event.edit(f"`➤ No profile '{safe_name}' found.`")

    # .vo on|off|status
    @client.flood_safe
    async def vo_handler(event):
        raw = (event.pattern_match.group(1) or "").strip().lower() or "status"
        if raw in ("on","enable","true","1"):
            client.vo_enabled = True
            await event.edit("`✅ View-Once saving ON.`")
        elif raw in ("off","disable","false","0"):
            client.vo_enabled = False
            await event.edit("`✅ View-Once saving OFF.`")
        else:
            st = "ON ✅" if client.vo_enabled else "OFF ❌"
            await event.edit(f"`👁️ VO saving: {st}`")

    async def vo_watcher(event):
        try:
            if not client.vo_enabled:
                return
            if event.out:
                return
            if not _is_view_once(event.message):
                return
            me = await client.get_input_entity("me")
            sender = await event.get_sender()
            sid = sender.id if sender else "?"
            sname = ""
            if sender:
                sname = f"{getattr(sender,'first_name','') or ''} {getattr(sender,'last_name','') or ''}".strip() or str(sid)
            ts = event.message.date.strftime("%Y-%m-%d %H:%M:%S") if event.message.date else "?"
            mtype = "Photo" if isinstance(event.message.media, MessageMediaPhoto) else "Video/Doc"
            try:
                dl = await client.download_media(event.message)
            except Exception as e:
                print(f"[vo] dl fail {e}")
                return
            if not dl:
                return
            cap = f"👁️ **VO {mtype} Saved**\nFrom: {sname} (`{sid}`)\nTime: {ts}"
            try:
                await client.send_file(me, dl, caption=cap)
            except Exception as e:
                print(f"[vo] send fail {e}")
            finally:
                try:
                    if isinstance(dl, str) and os.path.exists(dl):
                        os.remove(dl)
                except Exception:
                    pass
        except Exception as e:
            print(f"[vo] error {e}")

    @client.flood_safe
    async def setname_handler(event):
        raw = (event.pattern_match.group(1) or "").strip()
        if not raw:
            await event.edit("`➤ .setname <first> [last]`")
            return
        parts = raw.split(None,1)
        first = parts[0][:64]
        last = parts[1][:64] if len(parts)>1 else ""
        try:
            await client(UpdateProfileRequest(first_name=first, last_name=last))
            await event.edit(f"`✅ Name: {first} {last}`")
        except FloodWaitError as e:
            await event.edit(f"`⏳ FloodWait {e.seconds}s`")
        except Exception as e:
            await event.edit(f"`❌ {e}`")

    @client.flood_safe
    async def setbio_handler(event):
        raw = (event.pattern_match.group(1) or "").strip()
        if not raw:
            await event.edit("`➤ .setbio <text>`")
            return
        try:
            await client(UpdateProfileRequest(about=raw[:70]))
            await event.edit("`✅ Bio updated.`")
        except FloodWaitError as e:
            await event.edit(f"`⏳ FloodWait {e.seconds}s`")
        except Exception as e:
            await event.edit(f"`❌ {e}`")

    @client.flood_safe
    async def delpfp_handler(event):
        raw = (event.pattern_match.group(1) or "").strip()
        n = None
        if raw.isdigit():
            n = int(raw)
        try:
            if n:
                deleted = await _delete_n_photos(client, n)
                await _safe_edit(event, f"`✅ Deleted {deleted} photo(s).`")
            else:
                deleted = await _delete_all_profile_photos(client)
                if not deleted:
                    await _safe_edit(event, "`➤ No pfps to delete.`")
                else:
                    await _safe_edit(event, f"`✅ Deleted {deleted} photo(s).`")
        except FloodWaitError as e:
            await _safe_edit(event, f"`⏳ FloodWait {e.seconds}s`")
        except Exception as e:
            await _safe_edit(event, f"`❌ {e}`")

    # .cleanpics — v7.9: purani photos clean, sirf current main bache
    # (clone ke baad gallery me purani photos rah jayein to ye command)
    @client.flood_safe
    async def cleanpics_handler(event):
        await _safe_edit(event, "`➤ Cleaning old profile photos...`")
        try:
            before = len(await _list_own_photos(client))
            deleted = await _purge_old_photos(client)
            after = len(await _list_own_photos(client))
            if deleted:
                await _safe_edit(
                    event,
                    f"`✅ Old photos removed: {deleted}`\n"
                    f"Before: {before} → Now: {after} (current main kept)")
            elif before <= 1:
                await _safe_edit(
                    event, f"`✅ Already clean — {before} photo(s), nothing to remove.`")
            else:
                await _safe_edit(
                    event,
                    f"`⚠️ Could not remove old photos ({before - 1} left) — "
                    "Telegram may be rate-limiting. Try again in a minute.`")
        except FloodWaitError as e:
            await _safe_edit(event, f"`⏳ FloodWait {e.seconds}s`")
        except Exception as e:
            await _safe_edit(event, f"`❌ {e}`")

    # ---------- NEW: PFP SAVE / GET / SET / LIST / AUTOROTATE ----------

    @client.flood_safe
    async def pfpsave_handler(event):
        # save own pfps or replied user's pfps
        await event.edit("`➤ Saving pfps...`")
        target = "me"
        if event.is_reply:
            reply = await event.get_reply_message()
            try:
                target = await reply.get_input_sender()
            except Exception:
                target = "me"
        dest = os.path.join(PFP_DIR, f"saved_{int(time.time())}")
        try:
            files = await _download_all_pfps(client, target, dest, limit=15)
            if not files:
                await event.edit("`➤ No profile photos found.`")
                try:
                    import shutil
                    shutil.rmtree(dest, ignore_errors=True)
                except Exception:
                    pass
                return
            await event.edit(f"`✅ Saved {len(files)} pfp(s) to `{dest}`\nUse .pfplist to see, .autopfp to rotate`")
        except Exception as e:
            await event.edit(f"`❌ Save error: {e}`")

    @client.flood_safe
    async def getpfp_handler(event):
        if not event.is_reply:
            await event.edit("`➤ Reply to user to get their pfp(s). .getpfp [limit]`")
            return
        raw = (event.pattern_match.group(1) or "").strip()
        limit = 5
        if raw.isdigit():
            limit = max(1, min(int(raw), 20))
        reply = await event.get_reply_message()
        try:
            target = await reply.get_input_sender()
        except Exception as e:
            await event.edit(f"`➤ Failed: {e}`")
            return
        await event.edit(f"`➤ Getting {limit} pfp(s)...`")
        tmp_dir = os.path.join(DATA_DIR, f"getpfp_{event.id}")
        try:
            files = await _download_all_pfps(client, target, tmp_dir, limit=limit)
            if not files:
                await event.edit("`➤ No pfps found.`")
                return
            # send to chat
            for fp,_ in files[:limit]:
                try:
                    await safe_sleep(0.8, floor=0.4)
                    await client.send_file(event.chat_id, fp, caption=f"`{os.path.basename(fp)}`")
                except Exception as e:
                    print(f"[getpfp] send fail {e}")
            await event.edit(f"`✅ Sent {len(files)} pfp(s).`")
        except Exception as e:
            await event.edit(f"`❌ {e}`")
        finally:
            try:
                import shutil
                if os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

    @client.flood_safe
    async def setpfp_handler(event):
        # reply to photo to set as pfp
        if not event.is_reply:
            await event.edit("`➤ Reply to a photo/video to set as pfp. .setpfp`")
            return
        reply = await event.get_reply_message()
        if not reply or not reply.media:
            await event.edit("`➤ Reply to a photo/video.`")
            return
        await event.edit("`➤ Setting pfp...`")
        tmp = os.path.join(DATA_DIR, f"setpfp_{event.id}")
        try:
            dl = await client.download_media(reply, file=tmp)
            if not dl or not os.path.exists(dl):
                await event.edit("`❌ Download failed.`")
                return
            is_vid = dl.lower().endswith(('.mp4','.mov'))
            await safe_sleep(0.6, floor=0.3)
            ok = await _upload_pfp_file(client, dl, is_video=is_vid)
            if ok:
                await event.edit("`✅ PFP updated.`")
            else:
                await event.edit("`❌ Upload failed (maybe video not square/<=10s/<=2MB).`")
        except FloodWaitError as e:
            await event.edit(f"`⏳ FloodWait {e.seconds}s`")
        except Exception as e:
            await event.edit(f"`❌ {e}`")
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

    @client.flood_safe
    async def pfplist_handler(event):
        # list saved pfps
        try:
            entries = []
            if os.path.exists(PFP_DIR):
                for d in os.listdir(PFP_DIR):
                    dp = os.path.join(PFP_DIR, d)
                    if os.path.isdir(dp):
                        cnt = len([f for f in os.listdir(dp) if os.path.isfile(os.path.join(dp,f))])
                        entries.append(f"`{d}` — {cnt} file(s)")
                    elif os.path.isfile(dp):
                        entries.append(f"`{d}` — file")
            # also profiles
            prof_entries = []
            if os.path.exists(PROFILES_DIR):
                for d in os.listdir(PROFILES_DIR):
                    pd = os.path.join(PROFILES_DIR, d)
                    if os.path.isdir(pd):
                        photos_dir = os.path.join(pd, "photos")
                        cnt = 0
                        if os.path.exists(photos_dir):
                            cnt = len([f for f in os.listdir(photos_dir) if os.path.isfile(os.path.join(photos_dir,f))])
                        prof_entries.append(f"`{d}` — {cnt} pfp(s)")
            if not entries and not prof_entries:
                await event.edit("`📁 No saved pfps. Use .pfpsave or .saveprofile <name>`")
                return
            msg = ["**📁 Saved PFPs:**", ""]
            if entries:
                msg.append("**PFP Dir:**")
                msg.extend([f"• {e}" for e in entries[:20]])
                msg.append("")
            if prof_entries:
                msg.append("**Profiles:**")
                msg.extend([f"• {e}" for e in prof_entries[:20]])
                msg.append("")
            msg.append("`.autopfp <hours>` to auto-rotate • `.getpfp` to fetch user pfps")
            await event.edit("\n".join(msg)[:3500])
        except Exception as e:
            await event.edit(f"`❌ {e}`")

    @client.flood_safe
    async def autopfp_handler(event):
        raw = (event.pattern_match.group(1) or "").strip()
        if not raw:
            await event.edit(
                "`➤ Usage:\n"
                ".autopfp <hours> [profile_name]\n"
                "e.g. .autopfp 2  — rotate saved pfps every 2h\n"
                ".autopfp 3 myprofile — rotate from profile myprofile\n"
                ".stopautopfp — stop`"
            )
            return
        parts = raw.split()
        try:
            hours = float(parts[0])
            hours = max(0.1, min(hours, 48))  # 6min to 48h
        except Exception:
            await event.edit("`➤ First arg must be hours (e.g. 2)`")
            return
        profile_name = parts[1] if len(parts)>1 else None

        # determine source dir
        source_dir = None
        if profile_name:
            safe = "".join(c for c in profile_name if c.isalnum() or c in "_-")[:30]
            cand = os.path.join(PROFILES_DIR, safe, "photos")
            if os.path.exists(cand) and os.listdir(cand):
                source_dir = cand
            else:
                # try PFP_DIR subdir
                cand2 = os.path.join(PFP_DIR, profile_name)
                if os.path.exists(cand2):
                    source_dir = cand2
        if not source_dir:
            # find latest pfp dir with files
            latest = None
            latest_mtime = 0
            if os.path.exists(PFP_DIR):
                for d in os.listdir(PFP_DIR):
                    dp = os.path.join(PFP_DIR, d)
                    if os.path.isdir(dp):
                        files = [os.path.join(dp,f) for f in os.listdir(dp) if os.path.isfile(os.path.join(dp,f))]
                        if files:
                            mtime = os.path.getmtime(dp)
                            if mtime > latest_mtime:
                                latest_mtime = mtime
                                latest = dp
            if latest:
                source_dir = latest
            else:
                # any files in PROFILES_DIR?
                if os.path.exists(PROFILES_DIR):
                    for d in os.listdir(PROFILES_DIR):
                        pd = os.path.join(PROFILES_DIR, d, "photos")
                        if os.path.exists(pd) and os.listdir(pd):
                            source_dir = pd
                            break
        if not source_dir or not os.path.exists(source_dir):
            await event.edit("`➤ No saved pfps found. First .pfpsave or .saveprofile <name>`")
            return
        files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir,f)) and f.lower().endswith(('.jpg','.jpeg','.png','.mp4','.mov'))]
        if not files:
            await event.edit(f"`➤ No images in {source_dir}`")
            return
        files.sort()  # deterministic

        # stop old task if any
        old = client.stop_processes.get("autopfp")
        if old and not old.done():
            old.cancel()
            await asyncio.sleep(0.5)

        await event.edit(f"✅ AutoPFP started: {len(files)} photo(s) every {hours}h from `{source_dir}`\nHuman-like delays + no flood.")

        async def _autopfp_loop():
            idx = 0
            try:
                while True:
                    # human-like random delay: hours +/- 15%
                    jitter = random.uniform(-0.15, 0.25) * hours * 3600
                    delay = hours * 3600 + jitter
                    delay = max(300, delay)  # min 5min
                    await asyncio.sleep(delay)
                    # pick next file
                    fp = files[idx % len(files)]
                    idx += 1
                    try:
                        is_vid = fp.lower().endswith(('.mp4','.mov'))
                        # delete 1 old? keep 1 for clean rotate? we will delete all then upload 1 to avoid stack
                        # but to avoid flood, we delete only 1? Actually for rotate we want single pfp, so delete all then upload new
                        await _delete_all_profile_photos(client)
                        await safe_sleep(random.uniform(1.0, 2.5), floor=0.8)
                        ok = await _upload_pfp_file(client, fp, is_video=is_vid)
                        if ok:
                            print(f"[autopfp] rotated to {fp}")
                        else:
                            print(f"[autopfp] failed {fp}")
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)
                        await asyncio.sleep(fw.seconds + 5)
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        print(f"[autopfp] loop error {e}")
                        await asyncio.sleep(60)
            except asyncio.CancelledError:
                print("[autopfp] stopped")
                raise
            finally:
                client.stop_processes.pop("autopfp", None)

        task = asyncio.create_task(_autopfp_loop())
        client.stop_processes["autopfp"] = task

    @client.flood_safe
    async def stopautopfp_handler(event):
        task = client.stop_processes.get("autopfp")
        if not task or task.done():
            await event.edit("`➤ No AutoPFP running.`")
            return
        task.cancel()
        client.stop_processes.pop("autopfp", None)
        await event.edit("`✅ AutoPFP stopped.`")

    # bind
    client.add_event_handler(clone_handler, events.NewMessage(outgoing=True, pattern=r"^\.clone(?:\s+(.*))?$"))
    client.add_event_handler(fclone_handler, events.NewMessage(outgoing=True, pattern=r"^\.fclone(?:\s+(.*))?$"))
    client.add_event_handler(revert_handler, events.NewMessage(outgoing=True, pattern=r"^\.revert(?:\s+(.*))?$"))
    client.add_event_handler(rclone_handler, events.NewMessage(outgoing=True, pattern=r"^\.rclone(?:\s+(full|f|all))?\s*$"))
    client.add_event_handler(saveprofile_handler, events.NewMessage(outgoing=True, pattern=r"^\.saveprofile(?:\s+(.*))?$"))
    client.add_event_handler(loadprofile_handler, events.NewMessage(outgoing=True, pattern=r"^\.loadprofile(?:\s+(.*))?$"))
    client.add_event_handler(floadprofile_handler, events.NewMessage(outgoing=True, pattern=r"^\.floadprofile(?:\s+(.*))?$"))
    client.add_event_handler(savedprofiles_handler, events.NewMessage(outgoing=True, pattern=r"^\.savedprofiles$"))
    client.add_event_handler(delprofile_handler, events.NewMessage(outgoing=True, pattern=r"^\.delprofile(?:\s+(.*))?$"))
    client.add_event_handler(vo_handler, events.NewMessage(outgoing=True, pattern=r"^\.vo(?:\s+(on|off|status))?$\s*$"))
    client.add_event_handler(vo_watcher, events.NewMessage())
    client.add_event_handler(setname_handler, events.NewMessage(outgoing=True, pattern=r"^\.setname(?:\s+(.*))?$"))
    client.add_event_handler(setbio_handler, events.NewMessage(outgoing=True, pattern=r"^\.setbio(?:\s+(.*))?$"))
    client.add_event_handler(delpfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.delpfp(?:\s+(\d+))?$"))
    client.add_event_handler(cleanpics_handler, events.NewMessage(outgoing=True, pattern=r"^\.cleanpics$"))
    client.add_event_handler(pfpsave_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfpsave$"))
    client.add_event_handler(pfpsave_handler, events.NewMessage(outgoing=True, pattern=r"^\.savepfp$"))
    client.add_event_handler(getpfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.getpfp(?:\s+(.*))?$"))
    client.add_event_handler(setpfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.setpfp$"))
    client.add_event_handler(pfplist_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfplist$"))
    client.add_event_handler(pfplist_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfps$"))
    client.add_event_handler(autopfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.autopfp(?:\s+(.*))?$"))
    client.add_event_handler(autopfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfprotate(?:\s+(.*))?$"))
    client.add_event_handler(stopautopfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.stopautopfp$"))

    print("[Module] profile.py v7.9.1 loaded — .clone .fclone .rclone .revert .saveprofile .loadprofile .floadprofile .pfpsave .getpfp .setpfp .pfplist .autopfp .stopautopfp .delpfp .cleanpics")

COMMANDS_PROFILE = {
    "description": "Profile & PFP Tools (Full Clone + Video)",
    "commands": [
        (".clone [full] / .clone @username", "clone a profile (reply to them OR give their @username) — add 'full' for all photos"),
        (".fclone / .fclone @username", "full clone — all photos/videos"),
        (".rclone [full]", "clone a RANDOM group member — no reply needed"),
        (".revert", "restore your pre-clone state (name/bio/DP)"),
        (".saveprofile <name>", "save full profile (all pfps)"),
        (".loadprofile <name>", "load main photo + name/bio"),
        (".floadprofile <name> / .loadprofile <name> full", "load full copy (all photos)"),
        (".savedprofiles / .delprofile", "list / delete saved profiles"),
        (".pfpsave / .savepfp", "save own or replied user's pfps"),
        (".getpfp [n]", "get replied user's pfps (1-20)"),
        (".setpfp", "set pfp from replied photo/video"),
        (".pfplist / .pfps", "list saved pfp collections"),
        (".autopfp <h> [name] / .pfprotate", "auto-rotate pfps every h hours (human-like, no flood)"),
        (".stopautopfp", "stop auto rotate"),
        (".delpfp [n]", "delete all or n pfps"),
        (".setname / .setbio", "set name/bio"),
        (".vo on|off", "view-once saver"),
    ],
}

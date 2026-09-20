# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: PROFILE  v6.7 — FULL CLONE, VIDEO PFP, AUTOPFP ROTATE, NO FLOOD
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

async def _delete_all_profile_photos(client) -> int:
    from telethon.tl.functions.photos import DeletePhotosRequest
    from telethon.tl.types import InputPhoto
    try:
        photos = await client.get_profile_photos("me")
    except Exception:
        return 0
    if not photos:
        return 0
    inputs = [
        InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference)
        for p in photos
        if getattr(p, "access_hash", None) is not None
    ]
    # fallback old way if file_reference missing
    if not inputs:
        inputs = [
            InputPhoto(id=p.id, access_hash=p.access_hash)
            for p in photos
            if getattr(p, "access_hash", None) is not None
        ]
    if inputs:
        try:
            await client(DeletePhotosRequest(id=inputs))
        except Exception as e:
            print(f"[profile] delete photos failed: {e}")
    return len(inputs)

async def _delete_n_photos(client, n: int) -> int:
    from telethon.tl.functions.photos import DeletePhotosRequest
    from telethon.tl.types import InputPhoto
    try:
        photos = await client.get_profile_photos("me")
    except Exception:
        return 0
    if not photos:
        return 0
    to_del = photos[:max(1, n)]
    inputs = []
    for p in to_del:
        try:
            inputs.append(InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference))
        except Exception:
            try:
                inputs.append(InputPhoto(id=p.id, access_hash=p.access_hash))
            except Exception:
                continue
    if inputs:
        try:
            await client(DeletePhotosRequest(id=inputs))
        except Exception as e:
            print(f"[profile] delete n failed: {e}")
    return len(inputs)

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

async def _clone_profile(client, event, target, full: bool = False):
    """Core clone logic. full=True => all photos/videos."""
    await event.edit(f"`{'🔥 Full' if full else '👤'} Cloning {'full profile' if full else 'profile'}...`")
    temp_dir = os.path.join(DATA_DIR, f"clone_temp_{event.id}")
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except Exception:
        pass
    downloaded = []
    try:
        user_info, user_full = await _get_user_full(client, target)
        if not user_info:
            await event.edit("`❌ Could not fetch user info.`")
            return
        first_name = (user_info.first_name or "")[:64]
        last_name = (user_info.last_name or "")[:64]
        bio = getattr(user_full, "about", None) or getattr(user_full, "bio", None) or ""
        bio = bio[:70]

        # download photos
        try:
            downloaded = await _download_all_pfps(client, target, temp_dir, limit=20 if full else 1)
        except Exception as e:
            print(f"[clone] download all failed: {e}")

        # backup current name to saved messages? optional
        # update name/bio first (safe, no flood)
        await safe_sleep(0.8, floor=0.4)
        try:
            await client(UpdateProfileRequest(
                first_name=first_name or DEFAULT_NAME,
                last_name=last_name,
                about=bio
            ))
        except FloodWaitError as fw:
            await event.edit(f"`⏳ FloodWait {fw.seconds}s on name update, retrying...`")
            await asyncio.sleep(fw.seconds + 1)
            await client(UpdateProfileRequest(first_name=first_name, last_name=last_name, about=bio))

        # delete old photos
        if downloaded:
            await safe_sleep(0.8, floor=0.4)
            if full:
                await _delete_all_profile_photos(client)
            else:
                # for main clone, delete all too to make clean (or just 1)
                await _delete_all_profile_photos(client)

        # upload new photos
        if downloaded:
            # for full clone, upload oldest first so newest becomes main
            to_upload = list(reversed(downloaded)) if full else downloaded
            success = 0
            for fpath, is_vid in to_upload:
                try:
                    await safe_sleep(1.2, floor=0.6)  # human delay
                    ok = await _upload_pfp_file(client, fpath, is_video=is_vid)
                    if ok:
                        success += 1
                except FloodWaitError as fw:
                    await event.edit(f"`⏳ FloodWait {fw.seconds}s on photo upload, waiting...`")
                    await asyncio.sleep(fw.seconds + 2)
                    try:
                        ok = await _upload_pfp_file(client, fpath, is_video=is_vid)
                        if ok:
                            success += 1
                    except Exception:
                        continue
            await event.edit(
                f"`✅ {'Full' if full else 'Main'} clone done!\n"
                f"Name: {first_name} {last_name}\n"
                f"Bio: {bio or 'N/A'}\n"
                f"Photos: {success}/{len(downloaded)}`"
            )
        else:
            await event.edit(
                f"`✅ Profile cloned (no photo)\n"
                f"Name: {first_name} {last_name}\n"
                f"Bio: {bio or 'N/A'}`"
            )
    except FloodWaitError as e:
        await event.edit(f"`⏳ FloodWait: {e.seconds}s`")
    except Exception as e:
        await event.edit(f"`❌ Clone error: {e}`")
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

    # .clone — main clone
    @client.flood_safe
    async def clone_handler(event):
        if not event.is_reply:
            await event.edit("`➤ Reply to user to clone. Use .fclone for full copy.`")
            return
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("`➤ No replied message.`")
            return
        try:
            target = await reply.get_input_sender()
        except Exception as e:
            await event.edit(f"`➤ Failed to get target: {e}`")
            return
        # check arg full
        arg = (event.pattern_match.group(1) or "").strip().lower()
        is_full = arg in ("full", "f", "all", "fullcopy")
        await _clone_profile(client, event, target, full=is_full)

    # .fclone — full clone (all photos/videos)
    @client.flood_safe
    async def fclone_handler(event):
        if not event.is_reply:
            await event.edit("`➤ Reply to user for full clone (.fclone).`")
            return
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("`➤ No replied message.`")
            return
        try:
            target = await reply.get_input_sender()
        except Exception as e:
            await event.edit(f"`➤ Failed: {e}`")
            return
        await _clone_profile(client, event, target, full=True)

    @client.flood_safe
    async def revert_handler(event):
        await event.edit("`➤ Reverting to default...`")
        try:
            await client(UpdateProfileRequest(first_name=DEFAULT_NAME, last_name="", about=""))
            await safe_sleep(0.6, floor=0.3)
            await _delete_all_profile_photos(client)
            await event.edit(f"`✅ Reverted to {DEFAULT_NAME}`")
        except FloodWaitError as e:
            await event.edit(f"`⏳ FloodWait: {e.seconds}s`")
        except Exception as e:
            await event.edit(f"`❌ Revert error: {e}`")

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
                await event.edit(f"`✅ Deleted {deleted} photo(s).`")
            else:
                deleted = await _delete_all_profile_photos(client)
                if not deleted:
                    await event.edit("`➤ No pfps to delete.`")
                else:
                    await event.edit(f"`✅ Deleted {deleted} photo(s).`")
        except FloodWaitError as e:
            await event.edit(f"`⏳ FloodWait {e.seconds}s`")
        except Exception as e:
            await event.edit(f"`❌ {e}`")

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

        await event.edit(f"`✅ AutoPFP started: {len(files)} photo(s) every {hours}h from `{source_dir}`\nHuman-like delays + no flood.`")

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
    client.add_event_handler(revert_handler, events.NewMessage(outgoing=True, pattern=r"^\.rclone(?:\s+(.*))?$"))
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
    client.add_event_handler(pfpsave_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfpsave$"))
    client.add_event_handler(pfpsave_handler, events.NewMessage(outgoing=True, pattern=r"^\.savepfp$"))
    client.add_event_handler(getpfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.getpfp(?:\s+(.*))?$"))
    client.add_event_handler(setpfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.setpfp$"))
    client.add_event_handler(pfplist_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfplist$"))
    client.add_event_handler(pfplist_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfps$"))
    client.add_event_handler(autopfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.autopfp(?:\s+(.*))?$"))
    client.add_event_handler(autopfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.pfprotate(?:\s+(.*))?$"))
    client.add_event_handler(stopautopfp_handler, events.NewMessage(outgoing=True, pattern=r"^\.stopautopfp$"))

    print("[Module] profile.py v6.7 loaded — .clone .fclone .saveprofile .loadprofile .floadprofile .pfpsave .getpfp .setpfp .pfplist .autopfp .stopautopfp .delpfp")

COMMANDS_PROFILE = {
    "description": "Profile & PFP Tools (Full Clone + Video)",
    "commands": [
        (".clone [full]", "clone main profile (reply) — add 'full' for all photos"),
        (".fclone", "full clone — all photos/videos (reply)"),
        (".revert / .rclone", "revert to default"),
        (".saveprofile <name>", "save full profile (all pfps)"),
        (".loadprofile <name>", "load main photo + name/bio"),
        (".floadprofile <name> / .loadprofile <name> full", "load full copy (all photos)"),
        (".savedprofiles / .delprofile", "list / delete saved"),
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

# ── SUKUNA-X DOMAIN v7.0 plugin ──────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: IDVAULT — 🔐 ID BACKUP & RESTORE SYSTEM (v7.0 PHANTOM)
#  "Restore your ID exactly as it was" — full profile snapshots:
#
#   .pbsave [name]   → save current ID (name + bio + DP) as snapshot
#   .pblist          → list all snapshots
#   .pbload <name>   → RESTORE that ID (name + bio + DP) — flood-safe
#   .pbdel <name>    → delete a snapshot
#   .undp            → undo last DP change (auto-backup before every set)
#
#  Protection: human delays between name/bio/DP changes, FloodWait retry,
#  everything saved in data/idvault/ (gitignored, safe from git pull).
# ============================================================================

import datetime as _dt

VAULT_DIR = os.path.join(DATA_DIR, "idvault")
PREV_DP = os.path.join(DATA_DIR, "dp_pool", "_prev.jpg")   # written by dp.py
PREV_META = os.path.join(DATA_DIR, "dp_pool", "_prev.json")


def _vault_dir(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_\-]", "_", name.strip())[:24] or "snap"
    return os.path.join(VAULT_DIR, safe)


def _vault_list():
    """[(name, meta_dict, dir)] sorted newest first."""
    out = []
    if not os.path.isdir(VAULT_DIR):
        return out
    for d in sorted(os.listdir(VAULT_DIR)):
        meta_p = os.path.join(VAULT_DIR, d, "meta.json")
        if not os.path.isfile(meta_p):
            continue
        try:
            with open(meta_p, "r", encoding="utf-8") as fh:
                meta = json.load(fh)
            out.append((d, meta, os.path.join(VAULT_DIR, d)))
        except Exception:
            continue
    out.sort(key=lambda x: float((x[1] or {}).get("ts") or 0), reverse=True)
    return out


async def _get_my_bio(client) -> str:
    try:
        full = await client(GetFullUserRequest("me"))
        return (getattr(full.full_user, "about", "") or "")
    except Exception:
        return ""


async def _save_dp_now(client, dest: str) -> bool:
    """Download my current profile photo to dest. Returns True if saved."""
    try:
        photos = await client.get_profile_photos("me", limit=1)
        if not photos:
            return False
        dl = await client.download_media(photos[0], file=dest)
        return bool(dl and os.path.exists(dl))
    except Exception:
        return False


def register_idvault(client):
    """Profile snapshot save/restore commands."""

    # ---- .pbsave [name] ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pbsave(?:\s+(\S+))?$"))
    @client.flood_safe
    async def _pbsave(event):
        name = (event.pattern_match.group(1) or "").strip() or \
            _dt.datetime.now().strftime("snap_%d%b_%H%M")
        vdir = _vault_dir(name)
        os.makedirs(vdir, exist_ok=True)
        await event.edit("🔐 Saving ID snapshot… (name + bio + DP)")
        me = await client.get_me()
        bio = await _get_my_bio(client)
        has_dp = await _save_dp_now(client, os.path.join(vdir, "dp.jpg"))
        meta = {
            "ts": time.time(),
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "username": me.username or "",
            "bio": bio[:250],
            "has_dp": has_dp,
        }
        with open(os.path.join(vdir, "meta.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False)
        await event.edit(
            f"✦ ━━━〔 🔐 ID SAVED 〕━━━ ✦\n"
            f"✅ Snapshot **`{os.path.basename(vdir)}`** ready!\n"
            f"┃ 👤 Name: {meta['first_name']} {meta['last_name']}\n"
            f"┃ 📝 Bio : {bio[:60] or '—'}\n"
            f"┃ 🖼 DP  : {'saved' if has_dp else 'no DP saved'}\n"
            f"┃ 🗂 Total snapshots: `{len(_vault_list())}`\n\n"
            f"`.pbload {os.path.basename(vdir)}` to restore it anytime",
            link_preview=False)

    # ---- .pblist ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pblist$"))
    @client.flood_safe
    async def _pblist(event):
        snaps = _vault_list()
        if not snaps:
            return await event.edit(
                "📭 No snapshots yet.\n💡 `.pbsave old` — back up your current ID.")
        lines = ["✦ ━━━〔 🔐 ID VAULT 〕━━━ ✦",
                 f"🗂 `{len(snaps)}` snapshot(s)", "─" * 26]
        for name, meta, _d in snaps[:15]:
            ts = float(meta.get("ts") or 0)
            when = _dt.datetime.fromtimestamp(ts).strftime("%d %b, %H:%M") if ts else "—"
            dp = "🖼" if meta.get("has_dp") else "  "
            lines.append(f"┃ {dp} **`{name}`** — {when}\n"
                         f"┃    👤 {meta.get('first_name', '')} "
                         f"{meta.get('last_name', '')}".rstrip())
        lines += ["─" * 26, "💡 `.pbload <name>` restore · `.pbdel <name>` delete · `.undp` last DP undo"]
        await event.edit("\n".join(lines)[:3900], link_preview=False)

    # ---- .pbload <name> : RESTORE full ID ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pbload\s+(\S+)$"))
    @client.flood_safe
    async def _pbload(event):
        name = event.pattern_match.group(1).strip()
        vdir = _vault_dir(name)
        meta_p = os.path.join(vdir, "meta.json")
        if not os.path.isfile(meta_p):
            names = ", ".join(f"`{n}`" for n, _, _ in _vault_list()[:8]) or "none"
            return await event.edit(f"❌ Snapshot `{name}` not found.\n🗂 Available: {names}")
        with open(meta_p, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        await event.edit(f"♻️ ID **`{name}`** Restoring… (name → bio → DP)")
        errors = []
        # 1) name
        try:
            await throttle("send")
            await safe_sleep(random.uniform(1.0, 2.0), floor=0.6)
            await client(UpdateProfileRequest(
                first_name=(meta.get("first_name") or "User")[:64],
                last_name=(meta.get("last_name") or "")[:64],
                about=(meta.get("bio") or "")[:70]))
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 3)
            try:
                await client(UpdateProfileRequest(
                    first_name=(meta.get("first_name") or "User")[:64],
                    last_name=(meta.get("last_name") or "")[:64],
                    about=(meta.get("bio") or "")[:70]))
            except Exception as e:
                errors.append(f"name/bio: {e}")
        except Exception as e:
            errors.append(f"name/bio: {e}")
        # 2) DP
        dp_path = os.path.join(vdir, "dp.jpg")
        if meta.get("has_dp") and os.path.exists(dp_path):
            try:
                from plugins.profile import _delete_all_profile_photos, _upload_pfp_file
                await safe_sleep(random.uniform(1.5, 2.8), floor=0.8)
                await _delete_all_profile_photos(client)
                await safe_sleep(random.uniform(1.0, 2.0), floor=0.6)
                await _upload_pfp_file(client, dp_path, is_video=False)
            except FloodWaitError as fw:
                note_flood(fw.seconds)
                errors.append(f"DP: FloodWait {fw.seconds}s — `.setdp` retry later")
            except Exception as e:
                errors.append(f"DP: {e}")
        if errors:
            await event.edit(
                f"⚠️ Partial restore hua:\n" + "\n".join(f"┃ ❌ {e}" for e in errors),
                link_preview=False)
        else:
            await event.edit(
                f"✦ ━━━〔 ♻️ ID RESTORED 〕━━━ ✦\n"
                f"✅ **`{name}`** restored — exactly like before! 👑\n"
                f"👤 {meta.get('first_name', '')} {meta.get('last_name', '')}\n"
                f"🖼 DP: {'restored' if meta.get('has_dp') else 'n/a'}",
                link_preview=False)

    # ---- .pbdel <name> ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pbdel\s+(\S+)$"))
    @client.flood_safe
    async def _pbdel(event):
        name = event.pattern_match.group(1).strip()
        vdir = _vault_dir(name)
        if not os.path.isdir(vdir):
            return await event.edit(f"❌ Snapshot `{name}` not found. See `.pblist`.")
        shutil.rmtree(vdir, ignore_errors=True)
        await event.edit(f"🗑 Snapshot **`{os.path.basename(vdir)}`** deleted.")

    # ---- .undp : undo last DP change ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:undp|prevdp)$"))
    @client.flood_safe
    async def _undp(event):
        if not os.path.exists(PREV_DP) or os.path.getsize(PREV_DP) < 500:
            return await event.edit(
                "❌ Koi previous DP backup not found.\n"
                "💡 A backup is created automatically whenever `.setdp` / `.nextdp` / rotator changes the DP.")
        prev_name = ""
        try:
            if os.path.exists(PREV_META):
                with open(PREV_META, "r", encoding="utf-8") as fh:
                    prev_name = (json.load(fh) or {}).get("label", "")
        except Exception:
            pass
        await event.edit("↩️ Restoring the previous DP…")
        ok = False
        for attempt in range(2):
            try:
                from plugins.profile import _delete_all_profile_photos, _upload_pfp_file
                await throttle("send")
                await safe_sleep(random.uniform(1.2, 2.4), floor=0.7)
                await _delete_all_profile_photos(client)
                await safe_sleep(random.uniform(1.0, 1.8), floor=0.6)
                ok = await _upload_pfp_file(client, PREV_DP, is_video=False)
                if ok:
                    break
            except FloodWaitError as fw:
                note_flood(fw.seconds)
                await asyncio.sleep(fw.seconds + 5)
            except Exception:
                await asyncio.sleep(2)
        if ok:
            await event.edit(
                f"✦ ━━━〔 ↩️ DP UNDO 〕━━━ ✦\n✅ Previous DP restored! 👑\n"
                + (f"🏷 {prev_name}" if prev_name else ""),
                link_preview=False)
        else:
            await event.edit("❌ Undo failed — retry in 30 seconds.")


COMMANDS_IDVAULT = {
    "description": "ID Backup & Restore",
    "type": "Profile",
    "commands": [
        (".pbsave [name]", "snapshot the current ID (name+bio+DP)"),
        (".pblist", "list all snapshots"),
        (".pbload <name>", "restore that ID fully (name+bio+DP)"),
        (".pbdel <name>", "delete a snapshot"),
        (".undp / .prevdp", "undo the last DP change (auto-backup)"),
    ],
}

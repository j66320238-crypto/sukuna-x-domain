# ── SUKUNA-X DOMAIN v7.0 plugin ──────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: DP — 🖼 DP POOL SYSTEM + AUTO DP ROTATOR (v7.0 PHANTOM)
#  Inspired by Ultroid .autopic / CatUserbot autopfp — rebuilt tagra edition:
#
#   .adddp [n]      → reply to photo, save in numbered pool (1,2,3…)
#   .dplist         → list all pool DPs with numbers
#   .getdp <n>      → show DP number n in chat
#   .setdp <n>      → apply DP number n as your profile photo
#   .curdp          → which pool number is your CURRENT dp? (smart match)
#   .nextdp         → instantly rotate to the next DP
#   .deldp <n|all>  → delete one / all pool DPs (auto renumber)
#   .autodp <time> [shuffle] → auto rotate every 2h / 45m … (min 10m)
#   .stopautodp     → stop rotation
#
#  Protection: flood-safe uploads, human jitter, FloodWait auto-retry,
#  image auto-resize (no upload errors), state saved to disk, no limits.
# ============================================================================

import glob as _glob
import hashlib as _hashlib

DP_DIR = os.path.join(DATA_DIR, "dp_pool")
DP_STATE = os.path.join(DP_DIR, "state.json")
_MIN_INTERVAL_MIN = 10          # Telegram-safe floor
_MAX_INTERVAL_MIN = 7 * 24 * 60  # 7 days cap


# ── pool helpers ─────────────────────────────────────────────────────────
def _dp_ensure_dir():
    os.makedirs(DP_DIR, exist_ok=True)


def _dp_files():
    """Return sorted [(number, path)] of pool images."""
    _dp_ensure_dir()
    out = []
    for p in sorted(_glob.glob(os.path.join(DP_DIR, "dp_*.jpg"))):
        try:
            num = int(os.path.basename(p)[3:6])
            out.append((num, p))
        except Exception:
            continue
    out.sort(key=lambda x: x[0])
    return out


def _dp_path(n: int):
    return os.path.join(DP_DIR, f"dp_{n:03d}.jpg")


def _dp_load_state():
    try:
        with open(DP_STATE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _dp_save_state(state: dict):
    try:
        _dp_ensure_dir()
        with open(DP_STATE, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    except Exception:
        pass


def _dp_renumber():
    """Rename pool files so numbers stay 1,2,3… after deletions."""
    files = _dp_files()
    tmp_map = []
    for i, (_, path) in enumerate(files):
        tmp = os.path.join(DP_DIR, f"_tmp_{i:03d}.jpg")
        try:
            os.replace(path, tmp)
            tmp_map.append(tmp)
        except OSError:
            pass
    for i, tmp in enumerate(tmp_map, 1):
        try:
            os.replace(tmp, _dp_path(i))
        except OSError:
            pass
    return len(tmp_map)


def _dp_prep_image(src: str, dest: str) -> bool:
    """Convert/resize any image to a safe square-ish JPEG (≤512KB) for pfp upload."""
    if _HAS_PIL:
        try:
            im = Image.open(src)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            # downscale huge images (Telegram pfp sweet spot)
            if max(im.size) > 1080:
                im.thumbnail((1080, 1080), Image.LANCZOS)
            im.save(dest, "JPEG", quality=88)
            # if still big, squeeze harder
            if os.path.getsize(dest) > 500_000:
                im.save(dest, "JPEG", quality=72)
            return True
        except Exception:
            pass
    # no PIL / failed → copy raw file
    try:
        shutil.copyfile(src, dest)
        return True
    except OSError:
        return False


def _dp_fingerprint(path: str):
    """16x16 grayscale fingerprint for smart current-DP matching (PIL)."""
    if not _HAS_PIL:
        return None
    try:
        with Image.open(path) as im:
            im = im.convert("L").resize((16, 16), Image.LANCZOS)
            return tuple(im.getdata())
    except Exception:
        return None


def _fp_distance(a, b) -> float:
    if not a or not b or len(a) != len(b):
        return 9999.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def _parse_interval(text: str):
    """'90' / '45m' / '2h' / '1.5h' / '1d' → minutes (clamped to safe range)."""
    text = (text or "").strip().lower()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(m|min|mins|h|hr|hrs|d|day|days)?$", text)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or "m"
    if unit.startswith("h"):
        val *= 60
    elif unit.startswith("d"):
        val *= 1440
    return max(_MIN_INTERVAL_MIN, min(val, _MAX_INTERVAL_MIN))


async def _dp_backup_current(client, label: str = ""):
    """Save current profile photo as _prev.jpg (for .undp) — silent, best-effort."""
    prev_dp = os.path.join(DP_DIR, "_prev.jpg")
    prev_meta = os.path.join(DP_DIR, "_prev.json")
    try:
        photos = await client.get_profile_photos("me", limit=1)
        if not photos:
            return
        tmp = os.path.join(DP_DIR, "_prev_tmp.jpg")
        dl = await client.download_media(photos[0], file=tmp)
        if dl and os.path.exists(dl) and os.path.getsize(dl) > 500:
            try:
                if os.path.exists(prev_dp):
                    os.remove(prev_dp)
            except OSError:
                pass
            os.replace(tmp, prev_dp)
            try:
                with open(prev_meta, "w", encoding="utf-8") as fh:
                    json.dump({"label": label, "ts": time.time()}, fh)
            except OSError:
                pass
        elif os.path.exists(tmp):
            os.remove(tmp)
    except Exception as e:
        log.debug("[dp] prev-DP backup skipped: %s", e)


async def _dp_apply(client, event_msg, n: int, quiet: bool = False) -> bool:
    """Set pool DP #n as profile photo with full protection. Returns success."""
    path = _dp_path(n)
    if not os.path.exists(path):
        if not quiet:
            try:
                await event_msg.edit(f"❌ DP `{n}` is not in the pool. See `.dplist`.")
            except Exception:
                pass
        return False
    # 🔐 auto-backup current DP before changing (for .undp)
    await _dp_backup_current(client, label=f"before DP #{n}")
    try:
        from plugins.profile import _delete_all_profile_photos, _upload_pfp_file
    except Exception:
        if not quiet:
            try:
                await event_msg.edit("❌ Profile engine failed to load.")
            except Exception:
                pass
        return False
    ok = False
    for attempt in range(2):
        try:
            await throttle("send")
            await safe_sleep(random.uniform(1.0, 2.2), floor=0.5)
            await _delete_all_profile_photos(client)
            await safe_sleep(random.uniform(0.8, 1.6), floor=0.5)
            ok = await _upload_pfp_file(client, path, is_video=False)
            if ok:
                break
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            log.warning("[dp] FloodWait %ss while setting DP #%s", fw.seconds, n)
            await asyncio.sleep(fw.seconds + 5)
        except Exception as e:
            log.error("[dp] set DP #%s attempt %s failed: %s", n, attempt + 1, e)
            await asyncio.sleep(2)
    if ok:
        state = _dp_load_state()
        state["current"] = n
        state["last_set"] = time.time()
        _dp_save_state(state)
    return ok


def _autodp_task_key():
    return "autodp_rotator"


def _dp_start_rotator(client, mins: float, shuffle: bool) -> None:
    """(Re)start the rotation background task with given settings."""
    old = client.stop_processes.get(_autodp_task_key())
    if old and not old.done():
        old.cancel()

    state = _dp_load_state()
    state["interval_min"] = mins
    state["mode"] = "shuffle" if shuffle else "order"
    state["rot_started"] = time.time()
    _dp_save_state(state)

    async def _rotate_loop():
        consec_fails = 0
        try:
            while True:
                wait = (mins * 60) * random.uniform(0.92, 1.08)
                await asyncio.sleep(wait)
                if storm_active():  # 🚨 ban-storm cooldown — is cycle skip
                    log.info("[dp] storm active — rotation skipped for safety")
                    await asyncio.sleep(300)
                    continue
                pool = _dp_files()
                if len(pool) < 2:
                    log.info("[dp] autodp stopped — pool has <2 images")
                    break
                st = _dp_load_state()
                cur = st.get("current") or 0
                nums = [n for n, _ in pool]
                if st.get("mode") == "shuffle":
                    choices = [n for n in nums if n != cur] or nums
                    nxt = random.choice(choices)
                else:
                    nxt = nums[0] if cur not in nums else nums[(nums.index(cur) + 1) % len(nums)]
                ok = await _dp_apply(client, None, nxt, quiet=True)
                if ok:
                    consec_fails = 0
                    log.info("[dp] autodp rotated → DP #%s", nxt)
                else:
                    consec_fails += 1
                    if consec_fails >= 3:
                        log.warning("[dp] autodp: 3 fails — backoff 5min")
                        await asyncio.sleep(300)
                        consec_fails = 0
        except asyncio.CancelledError:
            log.info("[dp] autodp stopped by user")
            raise

    task = asyncio.create_task(_rotate_loop())
    client.stop_processes[_autodp_task_key()] = task


def _fmt_interval(mins: float) -> str:
    if mins < 60:
        return f"{mins:.0f} min"
    if mins < 1440:
        return f"{mins/60:.1f} h"
    return f"{mins/1440:.1f} din"


# ── registration ─────────────────────────────────────────────────────────
def register_dp(client):
    """DP pool + auto rotator commands."""

    # ---- .adddp [n] ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.adddp(?:\s+(\d+))?$"))
    @client.flood_safe
    async def _adddp(event):
        reply = await event.get_reply_message()
        if not reply or not reply.photo:
            return await event.edit(
                "❌ Reply to a **photo** with `.adddp`\n"
                "💡 `.adddp 3` → save as number 3 (replace).",
                link_preview=False)
        want_n = event.pattern_match.group(1)
        files = _dp_files()
        nums = [n for n, _ in files]
        if want_n:
            n = int(want_n)
            if n < 1 or n > len(nums) + 1:
                return await event.edit(
                    f"❌ Number `{n}` not allowed — the pool has {len(nums)} DPs "
                    f"(you can only use 1 to {len(nums) + 1}, no gaps).")
        else:
            n = (max(nums) + 1) if nums else 1
        await event.edit("💾 Saving DP…")
        tmp = os.path.join(DATA_DIR, f"dp_in_{event.id}.jpg")
        try:
            dl = await client.download_media(reply, file=tmp)
            if not dl:
                return await event.edit("❌ Photo could not be downloaded.")
            dest = _dp_path(n)
            if not _dp_prep_image(dl, dest):
                return await event.edit("❌ Image conversion failed — try another photo.")
            if not want_n and n not in nums:
                pass  # appending fresh
            state = _dp_load_state()
            _dp_save_state(state)
            total = len(_dp_files())
            await event.edit(
                f"✦ ━━━〔 🖼 DP SAVED 〕━━━ ✦\n"
                f"✅ DP **#{n}** saved to the pool!\n"
                f"📚 Pool total: `{total}` DP\n\n"
                f"`.getdp {n}` view · `.setdp {n}` apply · `.autodp 2h` rotate",
                link_preview=False)
        except Exception as exc:
            await event.edit(f"❌ Add error: `{exc}`")
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass

    # ---- .dplist ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dplist$"))
    @client.flood_safe
    async def _dplist(event):
        files = _dp_files()
        state = _dp_load_state()
        cur = state.get("current")
        if not files:
            return await event.edit(
                "📭 The DP pool is empty.\n"
                "💡 Reply to a photo with `.adddp` — the number is assigned automatically.",
                link_preview=False)
        lines = ["✦ ━━━〔 🖼 DP POOL 〕━━━ ✦",
                 f"📚 Total `{len(files)}` DP"
                 + (f" • 🎯 Current: **#{cur}**" if cur else "")]
        lines.append("─" * 26)
        for n, path in files:
            size_kb = os.path.getsize(path) / 1024
            mark = " 🎯" if n == cur else ""
            lines.append(f"┃ **{n}.** `{os.path.basename(path)}` ({size_kb:.0f} KB){mark}")
        lines.append("─" * 26)
        running = client.stop_processes.get(_autodp_task_key())
        rot = ("🔄 Auto-rotator **ON**" if running and not running.done()
               else "⏸ Rotator OFF — `.autodp 2h`")
        lines.append(f"{rot}\n`.getdp n` `.setdp n` `.deldp n` `.nextdp` `.curdp`")
        await event.edit("\n".join(lines)[:3900], link_preview=False)

    # ---- .getdp <n> ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.getdp\s+(\d+)$"))
    @client.flood_safe
    async def _getdp(event):
        n = int(event.pattern_match.group(1))
        path = _dp_path(n)
        if not os.path.exists(path):
            total = len(_dp_files())
            return await event.edit(
                f"❌ DP `{n}` is not in the pool."
                + (f" The pool has 1–{total}." if total else " The pool is empty — use `.adddp`"))
        await throttle("send")
        await client.send_file(
            await event.get_input_chat(), path,
            caption=f"🖼 **DP #{n}** — Sukuna-X pool",
            reply_to=event.id)
        await event.delete()

    # ---- .setdp <n> ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setdp\s+(\d+)$"))
    @client.flood_safe
    async def _setdp(event):
        n = int(event.pattern_match.group(1))
        await event.edit(f"🖼 DP **#{n}** applying… (the old DP will be deleted)")
        ok = await _dp_apply(client, event, n, quiet=True)
        if ok:
            await event.edit(
                f"✦ ━━━〔 🖼 DP SET 〕━━━ ✦\n✅ **DP #{n}** profile pe applied! 👑\n"
                f"Check anytime with `.curdp`", link_preview=False)
        else:
            await event.edit(f"❌ DP #{n} could not be set. Check `.dplist` or retry.")

    # ---- .curdp : which number is my current dp? ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.curdp$"))
    @client.flood_safe
    async def _curdp(event):
        files = _dp_files()
        state = _dp_load_state()
        if not files:
            return await event.edit("📭 The pool is empty — add photos with `.adddp` first.")
        await event.edit("🔍 Matching your current DP…")
        tmp = os.path.join(DATA_DIR, f"curdp_{event.id}.jpg")
        match_n = None
        try:
            photos = await client.get_profile_photos("me", limit=1)
            if not photos:
                return await event.edit("❌ You don't have any profile photo.")
            dl = await client.download_media(photos[0], file=tmp)
            if not dl:
                return await event.edit("❌ Could not download the current DP.")
            if str(dl).lower().endswith((".mp4", ".mov")):
                return await event.edit("🎥 Current DP **video** hai — pool me sirf images milti hain.")
            cur_fp = _dp_fingerprint(dl)
            if cur_fp is None:
                # no PIL fallback: state-based answer
                cur = state.get("current")
                return await event.edit(
                    f"🖼 Last rotation ke hisaab se current DP: **#{cur}**\n"
                    "_(Pillow not installed — pixel match skipped)_" if cur else
                    "❌ Unknown — use `.setdp <n>` or `.nextdp`.")
            best, best_d = None, 9999.0
            for n, path in files:
                d = _fp_distance(cur_fp, _dp_fingerprint(path))
                if d < best_d:
                    best, best_d = n, d
            if best is not None and best_d < 14:
                match_n = best
        except Exception as exc:
            return await event.edit(f"❌ Check error: `{exc}`")
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
        if match_n:
            await event.edit(
                f"✦ ━━━〔 🎯 CURRENT DP 〕━━━ ✦\n"
                f"🖼 Your current DP is pool **#{match_n}**! ✅\n"
                f"`.getdp {match_n}` · `.nextdp` to apply the next one", link_preview=False)
        else:
            last = state.get("current")
            await event.edit(
                "🤷 Your current DP **does not match** any pool image (it is custom).\n"
                + (f"ℹ️ Last rotation: #{last}" if last else "")
                + "\n💡 Apply a pool DP with `.setdp <n>` or `.nextdp`.")

    # ---- .nextdp : instant rotate ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.nextdp$"))
    @client.flood_safe
    async def _nextdp(event):
        files = _dp_files()
        if not files:
            return await event.edit("📭 The pool is empty — add photos with `.adddp`.")
        state = _dp_load_state()
        cur = state.get("current") or 0
        nums = [n for n, _ in files]
        nxt = nums[0] if cur not in nums else nums[(nums.index(cur) + 1) % len(nums)]
        await event.edit(f"🔄 DP **#{cur or '?'}** → **#{nxt}** rotating…")
        ok = await _dp_apply(client, event, nxt, quiet=True)
        if ok:
            await event.edit(f"✅ DP **#{nxt}** applied! 👑\n`.curdp` verify · automate with `.autodp 2h`")
        else:
            await event.edit(f"❌ DP #{nxt} could not be set — retry.")

    # ---- .deldp <n|all> ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.deldp\s+(\d+|all)$"))
    @client.flood_safe
    async def _deldp(event):
        arg = event.pattern_match.group(1)
        files = _dp_files()
        if not files:
            return await event.edit("📭 The pool is already empty.")
        state = _dp_load_state()
        if arg == "all":
            for _, p in files:
                try:
                    os.remove(p)
                except OSError:
                    pass
            state.pop("current", None)
            _dp_save_state(state)
            old = client.stop_processes.get(_autodp_task_key())
            if old and not old.done():
                old.cancel()
            return await event.edit(f"🗑 **{len(files)} DP** delete + pool clear + rotator OFF.")
        n = int(arg)
        path = _dp_path(n)
        if not os.path.exists(path):
            return await event.edit(f"❌ DP `{n}` is not in the pool. See `.dplist`.")
        os.remove(path)
        new_total = _dp_renumber()
        if state.get("current") == n:
            state.pop("current", None)
        elif isinstance(state.get("current"), int) and state["current"] > n:
            state["current"] = state["current"] - 1
        _dp_save_state(state)
        await event.edit(
            f"🗑 DP **#{n}** deleted.\n"
            f"📚 Pool me ab `{new_total}` DP (numbers re-align ho gaye: 1..{new_total}).")

    # ---- .autodp <time> [shuffle] ----
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.autodp(?:\s+(\S+)(?:\s+(shuffle))?)?$"))
    @client.flood_safe
    async def _autodp(event):
        files = _dp_files()
        if len(files) < 2:
            return await event.edit(
                "❌ Auto-rotation needs **at least 2 DPs** in the pool.\n"
                "💡 Reply to photos with `.adddp` to add them.")
        arg_time = event.pattern_match.group(1)
        shuffle = bool(event.pattern_match.group(2))
        if not arg_time:
            return await event.edit(
                "⏱ Usage: `.autodp <time> [shuffle]`\n"
                "💡 Examples: `.autodp 2h` · `.autodp 45m` · `.autodp 90` · `.autodp 6h shuffle`\n"
                f"🛡 Minimum {_MIN_INTERVAL_MIN} min (ban-safe).", link_preview=False)
        mins = _parse_interval(arg_time)
        if mins is None:
            return await event.edit(f"❌ Could not parse the time: `{arg_time}`\n💡 Try `2h`, `45m`, `1d`")

        files2 = _dp_files()
        _dp_start_rotator(client, mins, shuffle)
        mode_txt = "🔀 SHUFFLE" if shuffle else "➡️ ORDER (1→2→3→…)"
        await event.edit(
            f"✦ ━━━〔 🔄 AUTO DP ROTATOR 〕━━━ ✦\n"
            f"✅ every **{_fmt_interval(mins)}** your DP will change every interval!\n"
            f"📚 Pool: `{len(files2)}` DP • Mode: {mode_txt}\n"
            f"🛡 Flood-safe + human jitter + auto-retry\n\n"
            f"⏱ `.dptime <new time>` live change · `.dpstatus` for details\n"
            f"`.stopautodp` stop · `.nextdp` manual",
            link_preview=False)

    # ---- .stopautodp ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stopautodp$"))
    @client.flood_safe
    async def _stopautodp(event):
        task = client.stop_processes.get(_autodp_task_key())
        if task and not task.done():
            task.cancel()
            client.stop_processes.pop(_autodp_task_key(), None)
            await event.edit("⏹ Auto DP rotator stopped. 🛡️ The current DP stays as is.")
        else:
            await event.edit("ℹ️ The rotator is not running. Start it with `.autodp 2h`.")

    # ---- .dptime <interval> : live change rotator timer ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dptime\s+(\S+)$"))
    @client.flood_safe
    async def _dptime(event):
        arg = event.pattern_match.group(1)
        mins = _parse_interval(arg)
        if mins is None:
            return await event.edit(
                f"❌ Could not parse the time: `{arg}`\n"
                "💡 Examples: `.dptime 2h` · `.dptime 45m` · `.dptime 1d`\n"
                f"🛡 Range: {_MIN_INTERVAL_MIN} min se 7 din tak.")
        if len(_dp_files()) < 2:
            return await event.edit("❌ The pool needs at least 2 DPs — use `.adddp`.")
        state = _dp_load_state()
        old_min = state.get("interval_min")
        shuffle = (state.get("mode") == "shuffle")
        _dp_start_rotator(client, mins, shuffle)  # restart with new timing
        was_running = old_min is not None
        await event.edit(
            f"✦ ━━━〔 ⏱ TIMER UPDATED 〕━━━ ✦\n"
            f"✅ Your DP will now change every **{_fmt_interval(mins)}** me change hogi.\n"
            + (f"🔁 Previous timer {_fmt_interval(old_min)} replaced.\n" if was_running and old_min else "")
            + f"🔀 Mode: {'shuffle' if shuffle else 'order'} • 🛡️ Rotator restarted.\n"
            f"`.dpstatus` details · `.stopautodp` stop",
            link_preview=False)

    # ---- .dpstatus : full rotator status card ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dpstatus$"))
    @client.flood_safe
    async def _dpstatus(event):
        state = _dp_load_state()
        task = client.stop_processes.get(_autodp_task_key())
        running = bool(task and not task.done())
        pool_n = len(_dp_files())
        cur = state.get("current")
        mins = state.get("interval_min")
        mode = "🔀 shuffle" if state.get("mode") == "shuffle" else "➡️ order"
        lines = [
            "✦ ━━━〔 📊 DP STATUS 〕━━━ ✦",
            f"┃ 🔄 Rotator : {'✅ **RUNNING**' if running else '⏸ Stopped'}",
        ]
        if mins:
            lines.append(f"┃ ⏱ Interval : **{_fmt_interval(float(mins))}** ({mode})")
        if cur:
            lines.append(f"┃ 🎯 Current : DP **#{cur}**")
        last = state.get("last_set")
        if last:
            ago = int(time.time() - float(last))
            lines.append(f"┃ 🕒 Last set: {_fmt_uptime(ago)} ago")
        started = state.get("rot_started")
        if running and started:
            elapsed = time.time() - float(started)
            if mins:
                remain = max(0, (float(mins) * 60) - elapsed)
                lines.append(f"┃ ⏭ Next    : ~{_fmt_uptime(remain)} (approx)")
        lines.append(f"┃ 📚 Pool   : `{pool_n}` DP")
        lines.append("─" * 26)
        lines.append("💡 `.dptime 2h` timer change · `.nextdp` manual · `.dplist` pool")
        await event.edit("\n".join(lines), link_preview=False)


COMMANDS_DP = {
    "description": "DP Pool & Auto Rotator",
    "type": "AI & Media",
    "commands": [
        (".adddp [n]", "reply to a photo → save into the numbered pool"),
        (".dplist", "list every pooled DP with its number"),
        (".getdp <n>", "show pool DP number n in chat"),
        (".setdp <n>", "apply pool DP number n as profile photo"),
        (".curdp", "which pool number is the current DP?"),
        (".nextdp", "instantly rotate to the next DP"),
        (".deldp <n|all>", "delete one or all DPs (auto renumber)"),
        (".autodp <time> [shuffle]", "auto rotator: .autodp 2h / 45m / 6h shuffle"),
        (".dptime <time>", "change the rotator timer LIVE"),
        (".dpstatus", "full rotator status: interval/next ETA/current"),
        (".stopautodp", "stop the rotator"),
    ],
}

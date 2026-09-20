# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
# SECTION: FARMER — 🎮 Isolation Auto-Farmer (Baka engine, SUKUNA-X edition)
#
# Ported from "Baka Isolation Master" (baka12.py) and rebuilt on Telethon:
#   • multi-group rotation engine — one shared, safe pace for all groups
#   • SMART mode: auto /bal → read exact coins → /rob <exact> → protection
#     detect → skip protected user, take the next one
#   • processed-user memory (auto-resets every 4h) · ignore-list · deep scan
#   • everything runs inside the SUKUNA-X 5-layer anti-ban engine
#
# Game bot: @im_bakabot  (change anytime with `.mbot <username>`)
# Run it in YOUR OWN groups where the game bot is present.
# ============================================================================

# ---- settings (persisted in sukuna_data/farmer.json) ----
FARM_DEFAULTS = {
    "game_bot": "im_bakabot",   # game bot username (no @)
    "skip_protected": True,     # True = protected user chhodo, agla pakdo
    "min_rob": 10,              # isse kam coins = skip
    "history_depth": 300,       # kitni history scan karni hai
    "mode": "medium",           # slow | medium | fast (global pace)
    "ignore": [],
}
FARM_SPEEDS = {                 # (acc_gap, cmd_gap) seconds
    "slow": (12.0, 9.0),
    "medium": (7.0, 6.0),
    "fast": (5.0, 4.5),
}

# ---- engine limits (hard — tuned so the account stays ban-safe) ----
FARM_MIN_GAP = 4.0              # min seconds between two game commands
FARM_QUOTA = 60                 # max tasks per run, then full rest
FARM_BREAK_EVERY = (3, 5)       # human breather after N tasks
FARM_BREAK_LEN = (15, 45)       # breather length (seconds)
FARM_CYCLE_REST = (15, 45)      # rest between full group rotations
FARM_FLOOD_STRIKES = 3          # 3 FloodWaits → auto-bench
FARM_SKIP_CHANCE = 0.08         # 8% random skip — human-like
FARM_MAX_OFFSET = 2000          # deep-scan ceiling (older messages)
FARM_AUTO_RESET_HOURS = 4       # memory auto-clears every 4 hours
FARM_MAX_FLOOD_WAIT = 900
FARM_PASS_TIMEOUT = 480         # one pass can't hang more than 8 min

# ---- runtime state ----
FARM_JOBS: dict = {}            # chat_id → job config
FARM = {
    "running": False, "paused": False, "started_at": None,
    "benched": False, "strikes": 0, "run_tasks": 0,
    "breath_count": 0, "breath_at": 4,
    "processed": set(), "ignore": set(),
    "memory_at": time.time(), "min_id": {}, "scanned": {}, "fails": {},
    "stats": {"kill": 0, "rob": 0, "floods": 0, "skipped": 0,
              "lowbal": 0, "checks": 0},
}
_FARM_CLIENT = None


# ------------------------------------------------------------------ helpers
def _farm_cfg() -> dict:
    d = load_store("farmer")
    if not isinstance(d, dict):
        d = {}
    out = dict(FARM_DEFAULTS)
    for k in FARM_DEFAULTS:
        if k in d:
            out[k] = d[k]
    return out


def _farm_save() -> None:
    d = _farm_cfg()
    d["ignore"] = sorted(FARM["ignore"])
    save_store("farmer", d)


def _farm_bot() -> str:
    return str(_farm_cfg().get("game_bot") or "im_bakabot").lstrip("@")


def _farm_log(text: str) -> None:
    path = os.path.join(DATA_DIR, "farm.log")
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%m-%d %H:%M:%S')}] {text}\n")
        if os.path.getsize(path) > 200_000:
            with open(path, "r", encoding="utf-8") as fh:
                tail = fh.readlines()[-200:]
            with open(path, "w", encoding="utf-8") as fh:
                fh.writelines(tail)
    except Exception:
        pass
    log.info("[farmer] %s", text)


def _farm_parse_coins(text):
    """'💰 Coins: $1,250' / 'Balance: 500' jaisi line se number nikaalo."""
    if not text:
        return None
    for pat in (r"coins:\s*\$?\s*([\d,]+)",
                r"balance:\s*\$?\s*([\d,]+)",
                r"\$\s*([\d,]+)\b"):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def _farm_protected(text) -> bool:
    if not text:
        return False
    t = text.lower()
    if "not protected" in t or "no protection" in t or "no active protection" in t:
        return False
    return "protected" in t


def _farm_random_tag() -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(chars) for _ in range(random.randint(2, 4)))


async def _farm_delay(base: float) -> None:
    if base <= 0:
        base = 1.0
    delay = base * random.uniform(0.7, 1.6)
    if random.random() < 0.12:
        delay += random.uniform(3, 9)
    await asyncio.sleep(delay)


async def _farm_nap(seconds: float) -> None:
    """Interruptible sleep — `.mstop`/`.mstopall` se turant jaag jata hai."""
    end = time.time() + seconds
    while time.time() < end and FARM["running"]:
        await asyncio.sleep(1)


async def _farm_notify(text: str) -> None:
    _farm_log(text)
    try:
        await _FARM_CLIENT.send_message("me", f"🔔 FARMER: {text}")
    except Exception:
        pass


async def _farm_wait_reply(chat, our_id, timeout=12.0, game_ent=None):
    """Game bot ka reply dhoondo (reply-to hamare message se match)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            async for m in _FARM_CLIENT.iter_messages(chat, limit=8,
                                                      from_user=game_ent):
                rt = getattr(m, "reply_to", None)
                rid = getattr(rt, "id", rt) if rt is not None else None
                if rid == our_id:
                    return m
        except Exception:
            pass
        await asyncio.sleep(1.2)
    return None


class _FarmDead(Exception):
    """Pass ab chalta nahi — kind: 'chat' (group gone) | 'session'."""
    def __init__(self, kind: str, msg: str = ""):
        super().__init__(msg)
        self.kind = kind


# ------------------------------------------------------------------ engine
async def _farm_pass(chat_id, cfg, game_ent):
    """One full scan of the chat history. Returns (tasks_done, oldest_id)."""
    client = _FARM_CLIENT
    stats = FARM["stats"]
    limit = cfg["limit"]
    done = 0
    oldest = None
    depth = int(_farm_cfg()["history_depth"])
    mid = FARM["min_id"].get(chat_id)

    async for msg in client.iter_messages(chat_id, limit=depth, min_id=mid):
        if not FARM["running"] or chat_id not in FARM_JOBS:
            break
        while FARM["paused"] and FARM["running"]:
            await asyncio.sleep(1)
        if not FARM["running"]:
            break
        if done >= limit:
            break
        oldest = msg.id if oldest is None else min(oldest, msg.id)

        user = msg.from_user
        if (user is None or getattr(user, "is_bot", False)
                or getattr(user, "is_self", False)):
            continue
        uid = user.id
        if uid in FARM["processed"] or uid in FARM["ignore"]:
            continue
        if random.random() < FARM_SKIP_CHANCE:
            continue

        name = (user.first_name or user.username or "user").replace("_", "\\_")
        mention = f"[{name}](tg://user?id={uid})"

        try:
            if cfg["mode"] == "smart":
                # 1) auto balance check
                await throttle("send", chat_id=chat_id)
                bal = await client.send_message(
                    chat_id, f"/bal@{_farm_bot()}", reply_to=msg.id)
                stats["checks"] += 1
                rep = await _farm_wait_reply(chat_id, bal.id, timeout=12,
                                             game_ent=game_ent)
                if rep is None:
                    rep = await _farm_wait_reply(chat_id, bal.id, timeout=8,
                                                 game_ent=game_ent)
                coins = _farm_parse_coins(
                    getattr(rep, "text", None) or getattr(rep, "message", None))
                if coins is None or coins <= 0 or coins < int(_farm_cfg()["min_rob"]):
                    FARM["processed"].add(uid)
                    stats["lowbal"] += 1
                    _farm_log(f"💸 {name} — balance {coins if coins is not None else '?'} → skip")
                    await _farm_delay(2)
                    continue
                # 2) rob the exact coins
                await _farm_delay(cfg["cmd_gap"])
                await throttle("send", chat_id=chat_id)
                rob = await client.send_message(
                    chat_id, f"/rob {coins} {mention} {_farm_random_tag()}",
                    reply_to=msg.id)
                stats["rob"] += 1
                _farm_log(f"💰 /rob {coins} → {name}")
                # 3) protection detect
                if rob is not None:
                    rrep = await _farm_wait_reply(chat_id, rob.id, timeout=10,
                                                  game_ent=game_ent)
                    if rrep is not None and _farm_protected(getattr(rrep, "text", None)):
                        stats["skipped"] += 1
                        if _farm_cfg()["skip_protected"]:
                            FARM["processed"].add(uid)
                        _farm_log(f"🛡 {name} protected — next user")
                        continue
            else:
                if cfg["mode"] in ("kill", "mixed"):
                    await throttle("send", chat_id=chat_id)
                    await client.send_message(
                        chat_id, f"/kill {mention} {_farm_random_tag()}",
                        reply_to=msg.id)
                    stats["kill"] += 1
                    if cfg["mode"] == "mixed":
                        await _farm_delay(cfg["cmd_gap"])
                if cfg["mode"] in ("rob", "mixed"):
                    await throttle("send", chat_id=chat_id)
                    await client.send_message(
                        chat_id, f"/rob {cfg['amount']} {mention} {_farm_random_tag()}",
                        reply_to=msg.id)
                    stats["rob"] += 1
                    _farm_log(f"💰 /rob {cfg['amount']} → {name}")

            FARM["processed"].add(uid)
            done += 1
            FARM["run_tasks"] += 1
            cfg["done"] += 1
            if len(FARM["processed"]) % 25 == 0:
                save_store("farmer_processed", list(FARM["processed"])[-5000:])
            if FARM["run_tasks"] >= FARM_QUOTA:
                _farm_log(f"😮‍ quota {FARM_QUOTA} hit — resting")
                break
            # human breather
            FARM["breath_count"] += 1
            if FARM["breath_count"] >= FARM["breath_at"]:
                rest = random.uniform(*FARM_BREAK_LEN)
                _farm_log(f"☕ breather {rest:.0f}s")
                await _farm_nap(rest)
                FARM["breath_count"] = 0
                FARM["breath_at"] = random.randint(*FARM_BREAK_EVERY)
            await _farm_delay(cfg["acc_gap"])
        except FloodWaitError as e:
            note_flood(e.seconds)
            FARM["strikes"] += 1
            stats["floods"] += 1
            wait = min(e.seconds + random.uniform(10, 30), FARM_MAX_FLOOD_WAIT)
            _farm_log(f"⏳ FloodWait strike #{FARM['strikes']} — waiting {wait:.0f}s")
            await _farm_nap(wait)
            if FARM["strikes"] >= FARM_FLOOD_STRIKES:
                FARM["benched"] = True
                await _farm_notify(
                    f"🪑 Benched — {FARM['strikes']} FloodWait strikes. `.mrevive` to resume.")
                break
        except asyncio.CancelledError:
            raise
        except Exception as e:
            low = str(e).lower()
            if "auth key" in low or "authkey" in low or "deactivated" in low:
                raise _FarmDead("session", str(e))
            if any(k in low for k in ("chat", "channel", "peer", "member", "username")):
                raise _FarmDead("chat", str(e))
            log.warning("[farmer] target %s failed: %s", name, e)

    save_store("farmer_processed", list(FARM["processed"])[-5000:])
    return done, oldest


def _farm_start_engine() -> bool:
    """Start the shared rotation engine (idempotent)."""
    t = stop_processes.get("farm-engine")
    if t is not None and not t.done():
        return False
    FARM["running"] = True
    stop_processes["farm-engine"] = asyncio.ensure_future(_farm_engine())
    return True


async def _farm_engine() -> None:
    client = _FARM_CLIENT
    FARM["running"] = True
    log.info("[farmer] engine warming up…")
    await _farm_nap(random.uniform(3, 6))
    try:
        game_ent = await client.get_entity(f"@{_farm_bot()}")
    except Exception as e:
        _farm_log(f"❌ game bot @{_farm_bot()} not found: {e}")
        await _farm_notify(f"❌ Game bot @{_farm_bot()} not found — check `.mbot`. Engine off.")
        FARM["running"] = False
        return
    try:
        while FARM["running"] and FARM_JOBS:
            # auto memory reset
            if time.time() - FARM["memory_at"] >= FARM_AUTO_RESET_HOURS * 3600:
                FARM["processed"].clear()
                FARM["memory_at"] = time.time()
                FARM["min_id"].clear()
                FARM["scanned"].clear()
                save_store("farmer_processed", [])
                _farm_log(f"🧠 auto memory reset ({FARM_AUTO_RESET_HOURS}h)")
            for chat_id in list(FARM_JOBS.keys()):
                if not FARM["running"] or chat_id not in FARM_JOBS:
                    break
                if FARM["benched"] or FARM["run_tasks"] >= FARM_QUOTA:
                    break
                cfg = FARM_JOBS[chat_id]
                try:
                    await asyncio.sleep(random.uniform(0.8, 2.0))
                    done, oldest = await asyncio.wait_for(
                        _farm_pass(chat_id, cfg, game_ent), timeout=FARM_PASS_TIMEOUT)
                    FARM["fails"].pop(chat_id, None)
                    if done == 0:
                        depth = int(_farm_cfg()["history_depth"])
                        if oldest is not None and \
                                FARM["scanned"].get(chat_id, 0) + depth <= FARM_MAX_OFFSET:
                            FARM["min_id"][chat_id] = oldest
                            FARM["scanned"][chat_id] = FARM["scanned"].get(chat_id, 0) + depth
                            _farm_log(f"🔭 {cfg['title']}: no new targets — deep scan up")
                except _FarmDead as d:
                    if d.kind == "session":
                        await _farm_notify(
                            "💀 Session problem — farmer stopped. Re-run the userbot to re-login.")
                        FARM["running"] = False
                        break
                    FARM_JOBS.pop(chat_id, None)
                    _farm_log(f"⚠️ job removed (chat unreachable): {d}")
                    await _farm_notify("⚠️ Farmer job removed — chat no longer reachable.")
                    break
                except asyncio.TimeoutError:
                    log.warning("[farmer] pass timeout in %s — skipped", cfg["title"])
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    FARM["fails"][chat_id] = FARM["fails"].get(chat_id, 0) + 1
                    log.error("[farmer] engine error in %s: %s", cfg["title"], e,
                              exc_info=True)
                    _farm_log(f"⚠️ engine error: {e}")
                    if FARM["fails"][chat_id] >= 5:
                        FARM_JOBS.pop(chat_id, None)
                        FARM["fails"].pop(chat_id, None)
                        await _farm_notify(
                            f"⚠️ Farmer job auto-removed after 5 errors: {e}")
            if not FARM["running"] or not FARM_JOBS:
                break
            if FARM["benched"] or FARM["run_tasks"] >= FARM_QUOTA:
                _farm_log("😴 idle — benched or quota hit (`.mrevive` to resume)")
                await _farm_nap(15)
                continue
            rest = random.uniform(*FARM_CYCLE_REST)
            _farm_log(f"😴 cycle rest {rest:.0f}s · groups {len(FARM_JOBS)}")
            await _farm_nap(rest)
    finally:
        FARM["running"] = False
        stop_processes.pop("farm-engine", None)
        save_store("farmer_processed", list(FARM["processed"])[-5000:])
        _farm_log("engine stopped")


# ------------------------------------------------------------------ handlers
def register_farmer(client: TelegramClient) -> None:
    global _FARM_CLIENT
    _FARM_CLIENT = client

    # restore persisted state
    try:
        FARM["ignore"] = {int(x) for x in _farm_cfg().get("ignore", [])
                          if str(x).isdigit()}
    except Exception:
        FARM["ignore"] = set()
    try:
        _pm = load_store("farmer_processed") or []
        FARM["processed"] = {int(x) for x in _pm}
    except Exception:
        FARM["processed"] = set()

    # ---- .mstart — start farmer in THIS group (multi-group safe) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mstart(?:\s+([\s\S]+))?$"))
    async def _mstart(event):
        args = (event.pattern_match.group(1) or "").split()
        if not args or args[0].lower() not in ("kill", "rob", "mixed", "smart"):
            return await event.edit(
                "✦ ━━━〔 ❌ FORMAT 〕━━━ ✦\n"
                "┃ `.mstart <mode> [amount] [limit] [acc_gap] [cmd_gap]`\n"
                "┃ modes: `kill` · `rob` · `mixed` · `smart`\n"
                "┃ e.g. `.mstart mixed 100 8 9 7`\n"
                "┃ e.g. `.mstart smart 6 10 8`\n"
                "┃ safe defaults: limit 6-10 · gaps 7-12\n"
                "┃ full menu: `.mhelp`\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)
        mode = args[0].lower()
        try:
            amount = int(args[1]) if len(args) > 1 and mode in ("rob", "mixed") else 100
        except ValueError:
            return await event.edit("❌ Amount must be a number. See `.mhelp`")
        try:
            limit = max(1, min(50, int(args[2]))) if len(args) > 2 else 6
        except (ValueError, IndexError):
            limit = 6
        d_ag, d_cg = FARM_SPEEDS.get(_farm_cfg()["mode"], (7.0, 6.0))
        try:
            acc_gap = max(FARM_MIN_GAP, float(args[3])) if len(args) > 3 else d_ag
        except (ValueError, IndexError):
            acc_gap = d_ag
        try:
            cmd_gap = max(FARM_MIN_GAP, float(args[4])) if len(args) > 4 else d_cg
        except (ValueError, IndexError):
            cmd_gap = d_cg
        chat_id = event.chat_id
        if chat_id in FARM_JOBS:
            return await event.edit(
                "⚠️ **Already farming this group.**\n"
                "`.mstop` first, or `.mspeed <preset>` to change pace.")
        title = getattr(event.chat, "title", None) or str(chat_id)
        FARM_JOBS[chat_id] = {
            "mode": mode, "amount": amount, "limit": limit,
            "acc_gap": acc_gap, "cmd_gap": cmd_gap,
            "title": title, "done": 0, "started": time.time(),
        }
        if FARM["started_at"] is None:
            FARM["started_at"] = time.time()
        _farm_start_engine()
        _farm_log(f"job added: {title} ({mode}) — groups {len(FARM_JOBS)}")
        await event.edit("🎮 **Farmer deployed** — warming up…", link_preview=False)
        for fr in ("⠋", "⠙", "⠹"):
            await event.edit(f"{fr} Farmer warming up…", link_preview=False)
            await asyncio.sleep(1)
        cfg = FARM_JOBS.get(chat_id)
        if cfg is None:
            return await event.edit("⚠️ Job already removed.")
        await event.edit(
            "✦ ━━━〔 🎮 FARMER DEPLOYED 〕━━━ ✦\n"
            f"┃ 📍 Group  : **{title}**\n"
            f"┃ ⚔️ Mode   : `{mode.upper()}`"
            + ("  _auto /bal → exact /rob_" if mode == "smart" else "") + "\n"
            f"┃ 🤖 Bot    : @{_farm_bot()}\n"
            f"┃ 🚦 Pace   : `{acc_gap:.1f}s / {cmd_gap:.1f}s` · limit `{limit}`\n"
            f"┃ 🔭 Depth  : `{_farm_cfg()['history_depth']}` msgs\n"
            f"┃ 🗂 Jobs   : `{len(FARM_JOBS)}` group(s)\n"
            f"┃ 🛡 Guard  : {safety_line()}\n"
            "┃\n"
            "┃ 📊 `.mstatus` · ⏸ `.mpause` · ⏹ `.mstop` ·  `.mhelp`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .msmart — smart rob in THIS group ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.msmart(?:\s+([\s\S]+))?$"))
    async def _msmart(event):
        args = (event.pattern_match.group(1) or "").split()
        try:
            limit = max(1, min(50, int(args[0]))) if len(args) > 0 else 6
        except ValueError:
            return await event.edit("❌ Numbers please. `.msmart 6 10 8`")
        d_ag, d_cg = (10.0, 8.0)
        try:
            acc_gap = max(FARM_MIN_GAP, float(args[1])) if len(args) > 1 else d_ag
        except ValueError:
            acc_gap = d_ag
        try:
            cmd_gap = max(FARM_MIN_GAP, float(args[2])) if len(args) > 2 else d_cg
        except ValueError:
            cmd_gap = d_cg
        chat_id = event.chat_id
        if chat_id in FARM_JOBS:
            return await event.edit("⚠️ Already running here. `.mstop` first.")
        title = getattr(event.chat, "title", None) or str(chat_id)
        FARM_JOBS[chat_id] = {
            "mode": "smart", "amount": "auto", "limit": limit,
            "acc_gap": acc_gap, "cmd_gap": cmd_gap,
            "title": title, "done": 0, "started": time.time(),
        }
        if FARM["started_at"] is None:
            FARM["started_at"] = time.time()
        _farm_start_engine()
        _farm_log(f"SMART job added: {title} — groups {len(FARM_JOBS)}")
        await event.edit(
            "✦ ━━━〔 🧠 SMART ROB ON 〕━━━ ✦\n"
            f"┃ 📍 Group  : **{title}**\n"
            f"┃ Flow     : `/bal@{_farm_bot()}` → coins → `/rob <exact>`\n"
            "┃ 🛡 Protection detect → next user\n"
            f"┃ Limit    : `{limit}` tasks · depth `{_farm_cfg()['history_depth']}`\n"
            f"┃ Skip     : `{'ON' if _farm_cfg()['skip_protected'] else 'OFF'}` (`.mskip`) · "
            f"min `${_farm_cfg()['min_rob']}` (`.mmin`)\n"
            f"┃ 🗂 Jobs   : `{len(FARM_JOBS)}` group(s)\n"
            "┃ 🎭 Starting in a few seconds…\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .mspeed — pace for THIS group ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mspeed(?:\s+(\S+))?$"))
    async def _mspeed(event):
        preset = (event.pattern_match.group(1) or "").lower()
        if preset == "normal":
            preset = "medium"
        cfg = FARM_JOBS.get(event.chat_id)
        if preset not in ("slow", "medium", "fast"):
            return await event.edit(
                "⚡ **Pace presets (this group)**\n"
                "┌ `.mspeed slow`    → 12s / 9s (safest)\n"
                "├ `.mspeed medium`  → 7s / 6s (default)\n"
                "└ `.mspeed fast`    → 5s / 4.5s\n\n"
                "Global for all groups: `.mmode <preset>`",
                link_preview=False)
        if cfg is None:
            return await event.edit("⚠️ Not farming this group yet — `.mstart` first.")
        ag, cg = FARM_SPEEDS[preset]
        cfg["acc_gap"], cfg["cmd_gap"] = ag, cg
        await event.edit(
            f"⚡ Pace → **{preset.upper()}** for this group (`{ag}s / {cg}s`). "
            "Applies from the next pass.", link_preview=False)

    # ---- .mmode — global pace (all groups) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mmode(?:\s+(\S+))?$"))
    async def _mmode(event):
        arg = (event.pattern_match.group(1) or "").lower()
        if arg == "normal":
            arg = "medium"
        if arg not in ("slow", "medium", "fast"):
            cur = _farm_cfg()["mode"]
            return await event.edit(
                f"🚦 Current global mode: **{cur.upper()}**\n"
                "Set with `.mmode slow|medium|fast`\n"
                "└ slow 12s/9s · medium 7s/6s · fast 5s/4.5s",
                link_preview=False)
        d = _farm_cfg()
        d["mode"] = arg
        save_store("farmer", d)
        ag, cg = FARM_SPEEDS[arg]
        for cfg in FARM_JOBS.values():
            cfg["acc_gap"], cfg["cmd_gap"] = ag, cg
        await event.edit(
            f"🚦 Global mode → **{arg.upper()}** (`{ag}s / {cg}s`) — "
            "applied to all active groups.", link_preview=False)

    # ---- .mstop / .mstopall ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mstop$"))
    async def _mstop(event):
        chat_id = event.chat_id
        if chat_id in FARM_JOBS:
            FARM_JOBS.pop(chat_id, None)
            save_store("farmer_processed", list(FARM["processed"])[-5000:])
            left = len(FARM_JOBS)
            _farm_log(f"stopped: {chat_id} — left {left}")
            await event.edit(
                f"✦ ━━━〔  FARMER STOPPED 〕━━━ ✦\n"
                f"┃ This group is done. Still active: `{left}` group(s).\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)
        else:
            await event.edit("⚠️ Not farming this group.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mstopall$"))
    async def _mstopall(event):
        n = len(FARM_JOBS)
        FARM_JOBS.clear()
        save_store("farmer_processed", list(FARM["processed"])[-5000:])
        _farm_log(f"stopped all — {n} group(s)")
        await event.edit(
            f"✦ ━━━〔 🛑 ALL FARMING STOPPED 〕━━━ ✦\n"
            f"┃ `{n}` group(s) shut down. Engine idling.\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)

    # ---- .mjobs ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mjobs$"))
    async def _mjobs(event):
        if not FARM_JOBS:
            return await event.edit(
                "🗂 **No active groups.**\nUse `.mstart <mode>` inside a group.")
        text = f"✦ ━━━〔  ACTIVE GROUPS — {len(FARM_JOBS)} 〕━━━ ✦\n"
        for i, (cid, cfg) in enumerate(FARM_JOBS.items(), 1):
            up = _fmt_uptime(time.time() - cfg["started"])
            text += (f"┃ **{i}. {cfg['title']}**\n"
                     f"┃ └ `{cfg['mode']}` · done `{cfg['done']}` · "
                     f"uptime `{up}` · gaps `{cfg['acc_gap']}s/{cfg['cmd_gap']}s`\n")
        text += f"┃\n┃ State: {'⏸ paused' if FARM['paused'] else '🟢 running'}"
        if FARM["benched"]:
            text += " · 🪑 benched"
        text += "\n✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦"
        await event.edit(text, link_preview=False)

    # ---- .mpause / .mresume ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mpause$"))
    async def _mpause(event):
        if not FARM["running"]:
            return await event.edit("⚠️ Farmer not running.")
        FARM["paused"] = True
        await event.edit("⏸ **Paused everywhere.** `.mresume` to continue.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mresume$"))
    async def _mresume(event):
        if not FARM["running"]:
            return await event.edit("⚠️ Farmer isn't running. `.mstart <mode>`.")
        FARM["paused"] = False
        await event.edit("▶️ **Back in action!**")

    # ---- .mreset / .mrevive ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mreset$"))
    async def _mreset(event):
        FARM["processed"].clear()
        FARM["min_id"].clear()
        FARM["scanned"].clear()
        save_store("farmer_processed", [])
        _farm_log("memory reset")
        await event.edit(
            "✦ ━━━〔 🔄 MEMORY CLEARED 〕━━━ ✦\n"
            "┃ Every user is a fresh target again.\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mrevive$"))
    async def _mrevive(event):
        FARM["benched"] = False
        FARM["strikes"] = 0
        FARM["run_tasks"] = 0
        FARM["breath_count"] = 0
        FARM["breath_at"] = random.randint(*FARM_BREAK_EVERY)
        _farm_log("revived — counters reset")
        await event.edit(
            "✦ ━━━〔 💪 REVIVED 〕━━━ ✦\n"
            "┃ Bench cleared · flood strikes reset · quota reset.\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)

    # ---- .mstatus ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mstatus$"))
    async def _mstatus(event):
        s = FARM["stats"]
        cfg = _farm_cfg()
        if FARM["running"]:
            up = _fmt_uptime(time.time() - (FARM["started_at"] or time.time()))
            state = "🟢 Running" + (" (paused ⏸)" if FARM["paused"] else "")
        else:
            up, state = "—", "🔴 Idle"
        text = (
            "✦ ━━━〔 📊 FARMER STATUS 〕━━━ ✦\n"
            f"┃ State   : {state}{' · 🪑 benched' if FARM['benched'] else ''}\n"
            f"┃ Uptime  : `{up}`\n"
            f"┃ 🤖 Bot  : @{_farm_bot()} · 🚦 mode `{cfg['mode'].upper()}`\n"
            f"┃ 🗂 Jobs  : `{len(FARM_JOBS)}` · Quota: `{FARM['run_tasks']}/{FARM_QUOTA}`\n"
            f"┃ 🧠 Mem   : `{len(FARM['processed'])}` processed · "
            f"auto-reset har {FARM_AUTO_RESET_HOURS}h\n"
            f"┃\n"
            f"┃ ⚔️ Kills `{s['kill']}` · 💰 Robs `{s['rob']}` · "
            f"⏳ Floods `{s['floods']}`\n"
            f"┃ 🧠 Checks `{s['checks']}` · 🛡 Skipped `{s['skipped']}` · "
            f"💸 LowBal `{s['lowbal']}`\n"
            f"┃ 🎛 Skip-protected `{'ON' if cfg['skip_protected'] else 'OFF'}` · "
            f"Min rob `${cfg['min_rob']}` · Depth `{cfg['history_depth']}`\n"
            f"┃ 🚫 Ignored: `{len(FARM['ignore'])}` (`.mignored`)\n"
        )
        if FARM_JOBS:
            text += "┃\n**Active groups:**\n"
            for cfg2 in FARM_JOBS.values():
                text += f"┃ • {cfg2['title']} → `{cfg2['done']}` tasks ({cfg2['mode']})\n"
        text += "\n✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦"
        await event.edit(text, link_preview=False)

    # ---- .mlog ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mlog$"))
    async def _mlog(event):
        path = os.path.join(DATA_DIR, "farm.log")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()[-18:]
            body = "".join(lines).strip() or "(farm log abhi khali hai)"
        except Exception:
            body = "(farm log file not found)"
        await event.edit(
            "✦ ━━━〔 📜 FARM LOG 〕━━━ ✦\n"
            f"```{body[-3500:]}```\n✦ ━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- ignore list ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mignore(?:\s+(\d+))?$"))
    async def _mignore(event):
        uid = event.pattern_match.group(1)
        if not uid:
            r = await event.get_reply_message()
            uid = str(getattr(r, "sender_id", None) or "")
        if not uid or not str(uid).isdigit():
            return await event.edit(
                "🚫 Reply to a user's message with `.mignore`, "
                "or use `.mignore <user_id>`.")
        FARM["ignore"].add(int(uid))
        _farm_save()
        _farm_log(f"ignored {uid} (total {len(FARM['ignore'])})")
        await event.edit(
            f"✦ ━━━〔 🚫 IGNORED 〕━━━ ✦\n"
            f"┃ User `{uid}` kabhi target nahi hoga.\n"
            f"┃ Total ignored: `{len(FARM['ignore'])}` (`.mignored`)\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.munignore\s+(\d+)$"))
    async def _munignore(event):
        uid = int(event.pattern_match.group(1))
        if uid in FARM["ignore"]:
            FARM["ignore"].discard(uid)
            _farm_save()
            await event.edit(f"✅ User `{uid}` removed from ignore-list "
                             f"(`{len(FARM['ignore'])}` left).")
        else:
            await event.edit(f"ℹ️ User `{uid}` was not on the ignore-list.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mignored$"))
    async def _mignored(event):
        if not FARM["ignore"]:
            return await event.edit(
                "🚫 Ignore-list is empty. Add with `.mignore` (reply or id).")
        body = "\n".join(f"┃ • `{i}`" for i in sorted(FARM["ignore"])[:50])
        await event.edit(
            f"✦ ━━━〔 🚫 IGNORED USERS — {len(FARM['ignore'])} 〕━━━ ✦\n"
            f"{body}\n┃ Remove: `.munignore <id>`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)

    # ---- .mskip / .mmin / .mdepth / .mbot ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mskip(?:\s+(\S+))?$"))
    async def _mskip(event):
        arg = (event.pattern_match.group(1) or "").lower()
        if arg not in ("on", "off"):
            state = "ON 🛡" if _farm_cfg()["skip_protected"] else "OFF"
            return await event.edit(
                f"🛡 Protection-skip is **{state}**.\n"
                "`.mskip on`  → protected user chhodo, agla pakdo\n"
                "`.mskip off` → protection check mat karo")
        d = _farm_cfg()
        d["skip_protected"] = (arg == "on")
        save_store("farmer", d)
        state = "ON 🛡" if d["skip_protected"] else "OFF"
        await event.edit(f"🛡 Protection-skip turned **{state}**.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mmin(?:\s+(\d+))?$"))
    async def _mmin(event):
        g = event.pattern_match.group(1)
        if g is None:
            return await event.edit(
                f"💸 Current minimum rob: `${_farm_cfg()['min_rob']}`.\n"
                "Set with `.mmin <amount>`")
        d = _farm_cfg()
        d["min_rob"] = max(0, int(g))
        save_store("farmer", d)
        await event.edit(f"💸 Minimum rob → `${d['min_rob']}` — "
                         "isse kam wale skip honge.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mdepth(?:\s+(\d+))?$"))
    async def _mdepth(event):
        g = event.pattern_match.group(1)
        if g is None:
            return await event.edit(
                f"🔭 Current scan depth: `{_farm_cfg()['history_depth']}` msgs.\n"
                "Set with `.mdepth <100-1000>` — older members bhi cover honge.")
        d = _farm_cfg()
        d["history_depth"] = min(1000, max(100, int(g)))
        save_store("farmer", d)
        FARM["min_id"].clear()
        FARM["scanned"].clear()
        await event.edit(
            f"🔭 Scan depth → `{d['history_depth']}` msgs. "
            "Dry pass pe window khud older messages ki taraf badhti hai.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mbot(?:\s+([A-Za-z0-9_]{3,32}))?$"))
    async def _mbot(event):
        g = event.pattern_match.group(1)
        if g is None:
            return await event.edit(
                f"🤖 Current game bot: **@{_farm_bot()}**\n"
                "Change with `.mbot <username>` (no @ needed).")
        d = _farm_cfg()
        d["game_bot"] = g.lstrip("@")
        save_store("farmer", d)
        _farm_log(f"game bot → @{g.lstrip('@')}")
        await event.edit(
            f"🤖 Game bot → **@{g.lstrip('@')}**.\n"
            "Next `.mstart` will use it (running engine keeps the old one "
            "until `.mstopall` + start).")

    # ---- .mid / .ping ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mid$"))
    async def _mid(event):
        me = await client.get_me()
        uname = f"@{me.username}" if getattr(me, "username", None) else "—"
        await event.edit(
            "✦ ━━━〔 🪪 IDENTITY 〕━━━ ✦\n"
            f"┃ 👤 {me.first_name} ({uname})\n"
            f"┃ 🆔 ID: `{me.id}`\n"
            "┃ Farming runs as THIS account.\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
    async def _mping(event):
        state = "🟢 running" if FARM["running"] else "🔴 idle"
        await event.edit(
            f"🏓 **Pong!** Farmer alive ✅\n"
            f"┃ Engine {state} · `{len(FARM_JOBS)}` group(s) active.",
            link_preview=False)

    # ---- .mhelp ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.mhelp$"))
    async def _mhelp(event):
        await event.edit(
            "✦ ━━━━━〔 🎮 ISOLATION FARMER 〕━━━━━ ✦\n"
            "┃ _Baka engine · SUKUNA-X edition_\n"
            "┃\n"
            "**▶️ START** (har group me alag se)\n"
            "┌ `.mstart <mode> [amt] [limit] [gap] [gap]`\n"
            "├ modes: `kill` · `rob` · `mixed` · `smart`\n"
            "├ e.g. `.mstart mixed 100 8 9 7`\n"
            "└ `.msmart [limit] [acc_gap] [cmd_gap]`\n"
            "   _auto /bal → exact /rob → protection skip_\n"
            "┃\n"
            "**🎛 TUNING**\n"
            "┌ `.mspeed slow|medium|fast` → this group\n"
            "├ `.mmode slow|medium|fast` → all groups\n"
            "├ `.mskip on|off` → protected users skip karo ya nahi\n"
            "├ `.mmin <n>` → min coins to rob (below = skip)\n"
            "├ `.mdepth <100-1000>` → older members bhi scan\n"
            "└ `.mbot <username>` → game bot (default im_bakabot)\n"
            "┃\n"
            "**🚫 IGNORE LIST**\n"
            "┌ `.mignore` (reply) / `.mignore <id>` → hamesha skip\n"
            "├ `.munignore <id>` → list se hatao\n"
            "└ `.mignored` → list dekho\n"
            "┃\n"
            "**⚙️ CONTROLS**\n"
            "┌ `.mjobs` → active groups · `.mpause` · `.mresume`\n"
            "├ `.mstop` → sirf ye group · `.mstopall` → sab\n"
            "├ `.mreset` → memory clear · `.mrevive` → un-bench + quota reset\n"
            "├ `.mstatus` → dashboard · `.mlog` → recent log\n"
            "└ `.mid` → identity · `.ping` → alive check\n"
            "┃\n"
            f"**🛡 SAFE ENGINE (hamesha ON)**\n"
            f"┌ global anti-ban engine + 48h warm-up\n"
            f"├ max {FARM_QUOTA} tasks/run · breather har {FARM_BREAK_EVERY[0]}-{FARM_BREAK_EVERY[1]} tasks\n"
            f"├ {FARM_FLOOD_STRIKES} FloodWaits → auto-bench (`.mrevive`)\n"
            f"└ memory auto-reset har {FARM_AUTO_RESET_HOURS}h\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    log.info("Farmer registered: Isolation engine (24 .m commands)")


# ------------------------------------------------------------------ metadata
COMMANDS_FARMER = {
    "description": "Isolation Farmer",
    "commands": [
        (".mstart <mode> [amt] [limit] [gap] [gap]",
         "start farming THIS group (kill/rob/mixed/smart)"),
        (".msmart [limit] [acc_gap] [cmd_gap]",
         "smart mode: auto /bal → exact /rob → protection skip"),
        (".mspeed <slow|medium|fast>", "pace for THIS group"),
        (".mmode <slow|medium|fast>", "global pace (all groups)"),
        (".mstop", "stop in THIS group only"),
        (".mstopall", "stop farming everywhere"),
        (".mjobs", "list active groups"),
        (".mpause", "pause everywhere"),
        (".mresume", "resume farming"),
        (".mreset", "clear processed-user memory"),
        (".mrevive", "un-bench + reset flood strikes & quota"),
        (".mstatus", "full farmer dashboard"),
        (".mlog", "recent farmer log"),
        (".mignore", "never target a user (reply or .mignore <id>)"),
        (".munignore <id>", "remove from ignore-list"),
        (".mignored", "show ignore-list"),
        (".mskip <on|off>", "skip protected users or not"),
        (".mmin <n>", "min coins worth robbing"),
        (".mdepth <n>", "scan depth 100-1000 (older members too)"),
        (".mbot <username>", "set the game bot (default im_bakabot)"),
        (".mid", "show logged-in identity"),
        (".ping", "farmer alive check"),
        (".mhelp", "full farmer menu"),
    ],
}

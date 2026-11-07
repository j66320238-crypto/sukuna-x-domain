# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: BOTCONTROLLER — 👑 v7.5 MULTI-BOT ARMY COMMAND CENTER
############################################################################
"""
BotController — control your whole BOT ARMY from your MAIN account (or SUDO users).

  ⚙️ SETUP
  • .addbottoken <token>     — register a bot (1st/2nd/3rd… slot) + verify token
  • .addnewbotauto [n]       — create a NEW bot via BotFather automatically
                               (name: worker, auto username, retries, auto-register)
  • .delbottoken / .delbot <n> — delete the nth bot (slots auto-shift)
  • .listbots / .botlist     — all bots + ❄️ frozen status
  • .monitorb                — LIVE status (who is online + everyone's names)
  • .refreshb                — reconnect all bots (clear frozen attempt)

  📥 GROUP
  • .addallb [slots]         — add all bots to the current group
  • .addall 1-3              — only the 1st-3rd bots (single: .addall 2)
  • .removeallb              — remove all bots from the group

  🚀 ATTACK (NO lower limit on the interval — 0.1 / 0.5 all fine)
  • .spamb <n> <sec> <text>  — all bots text spam
  • .spamb1-2 <n> <sec> <txt>— only specific bots
  • .sspam <n> <sec>         — USER sticker spam (reply)
  • .sspamb <n> <sec>        — BOTS sticker spam (reply)
  • .raid [n] [gap] [text]   — user raid (saved slots rotate)
  • .raidb [slots] <n> [gap] [txt] — BOT raid (.raidb 10 .1 = 10x, 0.1s
                               gap · reply + tag BOTH + saved slots rotate)

  🎭 PROFILE
  • .cloneb [slots]          — bots clone the victim (name+bio via BotFather,
                               pfp via MTProto — bot-proof, error-free;
                               if the target has NO dp the bot's dp is cleared)
  • .clonebi [slots]         — 🧨 FORCE clone: ignores the BotFather hourly
                               cap, sleeps through every FloodWait, retries
                               each step until the name/bio/pfp REALLY lands
  • .revertb / .uncloneb [slot] — bots back to ORIGINAL (pre-clone) state
  • .loadprofileb [slots] <name> — put a .saveprofile profile on the bots
  • .botsay [slots] <text>   — make the bots say something

  🎬 ANIMATION DELEGATION
  • .<anim>b [sec]           — any animation on ALL bots (.roseb .hackb)
  • .<anim>b1-2 [sec]        — specific bots (.roseb1-2)

  ⌨️🤖 TYPE-X BOTS — typing effect on the BOT ARMY (v7.7)
  • .typeb on / off          — every bot message (.spamb .raidb .botsay
                               .rrb replies) gets the live typewriter effect
  • .typeb1-2 on             — only specific bots get the effect
  • .typeb <style>           — 12 styles (classic wave glitch scramble matrix
                               pulse fire hearts zoom eraser reverse random)
  • .typeb speed 0.2         — frame speed (0.05–1.0s)
  • .typeb styles / status   — gallery / mode card
  • .typeb sync              — copy style+speed from .type (user TYPE-X)
  • .typeb <text>            — one-shot: bots send <text> WITH the effect

  📜 RAID MESSAGES (slots 1st, 2nd, 3rd…)
  • .saverm <text>           — save a slot (reply works too; 1st → 2nd → 3rd…)
  • .listrm                  — list all slots
  • .delrm <n>               — delete a slot (rest AUTO-SHIFT: 4th → 3rd)
  • .delallrm                — delete all slots at once

  📡 RR / RRT — REPLY-RAID
  • .rr / .rrt               — reply to the target: EVERY message they send
                               gets a saved slot as reply (TOGGLE); the
                               replied message is auto-saved to the slots
  • .rrb [slots] / .rrtb     — the BOTS do the same (.rrb2-3 custom)
  • .stoprrt / .stoprr       — stop all RRT/RR (user + bots)

  🪞 COPYCAT / MIRROR (.ct / .ctb)
  • .ct (reply)              — MIRROR toggle: re-send everything the target
                               sends, same-to-same (sticker → sticker)
  • .ct copy (reply)         — one-shot: re-send the replied message once
  • .ct on/off               — self-copycat mode (mirror your own sends)
  • .ctb (reply) [slots]     — the BOTS mirror the target
  • .ctb on/off / .ctb2-3 on — bots copycat mode (custom slots)

  ⏹ STOP SYSTEM (a stop for everything)
  • .stop                    — stop all tasks (builtin)
  • .stopall                 — tasks + RRT + CopyCat all off
  • .stopb                   — stop all BOT tasks
  • .spamstop / .sspamstop   — text spam / sticker spam stop
  • .stopraid / .raidstop    — raid tasks + RRT off
  • .raidbstop / .stopraidb  — stop only the BOT raid
  • .animstop                — animations stop
  • .stopct / .ctstop        — copycat + all mirrors off

  🛠 UX
  • .autodelete on/off       — output auto-delete system (DEFAULT ON:
                               a new command deletes the previous output)
  • .autodeletem <sec>       — v7.5 TIMER: every output (help card /
                               spam-done / raid-done info) self-deletes in <sec>
  • .addsudo (reply/id)      — add a SUDO user → they can also control the bots
  • .delsudo / .listsudo     — remove / list sudos (owner only)
  • .bccheck                 — 🩺 self-diagnosis: versions/API creds/dirs/
                               bots/RRT/CopyCat/tasks — ALL in one card
  • .bchelp / .bch           — this help card

  v7.4.1: when a command crashes you get a VISIBLE ❌ error reply in chat
  (flood_safe used to swallow it silently — that's why "nothing happened").

Frozen bot = dead/revoked/deactivated token — shown as ❄️ in every list.
Bots cannot use account.updateProfile (official MTProto limit) — that is
why name/bio go through BotFather automation and pfp through MTProto.
"""

# ─── stores & dirs ──────────────────────────────────────────────────────
BC_STORE = "botcontroller"          # data/botcontroller.json  (bots + slots)
RM_STORE = "raid_messages"          # data/raid_messages.json (.saverm slots)
SUDO_STORE = "sudo"                 # data/sudo.json            (sudo users)
BC_DIR = os.path.join(DATA_DIR, "botcontroller")
BOT_SESSIONS_DIR = os.path.join(BC_DIR, "sessions")
BOT_PFP_DIR = os.path.join(BC_DIR, "pfps")
PROFILES_ROOT = os.path.join(DATA_DIR, "profiles")   # profile.py ke saves

for _d in (BC_DIR, BOT_SESSIONS_DIR, BOT_PFP_DIR, PROFILES_ROOT):
    try:
        os.makedirs(_d, exist_ok=True)
    except Exception:
        pass

# runtime: {slot(int 1-based): TelegramClient}
BOT_CLIENTS = {}
_bc_lock = None  # created in register (asyncio.Lock)

# ─── module-level telethon imports (ImportError-proof) ──────────────────
# v7.4 FIX: pehle ye import function ke ANDAR tha aur GALAT class name
# (AddChatMembersRequest — telethon me aisi class HAI NAHI) use karta tha
# → us se `.addallb` par "❌ ImportError" aata tha. Ab sahi class + top-level.
try:
    from telethon.tl.functions.messages import AddChatUserRequest
except ImportError:                                   # bahut purana telethon
    AddChatUserRequest = None


# ─── small helpers ───────────────────────────────────────────────────────

try:
    from telethon import utils as _tlutils   # get_peer_id (edit/send hook)
except ImportError:                          # very old telethon
    _tlutils = None


def _hook_extract_key(args):
    """edit_message(...) args se (chat_id, msg_id) — best-effort.

    Supports: (Message, text) · (entity, Message) · (entity, int_id, ...)
    """
    try:
        a0 = args[0] if args else None
        a1 = args[1] if len(args) > 1 else None
        if a0 is not None and hasattr(a0, "id") and hasattr(a0, "chat_id"):
            return (int(a0.chat_id), int(a0.id))
        if a1 is not None and hasattr(a1, "id") and hasattr(a1, "chat_id"):
            return (int(a1.chat_id), int(a1.id))
        if a1 is None or isinstance(a1, str) or isinstance(a0, (int, bool)):
            return None
        if _tlutils is None:
            return None
        return (int(_tlutils.get_peer_id(a0)), int(a1))
    except Exception:
        return None


_ORD_SUFFIX = {1: "st", 2: "nd", 3: "rd"}


def _ord(n: int) -> str:
    """1 → '1st', 2 → '2nd', 3 → '3rd', 4 → '4th', 11 → '11th', 21 → '21st'"""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "?"
    if 10 <= (n % 100) <= 20:
        return f"{n}th"
    return f"{n}{_ORD_SUFFIX.get(n % 10, 'th')}"


def _bc_load() -> dict:
    data = load_store(BC_STORE)
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("bots"), list):
        data["bots"] = []
    return data


def _bc_save(data: dict) -> bool:
    return save_store(BC_STORE, data)


def _rm_load() -> list:
    data = load_store(RM_STORE)
    msgs = data.get("messages") if isinstance(data, dict) else None
    if not isinstance(msgs, list):
        return []
    return [str(m) for m in msgs if str(m).strip()]


def _rm_save(msgs: list) -> bool:
    return save_store(RM_STORE, {"messages": [str(m) for m in msgs]})


# ─── SUDO users — bots ka control inko bhi milta hai ──────────────────────

_SUDO_CACHE = None   # [int, …] — None = store se dobara padho


def _sudo_ids() -> set:
    global _SUDO_CACHE
    if _SUDO_CACHE is None:
        data = load_store(SUDO_STORE)
        users = data.get("users") if isinstance(data, dict) else None
        ids = set()
        for u in (users or []):
            try:
                ids.add(int(u))
            except (TypeError, ValueError):
                pass
        _SUDO_CACHE = ids
    return _SUDO_CACHE


def _sudo_save(ids) -> bool:
    global _SUDO_CACHE
    ids = sorted({int(u) for u in ids if u})
    _SUDO_CACHE = set(ids)
    return save_store(SUDO_STORE, {"users": ids})


# ─── AUTODELETE — pichla command output khud delete (default ON) ─────────
# + v7.5 AUTODELETE TIMER (.autodeletem <sec>) — har command ka OUTPUT
#   (help cards / "spam done" / "raid done" info) N second baad KHUD udega.

_AD = {"on": True, "timer": 0}   # runtime flags (register me store se sync)
_AD_LAST = {}          # {chat_id: last_output_msg_id}
_CMD_IDS = {}          # {(chat_id, msg_id): ts} — recently issued commands
_CMD_IDS_MAX = 2000
_AD_TIMER_TASKS = {}   # {(chat_id, msg_id): asyncio.Task} — pending deletions


def _ad_load():
    try:
        data = _bc_load()
        _AD["on"] = bool(data.get("autodelete", True))
        _AD["timer"] = int(data.get("autodelete_timer", 0) or 0)
    except Exception:
        _AD["on"] = True
        _AD["timer"] = 0


def _ad_set(on: bool) -> bool:
    _AD["on"] = bool(on)
    try:
        data = _bc_load()
        data["autodelete"] = bool(on)
        return _bc_save(data)
    except Exception:
        return False


def _ad_timer() -> int:
    """Current timed auto-delete seconds (0 = OFF)."""
    try:
        t = int(_AD.get("timer", 0) or 0)
    except (TypeError, ValueError):
        t = 0
    return t if t > 0 else 0


def _ad_timer_set(sec) -> int:
    """.autodeletem — timer save + persist. Returns applied seconds."""
    try:
        sec = int(sec)
    except (TypeError, ValueError):
        sec = 0
    sec = max(0, min(sec, 86400))
    _AD["timer"] = sec
    try:
        data = _bc_load()
        data["autodelete_timer"] = sec
        _bc_save(data)
    except Exception:
        pass
    if sec <= 0:
        for t in list(_AD_TIMER_TASKS.values()):
            try:
                t.cancel()
            except Exception:
                pass
        _AD_TIMER_TASKS.clear()
    return sec


def _cmd_track(chat_id, msg_id):
    """Command message id ko track karo (output-timer delete ke liye)."""
    try:
        _CMD_IDS[(int(chat_id), int(msg_id))] = time.time()
        if len(_CMD_IDS) > _CMD_IDS_MAX:
            cutoff = time.time() - 1200
            for k in [k for k, ts in _CMD_IDS.items() if ts < cutoff]:
                _CMD_IDS.pop(k, None)
            while len(_CMD_IDS) > _CMD_IDS_MAX:
                _CMD_IDS.pop(next(iter(_CMD_IDS)))
    except Exception:
        pass


def _ad_schedule_delete(client, chat_id, msg_id, delay):
    """Ek output message ko `delay` sec baad KHUD delete karo (timer system).

    Same message dobara edit/output ho toh timer RESET hota hai (purana task
    cancel, naya schedule) — isliye animations/loops ka final output hi
    timer ke baad jaata hai, beech me nahi.
    """
    if delay <= 0:
        return
    key = (int(chat_id), int(msg_id))
    old = _AD_TIMER_TASKS.get(key)
    if old is not None and not old.done():
        try:
            old.cancel()
        except Exception:
            pass
    if len(_AD_TIMER_TASKS) > 400:
        try:
            _AD_TIMER_TASKS.pop(next(iter(_AD_TIMER_TASKS)))
        except Exception:
            pass

    async def _t():
        try:
            await asyncio.sleep(delay)
            try:
                await client.delete_messages(chat_id, msg_id)
            except Exception:
                pass  # already gone / rights nahi
        except asyncio.CancelledError:
            pass
        finally:
            _AD_TIMER_TASKS.pop(key, None)

    try:
        _AD_TIMER_TASKS[key] = asyncio.create_task(_t())
    except Exception:
        pass


def _ad_track(chat_id, msg_id):
    """Ek output message ko track karo (sudo-reply outputs ke liye)."""
    try:
        _AD_LAST[chat_id] = msg_id
    except Exception:
        pass


async def _ad_delete_previous(client, chat_id, protect_id=None):
    """Chat ke pichle output ko khud delete karo (naya command aane par).

    v7.4.2 RACE FIX: protect_id = current command ka message id. Agar
    pichla tracked output HI current command hai (handler ne abhi-abhi
    edit kiya hai), toh use delete NAHI karna — warna command ka apna
    output usi ke dispatch me ud jaata tha (isliye botcommands ke cards
    user ko dikh hi nahi rahe the!). Sirf sach me PURANA output jayega.
    """
    if not _AD.get("on"):
        return
    mid = _AD_LAST.get(chat_id)
    if mid is None:
        return
    if protect_id is not None and mid == protect_id:
        return              # ye CURRENT command ka output hai — rehne do
    _AD_LAST.pop(chat_id, None)
    try:
        await client.delete_messages(chat_id, mid)
    except Exception:
        pass  # 48h+ purana / delete rights nahi — chhodo


# ─── frozen (dead-token) detection ───────────────────────────────────────

FREEZE_MARKERS = (
    "authkey", "auth_key", "deactivated", "deleted", "accesstoken",
    "access_token", "bot_token", "token", "unauthorized", "session revoked",
    "revoked", "key is unregistered", "keyid",
)


def _is_freeze_err(exc) -> bool:
    """True if this error means the bot token is dead/revoked (= frozen)."""
    try:
        s = (type(exc).__name__ + " " + str(exc)).lower()
        return any(m in s for m in FREEZE_MARKERS)
    except Exception:
        return False


# ─── API credentials (bot sessions need same api_id/hash) ────────────────

def _api_creds(main_client):
    """Resolve the api_id/api_hash the main userbot is running with."""
    from core import state as _state
    api_id = getattr(_state, "ACTIVE_API_ID", 0) or 0
    api_hash = getattr(_state, "ACTIVE_API_HASH", "") or ""
    if not api_id or not api_hash:
        api_id, api_hash = API_ID, API_HASH
    if not api_id or not api_hash:
        api_id = getattr(main_client, "api_id", None) or getattr(main_client, "_api_id", None) or 0
        api_hash = (getattr(main_client, "api_hash", None)
                    or getattr(main_client, "_api_hash", None) or "")
    return api_id, api_hash


# ─── slot parsing ────────────────────────────────────────────────────────

def _parse_slots(arg, total: int) -> list:
    """None → all slots · '1-3' range · '2' single · '1,3' list → sorted [int]."""
    if total <= 0:
        return []
    if arg is None or not str(arg).strip():
        return list(range(1, total + 1))
    slots = set()
    for part in str(arg).split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)(?:-(\d+))?$", part)
        if not m:
            continue
        a = int(m.group(1))
        b = int(m.group(2) or m.group(1))
        a, b = min(a, b), max(a, b)
        for s in range(a, b + 1):
            if 1 <= s <= total:
                slots.add(s)
    return sorted(slots)


def _parse_count_interval(arg, need_text=False):
    """'<count> [interval] [text]' → (count, interval, text, error).
    Interval par KOI lower limit nahi — 0 / 0.1 / 0.5 sab allowed."""
    parts = (arg or "").split(maxsplit=2)
    if not parts:
        return None, None, None, "empty"
    try:
        count = int(parts[0])
    except ValueError:
        return None, None, None, "count"
    if count <= 0:
        return None, None, None, "positive"
    interval = 0.5
    text = None
    if len(parts) >= 3:
        try:
            interval = float(parts[1])
            text = parts[2]
        except ValueError:
            interval = 0.5
            text = " ".join(parts[1:])
    elif len(parts) == 2:
        if need_text:
            text = parts[1]
        else:
            try:
                interval = float(parts[1])
            except ValueError:
                interval = 0.5
    if need_text and not text:
        return count, interval, None, "text"
    if interval < 0:
        interval = 0.0
    return count, interval, text, None


# ─── task killer (stop-family ka engine) ─────────────────────────────────

def _kill_tasks(client, pred) -> int:
    """stop_processes me se pred(key) True wale tasks cancel karo. Returns killed."""
    killed = 0
    try:
        items = list((client.stop_processes or {}).items())
    except Exception:
        return 0
    for key, task in items:
        try:
            if not pred(key):
                continue
            if task is not None and not task.done():
                task.cancel()
                killed += 1
            client.stop_processes.pop(key, None)
        except Exception:
            pass
    return killed


# ─── bot client manager ──────────────────────────────────────────────────

_BOT_SLOT_LOCKS = {}    # v7.6: per-slot connect locks — no 'database is locked'


def _bot_slot_lock(slot: int) -> asyncio.Lock:
    lk = _BOT_SLOT_LOCKS.get(slot)
    if lk is None:
        lk = asyncio.Lock()
        _BOT_SLOT_LOCKS[slot] = lk
    return lk


async def _bot_client(main_client, slot: int, data: dict = None):
    """Return a CONNECTED bot client for 1-based slot, or None if it can't connect.

    On dead-token errors the bot record gets frozen=True (❄️ in lists).
    On success, frozen flag is cleared automatically.
    v7.6: per-slot lock — two tasks connecting the same bot at the same time
    used to corrupt the sqlite session ('database is locked').
    """
    global BOT_CLIENTS
    async with _bot_slot_lock(slot):
        return await _bot_client_locked(main_client, slot, data)


async def _bot_client_locked(main_client, slot: int, data: dict = None):
    global BOT_CLIENTS
    if data is None:
        data = _bc_load()
    bots = data.get("bots") or []
    if slot < 1 or slot > len(bots):
        return None
    rec = bots[slot - 1]

    bc = BOT_CLIENTS.get(slot)
    if bc is not None and bc.is_connected():
        return bc
    if bc is not None:
        try:
            await bc.disconnect()
        except Exception:
            pass
        BOT_CLIENTS.pop(slot, None)

    api_id, api_hash = _api_creds(main_client)
    if not api_id or not api_hash:
        log.error("[botcontroller] API_ID/API_HASH unavailable — bots can't start")
        return None
    try:
        os.makedirs(BOT_SESSIONS_DIR, exist_ok=True)
    except Exception:
        pass
    session_path = os.path.join(BOT_SESSIONS_DIR, f"bot_{rec.get('id', slot)}")
    bc = TelegramClient(session_path, api_id, api_hash)
    try:
        await bc.start(bot_token=rec.get("token", ""))
    except Exception as e:
        if _is_freeze_err(e):
            rec["frozen"] = True
            rec["frozen_error"] = f"{type(e).__name__}: {e}"[:180]
            _bc_save(data)
            log.warning("[botcontroller] bot slot %s FROZEN: %s", slot, rec["frozen_error"])
        else:
            log.warning("[botcontroller] bot slot %s connect failed: %s", slot, e)
        try:
            await bc.disconnect()
        except Exception:
            pass
        return None

    # v7.7.1 — validate the fresh connection with a PING (capped). A socket
    # that connected but is wedged (no RPC answers) used to hang every
    # handler that tried to send through it.
    try:
        await asyncio.wait_for(bc.get_me(), timeout=30)
    except Exception as e:
        log.warning("[botcontroller] bot slot %s ping failed (%s) — "
                    "treating as frozen this round", slot,
                    type(e).__name__)
        try:
            await bc.disconnect()
        except Exception:
            pass
        return None

    if rec.get("frozen"):
        rec["frozen"] = False
        rec.pop("frozen_error", None)
        _bc_save(data)
    # v7.6: kick the update stream alive immediately — without this the
    # bot's first group updates can lag by 20s+, breaking the seen-cache
    # (reply-target translation) for the first command after connect.
    try:
        from telethon.tl.functions.updates import GetStateRequest
        await bc(GetStateRequest())
    except Exception:
        pass
    BOT_CLIENTS[slot] = bc
    # v7.7 TYPE-X B — typing effect hook (.typeb on/off)
    _txb_patch_bot(main_client, bc, slot)
    # v7.6: record everything this bot SEES (updates) so reply targets can
    # be translated into the bot's own id space (basic-group per-account ids)
    if not getattr(bc, "_bc_seen_hook", False):
        bc._bc_seen_hook = True
        try:
            from telethon import events as _evts

            _bme = await bc.get_me()
            _bid = _bme.id if _bme else 0

            @bc.on(_evts.NewMessage())
            async def _bc_seen_recorder(event):
                try:
                    rt = None
                    hdr = getattr(event.message, "reply_to", None)
                    if hdr is not None:
                        rt = getattr(hdr, "reply_to_msg_id", None)
                    _bot_seen_record(_bid, event.chat_id, event.sender_id,
                                     event.id, rt)
                except Exception:
                    pass
        except Exception:
            pass
    return bc


async def _connect_bots(main_client, slots, data):
    """Connect every requested slot → [(slot, client), …] (frozen ones skipped)."""
    pairs = []
    for s in slots:
        bc = await _bot_client(main_client, s, data)
        if bc is not None:
            pairs.append((s, bc))
    return pairs


async def _shutdown_bot(slot: int):
    global BOT_CLIENTS
    bc = BOT_CLIENTS.pop(slot, None)
    if bc is not None:
        try:
            await bc.disconnect()
        except Exception:
            pass


# ─── animation frames lookup (delegation) ────────────────────────────────

_ANIM_ALIASES = {"solarsystem": "SOLAR", "moneyrain": "MONEY"}


def _anim_frames(name: str):
    """Resolve an animation name (rose/hack/theart…) to its frame list, else None."""
    try:
        import importlib
        anim = importlib.import_module("plugins.animations")
    except Exception:
        return None
    key = _ANIM_ALIASES.get(name.lower(), name.upper()).upper()
    frames = getattr(anim, f"{key}_FRAMES", None)
    if frames:
        try:
            return list(frames)
        except Exception:
            return None
    fn = getattr(anim, f"_{name.lower()}_frames", None)
    if callable(fn):
        try:
            return list(fn())
        except Exception:
            pass
    # inline specials (frames jo animations.py me local build hoti hain)
    if name.lower() == "countdown":
        nums = ["🔟", "9️⃣", "8️⃣", "7️⃣", "6️⃣", "5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣", "⭕"]
        return [f"{n}\n˹ get ready ˼" for n in nums] + ["🚀 GO!! 🚀"]
    if name.lower() == "typewriter":
        text = "⚡ Sukuna-X Userbot ⚡"
        return [text[:i] + "▌" for i in range(1, len(text) + 1)] + [text]
    return None


# delegation safety — ye bases kabhi animation nahi hain (apne hi commands)
DELEG_EXCLUDE_BASES = {
    "spam", "sspa", "raid", "clone", "revert", "addall", "removeall",
    "monitor", "stop", "botsay", "bchelp", "addbot", "delbot", "list",
    "ct", "rrt", "rr", "refresh", "loadprofile", "unclone", "addnewbotauto",
    "type",   # v7.7: .typeb = TYPE-X BOT system (NOT an animation)
}


# ─── TYPE-X B ⌨️🤖 — TYPING EFFECT FOR BOTS (v7.7) ────────────────────────
# `.typeb on`  → every message the BOTS send (`.spamb`, `.raidb`, `.botsay`,
#                `.rrb` replies…) gets the typewriter animation, live!
# `.typeb off` → bots send normal again
# `.typeb1-2 on` → only specific bots get the effect
# `.typeb <style>` / `.typeb speed 0.2` / `.typeb styles` / `.typeb status`
# `.typeb sync`  → copy style+speed from the user-side TYPE-X (`.type`)
# `.typeb <text>` → one-shot: bots send <text> WITH the effect (even if off)
#
# Engine: every bot client's send_message is wrapped ONCE at connect time.
# Plain-text sends are queued per-bot and animated sequentially (flood-safe:
# frame cap + per-bot queue cap + storm guard + FloodWait retry). Messages
# with markup (mentions/bold) animate only their plain prefix, then the
# final edit restores the EXACT original text + entities. Animation
# delegation (.<anim>b) and copycat mirrors are auto-skipped.
_TXB_STORE = "typexb"                       # data/typexb.json
_TXB_STATE = {"on": False, "style": "classic", "speed": 0.15, "slots": []}
_TXB_SUPPRESS = set()      # slots currently running .<anim>b (self-animating)
_TXB_ONE_SHOT = set()      # slots doing a `.typeb <text>` demo right now
_TXB_SKIP_IDS = set()      # msg ids that must NEVER animate (copycat copies)
_TXB_QUEUES = {}           # {slot: asyncio.Queue}
_TXB_WORKERS = {}          # {slot: task}
_TXB_DONE = 0              # lifetime animated counter (stats card)
_TXB_MAX_PENDING = 12      # per-bot queue cap — heavy spam → extra skips
_TXB_MAX_FRAMES = 6        # frames per bot message (bots edit-limit safe)
_TXB_FLOOR = 1.0           # min seconds between bot edits (bots: ~1 edit/s!)
_TXB_MAX_CHARS = 280       # longer bot messages are not animated


def _txb_load():
    global _TXB_DONE
    try:
        d = load_store(_TXB_STORE)
        if isinstance(d, dict):
            _TXB_STATE["on"] = bool(d.get("on", False))
            _TXB_STATE["style"] = str(d.get("style") or "classic")
            try:
                _TXB_STATE["speed"] = min(1.0, max(0.05, float(d.get("speed", 0.15))))
            except (TypeError, ValueError):
                pass
            slots = d.get("slots")
            _TXB_STATE["slots"] = [int(s) for s in slots if int(s) > 0] \
                if isinstance(slots, list) else []
            _TXB_DONE = int(d.get("done", 0) or 0)
    except Exception:
        pass
    # default style/speed = user-side TYPE-X (.type) se — same feel everywhere
    try:
        fun = _txb_fun()
        if fun is not None and "style" not in (load_store(_TXB_STORE) or {}):
            _TXB_STATE["style"] = fun._TX_STATE.get("style", "classic")
            _TXB_STATE["speed"] = float(fun._TX_STATE.get("speed", 0.15))
    except Exception:
        pass


def _txb_save():
    try:
        save_store(_TXB_STORE, {
            "on": _TXB_STATE["on"], "style": _TXB_STATE["style"],
            "speed": _TXB_STATE["speed"], "slots": _TXB_STATE["slots"],
            "done": _TXB_DONE,
        })
    except Exception:
        pass


_txb_fun_mod = None


def _txb_fun():
    """plugins.fun (TYPE-X engine) — shared frames + style hints."""
    global _txb_fun_mod
    if _txb_fun_mod is None:
        try:
            import importlib
            _txb_fun_mod = importlib.import_module("plugins.fun")
        except Exception:
            _txb_fun_mod = False
    return _txb_fun_mod or None


def _txb_styles():
    fun = _txb_fun()
    if fun is not None:
        try:
            return tuple(fun._TX_STYLES)
        except Exception:
            pass
    return ("classic", "wave", "glitch", "scramble", "matrix", "pulse",
            "fire", "hearts", "zoom", "eraser", "reverse", "random")


def _txb_style_hints():
    fun = _txb_fun()
    if fun is not None:
        try:
            return dict(fun._TX_STYLE_HINTS)
        except Exception:
            pass
    return {"classic": "classic typewriter cursor ▌"}


_txb_load()


def _txb_slot_ok(slot: int) -> bool:
    """True if this bot slot is inside the TYPE-X B scope (empty = ALL)."""
    try:
        scope = _TXB_STATE.get("slots") or []
        return (not scope) or (int(slot) in scope)
    except Exception:
        return True


def _txb_split(text: str):
    """(plain prefix, has_markup) — animate only before the first markup
    char; the final edit then restores the exact original (mentions safe)."""
    try:
        cut, found = len(text), False
        for ch in "<*_`[":
            i = text.find(ch)
            if i != -1 and i < cut:
                cut, found = i, True
        if not found:
            return text, False
        return text[:cut], True
    except Exception:
        return text, False


def _txb_frames(text: str, style):
    """Typewriter frames for a bot message — ≤ _TXB_MAX_FRAMES (fast)."""
    frames = None
    fun = _txb_fun()
    if fun is not None:
        try:
            frames = fun._tx_frames(text, style)
        except Exception:
            frames = None
    if not frames:                                  # fallback: classic
        n = len(text)
        step = max(1, math.ceil(n / _TXB_MAX_FRAMES))
        frames = [text[:i] + "▌" for i in range(1, n + 1, step)]
        frames.append(text)
    if len(frames) > _TXB_MAX_FRAMES:               # downsample (fast bots)
        pos = len(frames) / _TXB_MAX_FRAMES
        frames = [frames[min(len(frames) - 1, int(i * pos))]
                  for i in range(_TXB_MAX_FRAMES)]
        if frames[-1] != text:
            frames.append(text)
    out = []
    for f in frames:
        if not out or f != out[-1]:
            out.append(f)
    return out


def _txb_skip(msg_or_id):
    """Mark a message id as never-animate (copycat copies, mirrors…)."""
    try:
        _TXB_SKIP_IDS.add(int(getattr(msg_or_id, "id", msg_or_id)))
        if len(_TXB_SKIP_IDS) > 400:
            _TXB_SKIP_IDS.clear()
    except Exception:
        pass


async def _txb_animate(msg, text: str, pm, lp):
    """Play typewriter frames on a bot-sent message (flood-safe)."""
    global _TXB_DONE
    style = _TXB_STATE.get("style") or "classic"
    try:
        speed = float(_TXB_STATE.get("speed") or 0.15)
    except (TypeError, ValueError):
        speed = 0.15
    prefix, _markup = _txb_split(text)
    if len(prefix.strip()) < 2:
        return
    frames = _txb_frames(prefix, style)
    if len(frames) < 2:
        return
    delay = max(speed, _TXB_FLOOR)
    await asyncio.sleep(0.35)                       # natural beat + skip grace
    if getattr(msg, "id", 0) in _TXB_SKIP_IDS:
        return
    last, fails = None, 0
    for fr in frames:
        if fr == last:
            continue
        try:
            await msg.edit(fr, parse_mode=None, link_preview=False)
            last = fr
        except MessageNotModifiedError:
            pass
        except FloodWaitError as e:
            try:
                await asyncio.sleep(min(int(e.seconds or 0), 30) + 1)
                await msg.edit(fr, parse_mode=None, link_preview=False)
                last = fr
            except Exception:
                fails += 1
        except asyncio.CancelledError:
            raise
        except Exception:
            fails += 1
        if fails >= 2:
            return
        await asyncio.sleep(delay + random.uniform(0, 0.06))
    # final frame — EXACT original text + entities (mention/tag pop in!)
    if last != text:
        kw = {}
        if lp is not None:
            kw["link_preview"] = lp
        if pm is not None:
            kw["parse_mode"] = pm
        try:
            await msg.edit(text, **kw)
        except Exception:
            pass
    _TXB_DONE += 1


def _txb_worker(main_client, slot: int):
    """Get (or spawn) the per-bot sequential animation worker."""
    q = _TXB_QUEUES.setdefault(slot, asyncio.Queue())
    w = _TXB_WORKERS.get(slot)
    if w is not None and not w.done():
        return q

    async def _run():
        while True:
            ts, msg, text, pm, lp = await q.get()
            try:
                if time.time() - ts > 90:           # stale (queue was stopped)
                    continue
                if getattr(msg, "id", 0) in _TXB_SKIP_IDS:
                    continue
                if storm_active():                  # 🚨 ID protection first
                    continue
                if not (_TXB_STATE.get("on") or slot in _TXB_ONE_SHOT):
                    continue
                await _txb_animate(msg, text, pm, lp)
                # v7.7.1 — animation batch drained? verify the main
                # account's update stream and heal it if wedged.
                if q.empty():
                    await _txb_verify_stream(main_client)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

    t = asyncio.create_task(_run())
    _TXB_WORKERS[slot] = t
    try:
        (main_client.stop_processes or {})[f"bc_txb_{slot}"] = t
    except Exception:
        pass
    return q


def _txb_offer(slot: int, msg, text, kwargs, main_client):
    """Called after EVERY bot send — decide + enqueue the effect. Never raises."""
    try:
        if msg is None or not isinstance(text, str):
            return
        t = text.strip()
        if not t or len(t) > _TXB_MAX_CHARS:
            return
        if not (_TXB_STATE.get("on") or slot in _TXB_ONE_SHOT):
            return
        if slot in _TXB_SUPPRESS:                   # .<anim>b is self-animating
            return
        if storm_active():
            return
        if not _txb_slot_ok(slot):
            return
        for k in ("file", "photo", "voice", "video", "audio", "document",
                  "sticker", "buttons", "formatting_entities", "attributes"):
            if kwargs.get(k):
                return
        q = _TXB_QUEUES.get(slot)
        if q is None:
            q = _txb_worker(main_client, slot)
        if q.qsize() >= _TXB_MAX_PENDING:           # overloaded → skip extra
            return
        pm = kwargs.get("parse_mode")
        if pm == ():
            pm = None                               # Telethon default sentinel
        q.put_nowait((time.time(), msg, text, pm, kwargs.get("link_preview")))
    except Exception:
        pass


def _txb_patch_bot(main_client, bc, slot: int):
    """v7.7 — wrap a bot client's send_message ONCE (TYPE-X B hook)."""
    try:
        bc._txb_slot = slot
        if getattr(bc, "_txb_patched", False):
            return
        orig = bc.send_message

        async def _txb_send(entity, message=None, *args, **kwargs):
            msg = await orig(entity, message, *args, **kwargs)
            _txb_offer(slot, msg, message, kwargs, main_client)
            return msg

        bc.send_message = _txb_send
        bc._txb_patched = True
    except Exception:
        pass


def _txb_stop_all():
    """`.typeb off` / engine stop — kill workers, drop queues."""
    for t in _TXB_WORKERS.values():
        try:
            if t is not None and not t.done():
                t.cancel()
        except Exception:
            pass
    _TXB_WORKERS.clear()
    _TXB_QUEUES.clear()
    _TXB_ONE_SHOT.clear()


# ─── v7.7.1 STREAM VERIFY-AND-HEAL (after bot animation batches) ─────────
# EMPIRICAL (live-tested 2026-11-07): plain bot sends are fine, but a bot
# message EDIT (typewriter frame) can wedge the MAIN account's update push
# stream server-side for minutes — commands then "don't work" until the
# stream re-binds. Cure: after an animation batch drains, probe the stream
# with a Saved-Messages message; if it does not come back as an update,
# reconnect (fresh getState re-binds the stream in ~1 min).
_TXB_PROBE = {"seen": False, "busy": False}


def _txb_install_probe(client):
    """One catch-all listener that flags our own Saved-Messages probes."""
    try:
        if getattr(client, "_txb_probe_on", False):
            return
        client._txb_probe_on = True

        @client.on(events.NewMessage(outgoing=True))
        async def _txb_probe_touch(event):
            try:
                if (event.is_private and event.chat_id == event.sender_id
                        and (getattr(event, "raw_text", "") or "") == "🩺"):
                    _TXB_PROBE["seen"] = True
            except Exception:
                pass
    except Exception:
        pass


async def _txb_verify_stream(client):
    """Probe the update stream; heal with reconnects if wedged.

    Up to 3 rounds of (probe → reconnect → wait) — empirically a fresh
    connection re-binds the stream in ~1 min."""
    if _TXB_PROBE["busy"]:
        return
    _TXB_PROBE["busy"] = True
    try:
        for attempt in range(1, 4):
            _TXB_PROBE["seen"] = False
            probe_msg = await client.send_message("me", "🩺")
            await asyncio.sleep(12)
            healthy = _TXB_PROBE["seen"]
            try:
                await client.delete_messages("me", probe_msg.id)
            except Exception:
                pass
            if healthy:
                if attempt > 1:
                    log.warning("[typeb] 🩺 update stream HEALTHY again "
                                "(heal round %d)", attempt)
                return
            log.warning("[typeb] 🩺 update stream wedged after bot animation "
                        "(round %d/3) — healing reconnect…", attempt)
            await client.disconnect()
            await client.connect()
            await asyncio.sleep(70)          # give the fresh connection time
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.warning("[typeb] stream verify failed: %r", e)
    finally:
        _TXB_PROBE["busy"] = False


# ─── v7.3.1 RRT (reply-raid turbo) + COPYCAT state ────────────────────────
# RRT: target user ka har message → reply me saved raid slots me se ek-ek
RRT_USERS = {}    # {uid: {"idx": int, "name": str}}
RRT_BOTS = {}     # {uid: {"slots": [int], "idx": {slot: int}, "name": str}}
# CopyCat: jo bheja wahi wapas (user + bots)
# v7.6 MIRROR targets: kisi user ka HAR message same-to-same copy
CT_STATE = {
    "user": False, "bots": False, "bot_slots": None,
    "targets": {},      # {uid: name}   — userbot mirrors this user
    "bot_targets": {},  # {uid: {"slots": [..], "name": str}} — bots mirror
}
_COPY_SEEN = set()   # humari copy ke msg ids (infinite-loop guard)
_COPY_CAP = 800


def _ct_load_state():
    """RRT + CopyCat state store se load (restart-proof)."""
    try:
        data = _bc_load()
        for k, v in (data.get("rrt_users") or {}).items():
            try:
                RRT_USERS[int(k)] = v
            except (TypeError, ValueError):
                pass
        for k, v in (data.get("rrt_bots") or {}).items():
            try:
                RRT_BOTS[int(k)] = v
            except (TypeError, ValueError):
                pass
        cc = data.get("copycat") or {}
        CT_STATE["user"] = bool(cc.get("user"))
        CT_STATE["bots"] = bool(cc.get("bots"))
        CT_STATE["bot_slots"] = cc.get("bot_slots")
        CT_STATE["targets"] = {}
        for k, v in (cc.get("targets") or {}).items():
            try:
                CT_STATE["targets"][int(k)] = str(v)
            except (TypeError, ValueError):
                pass
        CT_STATE["bot_targets"] = {}
        for k, v in (cc.get("bot_targets") or {}).items():
            try:
                CT_STATE["bot_targets"][int(k)] = {
                    "slots": [int(s) for s in (v.get("slots") or [])],
                    "name": v.get("name", "User"),
                }
            except (TypeError, ValueError, AttributeError):
                pass
    except Exception:
        pass


def _ct_save_state():
    """RRT + CopyCat state store me save."""
    try:
        data = _bc_load()
        data["rrt_users"] = {str(k): v for k, v in RRT_USERS.items()}
        data["rrt_bots"] = {
            str(k): {"slots": v.get("slots", []), "name": v.get("name", "User")}
            for k, v in RRT_BOTS.items()
        }
        data["copycat"] = {
            "user": CT_STATE["user"], "bots": CT_STATE["bots"],
            "bot_slots": CT_STATE["bot_slots"],
            "targets": {str(k): v for k, v in CT_STATE["targets"].items()},
            "bot_targets": {
                str(k): {"slots": v.get("slots", []), "name": v.get("name", "User")}
                for k, v in CT_STATE["bot_targets"].items()
            },
        }
        _bc_save(data)
    except Exception:
        pass


def _rrt_pool():
    """Saved raid slots (ya fallback raid text) — reply-raid ke liye."""
    msgs = _rm_load()
    if msgs:
        return msgs
    try:
        from plugins.raid import _load_raid_text as _rt
        return [_rt()]
    except Exception:
        return ["hi"]


# ─── bot-side low-level send helpers ─────────────────────────────────────

# v7.6 — bot-side "seen messages" cache.
# Basic-group chats use PER-ACCOUNT message-id sequences: an id taken from
# the MAIN account's event is meaningless for a bot, and Telegram silently
# DROPS the reply header (bot raids had tags but no reply header).
# Bots cannot read history (GetHistory = user-only), but they DO receive
# every group message as an update (privacy mode is disabled on our bots).
# So every connected bot records what it sees here, and reply targets are
# translated into each bot's own id space from this cache.
_BOT_SEEN = {}          # {(bot_id, chat_id): [(sender_id, msg_id, reply_to, ts), …]}
_BOT_SEEN_CAP = 60      # per bot+chat
_PRIVACY_ATTEMPTED = set()   # bot ids already attempted this boot


def _bot_seen_record(bot_id, chat_id, sender_id, msg_id, reply_to):
    try:
        key = (int(bot_id), int(chat_id))
        lst = _BOT_SEEN.setdefault(key, [])
        lst.append((sender_id, int(msg_id), reply_to, time.time()))
        if len(lst) > _BOT_SEEN_CAP:
            del lst[:len(lst) - _BOT_SEEN_CAP]
    except Exception:
        pass


def _bot_seen_lookup(bot_id, chat_id, target_uid, owner_uid=None,
                     prefer_owner=False):
    """Latest message id from `target_uid` AS THE BOT saw it. Fallback: the
    reply header of the owner's command message (already in bot id space)."""
    try:
        lst = _BOT_SEEN.get((int(bot_id), int(chat_id))) or []
        owner_hdr = None
        if owner_uid:
            for s, mid, rt, _ts in reversed(lst):
                if s == owner_uid and rt:
                    owner_hdr = rt
                    break
        if prefer_owner and owner_hdr:
            return owner_hdr
        for s, mid, rt, _ts in reversed(lst):
            if s == target_uid:
                return mid
        if owner_hdr:
            return owner_hdr
    except Exception:
        pass
    return None


async def _bot_reply_target(bc, chat, target_uid, owner_uid=None,
                            prefer_owner=False, patience=6.0):
    """v7.6 KEY FIX — the reply-anchor id in THIS BOT's id space.

    Order: (1) live updates cache, (2) short wait-retry (the bot's update
    may be a moment behind the main account's), (3) history read — works
    only in supergroups (basic groups raise BotMethodInvalid for bots).
    Returns id | None (None = tag-only fallback)."""
    if target_uid is None:
        return None
    try:
        ckey = chat if isinstance(chat, int) else getattr(chat, "chat_id", chat)
        bme = await bc.get_me()
        bid = bme.id if bme else None
        if bid is not None:
            hit = _bot_seen_lookup(bid, ckey, target_uid, owner_uid,
                                   prefer_owner)
            if hit:
                return hit
            # the bot's update may lag the main session — patient retry
            for _ in range(max(1, int(patience / 1.5))):
                await asyncio.sleep(1.5)
                hit = _bot_seen_lookup(bid, ckey, target_uid, owner_uid,
                                       prefer_owner)
                if hit:
                    return hit
    except Exception:
        pass
    # history read (supergroups only — bots can read channel history)
    try:
        async for m in bc.iter_messages(chat, limit=10):
            if getattr(m, "sender_id", None) == target_uid:
                return m.id
    except Exception:
        pass
    return None


async def _bc_send_text(bc, chat, text, **kw):
    """Send text through a bot with FloodWait retry + v7.7.1 RPC TIMEOUT.

    A zombie bot connection used to wedge handlers FOREVER (send_message
    never returned → .typeb/.botsay/.rrb handlers stuck). Now every attempt
    is capped and a wedged connection is discarded.
    Returns msg | None."""
    for _attempt in range(3):
        try:
            return await asyncio.wait_for(
                bc.send_message(chat, text, link_preview=False, **kw),
                timeout=75)
        except FloodWaitError as fw:
            note_flood(fw.seconds)          # 🛡 safety engine auto slow-down
            await asyncio.sleep(fw.seconds + 1)
        except asyncio.TimeoutError:
            log.warning("[botcontroller] bot send timed out (75s) — "
                        "recycling connection")
            try:
                await bc.disconnect()
            except Exception:
                pass
        except asyncio.CancelledError:
            raise
        except Exception:
            return None
    return None


async def _bc_clear_bot_photos(bc) -> bool:
    """Bot ke apne profile photos delete (best-effort)."""
    try:
        from telethon.tl.functions.photos import DeletePhotosRequest
        from telethon.tl.types import InputPhoto
        cur = await bc.get_profile_photos("me")
        if cur:
            inputs = [InputPhoto(id=p.id, access_hash=p.access_hash,
                                  file_reference=p.file_reference)
                      for p in cur if getattr(p, "access_hash", None) is not None]
            if inputs:
                await bc(DeletePhotosRequest(id=inputs))
        return True
    except Exception:
        return False


def _bc_bot_line(rec, slot) -> str:
    frozen = " ❄️ **FROZEN**" if rec.get("frozen") else ""
    uname = rec.get("username") or rec.get("id")
    return f"┃ **{_ord(slot)}** · @{uname} — `{rec.get('first_name', 'Bot')}`{frozen}"


# ═════════════════════════════════════════════════════════════════════════
#  v7.4 — BOTFATHER AUTOMATION ENGINE
#  (bots account.updateProfile use NAHI kar sakte — official MTProto limit.
#   isliye name/bio BotFather conversation se set hote hain, pfp MTProto se.)
# ═════════════════════════════════════════════════════════════════════════

# ─── BotFather RATE GUARD (v7.5) ──────────────────────────────────────────
# BotFather ko rapid-fire automation messages bhejne par ACCOUNT par spam
# flag lag sakta hai. Isliye: (1) poori duniya me EK hi BF conversation
# ek time par (global lock), (2) do conversations ke beech MIN gap,
# (3) per-hour hard cap, (4) har send ke beech pacing sleep.

_BF = "BotFather"
_BF_LOCK = None                       # lazy asyncio.Lock
_BF_STATE = {"last": 0.0, "calls": deque()}
_BF_MIN_GAP = 4.0                     # sec between two BF conversations (spam-shield)
_BF_MAX_PER_HOUR = 24                 # hourly hard cap (spam-shield)
_BF_SEND_PACE = 1.2                   # sec pacing inside one conversation


def _bf_gate():
    global _BF_LOCK
    if _BF_LOCK is None:
        _BF_LOCK = asyncio.Lock()
    return _BF_LOCK


def _bf_hourly_count():
    now = time.time()
    while _BF_STATE["calls"] and now - _BF_STATE["calls"][0] > 3600:
        _BF_STATE["calls"].popleft()
    return len(_BF_STATE["calls"])


async def _bf_run(main_client, sends, timeout: int = 90, force: bool = False):
    """BotFather conversation chalao — RATE-SAFE (lock + gap + cap + pacing).

    force=True (used by .clonebi) → the internal hourly cap is IGNORED, the
    anti-spam gap is shortened, every Telegram FloodWait is slept through in
    full and every send is retried — the change ALWAYS lands in the end.
    sends: [("text", str) | ("file", path)] — har send ke baad response padho.
    Returns (responses: [str], error: str|None)."""
    res = []
    try:
        async with _bf_gate():
            # ── per-hour cap (ID spam-shield) — force mode BYPASSES it ──
            if not force and _bf_hourly_count() >= _BF_MAX_PER_HOUR:
                return res, ("BotFather hourly safety limit reached — try again "
                             "in a while, or use `.clonebi` (force mode) to "
                             "ignore the cap")
            # ── min gap between conversations (shorter when forced) ──
            wait = (1.2 if force else _BF_MIN_GAP) - (time.time() - _BF_STATE["last"])
            if wait > 0:
                await asyncio.sleep(wait)
            _BF_STATE["last"] = time.time()
            _BF_STATE["calls"].append(time.time())
            async with main_client.conversation(_BF, timeout=timeout) as conv:
                for kind, val in sends:
                    sent = False
                    for _attempt in range(3 if force else 1):
                        try:
                            if kind == "file":
                                await conv.send_file(val)
                            else:
                                await conv.send_message(val)
                            sent = True
                            break
                        except FloodWaitError as fw:
                            note_flood(fw.seconds)
                            # force mode SLEEPS the full wait, then retries
                            await asyncio.sleep(fw.seconds + 2)
                        except asyncio.TimeoutError:
                            await asyncio.sleep(1.0)
                    if not sent:
                        return res, ("could not reach BotFather after retries "
                                     "— Telegram is rate-limiting right now")
                    r = await conv.get_response()
                    res.append((getattr(r, "raw_text", "") or "") if r else "")
                    await asyncio.sleep(0.8 if force else _BF_SEND_PACE)
        return res, None
    except asyncio.TimeoutError:
        return res, ("BotFather did not reply in time — it may be busy or "
                     "rate-limiting. Try again in a minute.")
    except FloodWaitError as fw:
        note_flood(fw.seconds)
        return res, (f"Telegram FloodWait {fw.seconds}s — paused to keep your "
                     "ID safe. Try again later.")
    except Exception as e:
        return res, f"{type(e).__name__}: {e}"[:140]


_TOKEN_RE = re.compile(r"(\d{5,14}:[A-Za-z0-9_-]{25,60})")   # bot token pattern


def _gen_bot_username(base: str = "worker") -> str:
    """Auto username — hamesha 'bot' par khatam hota hai (TG rule).
    e.g. worker482913_bot"""
    digits = "".join(random.choice("0123456789") for _ in range(6))
    base = re.sub(r"[^a-z0-9_]", "", (base or "worker").lower())[:20] or "worker"
    return f"{base}{digits}_bot"


def _bf_ok(text: str) -> bool:
    return "success" in text.lower() or "updated" in text.lower() or "done" in text.lower()


def _bot_selector(rec) -> str:
    """BotFather ko bot kaise bataoon — @username ya numeric id."""
    return f"@{rec['username']}" if rec.get("username") else str(rec.get("id", ""))


async def _bf_set_bot_name(main_client, rec, new_name: str, force: bool = False):
    """Bot ka naam BotFather /setname se badlo (MTProto bots ke liye hi raasta)."""
    name = (new_name or "").strip()[:64]
    if not name:
        return False, "empty name"
    res, err = await _bf_run(main_client, [
        ("text", "/setname"),
        ("text", _bot_selector(rec)),
        ("text", name),
    ], force=force)
    if err:
        return False, err
    last = res[-1] if res else ""
    if _bf_ok(last):
        return True, "name ✅"
    return False, last[:90] or "BotFather did not confirm"


async def _bf_set_bot_description(main_client, rec, bio: str, force: bool = False):
    """Bot ka bio/description BotFather /setdescription se set karo."""
    bio = (bio or "").strip()[:500]
    if not bio:
        return False, "empty bio"
    res, err = await _bf_run(main_client, [
        ("text", "/setdescription"),
        ("text", _bot_selector(rec)),
        ("text", bio),
    ], force=force)
    if err:
        return False, err
    last = res[-1] if res else ""
    if _bf_ok(last):
        return True, "bio ✅"
    return False, last[:90] or "BotFather did not confirm"


async def _bf_set_bot_pic(main_client, rec, photo_path: str, force: bool = False):
    """Bot ka pfp BotFather /setuserpic se (MTProto fail hone par fallback)."""
    if not photo_path or not os.path.exists(photo_path):
        return False, "photo file missing"
    res, err = await _bf_run(main_client, [
        ("text", "/setuserpic"),
        ("text", _bot_selector(rec)),
        ("file", photo_path),
    ], force=force)
    if err:
        return False, err
    last = res[-1] if res else ""
    if _bf_ok(last):
        return True, "pfp ✅"
    return False, last[:90] or "BotFather did not confirm"


async def _bf_set_bot_privacy(main_client, rec, enable: bool = False):
    """Bot ki PRIVACY MODE set karo (/setprivacy).

    Disable = bot group ke SAB messages dekhta hai → reply/raid ke
    reply-headers kaam karte hain. Default naye bots me hum Disable
    hi karte hain (reply+tag raid ke liye zaroori)."""
    mode = "Enable" if enable else "Disable"
    res, err = await _bf_run(main_client, [
        ("text", "/setprivacy"),
        ("text", _bot_selector(rec)),
        ("text", mode),
    ])
    if err:
        return False, err
    last = res[-1] if res else ""
    low = last.lower()
    if ("success" in low or "updated" in low or "done" in low
            or "privacy" in low):
        return True, f"privacy {mode} ✅"
    return False, last[:90] or "BotFather did not confirm"


async def _bf_create_bot(main_client, name: str = "worker", tries: int = 4):
    """BotFather se NAYA bot banao.
    Returns (token, username, error, log_lines)."""
    lines = []
    try:
        async with main_client.conversation(_BF, timeout=120) as conv:
            await conv.send_message("/newbot")
            r1 = await conv.get_response()
            t1 = (getattr(r1, "raw_text", "") or "")
            lines.append(t1[:60])
            low1 = t1.lower()
            if "name" not in low1 and "bot" not in low1:
                # BotFather ne /newbot reject kar diya (limit/pattern)
                return None, None, t1[:160], lines
            await conv.send_message((name or "worker")[:64])
            r2 = await conv.get_response()
            t2 = (getattr(r2, "raw_text", "") or "")
            lines.append(t2[:60])
            if "username" not in t2.lower() and "bot" not in t2.lower():
                return None, None, t2[:160], lines
            for attempt in range(max(2, tries)):
                uname = _gen_bot_username(name or "worker")
                await conv.send_message(uname)
                r3 = await conv.get_response()
                t3 = (getattr(r3, "raw_text", "") or "")
                m = _TOKEN_RE.search(t3)
                if m:
                    lines.append(f"✓ @{uname}")
                    return m.group(1), uname, None, lines
                low3 = t3.lower()
                if any(w in low3 for w in ("taken", "unacceptable",
                                           "try again", "already", "occupied")):
                    lines.append(f"✗ @{uname} taken → retry {attempt + 1}")
                    continue
                return None, None, t3[:160], lines
            return None, None, "all usernames were taken — try again in a while", lines
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"[:140], lines


# ─── token verify + register (shared: .addbottoken & .addnewbotauto) ─────

async def _probe_bot_token(main_client, token: str):
    """Token verify karo → (me|None, error|None)."""
    api_id, api_hash = _api_creds(main_client)
    if not api_id or not api_hash:
        return None, "API_ID/API_HASH missing (fill core/config.py or run first-run setup)"
    probe = TelegramClient(StringSession(), api_id, api_hash)
    me = None
    try:
        await probe.start(bot_token=token)
        me = await probe.get_me()
    except Exception as e:
        err = f"{type(e).__name__}: {e}"[:160]
        if _is_freeze_err(e):
            err = "FROZEN " + err
        return None, err
    finally:
        try:
            await probe.disconnect()
        except Exception:
            pass
    return me, None


async def _register_bot_token(main_client, token: str):
    """Verify + slot me add (async with _bc_lock ke SAATH call karo).
    Returns (me|None, why: str)."""
    data = _bc_load()
    if any(b.get("token") == token for b in data["bots"]):
        return None, "This token is **already registered**"
    me, err = await _probe_bot_token(main_client, token)
    if me is None:
        if err and err.startswith("FROZEN"):
            return None, f"Token is **DEAD/FROZEN** — `{err[7:80]}`"
        return None, f"Token connect failed — `{err or 'unknown'}`"
    if any(b.get("id") == me.id for b in data["bots"]):
        return None, f"@{me.username or me.id} is **already registered**"
    rec = {
        "token": token,
        "id": me.id,
        "username": me.username or "",
        "first_name": me.first_name or "Bot",
        "added_at": time.time(),
        "frozen": False,
        "pre_clone": {
            "first_name": (me.first_name or "Bot"),
            "last_name": (me.last_name or ""),
            "bio": "",
            "has_photo": False,
            "pfp_file": None,
        },
    }
    data["bots"].append(rec)
    _bc_save(data)
    # v7.5: privacy OFF — taki bot reply/raid ke reply-headers dekh sake
    try:
        ok, _why = await _bf_set_bot_privacy(main_client, rec, enable=False)
    except Exception:
        ok = False
    try:
        data = _bc_load()
        for b in data["bots"]:
            if b.get("id") == me.id:
                b["privacy_disabled"] = bool(ok)
        _bc_save(data)
    except Exception:
        pass
    return me, None


def _invite_hint(e) -> str:
    """Common invite errors ka human hint (asli reason AB dikhta hai)."""
    n = type(e).__name__
    s = str(e).lower()
    if "Already" in n:
        return "already in group ✅"
    if "admin" in n.lower() or "admin" in s:
        return "❗ you are not an admin — need the add-members permission"
    if "peer" in s:
        return "❗ /start the bot first (PEER_ID)"
    if "privacy" in s:
        return "❗ privacy restriction"
    if "private" in s or "banned" in s:
        return "❗ group private/banned"
    if "limit" in s or "too many" in s or "userlist" in s:
        return "❗ group limit reached"
    if "kick" in s:
        return "❗ the bot was kicked before"
    return f"`{n}` {str(e)[:34]}"


# ─── copy sender (.ct / .ctb one-shot) ───────────────────────────────────

async def _copy_send(cl, chat, msg, tmp_dir: str, reply_to=None, helper=None):
    """Replied message ka EXACT copy bhejo (text/sticker/photo/media).

    v7.8 .ctb FIX — bots mirror engine is now 4-layer:
      1. direct media-reference send (fast path, sticker attrs kept)
      2. download via HELPER (the main account — full media access) +
         re-upload through the SENDING client with ORIGINAL attributes
         (sticker → sticker, voice → voice, round video → round video)
      3. download via the sending client itself (last resort)
      4. text-only fallback
    FloodWait is slept through on every layer. Copies are marked in
    _COPY_SEEN so the copycat listeners never echo our own copies back.
    Returns True/False."""
    raw = (getattr(msg, "raw_text", "") or "").strip()
    media = getattr(msg, "media", None)
    sent = None
    # original file attributes → same-to-same re-upload (sticker/voice/video)
    _f = getattr(msg, "file", None)
    _attrs = list(getattr(_f, "attributes", None) or [])
    _mime = getattr(_f, "mime_type", None)
    _name = getattr(_f, "name", None)

    def _kw(cap=True, attr=True):
        kw = {}
        if cap and raw:
            kw["caption"] = raw
        if reply_to:
            kw["reply_to"] = reply_to
        if attr and _attrs and _mime:
            kw["attributes"] = _attrs
            kw["mime_type"] = _mime
            if _name:
                kw["file_name"] = _name
        return kw

    if media is not None:
        # ── layer 1: direct media-reference send ──
        try:
            sent = await cl.send_file(chat, media, **_kw())
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 1)
            try:
                sent = await cl.send_file(chat, media, **_kw())
            except Exception:
                sent = None
        except Exception:
            sent = None
        # ── layers 2+3: download + re-upload (helper first, then self) ──
        if sent is None:
            for dl_cl in ([helper, cl] if helper is not None and helper is not cl
                          else [cl]):
                path = None
                try:
                    path = await dl_cl.download_media(msg, file=tmp_dir)
                except Exception:
                    path = None
                if not (path and os.path.exists(path)):
                    continue
                for _try in range(2):
                    try:
                        sent = await cl.send_file(chat, path, **_kw())
                        break
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)
                        await asyncio.sleep(fw.seconds + 1)
                    except Exception:
                        await asyncio.sleep(0.5)
                try:
                    os.remove(path)
                except OSError:
                    pass
                if sent is not None:
                    break
    if sent is None and raw:
        for _try in range(2):
            try:
                kw = {"link_preview": False}
                if reply_to:
                    kw["reply_to"] = reply_to
                sent = await cl.send_message(chat, raw, **kw)
                # v7.7 TYPE-X B: copycat copies are same-to-same — never animated
                if sent is not None and getattr(cl, "_txb_slot", None) is not None:
                    _txb_skip(sent)
                break
            except FloodWaitError as fw:
                note_flood(fw.seconds)
                await asyncio.sleep(fw.seconds + 1)
            except Exception:
                break
    if sent is not None:
        try:
            _COPY_SEEN.add(int(sent.id))
            if len(_COPY_SEEN) > _COPY_CAP:
                _COPY_SEEN.clear()
        except Exception:
            pass
        return True
    return False


# ─── saved-profile loader (.loadprofileb) ────────────────────────────────

def _load_profile_meta(name: str):
    """profile.py ke .saveprofile wale profile ka meta nikalo.
    Returns (meta: dict|None, photo_files: [str], why: str|None)."""
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "", (name or "").strip())[:30]
    if not safe:
        return None, [], "give a name"
    pdir = os.path.join(PROFILES_ROOT, safe)
    info_path = os.path.join(pdir, "info.json")
    photos = []
    meta = None
    if os.path.exists(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as fh:
                meta = json.load(fh)
        except Exception:
            meta = None
        pdirp = os.path.join(pdir, "photos")
        if os.path.isdir(pdirp):
            for fn in sorted(os.listdir(pdirp)):
                fp = os.path.join(pdirp, fn)
                if os.path.isfile(fp):
                    photos.append(fp)
    if meta is None:
        # legacy store (profiles_data.json / data/profiles)
        legacy = load_store("profiles_data")
        rec = legacy.get(safe) if isinstance(legacy, dict) else None
        if isinstance(rec, dict):
            meta = {
                "first_name": rec.get("first_name", ""),
                "last_name": rec.get("last_name", ""),
                "bio": rec.get("bio", ""),
            }
            if rec.get("photo"):
                try:
                    fp = os.path.join(BOT_PFP_DIR, f"prof_{safe}.jpg")
                    with open(fp, "wb") as fh:
                        fh.write(base64.b64decode(rec["photo"]))
                    photos.append(fp)
                except Exception:
                    pass
    if meta is None:
        return None, [], f"`{safe}` saved profile not found — see `.savedprofiles`"
    return meta, photos, None


# ═════════════════════════════════════════════════════════════════════════
#  REGISTRATION
# ═════════════════════════════════════════════════════════════════════════

def register_botcontroller(client):
    global _bc_lock
    _bc_lock = asyncio.Lock()

    if not hasattr(client, "stop_processes"):
        client.stop_processes = {}

    # 🤖 v7.4: RRT + CopyCat + Autodelete state load (restart-proof)
    _ct_load_state()
    _ad_load()

    # ⌨️ v7.7.1 TYPE-X B: Saved-Messages probe listener (stream verify-heal)
    _txb_install_probe(client)

    # ── v7.5 TIMED-DELETE HOOKS (production-safe) ──────────────────────
    # Telegram same-session ke apne edits/sends par update event NAHI
    # bhejta — isliye MessageEdited listener production me kaafi nahi.
    # edit_message / send_message ko hook karke seedha schedule karo:
    #   • edit_message → command output (help card, start card) delete
    #   • send_message(reply_to=command) → done-cards (spam/raid done)
    if not getattr(client, "_ad_hooks_installed", False):
        client._ad_hooks_installed = True

        async def _timed_edit_hook(*args, **kwargs):
            key = _hook_extract_key(args)
            res = await _orig_edit_msg(*args, **kwargs)
            try:
                if (key is not None and key in _CMD_IDS and _ad_timer() > 0):
                    # timer RESET on re-edit (purana task cancel hota hai)
                    _ad_schedule_delete(client, key[0], key[1], _ad_timer())
            except Exception:
                pass
            return res

        async def _timed_send_hook(entity, message=None, *args, **kwargs):
            rid = kwargs.get("reply_to")
            try:
                rid = int(rid) if rid is not None else None
            except (TypeError, ValueError):
                rid = None
            res = await _orig_send_msg(entity, message, *args, **kwargs)
            try:
                if rid and res is not None and _ad_timer() > 0:
                    chat_key = None
                    if _tlutils is not None:
                        try:
                            chat_key = int(_tlutils.get_peer_id(entity))
                        except Exception:
                            chat_key = None
                    if chat_key is not None and (chat_key, rid) in _CMD_IDS:
                        _ad_schedule_delete(client, chat_key, res.id,
                                            _ad_timer())
            except Exception:
                pass
            return res

        try:
            if hasattr(client, "edit_message"):
                _orig_edit_msg = client.edit_message
                client.edit_message = _timed_edit_hook
            if hasattr(client, "send_message"):
                _orig_send_msg = client.send_message
                client.send_message = _timed_send_hook
            log.info("[botcontroller] ⏱ timed-delete hooks installed "
                     "(edit + reply-cards)")
        except Exception as _e:
            log.warning("[botcontroller] hook install failed: %s", _e)

    # ─── SUDO filter + event proxy ──────────────────────────────────────
    # Owner apne messages se commands chalata hai (outgoing), SUDO users
    # apne messages se (incoming + sudo list). _Ev proxy sudo ke liye
    # edit() ko reply() bana deta hai (unki message edit nahi ho sakti).

    def _bc_allow(ev):
        try:
            # v7.4.2 CRITICAL FIX: pehle `is_outgoing` check hota tha — wo
            # attribute Telethon me EXIST nahi karta (sirf `out` hota hai)
            # → getattr hamesha False deta → OWNER ke apne commands bhi
            # reject ho rahe the (yahi "bot commands not working" ka
            # asli root cause tha!). Ab sahi attribute + message fallback.
            if getattr(ev, "out", False) or getattr(getattr(ev, "message", None), "out", False):
                return True
            sid = ev.sender_id
            return bool(sid) and sid in _sudo_ids()
        except Exception:
            return False

    class _Ev:
        """Event proxy — sudo-triggered commands me edit() → reply()."""
        __slots__ = ("_ev", "_cl")

        def __init__(self, ev, cl):
            object.__setattr__(self, "_ev", ev)
            object.__setattr__(self, "_cl", cl)

        def __getattr__(self, name):
            return getattr(self._ev, name)

        def __setattr__(self, name, val):
            setattr(self._ev, name, val)

        async def edit(self, text, *args, **kwargs):
            ev = self._ev
            # v7.4.2: `is_outgoing` → `out` (Telethon me asli attribute)
            if getattr(ev, "out", False) or getattr(getattr(ev, "message", None), "out", False):
                try:
                    m = await ev.edit(text, *args, **kwargs)
                    # v7.4.2 RACE FIX: yahan _ad_track HATA diya —
                    # autodelete-listener khud event.id track karta hai;
                    # yahan track karne se listener usi message ko 'purana
                    # output' samajh kar delete kar deta tha (instant-vanish
                    # bug). Sirf fallback/reply wale NAYE ids track hote hain.
                    return m
                except MessageNotModifiedError:
                    return None
                except Exception as e:
                    # v7.4.2: silent swallow khatam — exact reason log me dikhega
                    log.warning("[botcontroller] _Ev.edit fallback → %s: %s",
                                type(e).__name__, str(e)[:140])
            kwargs.pop("buttons", None)
            try:
                m = await self._cl.send_message(ev.chat_id, text, *args, **kwargs)
            except Exception:
                return None
            _ad_track(ev.chat_id, m.id)
            return m

        async def reply(self, text, *args, **kwargs):
            try:
                m = await self._ev.reply(text, *args, **kwargs)
            except Exception as e:
                log.warning("[botcontroller] _Ev.reply fallback → %s: %s",
                            type(e).__name__, str(e)[:140])
                try:
                    m = await self._cl.send_message(self._ev.chat_id, text,
                                                    *args, **kwargs)
                except Exception as e2:
                    log.error("[botcontroller] _Ev.reply bhi fail: %s", e2)
                    return None
            _ad_track(self._ev.chat_id, m.id)
            return m

    def _on(pattern, sudo_ok=True):
        """Handler register karo: pattern + (owner|sudo) + event proxy.

        v7.4.1: handler crash par chat me VISIBLE error reply hota hai —
        flood_safe ka silent-swallow khatam, user ko turant pata chalega
        ki kya fail hua aur kyun (pehle "kuch bhi nahi hota tha")."""
        def deco(fn):
            async def _wrapped(ev):
                try:
                    return await fn(_Ev(ev, client))
                except asyncio.CancelledError:
                    raise
                except events.StopPropagation:
                    raise
                except Exception as e:
                    log.error("[botcontroller] %s failed: %s",
                              getattr(fn, "__name__", "handler"), e, exc_info=True)
                    # 🚨 VISIBLE error — silent failure NO MORE
                    try:
                        await ev.reply(
                            f"❌ **Command failed:** `{type(e).__name__}`\n"
                            f"`┃ {str(e)[:140]}`\n"
                            "┃ 🛠 Run `.bccheck` for a full diagnosis",
                            link_preview=False)
                    except Exception:
                        pass
                    raise
            _wrapped.__name__ = getattr(fn, "__name__", "bc_handler")
            fs = getattr(client, "flood_safe", None)
            wrapped = fs(_wrapped) if callable(fs) else _wrapped
            ev_obj = (events.NewMessage(pattern=pattern, func=_bc_allow)
                      if sudo_ok
                      else events.NewMessage(outgoing=True, pattern=pattern))
            client.add_event_handler(wrapped, ev_obj)
            return wrapped
        return deco

    # ════════════════════════════════════════════════════════════════════
    #  A) BOT ARMY MANAGEMENT
    # ════════════════════════════════════════════════════════════════════

    # ── .addbottoken <token> ────────────────────────────────────────────
    @_on(r"^\.addbottoken\s+([\s\S]+)$")
    async def _addbottoken(event):
        token = (event.pattern_match.group(1) or "").strip()
        if not re.match(r"^\d{5,14}:[A-Za-z0-9_-]{25,}$", token):
            return await event.edit(
                "❌ **Invalid token format.**\n"
                "📖 Usage: `.addbottoken 123456789:AAxxxx...` (from **@BotFather**)")
        await event.edit("🔍 **Validating the token…**")
        async with _bc_lock:
            me, why = await _register_bot_token(client, token)
            if me is None:
                return await event.edit(f"❌ {why}")
            data = _bc_load()
            total = len(data["bots"])
            listing = "\n".join(_bc_bot_line(b, i + 1)
                               for i, b in enumerate(data["bots"]))
        await event.edit(
            "✦ ━━━〔 🤖 **BOT ARMY — ADDED** 〕━━━ ✦\n"
            f"✅ **{_ord(total)} bot registered:** @{me.username or me.id}\n"
            f"┃ 👤 Name: `{me.first_name or 'Bot'}`\n"
            f"┃ 🧩 Total bots: `{total}`\n"
            f"{listing}\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦\n"
            "💡 `.monitorb` live status · `.addallb` adds them to the group",
            link_preview=False)

    # ── .addnewbotauto [count] — BotFather se KHUD naya bot ─────────────
    @_on(r"^\.addnewbotauto(?:\s+(\d+))?\s*$")
    async def _addnewbotauto(event):
        count = min(int(event.pattern_match.group(1) or 1), 5)
        await event.edit(
            f"🤖 **Creating {count} new bot(s) via BotFather…**\n"
            "┃ name: `worker` · username auto (…bot)\n"
            "┃ retries automatically if a username is taken")
        created, rows = [], []
        for i in range(count):
            token, uname, err, lines = await _bf_create_bot(client, "worker")
            if token is None:
                rows.append(f"┃ ❌ Bot {i + 1} fail: `{err or 'unknown'}`")
                break
            async with _bc_lock:
                me, why = await _register_bot_token(client, token)
            if me is None:
                rows.append(f"┃ ⚠️ @{uname} was created BUT register failed: {why}")
                continue
            # bot ko /start karo taaki group me add na fail ho
            try:
                await client.send_message(uname, "/start")
            except Exception:
                pass
            created.append(uname)
            total = len(_bc_load()["bots"])
            rows.append(f"┃ ✅ **{_ord(total)}** @{uname} — created + registered")
        card = (
            "✦ ━━━〔 🤖 **AUTO-BOT CREATOR** 〕━━━ ✦\n" + "\n".join(rows) +
            f"\n┃ 🧩 Naye bots: `{len(created)}` · Total: `{len(_bc_load()['bots'])}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦\n"
            "💡 `.monitorb` check · `.addallb` adds them to the group")
        await event.edit(card, link_preview=False)

    # ── .delbottoken / .delbot <n> — delete + slots auto-shift ──────────
    @_on(r"^\.(?:delbottoken|delbot)\s+(\d+)$")
    async def _delbottoken(event):
        n = int(event.pattern_match.group(1))
        async with _bc_lock:
            data = _bc_load()
            bots = data["bots"]
            if n < 1 or n > len(bots):
                return await event.edit(
                    f"❌ Bot **{_ord(n)}** does not exist. Total: `{len(bots)}`")
            rec = bots.pop(n - 1)          # ← slots automatically shift ho jate hain
            await _shutdown_bot(n)
            # cached clients reindex (shift ke baad)
            for s in list(BOT_CLIENTS.keys()):
                if s >= n:
                    BOT_CLIENTS[s - 1] = BOT_CLIENTS.pop(s)
            # session + pfp files cleanup
            for suffix in ("", "-journal"):
                try:
                    os.remove(os.path.join(BOT_SESSIONS_DIR,
                                           f"bot_{rec.get('id')}.session{suffix}"))
                except OSError:
                    pass
            pre = rec.get("pre_clone") or {}
            if pre.get("pfp_file"):
                try:
                    os.remove(os.path.join(BOT_PFP_DIR, pre["pfp_file"]))
                except OSError:
                    pass
            _bc_save(data)
            listing = "\n".join(_bc_bot_line(b, i + 1)
                                for i, b in enumerate(bots)) or "┃ *(no bots left)*"
        await event.edit(
            "✦ ━━━〔 🗑 **BOT REMOVED** 〕━━━ ✦\n"
            f"✅ **{_ord(n)} bot delete** — @{rec.get('username') or rec.get('id')}\n"
            f"┃ Remaining slots shifted automatically:\n{listing}\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .listbots / .botlist — sab bots + frozen ────────────────────────
    @_on(r"^\.(?:botlist|listbots)$")
    async def _listbots(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit(
                "🤖 **No bots registered yet.**\n"
                "📖 `.addbottoken <token>` — grab a token from @BotFather\n"
                "⚡ or `.addnewbotauto` — BotFather creates one for you")
        frozen = sum(1 for b in bots if b.get("frozen"))
        listing = "\n".join(_bc_bot_line(b, i + 1) for i, b in enumerate(bots))
        await event.edit(
            "✦ ━━━〔 🤖 **BOT ARMY** 〕━━━ ✦\n"
            f"{listing}\n"
            f"┃ 🧩 Total: `{len(bots)}` · ❄️ Frozen: `{frozen}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦\n"
            "📥 `.addallb` / `.addall 1-3` · 📡 `.monitorb`\n"
            "🚀 `.spamb` · 💥 `.raidb` · 🎭 `.cloneb` · 🎬 `.roseb`",
            link_preview=False)

    # ── .monitorb — LIVE online/frozen status + naam ────────────────────
    @_on(r"^\.monitorb$")
    async def _monitorb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit(
                "🤖 No bots yet — `.addbottoken <token>` or `.addnewbotauto`.")
        await event.edit("📡 **Checking all bots…**")
        rows = []
        online = 0
        for i, rec in enumerate(bots, 1):
            bc = await _bot_client(client, i, data)
            uname = rec.get("username") or rec.get("id")
            if bc is None:
                err = rec.get("frozen_error") or "connect failed"
                rows.append(f"┃ {_ord(i)}: ❄️ @{uname} — **FROZEN** `{str(err)[:40]}`")
            else:
                online += 1
                try:
                    me = await bc.get_me()
                    nm = me.first_name or rec.get("first_name", "Bot")
                except Exception:
                    nm = rec.get("first_name", "Bot")
                rows.append(f"┃ {_ord(i)}: 💚 @{uname} — {nm} · **online**")
        await event.edit(
            "✦ ━━━〔 📡 **BOT MONITOR** 〕━━━ ✦\n"
            + "\n".join(rows) +
            f"\n\n┃ 🟢 Online: `{online}/{len(bots)}` · ❄️ Frozen: `{len(bots) - online}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .refreshb — sab bots reconnect ──────────────────────────────────
    @_on(r"^\.refreshb\s*$")
    async def _refreshb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        await event.edit("🔄 **Reconnecting all bots…**")
        rows = []
        online = 0
        for i, rec in enumerate(bots, 1):
            await _shutdown_bot(i)
            bc = await _bot_client(client, i, data)
            uname = rec.get("username") or rec.get("id")
            if bc is None:
                err = rec.get("frozen_error") or "connect failed"
                rows.append(f"┃ {_ord(i)} ❄️ @{uname} — {str(err)[:36]}")
            else:
                online += 1
                rows.append(f"┃ {_ord(i)} 💚 @{uname} — online")
        await event.edit(
            "✦ ━〔 🔄 **BOT REFRESH** 〕━ ✦\n" + "\n".join(rows) +
            f"\n\n┃ 🟢 Online: `{online}/{len(bots)}` · ❄️ Frozen: `{len(bots) - online}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━ ✦", link_preview=False)

    # ════════════════════════════════════════════════════════════════════
    #  B) GROUP ADD/REMOVE — ImportError FIXED (v7.4)
    # ════════════════════════════════════════════════════════════════════

    async def _resolve_bot_entity(main_client, rec):
        """Main client se bot ka entity nikalo (username → id → None)."""
        if rec.get("username"):
            try:
                return await main_client.get_entity(rec["username"])
            except Exception:
                pass
        try:
            return await main_client.get_entity(int(rec["id"]))
        except Exception:
            return None

    async def _invite_bot(main_client, input_chat, chat_id, rec):
        """Ek bot ko current chat me add. Returns (ok, why).
        v7.4 FIX: (1) asli telethon class AddChatUserRequest use hota hai
        (AddChatMembersRequest EXIST nahi karta → pehle ImportError aata tha)
        (2) har error ka ASLI reason + hint dikhta hai (ab chhupega nahi)."""
        entity = await _resolve_bot_entity(main_client, rec)
        if entity is None:
            return False, "not found — /start the bot first"
        # 1) supergroup / channel → channels.inviteToChannel
        try:
            await main_client(InviteToChannelRequest(input_chat, [entity]))
            return True, "added ✅"
        except Exception as e1:
            if "Already" in type(e1).__name__:
                return True, "already in group ✅"
            hint1 = _invite_hint(e1)
            # 2) basic (chhota) group → messages.addChatUser
            if AddChatUserRequest is not None:
                try:
                    peer = await main_client.get_input_entity(chat_id)
                    raw_chat = getattr(peer, "chat_id", None)
                    user_input = await main_client.get_input_entity(entity.id)
                    if raw_chat:
                        await main_client(
                            AddChatUserRequest(raw_chat, user_input, 100))
                        return True, "added ✅"
                except Exception as e2:
                    if "Already" in type(e2).__name__:
                        return True, "already in group ✅"
                    hint2 = _invite_hint(e2)
                    return False, hint2[:60]
            return False, hint1[:60]

    async def _do_addall(event, arg):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit(
                "🤖 No bots registered yet — `.addbottoken <token>` or `.addnewbotauto`.")
        slots = _parse_slots(arg, len(bots))
        if not slots:
            return await event.edit(
                f"❌ Invalid slot. Total bots: `{len(bots)}` — e.g. `.addall 1-3`")
        try:
            input_chat = await event.get_input_chat()
        except Exception:
            return await event.edit("❌ Could not resolve the chat.")
        chat_id = event.chat_id
        await event.edit(f"📥 **Adding {len(slots)} bot(s)**…")
        rows = []
        for s in slots:
            rec = bots[s - 1]
            ok, why = await _invite_bot(client, input_chat, chat_id, rec)
            mark = "✅" if ok else "❌"
            rows.append(f"┃ {_ord(s)} @{rec.get('username') or rec['id']} {mark} {why}")
        await event.edit(
            "✦ ━━━〔 📥 **BOTS → GROUP** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .addallb — SAB bots add ──────────────────────────────────────────
    @_on(r"^\.addallb(\d+(?:-\d+)?)?\s*$")
    async def _addallb(event):
        slots_arg = (event.pattern_match.group(1) or "").strip() or None
        await _do_addall(event, slots_arg)

    # ── .addall 1-3 — specific bots add ──────────────────────────────────
    @_on(r"^\.addall(?:\s+(\S+))?\s*$")
    async def _addall(event):
        arg = (event.pattern_match.group(1) or "").strip() or None
        if arg is None:
            return await event.edit(
                "📖 Usage: `.addall <slots>`\n"
                "e.g. `.addall 1-3` (1st-3rd) · `.addall 2` (only 2nd) · "
                "`.addall 1,3` — for all bots use `.addallb`")
        await _do_addall(event, arg)

    # ── .removeallb — sab bots group se hatao ─────────────────────────────
    @_on(r"^\.removeallb$")
    async def _removeallb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots registered yet.")
        try:
            chat = await event.get_input_chat()
        except Exception:
            return await event.edit("❌ Could not resolve the chat.")
        await event.edit("📤 **Removing the bots…**")
        rows = []
        for i, rec in enumerate(bots, 1):
            entity = await _resolve_bot_entity(client, rec)
            uname = rec.get("username") or rec.get("id")
            if entity is None:
                rows.append(f"┃ {_ord(i)} @{uname} ❌ not found")
                continue
            try:
                await client.kick_participant(chat, entity)
                rows.append(f"┃ {_ord(i)} @{uname} ✅ removed")
            except Exception as e:
                rows.append(f"┃ {_ord(i)} @{uname} ❌ {_invite_hint(e)[:44]}")
        await event.edit(
            "✦ ━━━〔 📤 **BOTS KICKED** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ════════════════════════════════════════════════════════════════════
    #  C) ATTACK — text spam / sticker spam / raid (bots)
    # ════════════════════════════════════════════════════════════════════

    # ── .spamb [slots] <count> <interval> <text> — bot army spam ──────────
    @_on(r"^\.spamb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$")
    async def _spamb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit(
                "🤖 No bots yet — `.addbottoken <token>` or `.addnewbotauto`.")
        arg = (event.pattern_match.group(2) or "").strip()
        if not arg:
            return await event.edit(
                "📖 **Bot Spam Usage:**\n"
                "`.spamb <count> <interval> <text>` — **all bots**\n"
                "`.spamb1-3 <count> <interval> <text>` — only 1st-3rd\n"
                "`.spamb2 20 0.5 hello` — only the 2nd\n"
                "⏱ interval in seconds — **float allowed, NO lower limit** "
                "(`0.1`, `0.5`, `0` all fine)\n"
                "⛔ Stop: `.stop` or `.stopb`")
        count, interval, text, err = _parse_count_interval(arg, need_text=True)
        if err == "count":
            return await event.edit("❌ `<count>` must be an integer.")
        if err == "positive":
            return await event.edit("❌ Count must be positive.")
        if err == "text":
            return await event.edit("❌ Give text too — e.g. `.spamb 10 0.5 hello`")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit(
                "❄️ No bot connected (all frozen?). Check `.monitorb`.")
        count = safe_cap(count)
        chat = event.chat_id
        await event.edit(
            f"🚀 **BOT SPAM STARTED**\n"
            f"┃ 🤖 Bots: `{len(pairs)}` · 💬 Messages: `{count}` each\n"
            f"┃ ⏱ Interval: `{interval}s` (no floor)\n"
            f"⛔ Stop with `.stop` / `.stopb`")

        async def _one(slot, bc):
            key = f"bc_spam_{event.id}_{slot}"
            sent = 0
            fails = 0
            try:
                for _i in range(count):
                    try:
                        await bc.send_message(chat, text, link_preview=False)
                        sent += 1
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)
                        await asyncio.sleep(fw.seconds + 1)
                        try:
                            await bc.send_message(chat, text, link_preview=False)
                            sent += 1
                        except Exception:
                            fails += 1
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        fails += 1
                    if fails >= 3:
                        break
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                raise
            finally:
                client.stop_processes.pop(key, None)
            return sent

        tasks = []
        for slot, bc in pairs:
            t = asyncio.create_task(_one(slot, bc))
            client.stop_processes[f"bc_spam_{event.id}_{slot}"] = t
            tasks.append(t)

        async def _gatherer():
            try:
                res = await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                raise
            # .stop se cancel hua? → done card MAT bhejo
            if any(isinstance(r, asyncio.CancelledError) for r in res):
                for slot, _bc in pairs:
                    client.stop_processes.pop(f"bc_spam_{event.id}_{slot}", None)
                return
            total = sum(r for r in res if isinstance(r, int))
            per = ", ".join(
                f"{_ord(slot)}:`{r if isinstance(r, int) else 0}`"
                for (slot, _bc), r in zip(pairs, res))
            try:
                hint = "" if total else "\n💡 Got 0? First add the bots to the group with `.addallb`."
                await event.reply(
                    f"✅ **Bot spam done** — `{total}/{count * len(pairs)}` msgs\n"
                    f"┃ {per}{hint}")
            except Exception:
                pass
            for slot, _bc in pairs:
                client.stop_processes.pop(f"bc_spam_{event.id}_{slot}", None)

        client.stop_processes[f"bc_gather_{event.id}"] = asyncio.create_task(_gatherer())

    # ── .sspam <count> [interval] — USER sticker spam (reply) ────────────
    @_on(r"^\.sspam(?:\s+([\s\S]+))?$")
    async def _sspam(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sticker:
            return await event.edit(
                "↩️ **Reply to a sticker** — `.sspam <count> [interval]`")
        arg = (event.pattern_match.group(1) or "").strip()
        count, interval, _t, err = _parse_count_interval(arg, need_text=False)
        if err in ("count",):
            return await event.edit("❌ Give an integer `<count>` — `.sspam 20 0.5`")
        if err == "positive":
            return await event.edit("❌ Count must be positive.")
        if err == "empty":
            return await event.edit("❌ `.sspam <count> [interval]`")
        doc = reply.media.document
        sticker_input = InputDocument(
            id=doc.id, access_hash=doc.access_hash,
            file_reference=doc.file_reference)
        chat = await event.get_input_chat()
        count = safe_cap(count)
        await event.edit(
            f"🩸 **Sticker spam** — `{count}`x · `{interval}s` gap\n"
            "⛔ Stop with `.stop` / `.sspamstop`")
        key = f"bc_sspam_{event.id}"
        sent = 0
        try:
            for _i in range(count):
                try:
                    await client.send_file(chat, sticker_input)
                    sent += 1
                except FloodWaitError as fw:
                    note_flood(fw.seconds)
                    await asyncio.sleep(fw.seconds + 1)
                    try:
                        await client.send_file(chat, sticker_input)
                        sent += 1
                    except Exception:
                        pass
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            try:
                await event.reply(f"⛔ **sspam stopped** — {sent}/{count}")
            except Exception:
                pass
            raise
        finally:
            client.stop_processes.pop(key, None)
        try:
            await event.reply(f"✅ **Sticker spam done** — {sent}/{count}")
        except Exception:
            pass

    # ── .sspamb [slots] <count> [interval] — BOTS sticker spam ──────────
    @_on(r"^\.sspamb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$")
    async def _sspamb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply or not reply.sticker:
            return await event.edit(
                "↩️ **Reply to a sticker** — `.sspamb <count> [interval]`\n"
                "specific bots: `.sspamb1-3 20 0.5`")
        arg = (event.pattern_match.group(2) or "").strip()
        count, interval, _t, err = _parse_count_interval(arg, need_text=False)
        if err == "empty":
            return await event.edit("❌ Usage: `.sspamb <count> [interval]`")
        if err == "count":
            return await event.edit("❌ Give an integer `<count>` — `.sspamb 20 0.5`")
        if err == "positive":
            return await event.edit("❌ Count must be positive.")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ No bot connected. Check `.monitorb`.")
        doc = reply.media.document
        sticker_input = InputDocument(
            id=doc.id, access_hash=doc.access_hash,
            file_reference=doc.file_reference)
        # fallback file — agar document direct na chale to ek baar download
        fallback_path = os.path.join(BC_DIR, f"stk_{event.id}.webp")
        downloaded = {"done": False}
        count = safe_cap(count)
        chat = event.chat_id
        await event.edit(
            f"🩸 **BOT STICKER SPAM** — {len(pairs)} bot(s) × {count} · `{interval}s`\n"
            "⛔ `.stop` / `.stopb`")

        async def _get_fallback():
            if downloaded["done"]:
                return fallback_path if os.path.exists(fallback_path) else None
            downloaded["done"] = True
            try:
                p = await client.download_media(reply, file=fallback_path)
                return p if p and os.path.exists(p) else None
            except Exception:
                return None

        async def _one(slot, bc):
            key = f"bc_sspam_{event.id}_{slot}"
            sent = 0
            fails = 0
            use_file = False
            try:
                for _i in range(count):
                    try:
                        if use_file:
                            fp = await _get_fallback()
                            if not fp:
                                fails += 1
                                break
                            await bc.send_file(chat, fp)
                        else:
                            await bc.send_file(chat, sticker_input)
                        sent += 1
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)
                        await asyncio.sleep(fw.seconds + 1)
                        try:
                            await bc.send_file(chat, sticker_input)
                            sent += 1
                        except Exception:
                            fails += 1
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        # document direct fail → file fallback try karo
                        use_file = True
                        fails += 1
                        if fails >= 3:
                            break
                        continue
                    if fails >= 3:
                        break
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                raise
            finally:
                client.stop_processes.pop(key, None)
            return sent

        tasks = []
        for slot, bc in pairs:
            t = asyncio.create_task(_one(slot, bc))
            client.stop_processes[f"bc_sspam_{event.id}_{slot}"] = t
            tasks.append(t)

        async def _gatherer():
            try:
                res = await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                raise
            try:
                if os.path.exists(fallback_path):
                    os.remove(fallback_path)
            except OSError:
                pass
            if any(isinstance(r, asyncio.CancelledError) for r in res):
                for slot, _bc in pairs:
                    client.stop_processes.pop(f"bc_sspam_{event.id}_{slot}", None)
                return
            total = sum(r for r in res if isinstance(r, int))
            try:
                hint = "" if total else "\n💡 0? First add the bots to the group with `.addallb`."
                await event.reply(
                    f"✅ **Bot sticker spam done** — `{total}/{count * len(pairs)}`{hint}")
            except Exception:
                pass
            for slot, _bc in pairs:
                client.stop_processes.pop(f"bc_sspam_{event.id}_{slot}", None)

        client.stop_processes[f"bc_gather_{event.id}"] = asyncio.create_task(_gatherer())

    # ── .raidb [slots] <count> [gap] [text] — BOT RAID (reply+tag) ────────
    # v7.5: `.raidb 10 .1` → 10 baar, 0.1s gap (float gap allowed)
    #       reply karke chalao → bots VICTIM ko reply + TAG dono karte hain
    @_on(r"^\.raidb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$")
    async def _raidb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        # target optional: reply → victim, warna pura chat raid
        uid = None
        uname = None
        reply = await event.get_reply_message()
        if reply:
            try:
                tent = await reply.get_input_sender()
                u = await client.get_entity(tent)
                uid = u.id
                uname = (getattr(u, "first_name", None) or getattr(u, "title", None)
                        or "User")
            except Exception:
                uid = None
                uname = None
        # ── v7.5 arg parse: <count> [gap] [text] — gap float (.1 = 100ms) ──
        arg = (event.pattern_match.group(2) or "").strip()
        count, gap, text = 10, 0.3, None
        if arg:
            parts = arg.split(maxsplit=2)
            if parts[0].isdigit():
                count = int(parts[0])
                rest = parts[1:]
                if rest:
                    try:
                        gap = float(rest[0])          # ".1" → 0.1 ✅
                        text = ((rest[1].strip() or None)
                                if len(rest) > 1 else None)
                    except ValueError:
                        gap = 0.3
                        text = " ".join(rest).strip() or None
            else:
                text = arg
        if count <= 0:
            return await event.edit("❌ Give a positive integer count — e.g. `.raidb 10 .1`")
        count = max(1, min(count, 500))
        gap = max(0.0, min(gap, 60.0))
        count = safe_cap(count)
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ No bot connected. Check `.monitorb`.")
        # raid builders — raid.py ke saath same formatting (name + text + mention)
        try:
            import importlib as _il
            _raid_mod = _il.import_module("plugins.raid")
            _builder = _raid_mod._build_raid_message
            _default_text = _raid_mod._load_raid_text()
        except Exception:
            def _builder(t, i, n):
                return f"{n} {t} <a href='tg://user?id={i}'>{n}</a>"
            _default_text = "hi"
        saved = _rm_load()
        if not text and not saved:
            text = _default_text
        chat = event.chat_id
        # reply+tag: victim ke replied message id — har raid message isi ka
        # reply hoga AUR text me mention/tag rahega (builder laga hi rahega)
        reply_to_id = None
        sender_uid = event.sender_id   # v7.6: bot-side anchor via this msg
        if uid is not None:
            reply_to_id = event.reply_to_msg_id or (reply.id if reply else None)
        src = text or "saved slots"
        whom = f"**{uname}**" if uid is not None else "**chat**"
        mode = ("reply + tag" if uid is not None else "chat raid")
        await event.edit(
            f"💥 **BOT RAID STARTED** on {whom}\n"
            f"┃ 🤖 Bots: `{len(pairs)}` · 💬 `{count}` each · ⏱ gap `{gap}s`\n"
            f"┃ 🎭 Mode: `{mode}` · 📜 text: `{src[:40]}`\n"
            f"⛔ `.stopraid` / `.stopb`")

        async def _one(slot, bc):
            key = f"bc_raid_{event.id}_{slot}"
            sent = 0
            fails = 0
            flood_retries = 0
            # v7.6: resolve the reply anchor ONCE per bot (long patience —
            # bot update delivery can lag up to ~20s); reuse it for every
            # message this bot sends in this raid.
            rid0 = None
            if uid is not None:
                rid0 = await _bot_reply_target(bc, chat, uid,
                                               owner_uid=sender_uid,
                                               prefer_owner=True, patience=20.0)
            rid = rid0
            try:
                for i in range(count):
                    raw = text if text else saved[i % len(saved)]
                    if uid is not None:
                        try:
                            msg_i = _builder(raw, uid, uname)   # reply + TAG both
                        except Exception:
                            msg_i = f"{uname} {raw} <a href='tg://user?id={uid}'>{uname}</a>"
                    else:
                        msg_i = raw
                    try:
                        await bc.send_message(chat, msg_i, parse_mode="html",
                                              link_preview=False,
                                              reply_to=rid)
                        sent += 1
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)          # 🛡 safety engine
                        flood_retries += 1
                        if flood_retries > 5:            # too heavy — bail
                            break
                        await asyncio.sleep(fw.seconds + 1)
                        try:
                            await bc.send_message(chat, msg_i, parse_mode="html",
                                                  link_preview=False,
                                                  reply_to=rid)
                            sent += 1
                        except Exception:
                            fails += 1
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        fails += 1
                    if fails >= 3:
                        break
                    await asyncio.sleep(gap)              # ⏱ user ka gap (.1 ok)
            except asyncio.CancelledError:
                raise
            finally:
                client.stop_processes.pop(key, None)
            return sent

        tasks = []
        for slot, bc in pairs:
            t = asyncio.create_task(_one(slot, bc))
            client.stop_processes[f"bc_raid_{event.id}_{slot}"] = t
            tasks.append(t)

        async def _gatherer():
            try:
                res = await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                raise
            if any(isinstance(r, asyncio.CancelledError) for r in res):
                for slot, _bc in pairs:
                    client.stop_processes.pop(f"bc_raid_{event.id}_{slot}", None)
                return
            total = sum(r for r in res if isinstance(r, int))
            per = ", ".join(
                f"{_ord(slot)}:`{r if isinstance(r, int) else 0}`"
                for (slot, _bc), r in zip(pairs, res))
            try:
                hint = "" if total else "\n💡 0? First add the bots to the group with `.addallb`."
                await event.reply(
                    f"💥 **Bot raid done** — `{total}/{count * len(pairs)}`\n"
                    f"┃ {per}{hint}")
            except Exception:
                pass
            for slot, _bc in pairs:
                client.stop_processes.pop(f"bc_raid_{event.id}_{slot}", None)

        client.stop_processes[f"bc_gather_{event.id}"] = asyncio.create_task(_gatherer())

    # ════════════════════════════════════════════════════════════════════
    #  D) ANIMATION DELEGATION ENGINE
    # ════════════════════════════════════════════════════════════════════

    async def _run_anim_bots(event, name, frames, slots_arg, secs):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        slots = _parse_slots(slots_arg, len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ No bot connected. Check `.monitorb`.")
        chat = event.chat_id
        await event.edit(
            f"🎬 **.{name}** → {len(pairs)} bot(s) par · `{secs}s`\n"
            f"⛔ `.stop` / `.stopb`")

        async def _one(slot, bc):
            key = f"bc_anim_{event.id}_{slot}"
            _TXB_SUPPRESS.add(slot)      # v7.7: apne frames khud chal rahe — TYPE-X B off for now
            try:
                start = time.time()
                msg = None
                idx = 0
                fails = 0
                while (time.time() - start) < secs:
                    frame = frames[idx % len(frames)]
                    idx += 1
                    try:
                        if msg is None:
                            msg = await bc.send_message(chat, frame,
                                                        link_preview=False)
                        else:
                            await msg.edit(frame)
                        fails = 0
                    except MessageNotModifiedError:
                        pass
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)
                        await asyncio.sleep(fw.seconds + 1)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        fails += 1
                        if fails >= 3:
                            break
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                raise
            finally:
                _TXB_SUPPRESS.discard(slot)
                client.stop_processes.pop(key, None)

        tasks = []
        for slot, bc in pairs:
            t = asyncio.create_task(_one(slot, bc))
            client.stop_processes[f"bc_anim_{event.id}_{slot}"] = t
            tasks.append(t)

        async def _gatherer():
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                raise
            try:
                await event.reply(f"🎬 **.{name}** animation done — {len(pairs)} bot(s).")
            except Exception:
                pass
            for slot, _bc in pairs:
                client.stop_processes.pop(f"bc_anim_{event.id}_{slot}", None)

        client.stop_processes[f"bc_gather_{event.id}"] = asyncio.create_task(_gatherer())

    # ── .<anim>b — SAB bots par animation ────────────────────────────────
    @_on(r"^\.([a-z]+)b(?:\s+(\d+))?$")
    async def _anim_deleg_all(event):
        base = event.pattern_match.group(1)
        if base in DELEG_EXCLUDE_BASES:
            return
        frames = _anim_frames(base)
        if not frames:
            return  # koi animation nahi (e.g. .bomb/.imdb/.web — apne handlers chalenge)
        secs = min(int(event.pattern_match.group(2) or 25), 60)
        await _run_anim_bots(event, base, frames, None, secs)

    # ── .<anim>b1-2 — SPECIFIC bots par animation ─────────────────────────
    @_on(r"^\.([a-z]+)b(\d+)(?:-(\d+))?(?:\s+(\d+))?$")
    async def _anim_deleg_range(event):
        base = event.pattern_match.group(1)
        if base in DELEG_EXCLUDE_BASES:
            return
        frames = _anim_frames(base)
        if not frames:
            return
        slots_arg = event.pattern_match.group(2)
        if event.pattern_match.group(3):
            slots_arg += "-" + event.pattern_match.group(3)
        secs = min(int(event.pattern_match.group(4) or 25), 60)
        await _run_anim_bots(event, base, frames, slots_arg, secs)

    # ════════════════════════════════════════════════════════════════════
    #  E) PROFILE — clone / revert / saved-profile / botsay
    #  v7.4 FIX: bots account.updateProfile use NAHI kar sakte (Telegram
    #  BOT_METHOD_INVALID deta hai). Isliye naam/bio BotFather automation
    #  se set hote hain, pfp MTProto uploadProfilePhoto se (wo bots kar
    #  sakte hain) + BotFather /setuserpic fallback.
    # ════════════════════════════════════════════════════════════════════

    async def _target_profile(event, reply):
        """Reply-message wale user ka (first, last, bio) nikalo."""
        try:
            tent = await reply.get_input_sender()
        except Exception:
            return None, None, None, "❌ Could not resolve the target."
        try:
            u = await client.get_entity(tent)
        except Exception:
            u = None
        first = ((getattr(u, "first_name", None) or "User"))[:64]
        last = ((getattr(u, "last_name", None) or ""))[:64]
        bio = ""
        try:
            full = await client(GetFullUserRequest(tent))
            bio = (getattr(full.full_user, "about", None) or "")[:500]
        except Exception:
            pass
        return first, last, bio, None

    async def _target_pfp(event, tent_holder):
        """Target ka DP download karo (path ya None)."""
        os.makedirs(BOT_PFP_DIR, exist_ok=True)
        target_pfp = os.path.join(BOT_PFP_DIR, f"target_{event.id}.jpg")
        try:
            photos = await client.get_profile_photos(tent_holder, limit=1)
            if photos:
                p = await client.download_media(photos[0], file=target_pfp)
                if p and os.path.exists(p):
                    return target_pfp
        except Exception:
            pass
        return None

    async def _apply_bot_profile(event, rec, first, last, bio, pfp_path,
                                 force: bool = False):
        """Ek bot par naam+bio+pfp lagao (BotFather + MTProto mix).
        force=True (.clonebi) → every failed BotFather step is retried up to
        3 times with backoff until it lands — limits are pushed through.
        Returns done-list (strings)."""
        done = []
        uname = rec.get("username") or rec.get("id")

        async def _force_step(fn, *a):
            if not force:
                return await fn(*a)
            why = ""
            for i in range(3):
                ok, why = await fn(*a)
                if ok:
                    return ok, why
                await asyncio.sleep(min(2 ** i * 2, 8))   # 2s → 4s → 8s backoff
            return False, why

        # ── NAME (BotFather — bots ke liye hi raasta) ──
        full_name = " ".join(x for x in (first, last) if x).strip()[:64] or "User"
        ok, why = await _force_step(_bf_set_bot_name, client, rec, full_name, force)
        done.append("name ✅" if ok else f"name❌ {why[:40]}")
        await asyncio.sleep(0.4)
        # ── BIO (BotFather /setdescription — bot ka "about") ──
        if bio:
            ok, why = await _force_step(_bf_set_bot_description,
                                        client, rec, bio, force)
            done.append("bio ✅" if ok else f"bio❌ {why[:40]}")
            await asyncio.sleep(0.4)
        # ── PFP (MTProto — bots uploadProfilePhoto KAR sakte hain) ──
        if pfp_path:
            bc = await _bot_client(client, _slot_of(rec), _bc_load())
            if bc is None:
                done.append("pfp❌ bot offline")
            else:
                try:
                    await _bc_clear_bot_photos(bc)
                    await asyncio.sleep(0.3)
                    up = await bc.upload_file(pfp_path)
                    await bc(UploadProfilePhotoRequest(file=up))
                    done.append("pfp ✅")
                except Exception:
                    # BotFather fallback
                    ok, why = await _force_step(_bf_set_bot_pic,
                                                client, rec, pfp_path, force)
                    done.append("pfp ✅" if ok else f"pfp❌ {why[:36]}")
        elif first:
            # v7.6: target has NO profile photo → clear the bot's photos too,
            # so the clone is 100% identical (no DP on either side).
            try:
                bc2 = await _bot_client(client, _slot_of(rec), _bc_load())
                if bc2 is not None:
                    cleared = await _bc_clear_bot_photos(bc2)
                    done.append("pfp ✅ (cleared — target has no DP)"
                                if cleared else "pfp ⚠️ clear failed")
                else:
                    done.append("pfp ⚠️ bot offline — could not clear")
            except Exception:
                done.append("pfp ⚠️ clear failed")
        return done

    def _slot_of(rec):
        """Record se 1-based slot dhundo (cloneb loop me current slot)."""
        try:
            data = _bc_load()
            for i, b in enumerate(data["bots"], 1):
                if b.get("id") == rec.get("id"):
                    return i
        except Exception:
            pass
        return 1

    async def _save_pre_clone(bc, rec, event_id):
        """pre-clone backup (sirf pehli baar — original kabhi overwrite nahi)."""
        if rec.get("pre_clone"):
            return
        pre = {"first_name": rec.get("first_name") or "Bot",
               "last_name": "", "bio": "",
               "has_photo": False, "pfp_file": None}
        try:
            bme = await bc.get_me()
            pre["first_name"] = bme.first_name or pre["first_name"]
            pre["last_name"] = bme.last_name or ""
        except Exception:
            pass
        try:
            bphotos = await bc.get_profile_photos("me", limit=1)
            if bphotos:
                fn = f"bot{_slot_of(rec)}_orig_{event_id}.jpg"
                pp = await bc.download_media(bphotos[0],
                                             file=os.path.join(BOT_PFP_DIR, fn))
                if pp and os.path.exists(pp):
                    pre["has_photo"] = True
                    pre["pfp_file"] = fn
        except Exception:
            pass
        rec["pre_clone"] = pre

    # ── .cloneb / .clonebi [slots] — bots victim ka clone banein ──────────
    # .cloneb  = normal (BotFather safety caps ON — 24 ops/hour)
    # .clonebi = IGNORE-LIMITS mode: caps bypassed, FloodWaits slept in
    #            full, every step retried until the change lands
    async def _clone_run(event, force: bool):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply:
            hint = "`.clonebi [slots]`" if force else "`.cloneb [slots]`"
            return await event.edit(f"↩️ **Reply to a user** — {hint}")
        first, last, bio, err = await _target_profile(event, reply)
        if err:
            return await event.edit(err)
        mode_txt = ("⚡ **FORCE mode** — limits ignored, changes WILL land\n"
                    "┃" if force else
                    "┃ name/bio are set via BotFather (2-4s per bot)")
        await event.edit(
            "🎭 **Bots are cloning the profile…**\n" + mode_txt)
        try:
            tent = await reply.get_input_sender()
        except Exception:
            tent = None
        pfp_path = await _target_pfp(event, tent) if tent else None
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            if pfp_path:
                try:
                    os.remove(pfp_path)
                except OSError:
                    pass
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        rows = []
        for s in slots:
            rec = bots[s - 1]
            uname = rec.get("username") or rec.get("id")
            bc = await _bot_client(client, s, data)
            if bc is None:
                rows.append(f"┃ {_ord(s)} @{uname} ❄️ frozen")
                continue
            await _save_pre_clone(bc, rec, event.id)
            done = await _apply_bot_profile(event, rec, first, last, bio,
                                            pfp_path, force=force)
            rows.append(f"┃ {_ord(s)} @{uname} ✅ {', '.join(done)}")
        _bc_save(data)
        if pfp_path:
            try:
                os.remove(pfp_path)
            except OSError:
                pass
        title = "🧨 **BOT CLONE — FORCED**" if force else "🎭 **BOT CLONE**"
        hint = ("\n┃ ♻️ Same command again = re-force any missed step\n"
                "┃ ↩️ Restore originals: `.revertb`" if force else
                "\n┃ ↩️ Restore originals: `.revertb`")
        await event.edit(
            f"✦ ━━━〔 {title} 〕━━━ ✦\n"
            f"┃ 👤 Target: `{first} {last}`\n" + "\n".join(rows) + hint +
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    @_on(r"^\.cloneb(\d+(?:-\d+)?)?\s*$")
    async def _cloneb(event):
        await _clone_run(event, force=False)

    @_on(r"^\.clonebi(\d+(?:-\d+)?)?\s*$")
    async def _clonebi(event):
        await _clone_run(event, force=True)

    # ── .revertb / .uncloneb [slots] — bots ORIGINAL state me ────────────
    @_on(r"^\.(?:revertb|uncloneb)(\d+(?:-\d+)?)?\s*$")
    async def _revertb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        await event.edit("↩️ **Reverting bots…** (BotFather automation)")
        rows = []
        for s in slots:
            rec = bots[s - 1]
            uname = rec.get("username") or rec.get("id")
            bc = await _bot_client(client, s, data)
            if bc is None:
                rows.append(f"┃ {_ord(s)} @{uname} ❄️ frozen")
                continue
            pre = rec.get("pre_clone")
            if not pre:
                rows.append(f"┃ {_ord(s)} @{uname} ⚠️ no pre-clone backup "
                            "(use `.cloneb` first)")
                continue
            done = []
            # ── NAME (BotFather) ──
            orig_name = (pre.get("first_name") or "worker")[:64]
            ok, why = await _bf_set_bot_name(client, rec, orig_name)
            done.append("name ✅" if ok else f"name❌ {why[:36]}")
            await asyncio.sleep(0.4)
            # ── PFP restore (MTProto) ──
            if pre.get("has_photo") and pre.get("pfp_file"):
                fp = os.path.join(BOT_PFP_DIR, pre["pfp_file"])
                if os.path.exists(fp):
                    try:
                        await _bc_clear_bot_photos(bc)
                        up = await bc.upload_file(fp)
                        await bc(UploadProfilePhotoRequest(file=up))
                        done.append("pfp ✅")
                    except Exception:
                        ok2, why2 = await _bf_set_bot_pic(client, rec, fp)
                        done.append("pfp ✅" if ok2 else f"pfp❌ {why2[:32]}")
                else:
                    done.append("pfp⚠️ file missing")
            elif not pre.get("has_photo"):
                # v7.4.2 FIX: pre-clone state me photo thi NAHI → cloned
                # photo revert ke baad bhi bot par lagi reh jaati thi.
                cleared = await _bc_clear_bot_photos(bc)
                done.append("pfp ✅ (cleared)" if cleared else "pfp⚠️ clear failed")
            rows.append(f"┃ {_ord(s)} @{uname} ✅ reverted ({', '.join(done)})")
        _bc_save(data)
        await event.edit(
            "✦ ━━━〔 ↩️ **BOTS REVERTED** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .loadprofileb [slots] <name> — saved profile bots par ────────────
    @_on(r"^\.loadprofileb(\d+(?:-\d+)?)?\s+(\S+)\s*$")
    async def _loadprofileb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        pname = event.pattern_match.group(2).strip()
        meta, photos, err = _load_profile_meta(pname)
        if meta is None:
            return await event.edit(f"❌ {err}")
        first = (meta.get("first_name") or "User")[:64]
        last = (meta.get("last_name") or "")[:64]
        bio = (meta.get("bio") or "")[:500]
        pfp_path = photos[0] if photos else None
        await event.edit(
            f"🎭 **Loading saved profile `{pname}` onto the bots…**")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        rows = []
        for s in slots:
            rec = bots[s - 1]
            uname = rec.get("username") or rec.get("id")
            bc = await _bot_client(client, s, data)
            if bc is None:
                rows.append(f"┃ {_ord(s)} @{uname} ❄️ frozen")
                continue
            await _save_pre_clone(bc, rec, event.id)
            done = await _apply_bot_profile(event, rec, first, last, bio, pfp_path)
            rows.append(f"┃ {_ord(s)} @{uname} ✅ {', '.join(done)}")
        _bc_save(data)
        await event.edit(
            "✦ ━━━〔 🎭 **BOT ← SAVED PROFILE** 〕━━━ ✦\n"
            f"┃ 📁 Profile: `{pname}` · 🖼 Photos: `{len(photos)}`\n"
            + "\n".join(rows) +
            "\n┃ ↩️ Undo: `.revertb`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .botsay [slots] <text> — bots se message bulwao ───────────────────
    @_on(r"^\.botsay(\d+(?:-\d+)?)?\s+([\s\S]+)$")
    async def _botsay(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        text = event.pattern_match.group(2).strip()
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ No bot connected. Check `.monitorb`.")
        chat = event.chat_id
        said = 0
        for slot, bc in pairs:
            if await _bc_send_text(bc, chat, text) is not None:
                said += 1
            await asyncio.sleep(0.4)
        await event.edit(
            f"🗣 **{said}/{len(pairs)}** bot(s) said:\n`{text[:100]}`",
            link_preview=False)

    # ── .typeb [slots] — TYPE-X BOTS ⌨️🤖 typing effect (v7.7) ─────────────
    # .typeb on/off · .typeb1-2 on · .typeb <style> · .typeb speed 0.2
    # .typeb styles / status / sync · .typeb <text> = one-shot demo
    @_on(r"^\.typeb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$")
    async def _typeb(event):
        data = _bc_load()
        bots = data["bots"]
        suffix = event.pattern_match.group(1)
        arg = (event.pattern_match.group(2) or "").strip()
        low = arg.lower()
        styles = _txb_styles()

        def _scope_txt():
            sc = _TXB_STATE.get("slots") or []
            return f"bots `{'/'.join(str(s) for s in sc)}`" if sc else "**ALL** bots"

        if not arg:
            return await event.edit(
                "✦ ━━━〔 ⌨️🤖 **TYPE-X BOTS** 〕━━━ ✦\n"
                "┃ `.typeb on` — every bot message gets the typing effect\n"
                "┃ `.typeb off` — bots send normal again\n"
                "┃ `.typeb1-2 on` — only specific bots get the effect\n"
                "┃ `.typeb <style>` — set style (`.typeb glitch`)\n"
                "┃ `.typeb speed 0.2` — frame speed (0.05–1.0s)\n"
                "┃ `.typeb styles` — 12 animation styles\n"
                "┃ `.typeb status` — mode/style/speed card\n"
                "┃ `.typeb sync` — copy style+speed from `.type`\n"
                "┃ `.typeb <text>` — one-shot: bots send text WITH effect\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━ ✦\n"
                "⚡ Works on `.spamb` `.raidb` `.botsay` `.rrb` replies\n"
                "_🛡 Flood-safe: frame cap + queue cap + storm guard_",
                link_preview=False)

        # scope forms: `.typeb 1-2 on` / `.typeb 1-2 off`
        toks = low.split()
        if (len(toks) == 2 and toks[1] in ("on", "enable", "off", "disable")
                and re.fullmatch(r"(?:all|\d+(?:-\d+)?)", toks[0])):
            if not bots:
                return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
            if toks[0] == "all":
                _TXB_STATE["slots"] = []
            else:
                _TXB_STATE["slots"] = _parse_slots(toks[0], len(bots)) or []
            if toks[1] in ("on", "enable"):
                _TXB_STATE["on"] = True
            else:
                _TXB_STATE["on"] = False
                _txb_stop_all()
            _txb_save()
            sc = _scope_txt()
            return await event.edit(
                f"✦ ━━━〔 ⌨️🤖 **TYPE-X BOTS: "
                f"{'ON' if _TXB_STATE['on'] else 'OFF'}** 〕━━━ ✦\n"
                f"┃ 🎯 Scope: {sc}\n"
                f"┃ 🎬 Style: **{_TXB_STATE['style']}** · "
                f"⚡ Speed: `{_TXB_STATE['speed']}s`",
                link_preview=False)

        if low in ("on", "enable"):
            if not bots:
                return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
            if suffix:      # .typeb1-2 on → scope wale hi bots
                _TXB_STATE["slots"] = _parse_slots(suffix, len(bots)) or []
            _TXB_STATE["on"] = True
            _txb_save()
            return await event.edit(
                "✦ ━━━〔 ⌨️🤖 **TYPE-X BOTS: ON** 〕━━━ ✦\n"
                f"✅ Every message {_scope_txt()} send(s) now gets the\n"
                "   live typewriter effect — `.spamb`, `.raidb`, `.botsay`,\n"
                "   `.rrb` replies… sab!\n\n"
                f"🎬 Style: **{_TXB_STATE['style']}** · "
                f"⚡ Speed: `{_TXB_STATE['speed']}s`\n"
                "💡 `.typeb styles` — 12 styles · `.typeb off` — off",
                link_preview=False)

        if low in ("off", "disable", "of"):
            _TXB_STATE["on"] = False
            _txb_stop_all()
            _txb_save()
            return await event.edit(
                "⏹ **TYPE-X BOTS OFF** — bots send normal messages again.\n"
                "💡 `.typeb on` — back on · `.typeb <text>` — one-shot demo",
                link_preview=False)

        if low in ("status", "info"):
            qd = sum(q.qsize() for q in _TXB_QUEUES.values())
            return await event.edit(
                "✦ ━━━〔 ⌨️🤖 **TYPE-X BOTS STATUS** 〕━━━ ✦\n"
                f"┃ Mode  : {'🟢 ON — bot messages get animated' if _TXB_STATE['on'] else '⛔ OFF'}\n"
                f"┃ Scope : {_scope_txt()} (of `{len(bots)}` registered)\n"
                f"┃ Style : **{_TXB_STATE['style']}**\n"
                f"┃ Speed : `{_TXB_STATE['speed']}s`/frame (floor `{_TXB_FLOOR}s` — bot-safe)\n"
                f"┃ Frames: ≤{_TXB_MAX_FRAMES}/message · queue ≤{_TXB_MAX_PENDING}/bot\n"
                f"┃ Queue : `{qd}` pending · 🎬 `{_TXB_DONE}` animated till now\n"
                "┃ Saved : persists across restarts ✅\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False)

        if low in ("styles", "list"):
            hints = _txb_style_hints()
            rows = "\n".join(f"┃ `{s:<10}` {hints.get(s, '')}" for s in styles)
            return await event.edit(
                f"✦ ━━━〔 ⌨️🤖 **TYPE-X BOTS STYLES ({len(styles)})** 〕━━━ ✦\n"
                f"{rows}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━ ✦\n"
                "💡 `.typeb glitch` — set · `.typeb on` — start",
                link_preview=False)

        if toks and toks[0] in ("speed", "spd") and len(toks) == 2:
            try:
                v = min(1.0, max(0.05, float(toks[1])))
            except ValueError:
                return await event.edit("❌ Speed must be a number — `.typeb speed 0.2`")
            _TXB_STATE["speed"] = v
            _txb_save()
            return await event.edit(
                f"⚡ **TYPE-X BOTS speed** → `{v}s` per frame\n"
                f"┃ 🛡 flood-floor stays `{_TXB_FLOOR}s` — ID safe",
                link_preview=False)

        if low in ("sync", "copy"):
            fun = _txb_fun()
            if fun is None:
                return await event.edit("❌ User-side TYPE-X (`.type`) not available.")
            _TXB_STATE["style"] = fun._TX_STATE.get("style", "classic")
            _TXB_STATE["speed"] = float(fun._TX_STATE.get("speed", 0.15))
            _txb_save()
            return await event.edit(
                "🔄 **Synced from `.type`** — bots now use the SAME style+speed\n"
                f"┃ 🎬 Style: **{_TXB_STATE['style']}** · "
                f"⚡ Speed: `{_TXB_STATE['speed']}s`",
                link_preview=False)

        if low in styles:
            _TXB_STATE["style"] = low
            _txb_save()
            return await event.edit(
                f"🎬 **TYPE-X BOTS style** → **{low}**\n"
                f"┃ ⚡ Speed: `{_TXB_STATE['speed']}s` · "
                f"Mode: {'ON' if _TXB_STATE['on'] else 'OFF'}\n"
                "💡 `.typeb on` — turn the effect on",
                link_preview=False)

        # ── one-shot: `.typeb <text>` — bots send <text> WITH the effect ──
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        text = arg
        slots = _parse_slots(suffix, len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ No bot connected. Check `.monitorb`.")
        chat = event.chat_id
        said = 0
        for slot, bc in pairs:
            _TXB_ONE_SHOT.add(slot)
            try:
                if await _bc_send_text(bc, chat, text) is not None:
                    said += 1
            finally:
                _TXB_ONE_SHOT.discard(slot)
            await asyncio.sleep(0.3)
        await event.edit(
            f"⌨️ **{said}/{len(pairs)}** bot(s) typed:\n`{text[:100]}`\n"
            f"┃ 🎬 one-shot · style **{_TXB_STATE['style']}**\n"
            "💡 `.typeb on` — make EVERY bot message animated",
            link_preview=False)

    # ════════════════════════════════════════════════════════════════════
    #  F) RAID MESSAGES — saverm slots (1st, 2nd, 3rd…)
    # ════════════════════════════════════════════════════════════════════

    # ── .saverm <text> — raid message slots (1st, 2nd, 3rd…) ─────────────
    @_on(r"^\.saverm(?:\s+([\s\S]+))?$")
    async def _saverm(event):
        text = event.pattern_match.group(1)
        if not text:
            # reply fallback — replied message ka text save ho jata hai
            try:
                r = await event.get_reply_message()
                if r:
                    text = getattr(r, "raw_text", None)
            except Exception:
                text = None
        if not text or not str(text).strip():
            return await event.edit(
                "📖 Usage: `.saverm <text>` — or **reply** to any message with `.saverm`")
        text = str(text).strip()[:3500]
        msgs = _rm_load()
        msgs.append(text)
        _rm_save(msgs)
        n = len(msgs)
        await event.edit(
            f"✅ **Raid message saved — {_ord(n)} slot**\n"
            f"┃ `{text[:80]}`\n"
            f"┃ 🧩 Total slots: `{n}`\n"
            f"💡 See `.listrm` · delete with `.delrm {n}` (slots auto-shift)",
            link_preview=False)

    # ── .listrm — saved raid message slots ────────────────────────────────
    @_on(r"^\.listrm$")
    async def _listrm(event):
        msgs = _rm_load()
        if not msgs:
            return await event.edit(
                "ℹ️ **No saved raid messages.**\n"
                "📖 `.saverm <text>` — saves slot 1st, then 2nd, 3rd…\n"
                "⚡ `.raid` / `.raidb` rotate through them")
        lines = "\n".join(f"┃ **{_ord(i + 1)}**: `{m[:60]}`"
                          for i, m in enumerate(msgs))
        await event.edit(
            "✦ ━━━〔 📜 **RAID MESSAGE SLOTS** 〕━━━ ✦\n" + lines +
            f"\n┃ 🧩 Total: `{len(msgs)}` · `.delrm <n>` delete\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .delrm <n> — delete + auto-shift ─────────────────────────────────
    @_on(r"^\.delrm\s+(\d+)$")
    async def _delrm(event):
        n = int(event.pattern_match.group(1))
        msgs = _rm_load()
        if n < 1 or n > len(msgs):
            return await event.edit(
                f"❌ Slot **{_ord(n)}** does not exist. Total: `{len(msgs)}`")
        removed = msgs.pop(n - 1)          # ← baaki slots automatically shift
        _rm_save(msgs)
        if msgs:
            lines = "\n".join(f"┃ **{_ord(i + 1)}**: `{m[:60]}`"
                              for i, m in enumerate(msgs))
        else:
            lines = "┃ *(empty — all deleted)*"
        await event.edit(
            f"✅ **{_ord(n)} slot delete:** `{removed[:50]}`\n"
            f"{lines}\n"
            f"┃ 🧩 Total: `{len(msgs)}`",
            link_preview=False)

    # ── .delallrm — SAB saved raid slots ek saath delete ───────────────────
    @_on(r"^\.delallrm\s*$")
    async def _delallrm(event):
        msgs = _rm_load()
        if not msgs:
            return await event.edit("ℹ️ There are no saved raid messages.")
        n = len(msgs)
        _rm_save([])
        await event.edit(
            f"🗑 **All {n} raid message slots deleted.**\n"
            "📖 Add new ones: `.saverm <text>`")

    # ════════════════════════════════════════════════════════════════════
    #  G) RRT — REPLY-RAID TURBO
    # ════════════════════════════════════════════════════════════════════

    # ── .rrt — reply-raid turbo (USER version) ────────────────────────────
    # Reply karke .rrt → jo bhi message target bheje, uske REPLY me
    # saved raid slots me se EK-EK (rotation) jata rahega.
    @_on(r"^\.rrt\s*$")
    async def _rrt(event):
        reply = await event.get_reply_message()
        if not reply:
            if not RRT_USERS and not RRT_BOTS:
                return await event.edit(
                    "📡 **Reply-Raid (RRT)**\n"
                    "┃ 📖 Reply to the target's message and send `.rrt` —\n"
                    "┃    every message they send gets a saved slot as reply\n"
                    "┃ ⚡ Short alias: `.rr` — same thing\n"
                    "┃ 🤖 `.rrtb` / `.rrb` — reply-raid via BOTS\n"
                    "┃ 📜 Fill slots with `.saverm <text>` (1st, 2nd, 3rd…)\n"
                    "┃ ♻️ `.rrt` again on the same user = toggle off\n"
                    "┃ ⛔ `.stoprrt` — stop all")
            lines = []
            for uid, st in RRT_USERS.items():
                lines.append(f"┃ 👤 `{uid}` ({st.get('name', 'User')}) — user RRT on")
            for uid, st in RRT_BOTS.items():
                lines.append(f"┃ 🤖 `{uid}` ({st.get('name', 'User')}) — bots "
                             f"{st.get('slots', [])} RRT on")
            return await event.edit(
                "✦ ━〔 📡 **RRT ACTIVE** 〕━ ✦\n" + "\n".join(lines) +
                "\n♻️ Toggle: `.rrt` again = off · ⛔ `.stoprrt` = stop all",
                link_preview=False)
        return await _rrt_arm(event, reply)

    # ── .rr — SHORT alias of .rrt (v7.5 reply raid) — same toggle
    @_on(r"^\.rr\s*$")
    async def _rr(event):
        # `.rr` = reply raid: target jo bhi message kare, saved raid
        # messages usi ke reply me ek-ek karke jayenge. Dobara = toggle off.
        return await _rrt(event)

    # ── .rrt arm engine — target resolve + TOGGLE + start card
    #    (.rrt aur .rr dono isi se chalte hain — reply-raid toggle)
    async def _rrt_arm(event, reply):
        try:
            tent = await reply.get_input_sender()
            u = await client.get_entity(tent)
            uid = u.id
            uname = (getattr(u, "first_name", None) or getattr(u, "title", None)
                     or "User")
        except Exception:
            return await event.edit("❌ Could not resolve the target.")
        if uid in RRT_USERS:
            # v7.5 TOGGLE — dobara .rrt usi user par = band
            RRT_USERS.pop(uid, None)
            _ct_save_state()
            return await event.edit(
                f"⛔ **Reply-raid STOPPED** on **{uname}** (toggle off)\n"
                "♻️ Use `.rrt` / `.rr` again on them to turn it back on",
                link_preview=False)
        # v7.6: arming reply-raid ALSO saves the replied message into the
        # raid slots — the exact message you replied with is what rotates.
        first_idx = 0
        try:
            rtext = (getattr(reply, "raw_text", "") or "").strip()
            if rtext:
                msgs = _rm_load()
                if (not msgs) or msgs[-1] != rtext:
                    msgs.append(rtext[:3500])
                    _rm_save(msgs)
                if msgs:
                    first_idx = len(msgs) - 1
        except Exception:
            first_idx = 0
        RRT_USERS[uid] = {"idx": first_idx, "name": uname}
        _ct_save_state()
        slots_n = len(_rm_load())
        await event.edit(
            f"✅ **Reply-raid STARTED** on **{uname}**\n"
            f"┃ 📜 Every message they send gets the saved slot as reply\n"
            f"┃ 🧩 Slots loaded: `{slots_n}`"
            + ("\n⚠️ 0 slots — nothing was saved, add some with `.saverm <text>`"
               if not slots_n else "") +
            "\n♻️ Toggle: `.rrt` / `.rr` again on them = off · "
            "⛔ `.stoprrt` = stop all",
            link_preview=False)


    # ── .rrtb [slots] — BOTS reply-raid turbo ────────────────────────────
    @_on(r"^\.rrtb(\d+(?:-\d+)?)?\s*$")
    async def _rrtb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots yet — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit(
                "📡 **RRT-Bots** — Reply to the target and send `.rrtb [slots]`\n"
                "┃ e.g. `.rrtb` (all bots) · `.rrtb2-3` (only 2nd-3rd)\n"
                "┃ 🤖 the bots reply to EVERY message the target sends,\n"
                "┃    one saved slot at a time\n"
                "┃ ♻️ `.rrtb` again on the same user = toggle off")
        try:
            tent = await reply.get_input_sender()
            u = await client.get_entity(tent)
            uid = u.id
            uname = (getattr(u, "first_name", None) or getattr(u, "title", None)
                     or "User")
        except Exception:
            return await event.edit("❌ Could not resolve the target.")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        # v7.5 ANTI-LOOP: target khud ARMY ka bot hai toh uska apna slot
        # replying slots se HATA do — warna wo apne hi reply par reply
        # karta rahega (infinite storm). Listener bhi guard karta hai.
        _excluded = []
        _eff = []
        for _s in slots:
            try:
                if int(bots[_s - 1].get("id", 0)) == int(uid):
                    _excluded.append(_s)
                    continue
            except Exception:
                pass
            _eff.append(_s)
        if not _eff:
            return await event.edit(
                "⚠️ **The target IS one of your bots** — no other slot given.\n"
                "┃ It would reply to its own messages in an infinite loop.\n"
                "📖 Use `.rrb` with other slots, or the user RR (`.rr`) instead")
        if _excluded:
            slots = _eff
        if uid in RRT_BOTS:
            # v7.5 TOGGLE — dobara .rrtb usi user par = band
            RRT_BOTS.pop(uid, None)
            _ct_save_state()
            return await event.edit(
                f"⛔ **BOT reply-raid STOPPED** on **{uname}** (toggle off)\n"
                "♻️ Use `.rrtb` / `.rrb` again to turn it back on")
        RRT_BOTS[uid] = {"slots": slots, "idx": {}, "name": uname}
        _ct_save_state()
        await event.edit(
            f"✅ **BOT reply-raid STARTED** on **{uname}**\n"
            f"┃ 🤖 Bots: `{len(slots)}` ({', '.join(_ord(s) for s in slots)})\n"
            f"┃ 📜 Every message the target sends gets the saved slots\n"
            "\n♻️ Toggle: `.rrtb` again = off · ⛔ `.stoprrt` = stop all",
            link_preview=False)

    # ── .rrb [slots] — SHORT alias of .rrtb (v7.5) — bots reply raid
    @_on(r"^\.rrb(\d+(?:-\d+)?)?\s*$")
    async def _rrb(event):
        # `.rrb2-3` → bots saved raid messages target ke reply me bhejein
        return await _rrtb(event)

    # ── .stoprrt — sab RRT band ────────────────────────────────────────────
    @_on(r"^\.(?:stoprrt|stoprr|rrstop)\s*$")
    async def _stoprrt(event):
        reply = await event.get_reply_message()
        target_uid = None
        if reply:
            try:
                tent = await reply.get_input_sender()
                u = await client.get_entity(tent)
                target_uid = u.id
            except Exception:
                target_uid = None
        if target_uid is not None:
            a = target_uid in RRT_USERS
            b = target_uid in RRT_BOTS
            RRT_USERS.pop(target_uid, None)
            RRT_BOTS.pop(target_uid, None)
            _ct_save_state()
            if a or b:
                return await event.edit("✅ All reply-raid for this user is now off.")
            return await event.edit("ℹ️ No reply-raid was active on this user.")
        n_users = len(RRT_USERS)
        n_bots = len(RRT_BOTS)
        RRT_USERS.clear()
        RRT_BOTS.clear()
        _ct_save_state()
        await event.edit(
            f"✅ **All RRT/RR stopped** — users: `{n_users}` · bots: `{n_bots}`")

    # ── RRT + COPY-MIRROR LISTENER — target ka har message → reply ───────
    @client.on(events.NewMessage(incoming=True))
    async def _rrt_listener(event):
        if not (RRT_USERS or RRT_BOTS or CT_STATE["targets"]
                or CT_STATE["bot_targets"]):
            return
        uid = event.sender_id
        if uid is None:
            return
        in_rrt = uid in RRT_USERS or uid in RRT_BOTS
        in_mirror = (uid in CT_STATE["targets"]
                     or uid in CT_STATE["bot_targets"])
        if not in_rrt and not in_mirror:
            return
        # guard: never mirror/reply-raid our OWN army bots (loop storm)
        try:
            _army_ids = {int(b.get("id", 0)) for b in (_bc_load().get("bots") or [])
                         if b.get("id")}
            if in_mirror and uid in _army_ids:
                return
        except Exception:
            pass
        chat_id = event.chat_id
        try:
            import importlib as _il
            _builder = _il.import_module("plugins.raid")._build_raid_message
        except Exception:
            def _builder(t, i, n):
                return f"{n} {t} <a href='tg://user?id={i}'>{n}</a>"
        pool = _rrt_pool() if in_rrt else None
        if in_rrt and not pool:
            return
        # ── user version ──
        if uid in RRT_USERS:
            st = RRT_USERS[uid]
            raw = pool[st.get("idx", 0) % len(pool)]
            st["idx"] = st.get("idx", 0) + 1
            try:
                msg_i = _builder(raw, uid, st.get("name") or "User")
            except Exception:
                msg_i = f"{st.get('name', 'User')} {raw}"
            try:
                await client.send_message(chat_id, msg_i, reply_to=event.id,
                                          parse_mode="html", link_preview=False)
            except FloodWaitError as fw:
                note_flood(fw.seconds)
                await asyncio.sleep(fw.seconds + 1)
                try:
                    await client.send_message(chat_id, msg_i, reply_to=event.id,
                                              parse_mode="html", link_preview=False)
                except Exception as e2:
                    log.warning("[botcontroller] RR-user retry fail: %s",
                                str(e2)[:100])
            except Exception as e:
                log.warning("[botcontroller] RR-user send fail: %s: %s",
                            type(e).__name__, str(e)[:100])
        # ── bots version ──
        if uid in RRT_BOTS:
            st = RRT_BOTS[uid]
            idxs = st.setdefault("idx", {})
            data = _bc_load()
            # v7.6 ANTI-LOOP GUARD (fixed): skip ONLY if the sender is one of
            # the REPLYING slot bots — their replies must never be answered
            # again (infinite storm). Messages from ANY OTHER army bot are
            # fine: `.rrb` can be armed on one of your own bots as long as
            # the OTHER bots do the replying (arm already excludes the
            # target's own slot).
            try:
                _slot_ids = set()
                for _s in st.get("slots", []):
                    try:
                        _bid = int(data["bots"][_s - 1].get("id", 0))
                        if _bid:
                            _slot_ids.add(_bid)
                    except Exception:
                        pass
                if uid in _slot_ids:
                    return
            except Exception:
                pass
            for slot in st.get("slots", []):
                bc = await _bot_client(client, slot, data)
                if bc is None:
                    continue
                i = idxs.get(slot, 0)
                raw = pool[i % len(pool)]
                idxs[slot] = i + 1
                try:
                    msg_i = _builder(raw, uid, st.get("name") or "User")
                except Exception:
                    msg_i = f"{st.get('name', 'User')} {raw}"
                # v7.6: bot-side id translation for the reply header
                rid = await _bot_reply_target(bc, chat_id, uid)
                try:
                    await bc.send_message(chat_id, msg_i, reply_to=rid,
                                          parse_mode="html", link_preview=False)
                except FloodWaitError as fw:
                    note_flood(fw.seconds)
                    await asyncio.sleep(fw.seconds + 1)
                    try:
                        await bc.send_message(chat_id, msg_i, reply_to=rid,
                                              parse_mode="html", link_preview=False)
                    except Exception as e2:
                        log.warning("[botcontroller] RR-bot slot %s retry fail: "
                                    "%s: %s", slot, type(e2).__name__, str(e2)[:80])
                except Exception as e:
                    log.warning("[botcontroller] RR-bot slot %s send fail: "
                                "%s: %s", slot, type(e).__name__, str(e)[:100])
        # ── v7.6 COPY-MIRROR — userbot (normal account) version ──
        if uid in CT_STATE["targets"]:
            try:
                await _copy_send(client, chat_id, event.message,
                                 os.path.join(BC_DIR, f"ctm_{event.id}"),
                                 reply_to=event.id)
            except FloodWaitError as fw:
                note_flood(fw.seconds)
                await asyncio.sleep(fw.seconds + 1)
            except Exception as e:
                log.warning("[botcontroller] mirror-user fail: %s: %s",
                            type(e).__name__, str(e)[:100])
        # ── v7.6 COPY-MIRROR — bots version (specific slots) ──
        if uid in CT_STATE["bot_targets"]:
            mst = CT_STATE["bot_targets"][uid]
            mdata = _bc_load()
            for mslot in mst.get("slots", []):
                mbc = await _bot_client(client, mslot, mdata)
                if mbc is None:
                    continue
                # v7.6: bot-side id translation for the reply header
                mrid = await _bot_reply_target(mbc, chat_id, uid)
                try:
                    await _copy_send(mbc, chat_id, event.message,
                                     os.path.join(BC_DIR,
                                                  f"ctmb_{event.id}_{mslot}"),
                                     reply_to=mrid, helper=client)
                except FloodWaitError as fw:
                    note_flood(fw.seconds)
                    await asyncio.sleep(fw.seconds + 1)
                except Exception as e:
                    log.warning("[botcontroller] mirror-bot slot %s fail: %s: %s",
                                mslot, type(e).__name__, str(e)[:80])
                await asyncio.sleep(0.25)

    # ════════════════════════════════════════════════════════════════════
    #  H) COPYCAT — .ct / .ctb
    # ════════════════════════════════════════════════════════════════════

    # ── v7.6 mirror-toggle engine (shared by .ct and .ctb) ───────────────
    # Reply to a user + .ct   → the USERBOT mirrors every message they send
    # Reply to a user + .ctb  → the given BOTS mirror every message they
    #                           send (specific slots: .ctb1-2). Repeat = off.
    async def _ct_mirror_toggle(event, reply, slots_arg):
        try:
            tent = await reply.get_input_sender()
            u = await client.get_entity(tent)
            uid = u.id
            uname = (getattr(u, "first_name", None) or getattr(u, "title", None)
                     or "User")
        except Exception:
            return await event.edit("❌ Could not resolve the target user.")
        if slots_arg is None:
            # ── userbot mirror (normal account) ──
            if uid in CT_STATE["targets"]:
                CT_STATE["targets"].pop(uid, None)
                _ct_save_state()
                return await event.edit(
                    f"⛔ **COPY-MIRROR OFF** — **{uname}** (toggle off)\n"
                    "🪞 Their messages are no longer copied. "
                    "Reply + `.ct` again to re-enable.",
                    link_preview=False)
            CT_STATE["targets"][uid] = uname
            _ct_save_state()
            return await event.edit(
                f"🪞 **COPY-MIRROR ON** — **{uname}**\n"
                "┃ 📜 EVERY message they send (text, sticker, photo, media…)\n"
                "┃ is re-sent here same-to-same, right away.\n"
                "┃ ♻️ Toggle: reply + `.ct` again on them = off · "
                "`.stopct` = stop all",
                link_preview=False)
        # ── bots mirror (specific slots) ──
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots registered — `.addbottoken <token>`.")
        slots = _parse_slots(slots_arg, len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        # anti-loop: never let a bot mirror itself (infinite storm guard)
        eff = []
        for s in slots:
            try:
                if int(bots[s - 1].get("id", 0)) == int(uid):
                    continue
            except Exception:
                pass
            eff.append(s)
        if not eff:
            return await event.edit(
                "⚠️ **That target IS one of your bots** — mirroring it by "
                "itself would loop forever. Pick other slots.")
        slots = eff
        if uid in CT_STATE["bot_targets"]:
            CT_STATE["bot_targets"].pop(uid, None)
            _ct_save_state()
            return await event.edit(
                f"⛔ **BOT COPY-MIRROR OFF** — **{uname}** (toggle off)\n"
                "🪞 Reply + `.ctb` again on them to re-enable.",
                link_preview=False)
        CT_STATE["bot_targets"][uid] = {"slots": slots, "name": uname}
        _ct_save_state()
        await event.edit(
            f"🪞 **BOT COPY-MIRROR ON** — **{uname}**\n"
            f"┃ 🤖 Bots: {', '.join(_ord(s) for s in slots)}\n"
            "┃ 📜 EVERY message they send is re-sent by the bots,\n"
            "┃ same-to-same (sticker → sticker, photo → photo…)\n"
            "┃ ♻️ Toggle: reply + `.ctb` again = off · `.stopct` = stop all",
            link_preview=False)

    # ── .ct — COPYCAT (user) ─────────────────────────────────────────────
    # reply + .ct → replied text/sticker SAME dobara | .ct on/off → mode
    @_on(r"^\.ct(?:\s+(on|off|status|copy))?\s*$")
    async def _ct(event):
        mode = (event.pattern_match.group(1) or "").strip().lower()
        reply = await event.get_reply_message()
        if mode == "copy" and reply is not None:
            # one-shot copy: re-send the replied message exactly once
            chat = await event.get_input_chat()
            ok = await _copy_send(client, chat, reply,
                                  os.path.join(BC_DIR, f"ct_{event.id}"))
            if ok:
                return await event.edit("🪞 **Copied** — the same message was sent again")
            return await event.edit("❌ Could not copy it (unsupported media?)")
        if not mode and reply is not None:
            # v7.6 MIRROR toggle: copy EVERY message this user sends,
            # same-to-same (text → text, sticker → sticker, photo → photo)
            return await _ct_mirror_toggle(event, reply, None)
        if mode == "on":
            CT_STATE["user"] = True
            _ct_save_state()
            await event.edit(
                "🪞 **COPYCAT ON (user)**\n"
                "┃ Everything YOU send (except commands) is re-sent\n"
                "┃ same-to-same in this chat\n"
                "┃ ⛔ Turn off: `.ct off`")
        elif mode == "off":
            CT_STATE["user"] = False
            CT_STATE["targets"].clear()
            _ct_save_state()
            await event.edit("🪞 **COPYCAT OFF (user)** — self mode + mirrors cleared")
        else:  # status / no-arg
            tgt = ", ".join(f"`{n}`" for n in CT_STATE["targets"].values()) or "—"
            btgt = ", ".join(f"`{v.get('name','User')}`→bots {v.get('slots')}"
                             for v in CT_STATE["bot_targets"].values()) or "—"
            await event.edit(
                f"🪞 **COPYCAT STATUS**\n"
                f"┃ 👤 Self mode: {'🟢 ON' if CT_STATE['user'] else '🔴 OFF'}\n"
                f"┃ 👤 Mirroring: {tgt}\n"
                f"┃ 🤖 Bots self: {'🟢 ON' if CT_STATE['bots'] else '🔴 OFF'}"
                + (f" (slots: {CT_STATE.get('bot_slots')})" if CT_STATE.get("bot_slots") else "") +
                f"\n┃ 🤖 Bots mirroring: {btgt}"
                "\n📖 reply+`.ct` mirror a user · `.ct on/off` self mode · "
                "`.ctb [slots]` bots mirror")

    # ── .ctb [slots] — COPYCAT BOTS (v7.6 mirror mode) ────────────────────
    # reply + .ctb [slots] → MIRROR toggle: the given bots re-send EVERY
    #                        message the target sends, same-to-same
    # reply + .ctb copy    → one-shot: bots re-send the replied message once
    # .ctb on / .ctb2-3 on → bots mirror YOUR OWN sends (self mode)
    @_on(r"^\.ctb(\d+(?:-\d+)?)?(?:\s+(on|off|status|copy))?\s*$")
    async def _ctb(event):
        data = _bc_load()
        bots = data["bots"]
        mode = (event.pattern_match.group(2) or "").strip().lower()
        slots_arg = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        if mode == "copy" and reply is not None:
            # one-shot: bots re-send the replied message exactly once
            if not bots:
                return await event.edit("🤖 No bots registered — `.addbottoken <token>`.")
            slots = _parse_slots(slots_arg, len(bots))
            if not slots:
                return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
            pairs = await _connect_bots(client, slots, data)
            if not pairs:
                return await event.edit("❄️ No bot connected. Check `.monitorb`.")
            tmp = os.path.join(BC_DIR, f"ctb_{event.id}")
            chat_id = event.chat_id
            sent, rows = 0, []
            for slot, bc in pairs:
                if await _copy_send(bc, chat_id, reply, tmp, helper=client):
                    sent += 1
                    rows.append(f"┃ {_ord(slot)} ✅")
                else:
                    rows.append(f"┃ {_ord(slot)} ❌")
                await asyncio.sleep(0.3)
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            return await event.edit(
                f"🪞 **Bots copied it** — `{sent}/{len(pairs)}`\n" + "\n".join(rows))
        if not mode and reply is not None:
            # v7.6: bots MIRROR this user (specific slots, e.g. `.ctb1-2`)
            return await _ct_mirror_toggle(event, reply, slots_arg)
        if mode == "off":
            CT_STATE["bots"] = False
            CT_STATE["bot_slots"] = None
            CT_STATE["bot_targets"].clear()
            _ct_save_state()
            return await event.edit(
                "🪞 **COPYCAT OFF (bots)** — self mode + bot mirrors cleared")
        if not bots and mode != "status":
            return await event.edit("🤖 No bots registered — `.addbottoken <token>`.")
        if slots_arg or mode == "on":
            slots = _parse_slots(slots_arg, len(bots))
            if not slots:
                return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
            CT_STATE["bots"] = True
            CT_STATE["bot_slots"] = slots
            _ct_save_state()
            return await event.edit(
                f"🪞 **COPYCAT ON (bots — self mode)**\n"
                f"┃ 🤖 Bots: {', '.join(_ord(s) for s in slots)}\n"
                "┃ Everything you send (except commands) the bots also\n"
                "┃ send same-to-same in this chat\n"
                "┃ ⛔ Turn off: `.ctb off`")
        # status / no-arg
        tgt = ", ".join(f"`{n}`" for n in CT_STATE["targets"].values()) or "—"
        btgt = ", ".join(f"`{v.get('name','User')}`→bots {v.get('slots')}"
                         for v in CT_STATE["bot_targets"].values()) or "—"
        await event.edit(
            f"🪞 **COPYCAT STATUS**\n"
            f"┃ 👤 Self mode: {'🟢 ON' if CT_STATE['user'] else '🔴 OFF'}\n"
            f"┃ 👤 Mirroring: {tgt}\n"
            f"┃ 🤖 Bots self: {'🟢 ON' if CT_STATE['bots'] else '🔴 OFF'}"
            + (f" (slots: {CT_STATE.get('bot_slots')})" if CT_STATE.get("bot_slots") else "") +
            f"\n┃ 🤖 Bots mirroring: {btgt}"
            "\n📖 reply+`.ctb [slots]` mirror a user via bots · "
            "`.ctb on` self mode · `.ctb off`")

    # ── COPYCAT LISTENER — outgoing (user + bots) ─────────────────────────
    @client.on(events.NewMessage(outgoing=True))
    async def _copycat_listener(event):
        if not (CT_STATE["user"] or CT_STATE["bots"]):
            return
        msg = event.message
        if msg.id in _COPY_SEEN:
            return
        text = (msg.text or getattr(msg, "raw_text", "") or "")
        is_sticker = bool(event.sticker)
        has_media = bool(event.media) or bool(event.file)
        if text:
            t = text.strip()
            if t.startswith(".") or t.startswith("/") or t.startswith("!"):
                return
        elif not (is_sticker or has_media):
            return
        # ── user copy ──
        if CT_STATE["user"]:
            try:
                chat = await event.get_input_chat()
                if text:
                    m = await client.send_message(chat, text, link_preview=False)
                else:
                    m = await client.send_file(chat, event.file)
                _COPY_SEEN.add(m.id)
                if len(_COPY_SEEN) > _COPY_CAP:
                    _COPY_SEEN.clear()
            except FloodWaitError as fw:
                note_flood(fw.seconds)
            except Exception:
                pass
        # ── bots copy ──
        if CT_STATE["bots"]:
            data = _bc_load()
            bots = data["bots"]
            if not bots:
                return
            slots = CT_STATE.get("bot_slots") or list(range(1, len(bots) + 1))
            chat_id = event.chat_id
            tmp_path = os.path.join(BC_DIR, f"ct_{event.id}")
            for slot in slots:
                bc = await _bot_client(client, slot, data)
                if bc is None:
                    continue
                try:
                    await _copy_send(bc, chat_id, msg, tmp_path, helper=client)
                except FloodWaitError as fw:
                    note_flood(fw.seconds)
                    await asyncio.sleep(fw.seconds + 1)
                except Exception:
                    pass
                await asyncio.sleep(0.2)
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    # ════════════════════════════════════════════════════════════════════
    #  I) STOP SYSTEM — har attack ka dedicated stop
    # ════════════════════════════════════════════════════════════════════

    # ── .stopb — sab bot tasks STOP ───────────────────────────────────────
    @_on(r"^\.stopb\s*$")
    async def _stopb(event):
        killed = _kill_tasks(client, lambda k: k.startswith("bc_"))
        await event.edit(
            f"⏹ **{killed}** bot task(s) stopped.\n"
            "💡 Bot sessions are saved — `.spamb` / `.raidb` will run instantly next time.")

    # ── .spamstop — text spam tasks ────────────────────────────────────────
    @_on(r"^\.spamstop\s*$")
    async def _spamstop(event):
        killed = _kill_tasks(client, lambda k: "spam" in k and "sspam" not in k)
        await event.edit(f"⏹ **{killed}** spam task(s) stopped. 🛡️")

    # ── .sspamstop — sticker spam tasks ───────────────────────────────────
    @_on(r"^\.sspamstop\s*$")
    async def _sspamstop(event):
        killed = _kill_tasks(client, lambda k: "sspam" in k)
        await event.edit(f"⏹ **{killed}** sticker-spam task(s) stopped. 🛡️")

    # ── .stopraid / .raidstop — raid tasks + RRT band ─────────────────────
    @_on(r"^\.(?:stopraid|raidstop)\s*$")
    async def _stopraid(event):
        killed = _kill_tasks(client, lambda k: "raid" in k)
        n_r = len(RRT_USERS) + len(RRT_BOTS)
        RRT_USERS.clear()
        RRT_BOTS.clear()
        _ct_save_state()
        await event.edit(
            f"⏹ **{killed}** raid task(s) stopped · reply-raid off: `{n_r}` 🛡️\n"
            "💡 The old `.drraid` system was removed — use `.rrt` now")

    # ── .raidbstop / .stopraidb — sirf BOT raid ──────────────────────────
    @_on(r"^\.(?:raidbstop|stopraidb)\s*$")
    async def _raidbstop(event):
        killed = _kill_tasks(client, lambda k: "bc_raid" in k)
        await event.edit(f"⏹ **{killed}** bot-raid task(s) stopped. 🛡️")

    # ── .animstop — animations stop ───────────────────────────────────────
    @_on(r"^\.animstop\s*$")
    async def _animstop(event):
        killed = _kill_tasks(client, lambda k: "anim" in k)
        await event.edit(f"⏹ **{killed}** animation task(s) stopped. 🛡️")

    # ── .stopct / .ctstop — copycat + mirrors band ────────────────────────
    @_on(r"^\.(?:stopct|ctstop)\s*$")
    async def _stopct(event):
        n_u = len(CT_STATE["targets"])
        n_b = len(CT_STATE["bot_targets"])
        CT_STATE["user"] = False
        CT_STATE["bots"] = False
        CT_STATE["bot_slots"] = None
        CT_STATE["targets"].clear()
        CT_STATE["bot_targets"].clear()
        _ct_save_state()
        await event.edit(
            f"⏹ **COPYCAT STOPPED** 🪞\n"
            f"┃ Mirrors cleared — users: `{n_u}` · bots: `{n_b}`\n"
            f"┃ Self modes: user OFF · bots OFF")

    # ── .stopall — sab kuch band (tasks + RRT + CopyCat) ──────────────────
    @_on(r"^\.stopall\s*$")
    async def _stopall(event):
        killed = _kill_tasks(client, lambda k: True)
        n_r = len(RRT_USERS) + len(RRT_BOTS)
        n_m = len(CT_STATE["targets"]) + len(CT_STATE["bot_targets"])
        RRT_USERS.clear()
        RRT_BOTS.clear()
        CT_STATE["user"] = False
        CT_STATE["bots"] = False
        CT_STATE["bot_slots"] = None
        CT_STATE["targets"].clear()
        CT_STATE["bot_targets"].clear()
        _ct_save_state()
        await event.edit(
            f"⏹ **FULL STOP** 🛑\n"
            f"┃ Tasks killed: `{killed}`\n"
            f"┃ Reply-raid off: `{n_r}` · CopyCat/mirrors off: `{n_m}`\n"
            "✦ Everything is silent now — ID kept safe")

    # ════════════════════════════════════════════════════════════════════
    #  J) UX — AUTODELETE (default ON) + SUDO management
    # ════════════════════════════════════════════════════════════════════

    # ── AUTODELETE LISTENER — naya command = pichla output khud delete ───
    # Default ON: `.help` likha → output aaya → `.help 1` likha → pichla
    # wala output khud delete ho gaya. Har chat me alag-alag track hota hai.
    # v7.5: ye hi listener COMMAND ids ko _CMD_IDS me track karta hai —
    # usse `.autodeletem <sec>` wala TIMED delete system chalta hai.
    @client.on(events.NewMessage(pattern=r"^\.[A-Za-z]"))
    async def _autodel_listener(event):
        try:
            own = bool(getattr(event, "out", False)
                       or getattr(getattr(event, "message", None), "out", False))
            sid = event.sender_id
            is_sudo_cmd = (not own) and bool(sid) and sid in _sudo_ids()
            if not (own or is_sudo_cmd):
                return
            chat_id = event.chat_id
            _cmd_track(chat_id, event.id)      # 🗑 timed-delete system
            # v7.4.2: protect_id — current command ka apna output kabhi delete nahi
            await _ad_delete_previous(client, chat_id, protect_id=event.id)
            if _AD.get("on"):
                _ad_track(chat_id, event.id)
        except Exception:
            pass

    # ── v7.5 TIMER LISTENER 1 — EDITED outputs → N sec baad khud delete ──
    # (.help card, .bchelp, start-cards — jo command message EDIT hota hai)
    @client.on(events.MessageEdited(outgoing=True))
    async def _ad_timed_edits(event):
        try:
            t = _ad_timer()
            if t <= 0:
                return
            if (event.chat_id, event.id) in _CMD_IDS:
                # timer RESET on every edit — final output hi delete hota hai
                _ad_schedule_delete(client, event.chat_id, event.id, t)
        except Exception:
            pass

    # ── v7.5 TIMER LISTENER 2 — reply-cards → N sec baad khud delete ────
    # ("spam done", "raid done" info cards jo command ke REPLY me aate hain)
    @client.on(events.NewMessage(outgoing=True))
    async def _ad_timed_cards(event):
        try:
            t = _ad_timer()
            if t <= 0:
                return
            rid = event.reply_to_msg_id
            if rid and (event.chat_id, rid) in _CMD_IDS:
                raw = (getattr(event, "raw_text", "") or "").strip()
                if raw.startswith("."):
                    return   # ye card nahi, doosra command hai
                _ad_schedule_delete(client, event.chat_id, event.id, t)
        except Exception:
            pass

    # ── .autodelete on/off/status (owner only) ────────────────────────────
    @_on(r"^\.(?:autodelete|adelete|adl)(?:\s+(on|off|status))?\s*$", sudo_ok=False)
    async def _autodelete(event):
        mode = (event.pattern_match.group(1) or "status").strip().lower()
        if mode == "on":
            _ad_set(True)
            return await event.edit(
                "🧹 **AUTO-DELETE ON** (default)\n"
                "┃ when you type a new command, the previous output\n"
                "┃ auto-deletes in the same chat — chat always clean")
        if mode == "off":
            _ad_set(False)
            _AD_LAST.clear()
            return await event.edit(
                "🧹 **AUTO-DELETE OFF** — outputs will now stay in the chat")
        await event.edit(
            f"🧹 **AUTO-DELETE: {'🟢 ON' if _AD.get('on') else '🔴 OFF'}** (default ON)\n"
            "┃ `.help` → output → `.help 1` → previous output auto-deletes\n"
            "📖 `.autodelete on` / `.autodelete off`")

    # ── .autodeletem <sec> — TIMED auto-delete (v7.5, owner only) ─────────
    # `.autodeletem 10` → har command ka output (help card, "spam done",
    # "raid done" info…) 10 second baad KHUD delete. 0/off = band.
    @_on(r"^\.(?:autodeletem|adelm|adtm)(?:\s+(\d+|on|off|status))?\s*$",
         sudo_ok=False)
    async def _autodeletem(event):
        arg = (event.pattern_match.group(1) or "status").strip().lower()
        if arg == "on":
            sec = 30
            _ad_timer_set(sec)
            return await event.edit(
                f"🗑 **AUTO-DELETE TIMER ON — `{sec}s`**\n"
                "┃ every command output now self-deletes within this time")
        if arg in ("off", "0"):
            _ad_timer_set(0)
            return await event.edit(
                "🗑 **AUTO-DELETE TIMER OFF**\n"
                "┃ outputs are no longer timer-managed — only `.autodelete`\n"
                "📖 back on: `.autodeletem 10`")
        if arg == "status":
            t = _ad_timer()
            return await event.edit(
                f"🗑 **AUTO-DELETE TIMER: {'`' + str(t) + 's`' if t else '🔴 OFF'}**\n"
                "┃ `.autodeletem <sec>` — help / spam-done / raid-done\n"
                "┃    outputs all self-delete within <sec>\n"
                "📖 e.g. `.autodeletem 10` · off: `.autodeletem off`")
        try:
            sec = int(arg)
        except ValueError:
            return await event.edit(
                "❌ Give seconds — e.g. `.autodeletem 10` (0/off = disable)")
        if sec < 3:
            return await event.edit(
                "❌ Minimum is **3 sec** (0 = off) — e.g. `.autodeletem 10`")
        sec = _ad_timer_set(sec)
        await event.edit(
            f"🗑 **AUTO-DELETE TIMER SET — `{sec}s`**\n"
            "┃ EVERY command output (help card, spam-complete,\n"
            "┃ raid-complete info) now self-deletes after that time\n"
            "┃ 🛡 only the info outputs vanish — not spam/raid messages\n"
            "📖 off: `.autodeletem off`")

    # ── .addsudo (reply ya id) — SUDO user add (owner only) ────────────────
    @_on(r"^\.addsudo(?:\s+(\d+))?\s*$", sudo_ok=False)
    async def _addsudo(event):
        uid = None
        arg = (event.pattern_match.group(1) or "").strip()
        if arg:
            uid = int(arg)
        else:
            reply = await event.get_reply_message()
            if reply:
                try:
                    tent = await reply.get_input_sender()
                    u = await client.get_entity(tent)
                    uid = u.id
                except Exception:
                    uid = None
        if not uid:
            return await event.edit(
                "📖 Reply to a user with `.addsudo`, or `.addsudo <user_id>`\n"
                "🤝 A SUDO user can then run every BOT ARMY command too")
        ids = set(_sudo_ids())
        if uid in ids:
            return await event.edit(f"ℹ️ `{uid}` is **already a sudo** user.")
        ids.add(uid)
        _sudo_save(ids)
        name = "user"
        try:
            u = await client.get_entity(uid)
            name = getattr(u, "first_name", None) or "User"
        except Exception:
            pass
        await event.edit(
            f"✅ **SUDO added:** {name} (`{uid}`)\n"
            f"┃ 🧩 Total sudos: `{len(ids)}`\n"
            "🤖 They can now also run `.spamb` `.raidb` `.cloneb` — everything")

    # ── .delsudo (reply ya id) — SUDO remove (owner only) ──────────────────
    @_on(r"^\.delsudo(?:\s+(\d+))?\s*$", sudo_ok=False)
    async def _delsudo(event):
        uid = None
        arg = (event.pattern_match.group(1) or "").strip()
        if arg:
            uid = int(arg)
        else:
            reply = await event.get_reply_message()
            if reply:
                try:
                    tent = await reply.get_input_sender()
                    u = await client.get_entity(tent)
                    uid = u.id
                except Exception:
                    uid = None
        if not uid:
            return await event.edit("📖 Reply to a user with `.delsudo`, or `.delsudo <user_id>`")
        ids = set(_sudo_ids())
        if uid not in ids:
            return await event.edit(f"ℹ️ `{uid}` is not in the sudo list.")
        ids.discard(uid)
        _sudo_save(ids)
        await event.edit(
            f"✅ **SUDO removed:** `{uid}`\n┃ 🧩 Remaining sudos: `{len(ids)}`")

    # ── .sudo <cmd> — REMOTE RELAY (v7.9) ─────────────────────────────────
    # A sudo user sends `.sudo .help` in any chat → the userbot sends the
    # command AS ITSELF and DIRECTLY DISPATCHES it through every NewMessage
    # handler. Direct dispatch is required because Telegram does NOT echo
    # own outgoing messages back to the sending connection when another
    # auth key (the owner's phone app) is online — a plain self-send would
    # never reach the outgoing handler chain. Incoming-only listener, so
    # the synthetic outgoing event can never re-trigger the relay.
    @client.on(events.NewMessage(incoming=True))
    async def _sudo_relay(event):
        try:
            sid = event.sender_id
            if not sid or sid not in _sudo_ids():
                return
            txt = (event.raw_text or "").strip()
            if not txt.startswith(".sudo "):
                return
            cmd_txt = txt[6:].strip()
            if not cmd_txt or not cmd_txt.startswith("."):
                return
            await asyncio.sleep(0.4)
            msg = await event.respond(cmd_txt[:4000])
            try:
                # refresh the message + entities so handlers get a fully
                # resolved event (server-side edit needs the exact peer)
                try:
                    fresh = await client.get_messages(event.chat_id,
                                                      ids=msg.id)
                    if fresh:
                        msg = fresh
                except Exception:
                    pass
                ent = {}
                try:
                    if _tlutils is not None:
                        ent = {int(_tlutils.get_peer_id(event.chat_id)):
                               await event.get_chat()}
                except Exception:
                    ent = {}
                from telethon.tl.types import UpdateNewMessage as _UNM
                upd = _UNM(message=msg, pts=0, pts_count=0)
                upd._entities = ent          # EventBuilderDict needs it
                client.loop.create_task(client._dispatch_update(upd))
            except Exception as e:
                log.warning("[sudo-relay] dispatch failed: %r", e)
            log.info("[sudo-relay] %s → %s (msg %s)", sid, cmd_txt[:60],
                     getattr(msg, "id", "?"))
        except Exception as e:
            log.warning("[sudo-relay] failed: %r", e)

    # ── .listsudo — sab sudo users (owner only) ───────────────────────────
    @_on(r"^\.listsudo\s*$", sudo_ok=False)
    async def _listsudo(event):
        ids = sorted(_sudo_ids())
        if not ids:
            return await event.edit(
                "👥 **No sudo users yet.**\n"
                "📖 Reply to a user with `.addsudo` — they can then control the bots too")
        rows = []
        for uid in ids:
            name = "user"
            try:
                u = await client.get_entity(uid)
                name = getattr(u, "first_name", None) or "User"
            except Exception:
                pass
            rows.append(f"┃ 👤 {name} — `{uid}`")
        await event.edit(
            "✦ ━━━〔 🛡 **SUDO USERS** 〕━━━ ✦\n" + "\n".join(rows) +
            f"\n┃ 🧩 Total: `{len(ids)}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ════════════════════════════════════════════════════════════════════
    #  K) HELP CARD + SELF-DIAGNOSIS
    # ════════════════════════════════════════════════════════════════════

    # ── .bccheck — SELF-DIAGNOSIS (kya galat hai, ek card me sab) ────────
    @_on(r"^\.bccheck\s*$")
    async def _bccheck(event):
        import platform
        try:
            import telethon as _tg
            tg_ver = getattr(_tg, "__version__", "?")
        except Exception:
            tg_ver = "?"
        rows = []

        def _mark(ok):
            return "✅" if ok else "❌"

        # 1) runtime versions
        rows.append(f"┃ 🐍 Python `{platform.python_version()}` · "
                    f"Telethon `{tg_ver}` (need ≥1.34)")

        # 2) API creds
        api_id, api_hash = _api_creds(client)
        rows.append(f"┃ 🔑 API_ID/API_HASH: "
                    f"{_mark(bool(api_id and api_hash))}"
                    + ("" if api_id and api_hash
                       else " — core/config.py ya first-run setup bharo"))

        # 3) data dirs writable
        w_ok = os.access(DATA_DIR, os.W_OK) and os.access(BC_DIR, os.W_OK)
        rows.append(f"┃ 📂 data dirs writable: {_mark(w_ok)}")

        # 4) bots registered
        data = _bc_load()
        bots = data["bots"]
        if bots:
            frozen = sum(1 for b in bots if b.get("frozen"))
            rows.append(f"┃ 🤖 Bots: `{len(bots)}` · ❄️ frozen: `{frozen}`")
        else:
            rows.append("┃ 🤖 Bots: `0` ❗ — run `.addbottoken <token>` "
                        "or `.addnewbotauto` first")

        # 5) live connect check (sirf pehle 3 bots — fast rakhne ke liye)
        if bots:
            await event.edit("🔍 **BC-CHECK:** bots connect ho rahe hain…")
            for i, rec in enumerate(bots[:3], 1):
                uname = rec.get("username") or rec.get("id")
                try:
                    bc = await asyncio.wait_for(
                        _bot_client(client, i, data), timeout=25)
                except asyncio.TimeoutError:
                    bc = None
                if bc is None:
                    err = (rec.get("frozen_error") or "connect failed")[:40]
                    rows.append(f"┃    {_ord(i)} @{uname} ❌ {err}")
                else:
                    try:
                        me = await bc.get_me()
                        rows.append(f"┃    {_ord(i)} @{uname} ✅ online "
                                    f"({me.first_name or 'Bot'})")
                    except Exception:
                        rows.append(f"┃    {_ord(i)} @{uname} ✅ online")

        # 6) states
        rows.append(f"┃ 📡 RRT: users `{len(RRT_USERS)}` · bots `{len(RRT_BOTS)}` · "
                    f"CopyCat: {'🟢' if (CT_STATE['user'] or CT_STATE['bots']) else 'off'}")
        _t = _ad_timer()
        rows.append(f"┃ 📜 Raid slots: `{len(_rm_load())}` · "
                    f"Autodelete: {'🟢 ON' if _AD.get('on') else '🔴 off'} · "
                    f"Timer: {'`' + str(_t) + 's`' if _t else 'off'} · "
                    f"Sudo: `{len(_sudo_ids())}`")
        try:
            n_tasks = len(client.stop_processes or {})
        except Exception:
            n_tasks = 0
        rows.append(f"┃ ⏳ Active tasks: `{n_tasks}`")

        await event.edit(
            "✦ ━━━〔 🩺 **BOTCONTROLLER SELF-CHECK** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n┃ 💡 If everything shows ✅ the commands are working. For any ❌"
            "\n┃    the fix hint is written on the same line."
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .bchelp — full help card ──────────────────────────────────────────
    @_on(r"^\.(?:bchelp|bch|bothelp)$")
    async def _bchelp(event):
        await event.edit(
            "✦ ━━━〔 🤖 **BOTCONTROLLER v7.6** 〕━━━ ✦\n"
            "**📐 Setup**\n"
            "┃ `.addbottoken <token>` — add a bot (1st/2nd/3rd… slot)\n"
            "┃ `.addnewbotauto [n]` — create a NEW bot via BotFather automatically\n"
            "┃ `.delbottoken` / `.delbot <n>` — delete (slots auto-shift)\n"
            "┃ `.listbots` · `.monitorb` · `.refreshb` — status\n"
            "**📥 Group**\n"
            "┃ `.addallb [slots]` — add bots (all, or `.addallb1-3`)\n"
            "┃ `.addall 1-3` — specific bots · `.removeallb` — remove all\n"
            "**🚀 Attack**\n"
            "┃ `.spamb <n> <sec> <text>` — spam (interval NO limit: 0.1 ok)\n"
            "┃ `.sspam <n> <sec>` — user sticker · `.sspamb` — bots sticker\n"
            "┃ `.raidb [slots] <n> [gap] [txt]` — bot raid (reply + tag)\n"
            "┃    `.raidb 10 .1` = 10 times, 0.1s gap (float gap ok)\n"
            "**🎭 Profile**\n"
            "┃ `.cloneb [slots]` — bots clone the victim (BotFather engine)\n"
            "┃ `.revertb [slots]` — bots back to ORIGINAL state\n"
            "┃ `.loadprofileb [slots] <name>` — load a saved profile on bots\n"
            "┃ `.botsay [slots] <text>` · `.<anim>b [slots]` (.roseb .hackb1-2)\n"
            "**⌨️🤖 TYPE-X Bots (typing effect)**\n"
            "┃ `.typeb on` / `.typeb off` — every bot message gets the\n"
            "┃    live typewriter effect (.spamb .raidb .botsay .rrb)\n"
            "┃ `.typeb1-2 on` — only specific bots · `.typeb <style>` — 12 styles\n"
            "┃ `.typeb speed 0.2` · `.typeb styles` · `.typeb status`\n"
            "┃ `.typeb sync` — copy style+speed from `.type` · `.typeb <text>` one-shot\n"
            "**📜 Raid Messages**\n"
            "┃ `.saverm <text>` — save a slot (1st, 2nd, 3rd… auto)\n"
            "┃ `.listrm` · `.delrm <n>` (auto-shift) · `.delallrm`\n"
            "**📡 Reply-Raid**\n"
            "┃ `.rrt` / `.rr` — reply-raid (userbot) — again = toggle off\n"
            "┃ `.rrtb` / `.rrb [slots]` — BOTS reply-raid (toggle)\n"
            "┃ `.stoprrt` / `.stoprr` — stop all reply-raid\n"
            "**🪞 CopyCat / Mirror**\n"
            "┃ reply+`.ct` — MIRROR that user same-to-same · `.ct copy` one-shot\n"
            "┃ reply+`.ctb [slots]` — bots mirror them · `.ctb2-3 on` self mode\n"
            "┃ `.stopct` — stop copycat + all mirrors\n"
            "**⏹ Stop System**\n"
            "┃ `.stop` · `.stopall` · `.stopb` · `.animstop`\n"
            "┃ `.spamstop` · `.sspamstop` · `.stopraid`/`.raidstop`\n"
            "┃ `.raidbstop` / `.stopraidb`\n"
            "**🛠 UX**\n"
            "┃ `.bccheck` — self-diagnosis (what's broken, in one card)\n"
            "┃ `.autodelete on/off` — previous output auto-delete (default ON)\n"
            "┃ `.autodeletem <sec>` — every output self-deletes in <sec>\n"
            "┃    (help cards, spam-done, raid-done) · off: `.autodeletem off`\n"
            "┃ `.addsudo`/`.delsudo`/`.listsudo` — give bots control to sudo users\n"
            "┃ `.fixprivacy` — repair bot privacy (bots must see group msgs)\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── v7.6 BOT PRE-WARM — connect all bots shortly after boot ─────────
    # Bots must be LISTENING from the start: they learn message ids from
    # their own updates (basic groups use per-account id sequences and bots
    # cannot read history). Pre-warming makes reply+tag work on the very
    # first command after startup, not just after the first bot command.
    async def _prewarm_bots():
        await asyncio.sleep(8)
        try:
            pdata = _bc_load()
            bots = pdata.get("bots") or []
            n = len(bots)
            for i in range(1, n + 1):
                try:
                    await _bot_client(client, i, pdata)
                except Exception:
                    pass
                await asyncio.sleep(0.6)
            log.info("[botcontroller] 🔥 bot pre-warm done (%d bots listening)", n)
        except Exception as e:
            log.warning("[botcontroller] pre-warm skipped: %s", str(e)[:90])
            return
        # ── v7.6 PRIVACY AUTO-FIX ──
        # A bot with privacy mode ENABLED never sees normal group messages
        # → no updates → no reply-target translation (tags worked, reply
        # headers silently dropped). If a connected bot has seen NOTHING
        # for a while, run ONE paced BotFather /setprivacy Disable for it.
        try:
            await asyncio.sleep(6)
            pdata = _bc_load()
            bots = pdata.get("bots") or []
            fixed = 0
            for i, rec in enumerate(bots, 1):
                try:
                    bcheck = BOT_CLIENTS.get(i)
                    if bcheck is None:
                        continue
                    _bid_chk = (await bcheck.get_me()).id
                    if _bid_chk in _PRIVACY_ATTEMPTED:
                        continue          # one attempt per boot
                    _PRIVACY_ATTEMPTED.add(_bid_chk)
                    bc_ = BOT_CLIENTS.get(i)
                    if bc_ is None:
                        continue
                    bme = await bc_.get_me()
                    seen_total = sum(len(v) for (b, _c), v in _BOT_SEEN.items()
                                     if b == bme.id)
                    if seen_total > 0:
                        rec["privacy_fixed_at"] = time.time()
                        rec["privacy_disabled"] = True
                        _bc_save(pdata)
                        continue          # receiving updates — all good
                    ok, _why = await _bf_set_bot_privacy(client, rec,
                                                         enable=False)
                    rec["privacy_fixed_at"] = time.time()
                    rec["privacy_disabled"] = bool(ok)
                    _bc_save(pdata)
                    if ok:
                        fixed += 1
                except Exception:
                    pass
            if fixed:
                log.info("[botcontroller] 🔓 privacy auto-fixed for %d bot(s) "
                         "— they will now receive group updates", fixed)
        except Exception:
            pass

    try:
        asyncio.create_task(_prewarm_bots())
    except Exception:
        pass

    # ── .fixprivacy — manual privacy repair (owner only) ────────────────
    @_on(r"^\.fixprivacy\s*$")
    async def _fixprivacy(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 No bots registered.")
        await event.edit(
            "🔓 **BotFather /setprivacy Disable** for every bot…\n"
            "┃ paced by the rate-guard (≈4s between bots, ID kept safe)")
        rows = []
        for i, rec in enumerate(bots, 1):
            ok, why = await _bf_set_bot_privacy(client, rec, enable=False)
            rec["privacy_disabled"] = bool(ok)
            rec["privacy_fixed_at"] = time.time()
            rows.append(f"┃ {_ord(i)} @{rec.get('username') or rec.get('id')} "
                        f"{'✅ privacy off' if ok else f'❌ {why[:40]}'}")
        _bc_save(data)
        await event.edit(
            "✦ ━━━〔 🔓 **BOT PRIVACY** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n┃ 📡 Privacy OFF = bots see every group message\n"
            "┃ (needed for `.rrb` reply-raid, `.ctb` mirror, `.raidb` reply)\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)


COMMANDS_BOTCONTROLLER = {
    "description": "🤖 BotController — Multi-Bot Army Command Center",
    "commands": [
        # setup
        (".addbottoken <token>", "register a bot + verify the token (1st/2nd/3rd slots)"),
        (".addnewbotauto [n]", "create a new bot via BotFather automatically (name: worker, auto username, retries)"),
        (".delbottoken / .delbot <n>", "delete a bot — slots auto-shift"),
        (".listbots / .botlist", "all bots + frozen status"),
        (".monitorb", "LIVE online/frozen check + every bot's name"),
        (".refreshb", "reconnect all bots + try to clear frozen"),
        # group
        (".addallb [slots] / .addall 1-3", "add bots to the group (all / specific)"),
        (".removeallb", "remove all bots from the group"),
        # attack
        (".spamb <n> <sec> <txt>", "all bots text spam — interval has NO lower limit"),
        (".spamb1-2 <n> <sec> <txt>", "only specific bots spam"),
        (".sspam <n> <sec>", "user sticker spam (reply)"),
        (".sspamb <n> <sec>", "bots sticker spam (reply)"),
        (".raidb [slots] <n> [gap] [txt]", "bot raid — `.raidb 10 .1` = 10x, 0.1s gap; reply+tag both (use via reply) + saved slots rotate"),
        # profile
        (".cloneb [slots]", "bots clone the replied user's profile (BotFather engine, DP logic included)"),
        (".revertb / .uncloneb [slots]", "bots back to their pre-clone (original) state"),
        (".loadprofileb [slots] <name>", "load a .saveprofile profile onto the bots"),
        (".botsay [slots] <txt>", "make the bots say something"),
        (".<anim>b [slots] [sec]", "run any animation on bots (.roseb, .hackb1-2)"),
        # type-x bots (v7.7)
        (".typeb on / off", "⌨️ TYPING EFFECT on the bot army — every bot message (.spamb/.raidb/.botsay/.rrb) gets the live typewriter animation"),
        (".typeb1-2 on / .typeb 1-2 on", "typing effect on only specific bots"),
        (".typeb <style>", "bot typing style — 12 styles (classic wave glitch scramble matrix pulse fire hearts zoom eraser reverse random)"),
        (".typeb speed 0.2", "bot typing frame speed (0.05–1.0s)"),
        (".typeb styles / status / sync", "style gallery / mode card / copy style+speed from .type"),
        (".typeb <text>", "one-shot — bots send <text> WITH the typing effect"),
        # raid messages
        (".saverm <text>", "save a raid message slot (reply works too · 1st, 2nd…)"),
        (".listrm / .delrm <n> / .delallrm", "raid message slots (auto-shift + delete all)"),
        # reply raid
        (".rrt / .rr", "reply-raid — every message the target sends gets a saved slot as reply (TOGGLE)"),
        (".rrb [slots]", "BOTS reply-raid — bots send the saved messages (toggle)"),
        (".rrtb [slots]", "same — full name version (toggle)"),
        (".stoprrt / .stoprr", "stop all reply-raid (user + bots)"),
        # copycat
        (".ct (reply) / .ct on/off", "MIRROR a user's every message same-to-same / self-copycat mode · `.ct copy` = one-shot"),
        (".ctb (reply) [slots] / .ctb on/off", "BOTS mirror a user — specific bots too (`.ctb1-2`)"),
        (".stopct / .ctstop", "stop copycat + all mirrors"),
        # stop system
        (".stop / .stopall", "stop all tasks / everything (tasks+reply-raid+copycat)"),
        (".stopb / .animstop", "bot tasks / animations stop"),
        (".spamstop / .sspamstop", "text spam / sticker spam stop"),
        (".stopraid / .raidstop", "raid tasks + reply-raid off"),
        (".raidbstop / .stopraidb", "stop only the bot raid"),
        # ux
        (".autodelete on/off", "previous command output auto-delete — DEFAULT ON"),
        (".autodeletem <sec>", "every command output self-deletes after <sec> seconds (help/spam-done/raid-done) — 0/off = disable"),
        (".addsudo / .delsudo / .listsudo", "give SUDO users control of the bots"),
        (".sudo <cmd>", "relay: run any command AS the userbot (sudo users)"),
        (".bccheck", "self-diagnosis — versions/API/bots/dirs/states in one card"),
        (".fixprivacy", "force BotFather /setprivacy Disable on all bots (reply/mirror needs it)"),
        (".bchelp / .bch / .bothelp", "this help card"),
    ],
}

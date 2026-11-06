# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: BOTCONTROLLER — 👑 v7.4.1 MULTI-BOT ARMY COMMAND CENTER
############################################################################
"""
BotController — apne MAIN account (ya SUDO users) se pura BOT ARMY control karo.

  ⚙️ SETUP
  • .addbottoken <token>     — bot register (1st/2nd/3rd… slots) + token verify
  • .addnewbotauto [n]       — BotFather se KHUD naya bot banao (name: worker,
                                username auto, 2 baar try, token auto-register)
  • .delbottoken/.delbot <n> — nth bot delete (slots auto-shift ho jate hain)
  • .listbots / .botlist     — sab bots + ❄️ frozen status
  • .monitorb                — LIVE status (kon online hai + sab ka naam)
  • .refreshb                — sab bots reconnect (frozen clear attempt)

  📥 GROUP
  • .addallb [slots]         — sab bots current group me add
  • .addall 1-3              — sirf 1st-3rd bots (single: .addall 2)
  • .removeallb              — sab bots group se remove

  🚀 ATTACK (interval ka KOI lower limit nahi — 0.1 / 0.5 sab ok)
  • .spamb <n> <sec> <text>  — sab bots text spam
  • .spamb1-2 <n> <sec> <txt>— sirf specific bots
  • .sspam <n> <sec>         — USER sticker spam (reply)
  • .sspamb <n> <sec>        — BOTS sticker spam (reply)
  • .raid [n] [text]         — user raid (saved slots rotate karte hain)
  • .raidb [slots] [n] [txt] — BOT raid (reply optional + saved slots)

  🎭 PROFILE
  • .cloneb [slots]          — bots victim ka clone (name+bio BotFather se,
                               pfp MTProto se — bot-proof, error-free)
  • .revertb/.uncloneb [slot]— bots wapas ORIGINAL (pre-clone) state me
  • .loadprofileb [slots] <name> — .saveprofile wala saved profile bots par
  • .botsay [slots] <text>   — bots se message bulwao

  🎬 ANIMATION DELEGATION
  • .<anim>b [sec]           — koi bhi animation SAB bots par (.roseb .hackb)
  • .<anim>b1-2 [sec]        — specific bots par (.roseb1-2)

  📜 RAID MESSAGES (slots 1st, 2nd, 3rd…)
  • .saverm <text>           — slot save (reply se bhi; 1st → 2nd → 3rd…)
  • .listrm                  — sab slots list
  • .delrm <n>               — slot delete (baaki AUTO-SHIFT: 4th → 3rd)
  • .delallrm                — sab slots ek saath delete

  📡 RRT — REPLY-RAID TURBO
  • .rrt                     — reply karke: target ka HAR message → reply me
                                saved slots me se ek-ek karke
  • .rrtb [slots]            — BOTS bhi wahi karein (.rrtb2-3 custom)
  • .stoprrt                 — sab RRT band (user + bots)

  🪞 COPYCAT (.ct / .ctb)
  • .ct (reply)              — replied text/sticker SAME dobara bhejo
  • .ct on/off               — jo bhi bhejoge wahi SAME dobara (mode)
  • .ctb (reply) [slots]     — BOTS replied content bhejein
  • .ctb on/off / .ctb2-3 on — bots copycat mode (custom slots)

  ⏹ STOP SYSTEM (har cheez ka stop)
  • .stop                    — sab tasks stop (builtin)
  • .stopall                 — tasks + RRT + CopyCat sab band
  • .stopb                   — sab BOT tasks stop
  • .spamstop / .sspamstop   — text spam / sticker spam stop
  • .stopraid / .raidstop    — raid tasks + RRT band
  • .raidbstop / .stopraidb  — sirf BOT raid stop
  • .animstop                — animations stop

  🛠 UX
  • .autodelete on/off       — output auto-delete system (DEFAULT ON:
                                naya command = pichla output khud delete)
  • .addsudo (reply/id)      — SUDO user add → wo bhi bots control kar sake
  • .delsudo / .listsudo     — sudo remove / list (sirf owner ke liye)
  • .bccheck                 — 🩺 self-diagnosis: versions/API creds/dirs/
                                bots/RRT/CopyCat/tasks — EK card me sab
  • .bchelp / .bch           — ye help card

  v7.4.1: command crash ho to chat me VISIBLE ❌ error reply aata hai
  (pehle flood_safe silently kha jata tha — isliye "kuch nahi hota tha").

Frozen bot = jiska token dead/revoked/deactivated — sab lists me ❄️ dikhta hai.
Bots profile change: MTProto bots account.updateProfile use NAHI kar sakte
(official limit) — isliye name/bio BotFather automation se, pfp MTProto se.
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

_AD = {"on": True}     # runtime flag (register me store se sync hota hai)
_AD_LAST = {}          # {chat_id: last_output_msg_id}


def _ad_load():
    try:
        _AD["on"] = bool(_bc_load().get("autodelete", True))
    except Exception:
        _AD["on"] = True


def _ad_set(on: bool) -> bool:
    _AD["on"] = bool(on)
    try:
        data = _bc_load()
        data["autodelete"] = bool(on)
        return _bc_save(data)
    except Exception:
        return False


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

async def _bot_client(main_client, slot: int, data: dict = None):
    """Return a CONNECTED bot client for 1-based slot, or None if it can't connect.

    On dead-token errors the bot record gets frozen=True (❄️ in lists).
    On success, frozen flag is cleared automatically.
    """
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

    if rec.get("frozen"):
        rec["frozen"] = False
        rec.pop("frozen_error", None)
        _bc_save(data)
    BOT_CLIENTS[slot] = bc
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
    "ct", "rrt", "refresh", "loadprofile", "unclone", "addnewbotauto",
}


# ─── v7.3.1 RRT (reply-raid turbo) + COPYCAT state ────────────────────────
# RRT: target user ka har message → reply me saved raid slots me se ek-ek
RRT_USERS = {}    # {uid: {"idx": int, "name": str}}
RRT_BOTS = {}     # {uid: {"slots": [int], "idx": {slot: int}, "name": str}}
# CopyCat: jo bheja wahi wapas (user + bots)
CT_STATE = {"user": False, "bots": False, "bot_slots": None}
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
        return ["kya kar rhe ho"]


# ─── bot-side low-level send helpers ─────────────────────────────────────

async def _bc_send_text(bc, chat, text, **kw):
    """Send text through a bot with FloodWait retry. Returns msg | None."""
    for _attempt in range(2):
        try:
            return await bc.send_message(chat, text, link_preview=False, **kw)
        except FloodWaitError as fw:
            note_flood(fw.seconds)
            await asyncio.sleep(fw.seconds + 1)
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

_BF = "BotFather"
_TOKEN_RE = re.compile(r"(\d{5,14}:[A-Za-z0-9_-]{25,60})")


def _gen_bot_username(base: str = "worker") -> str:
    """Auto username — hamesha 'bot' par khatam hota hai (TG rule).
    e.g. worker482913_bot"""
    digits = "".join(random.choice("0123456789") for _ in range(6))
    base = re.sub(r"[^a-z0-9_]", "", (base or "worker").lower())[:20] or "worker"
    return f"{base}{digits}_bot"


async def _bf_run(main_client, sends, timeout: int = 90):
    """BotFather conversation chalao.
    sends: [ ("text", str) | ("file", path) ] — har send ke baad response padho.
    Returns (responses: [str], error: str|None)."""
    res = []
    try:
        async with main_client.conversation(_BF, timeout=timeout) as conv:
            for kind, val in sends:
                if kind == "file":
                    await conv.send_file(val)
                else:
                    await conv.send_message(val)
                r = await conv.get_response()
                res.append((getattr(r, "raw_text", "") or "") if r else "")
        return res, None
    except Exception as e:
        return res, f"{type(e).__name__}: {e}"[:140]


def _bf_ok(text: str) -> bool:
    return "success" in text.lower() or "updated" in text.lower() or "done" in text.lower()


def _bot_selector(rec) -> str:
    """BotFather ko bot kaise bataoon — @username ya numeric id."""
    return f"@{rec['username']}" if rec.get("username") else str(rec.get("id", ""))


async def _bf_set_bot_name(main_client, rec, new_name: str):
    """Bot ka naam BotFather /setname se badlo (MTProto bots ke liye hi raasta)."""
    name = (new_name or "").strip()[:64]
    if not name:
        return False, "khali naam"
    res, err = await _bf_run(main_client, [
        ("text", "/setname"),
        ("text", _bot_selector(rec)),
        ("text", name),
    ])
    if err:
        return False, err
    last = res[-1] if res else ""
    if _bf_ok(last):
        return True, "name ✅"
    return False, last[:90] or "BotFather ne confirm nahi kiya"


async def _bf_set_bot_description(main_client, rec, bio: str):
    """Bot ka bio/description BotFather /setdescription se set karo."""
    bio = (bio or "").strip()[:500]
    if not bio:
        return False, "khali bio"
    res, err = await _bf_run(main_client, [
        ("text", "/setdescription"),
        ("text", _bot_selector(rec)),
        ("text", bio),
    ])
    if err:
        return False, err
    last = res[-1] if res else ""
    if _bf_ok(last):
        return True, "bio ✅"
    return False, last[:90] or "BotFather ne confirm nahi kiya"


async def _bf_set_bot_pic(main_client, rec, photo_path: str):
    """Bot ka pfp BotFather /setuserpic se (MTProto fail hone par fallback)."""
    if not photo_path or not os.path.exists(photo_path):
        return False, "photo file missing"
    res, err = await _bf_run(main_client, [
        ("text", "/setuserpic"),
        ("text", _bot_selector(rec)),
        ("file", photo_path),
    ])
    if err:
        return False, err
    last = res[-1] if res else ""
    if _bf_ok(last):
        return True, "pfp ✅"
    return False, last[:90] or "BotFather ne confirm nahi kiya"


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
            return None, None, "sab usernames taken — thodi der baad try karo", lines
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"[:140], lines


# ─── token verify + register (shared: .addbottoken & .addnewbotauto) ─────

async def _probe_bot_token(main_client, token: str):
    """Token verify karo → (me|None, error|None)."""
    api_id, api_hash = _api_creds(main_client)
    if not api_id or not api_hash:
        return None, "API_ID/API_HASH missing (core/config.py me bharo)"
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
        return None, "Ye token **already registered** hai"
    me, err = await _probe_bot_token(main_client, token)
    if me is None:
        if err and err.startswith("FROZEN"):
            return None, f"Token **DEAD/FROZEN** hai — `{err[7:80]}`"
        return None, f"Token connect fail — `{err or 'unknown'}`"
    if any(b.get("id") == me.id for b in data["bots"]):
        return None, f"@{me.username or me.id} **already registered** hai"
    data["bots"].append({
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
    })
    _bc_save(data)
    return me, None


def _invite_hint(e) -> str:
    """Common invite errors ka human hint (asli reason AB dikhta hai)."""
    n = type(e).__name__
    s = str(e).lower()
    if "Already" in n:
        return "already in group ✅"
    if "admin" in n.lower() or "admin" in s:
        return "❗ tum admin nahi ho — add members ki permission chahiye"
    if "peer" in s:
        return "❗ bot ko pehle /start karo (PEER_ID)"
    if "privacy" in s:
        return "❗ privacy restriction"
    if "private" in s or "banned" in s:
        return "❗ group private/banned"
    if "limit" in s or "too many" in s or "userlist" in s:
        return "❗ group limit aa gayi"
    if "kick" in s:
        return "❗ bot pehle kick hua tha"
    return f"`{n}` {str(e)[:34]}"


# ─── copy sender (.ct / .ctb one-shot) ───────────────────────────────────

async def _copy_send(cl, chat, msg, tmp_dir: str):
    """Replied message ka EXACT copy bhejo (text/sticker/photo/media).
    Returns True/False."""
    raw = (getattr(msg, "raw_text", "") or "").strip()
    media = getattr(msg, "media", None)
    if media is not None:
        try:
            kw = {"caption": raw} if raw else {}
            await cl.send_file(chat, media, **kw)
            return True
        except Exception:
            pass
        try:
            p = await cl.download_media(msg, file=tmp_dir)
            if p and os.path.exists(p):
                kw = {"caption": raw} if raw else {}
                await cl.send_file(chat, p, **kw)
                return True
        except Exception:
            pass
    if raw:
        try:
            await cl.send_message(chat, raw, link_preview=False)
            return True
        except Exception:
            return False
    return False


# ─── saved-profile loader (.loadprofileb) ────────────────────────────────

def _load_profile_meta(name: str):
    """profile.py ke .saveprofile wale profile ka meta nikalo.
    Returns (meta: dict|None, photo_files: [str], why: str|None)."""
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "", (name or "").strip())[:30]
    if not safe:
        return None, [], "naam do"
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
        return None, [], f"`{safe}` saved profile nahi mila — `.savedprofiles` dekho"
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
                            "┃ 🛠 `.bccheck` se full diagnosis chalao",
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
        await event.edit("🔍 **Token validate ho raha hai…**")
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
            "💡 `.monitorb` live status · `.addallb` group me add",
            link_preview=False)

    # ── .addnewbotauto [count] — BotFather se KHUD naya bot ─────────────
    @_on(r"^\.addnewbotauto(?:\s+(\d+))?\s*$")
    async def _addnewbotauto(event):
        count = min(int(event.pattern_match.group(1) or 1), 5)
        await event.edit(
            f"🤖 **BotFather se {count} naya bot ban raha hai…**\n"
            "┃ name: `worker` · username auto (…bot)\n"
            "┃ username na mile toh dobara try hoga")
        created, rows = [], []
        for i in range(count):
            token, uname, err, lines = await _bf_create_bot(client, "worker")
            if token is None:
                rows.append(f"┃ ❌ Bot {i + 1} fail: `{err or 'unknown'}`")
                break
            async with _bc_lock:
                me, why = await _register_bot_token(client, token)
            if me is None:
                rows.append(f"┃ ⚠️ @{uname} bana PAR register fail: {why}")
                continue
            # bot ko /start karo taaki group me add na fail ho
            try:
                await client.send_message(uname, "/start")
            except Exception:
                pass
            created.append(uname)
            total = len(_bc_load()["bots"])
            rows.append(f"┃ ✅ **{_ord(total)}** @{uname} — bana + register ho gaya")
        card = (
            "✦ ━━━〔 🤖 **AUTO-BOT CREATOR** 〕━━━ ✦\n" + "\n".join(rows) +
            f"\n┃ 🧩 Naye bots: `{len(created)}` · Total: `{len(_bc_load()['bots'])}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦\n"
            "💡 `.monitorb` check · `.addallb` group me add")
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
                    f"❌ Bot **{_ord(n)}** exist nahi karta. Total: `{len(bots)}`")
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
                                for i, b in enumerate(bots)) or "┃ *(koi bot nahi bacha)*"
        await event.edit(
            "✦ ━━━〔 🗑 **BOT REMOVED** 〕━━━ ✦\n"
            f"✅ **{_ord(n)} bot delete** — @{rec.get('username') or rec.get('id')}\n"
            f"┃ Baaki slots automatically shift ho gaye:\n{listing}\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .listbots / .botlist — sab bots + frozen ────────────────────────
    @_on(r"^\.(?:botlist|listbots)$")
    async def _listbots(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit(
                "🤖 **Koi bot registered nahi.**\n"
                "📖 `.addbottoken <token>` — @BotFather se token lo\n"
                "⚡ ya `.addnewbotauto` — BotFather khud bana dega")
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
                "🤖 Koi bot nahi — `.addbottoken <token>` ya `.addnewbotauto`.")
        await event.edit("📡 **Sab bots check ho rahe hain…**")
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
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        await event.edit("🔄 **Sab bots reconnect ho rahe hain…**")
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
            return False, "not found — bot ko pehle /start karo"
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
                "🤖 Koi bot registered nahi — `.addbottoken <token>` ya `.addnewbotauto`.")
        slots = _parse_slots(arg, len(bots))
        if not slots:
            return await event.edit(
                f"❌ Invalid slot. Total bots: `{len(bots)}` — e.g. `.addall 1-3`")
        try:
            input_chat = await event.get_input_chat()
        except Exception:
            return await event.edit("❌ Chat resolve nahi hua.")
        chat_id = event.chat_id
        await event.edit(f"📥 **{len(slots)} bot(s)** add ho rahe hain…")
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
                "e.g. `.addall 1-3` (1st-3rd) · `.addall 2` (sirf 2nd) · "
                "`.addall 1,3` — sab ke liye `.addallb`")
        await _do_addall(event, arg)

    # ── .removeallb — sab bots group se hatao ─────────────────────────────
    @_on(r"^\.removeallb$")
    async def _removeallb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot registered nahi.")
        try:
            chat = await event.get_input_chat()
        except Exception:
            return await event.edit("❌ Chat resolve nahi hua.")
        await event.edit("📤 **Bots remove ho rahe hain…**")
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
                "🤖 Koi bot nahi — `.addbottoken <token>` ya `.addnewbotauto`.")
        arg = (event.pattern_match.group(2) or "").strip()
        if not arg:
            return await event.edit(
                "📖 **Bot Spam Usage:**\n"
                "`.spamb <count> <interval> <text>` — **sab bots**\n"
                "`.spamb1-3 <count> <interval> <text>` — sirf 1st-3rd\n"
                "`.spamb2 20 0.5 hello` — sirf 2nd\n"
                "⏱ interval seconds me — **float allowed, NO lower limit** "
                "(`0.1`, `0.5`, `0` sab ok)\n"
                "⛔ Stop: `.stop` ya `.stopb`")
        count, interval, text, err = _parse_count_interval(arg, need_text=True)
        if err == "count":
            return await event.edit("❌ `<count>` integer hona chahiye.")
        if err == "positive":
            return await event.edit("❌ Count positive hona chahiye.")
        if err == "text":
            return await event.edit("❌ Text do — e.g. `.spamb 10 0.5 hello yaar`")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit(
                "❄️ Koi bhi bot connect nahi hua (sab frozen?). `.monitorb` dekho.")
        count = safe_cap(count)
        chat = event.chat_id
        await event.edit(
            f"🚀 **BOT SPAM STARTED**\n"
            f"┃ 🤖 Bots: `{len(pairs)}` · 💬 Messages: `{count}` each\n"
            f"┃ ⏱ Interval: `{interval}s` (no floor)\n"
            f"⛔ `.stop` / `.stopb` se roko")

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
                hint = "" if total else "\n💡 0 aaya? Pehle `.addallb` se bots group me add karo."
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
            return await event.edit("❌ `<count>` integer do — `.sspam 20 0.5`")
        if err == "positive":
            return await event.edit("❌ Count positive hona chahiye.")
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
            "⛔ `.stop` / `.sspamstop` se roko")
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
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply or not reply.sticker:
            return await event.edit(
                "↩️ **Reply to a sticker** — `.sspamb <count> [interval]`\n"
                "slots ke liye: `.sspamb1-3 20 0.5`")
        arg = (event.pattern_match.group(2) or "").strip()
        count, interval, _t, err = _parse_count_interval(arg, need_text=False)
        if err == "empty":
            return await event.edit("❌ `.sspamb <count> [interval]`")
        if err == "count":
            return await event.edit("❌ `<count>` integer do — `.sspamb 20 0.5`")
        if err == "positive":
            return await event.edit("❌ Count positive hona chahiye.")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ Koi bot connect nahi hua. `.monitorb` dekho.")
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
                hint = "" if total else "\n💡 0? Pehle `.addallb` se bots group me add karo."
                await event.reply(
                    f"✅ **Bot sticker spam done** — `{total}/{count * len(pairs)}`{hint}")
            except Exception:
                pass
            for slot, _bc in pairs:
                client.stop_processes.pop(f"bc_sspam_{event.id}_{slot}", None)

        client.stop_processes[f"bc_gather_{event.id}"] = asyncio.create_task(_gatherer())

    # ── .raidb [slots] [count] [text] — BOT RAID (reply OPTIONAL) ────────
    @_on(r"^\.raidb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$")
    async def _raidb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
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
        arg = (event.pattern_match.group(2) or "").strip()
        count = 10
        text = None
        if arg:
            parts = arg.split(maxsplit=1)
            if parts[0].isdigit():
                count = int(parts[0])
                text = parts[1].strip() if len(parts) > 1 else None
            else:
                text = arg
        count = max(1, min(count, 500))
        count = safe_cap(count)
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ Koi bot connect nahi hua. `.monitorb` dekho.")
        # raid builders — raid.py ke saath same formatting
        try:
            import importlib as _il
            _raid_mod = _il.import_module("plugins.raid")
            _builder = _raid_mod._build_raid_message
            _default_text = _raid_mod._load_raid_text()
        except Exception:
            def _builder(t, i, n):
                return f"{n} {t} <a href='tg://user?id={i}'>{n}</a>"
            _default_text = "kya kar rhe ho"
        saved = _rm_load()
        if not text and not saved:
            text = _default_text
        chat = event.chat_id
        src = text or "saved slots"
        whom = f"**{uname}**" if uid is not None else "**chat**"
        await event.edit(
            f"💥 **BOT RAID STARTED** on {whom}\n"
            f"┃ 🤖 Bots: `{len(pairs)}` · 💬 `{count}` each · 📜 text: `{src[:40]}`\n"
            f"⛔ `.stopraid` / `.stopb`")

        async def _one(slot, bc):
            key = f"bc_raid_{event.id}_{slot}"
            sent = 0
            fails = 0
            try:
                for i in range(count):
                    raw = text if text else saved[i % len(saved)]
                    if uid is not None:
                        try:
                            msg_i = _builder(raw, uid, uname)
                        except Exception:
                            msg_i = f"{uname} {raw}"
                    else:
                        msg_i = raw
                    try:
                        await bc.send_message(chat, msg_i, parse_mode="html",
                                              link_preview=False)
                        sent += 1
                    except FloodWaitError as fw:
                        note_flood(fw.seconds)
                        await asyncio.sleep(fw.seconds + 1)
                        try:
                            await bc.send_message(chat, msg_i, parse_mode="html",
                                                  link_preview=False)
                            sent += 1
                        except Exception:
                            fails += 1
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        fails += 1
                    if fails >= 3:
                        break
                    await asyncio.sleep(0.3)
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
                hint = "" if total else "\n💡 0? Pehle `.addallb` se bots group me add karo."
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
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        slots = _parse_slots(slots_arg, len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ Koi bot connect nahi hua. `.monitorb` dekho.")
        chat = event.chat_id
        await event.edit(
            f"🎬 **.{name}** → {len(pairs)} bot(s) par · `{secs}s`\n"
            f"⛔ `.stop` / `.stopb`")

        async def _one(slot, bc):
            key = f"bc_anim_{event.id}_{slot}"
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
            return None, None, None, "❌ Target resolve nahi hua."
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

    async def _apply_bot_profile(event, rec, first, last, bio, pfp_path):
        """Ek bot par naam+bio+pfp lagao (BotFather + MTProto mix).
        Returns done-list (strings)."""
        done = []
        uname = rec.get("username") or rec.get("id")
        # ── NAME (BotFather — bots ke liye hi raasta) ──
        full_name = " ".join(x for x in (first, last) if x).strip()[:64] or "User"
        ok, why = await _bf_set_bot_name(client, rec, full_name)
        done.append("name ✅" if ok else f"name❌ {why[:40]}")
        await asyncio.sleep(0.4)
        # ── BIO (BotFather /setdescription — bot ka "about") ──
        if bio:
            ok, why = await _bf_set_bot_description(client, rec, bio)
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
                    ok, why = await _bf_set_bot_pic(client, rec, pfp_path)
                    done.append("pfp ✅" if ok else f"pfp❌ {why[:36]}")
        elif first:
            done.append("pfp — (target ka koi dp nahi)")
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

    # ── .cloneb [slots] — bots victim ka clone banein ────────────────────
    @_on(r"^\.cloneb(\d+(?:-\d+)?)?\s*$")
    async def _cloneb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit("↩️ **Reply to a user** — `.cloneb [slots]`")
        first, last, bio, err = await _target_profile(event, reply)
        if err:
            return await event.edit(err)
        await event.edit(
            "🎭 **Bots cloning profile…**\n"
            "┃ name/bio BotFather se set ho rahe hain (2-4s per bot)")
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
            done = await _apply_bot_profile(event, rec, first, last, bio, pfp_path)
            rows.append(f"┃ {_ord(s)} @{uname} ✅ {', '.join(done)}")
        _bc_save(data)
        if pfp_path:
            try:
                os.remove(pfp_path)
            except OSError:
                pass
        await event.edit(
            "✦ ━━━〔 🎭 **BOT CLONE** 〕━━━ ✦\n"
            f"┃ 👤 Target: `{first} {last}`\n" + "\n".join(rows) +
            "\n┃ ↩️ Wapas asli roop me: `.revertb`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .revertb / .uncloneb [slots] — bots ORIGINAL state me ────────────
    @_on(r"^\.(?:revertb|uncloneb)(\d+(?:-\d+)?)?\s*$")
    async def _revertb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        await event.edit("↩️ **Bots revert ho rahe hain…** (BotFather automation)")
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
                rows.append(f"┃ {_ord(s)} @{uname} ⚠️ koi pre-clone backup nahi "
                            "(pehle `.cloneb` use karo)")
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
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        pname = event.pattern_match.group(2).strip()
        meta, photos, err = _load_profile_meta(pname)
        if meta is None:
            return await event.edit(f"❌ {err}")
        first = (meta.get("first_name") or "User")[:64]
        last = (meta.get("last_name") or "")[:64]
        bio = (meta.get("bio") or "")[:500]
        pfp_path = photos[0] if photos else None
        await event.edit(
            f"🎭 **Saved profile `{pname}` bots par load ho raha hai…**")
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
            "\n┃ ↩️ Wapas: `.revertb`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .botsay [slots] <text> — bots se message bulwao ───────────────────
    @_on(r"^\.botsay(\d+(?:-\d+)?)?\s+([\s\S]+)$")
    async def _botsay(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        text = event.pattern_match.group(2).strip()
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        pairs = await _connect_bots(client, slots, data)
        if not pairs:
            return await event.edit("❄️ Koi bot connect nahi hua. `.monitorb` dekho.")
        chat = event.chat_id
        said = 0
        for slot, bc in pairs:
            if await _bc_send_text(bc, chat, text) is not None:
                said += 1
            await asyncio.sleep(0.4)
        await event.edit(
            f"🗣 **{said}/{len(pairs)}** bot(s) ne bola:\n`{text[:100]}`",
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
                "📖 Usage: `.saverm <text>` — ya kisi message par **reply** karke `.saverm`")
        text = str(text).strip()[:3500]
        msgs = _rm_load()
        msgs.append(text)
        _rm_save(msgs)
        n = len(msgs)
        await event.edit(
            f"✅ **Raid message saved — {_ord(n)} slot**\n"
            f"┃ `{text[:80]}`\n"
            f"┃ 🧩 Total slots: `{n}`\n"
            f"💡 `.listrm` dekho · `.delrm {n}` se delete (slots auto-shift)",
            link_preview=False)

    # ── .listrm — saved raid message slots ────────────────────────────────
    @_on(r"^\.listrm$")
    async def _listrm(event):
        msgs = _rm_load()
        if not msgs:
            return await event.edit(
                "ℹ️ **Koi saved raid message nahi.**\n"
                "📖 `.saverm <text>` — slot 1st se save hota jayega\n"
                "⚡ `.raid` / `.raidb` inhi ko rotate karte hain")
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
                f"❌ Slot **{_ord(n)}** exist nahi karta. Total: `{len(msgs)}`")
        removed = msgs.pop(n - 1)          # ← baaki slots automatically shift
        _rm_save(msgs)
        if msgs:
            lines = "\n".join(f"┃ **{_ord(i + 1)}**: `{m[:60]}`"
                              for i, m in enumerate(msgs))
        else:
            lines = "┃ *(empty — sab delete ho gaye)*"
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
            return await event.edit("ℹ️ Koi saved raid message hai hi nahi.")
        n = len(msgs)
        _rm_save([])
        await event.edit(
            f"🗑 **Sab {n} raid message slots delete** ho gaye.\n"
            "📖 Naye: `.saverm <text>`")

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
                    "📡 **RRT — Reply-Raid Turbo**\n"
                    "┃ 📖 Reply karke `.rrt` — target ka har message\n"
                    "┃    reply me saved slots me se ek-ek aayega\n"
                    "┃ 🤖 `.rrtb` — same but BOTS se\n"
                    "┃ 📜 Slots `.saverm <text>` se bharo (1st, 2nd, 3rd…)\n"
                    "┃ ⛔ `.stoprrt` — sab RRT band")
            lines = []
            for uid, st in RRT_USERS.items():
                lines.append(f"┃ 👤 `{uid}` ({st.get('name', 'User')}) — user RRT on")
            for uid, st in RRT_BOTS.items():
                lines.append(f"┃ 🤖 `{uid}` ({st.get('name', 'User')}) — bots "
                             f"{st.get('slots', [])} RRT on")
            return await event.edit(
                "✦ ━〔 📡 **RRT ACTIVE** 〕━ ✦\n" + "\n".join(lines) +
                "\n⛔ `.stoprrt` se band", link_preview=False)
        try:
            tent = await reply.get_input_sender()
            u = await client.get_entity(tent)
            uid = u.id
            uname = (getattr(u, "first_name", None) or getattr(u, "title", None)
                     or "User")
        except Exception:
            return await event.edit("❌ Target resolve nahi hua.")
        if uid in RRT_USERS:
            return await event.edit(
                f"⚠️ RRT **pehle se active** hai **{uname}** pe.\n"
                "⛔ `.stoprrt` se band karo.")
        RRT_USERS[uid] = {"idx": 0, "name": uname}
        _ct_save_state()
        slots_n = len(_rm_load())
        await event.edit(
            f"✅ **RRT STARTED** on **{uname}**\n"
            f"┃ 📜 har message ka reply saved slots se aayega\n"
            f"┃ 🧩 Slots loaded: `{slots_n}`"
            + ("\n⚠️ 0 slots — `.saverm <text>` se bharo, warna default text jayega"
               if not slots_n else "") +
            "\n⛔ `.stoprrt` se band", link_preview=False)

    # ── .rrtb [slots] — BOTS reply-raid turbo ────────────────────────────
    @_on(r"^\.rrtb(\d+(?:-\d+)?)?\s*$")
    async def _rrtb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit(
                "📡 **RRT-Bots** — Reply karke `.rrtb [slots]`\n"
                "┃ e.g. `.rrtb` (sab bots) · `.rrtb2-3` (sirf 2nd-3rd)\n"
                "┃ 🤖 bots target ke HAR message ka reply denge\n"
                "┃    saved slots me se ek-ek karke")
        try:
            tent = await reply.get_input_sender()
            u = await client.get_entity(tent)
            uid = u.id
            uname = (getattr(u, "first_name", None) or getattr(u, "title", None)
                     or "User")
        except Exception:
            return await event.edit("❌ Target resolve nahi hua.")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        if uid in RRT_BOTS:
            return await event.edit(
                f"⚠️ Bot-RRT **pehle se active** hai **{uname}** pe.\n"
                "⛔ `.stoprrt` se band karo.")
        RRT_BOTS[uid] = {"slots": slots, "idx": {}, "name": uname}
        _ct_save_state()
        await event.edit(
            f"✅ **BOT-RRT STARTED** on **{uname}**\n"
            f"┃ 🤖 Bots: `{len(slots)}` ({', '.join(_ord(s) for s in slots)})\n"
            f"┃ 📜 har message ke reply me saved slots se ek-ek jayenge\n"
            "⛔ `.stoprrt` se band", link_preview=False)

    # ── .stoprrt — sab RRT band ────────────────────────────────────────────
    @_on(r"^\.stoprrt\s*$")
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
                return await event.edit("✅ Is user ke **sab RRT** band kar diye.")
            return await event.edit("ℹ️ Is user pe koi RRT active hi nahi tha.")
        n_users = len(RRT_USERS)
        n_bots = len(RRT_BOTS)
        RRT_USERS.clear()
        RRT_BOTS.clear()
        _ct_save_state()
        await event.edit(
            f"✅ **Sab RRT band** — users: `{n_users}` · bots: `{n_bots}`")

    # ── RRT LISTENER — target ka har message → reply (slots rotation) ────
    @client.on(events.NewMessage(incoming=True))
    async def _rrt_listener(event):
        if not RRT_USERS and not RRT_BOTS:
            return
        uid = event.sender_id
        if uid is None:
            return
        if uid not in RRT_USERS and uid not in RRT_BOTS:
            return
        pool = _rrt_pool()
        if not pool:
            return
        chat_id = event.chat_id
        try:
            import importlib as _il
            _builder = _il.import_module("plugins.raid")._build_raid_message
        except Exception:
            def _builder(t, i, n):
                return f"{n} {t} <a href='tg://user?id={i}'>{n}</a>"
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
                except Exception:
                    pass
            except Exception:
                pass
        # ── bots version ──
        if uid in RRT_BOTS:
            st = RRT_BOTS[uid]
            idxs = st.setdefault("idx", {})
            data = _bc_load()
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
                try:
                    await bc.send_message(chat_id, msg_i, reply_to=event.id,
                                          parse_mode="html", link_preview=False)
                except FloodWaitError as fw:
                    note_flood(fw.seconds)
                    await asyncio.sleep(fw.seconds + 1)
                    try:
                        await bc.send_message(chat_id, msg_i, reply_to=event.id,
                                              parse_mode="html", link_preview=False)
                    except Exception:
                        pass
                except Exception:
                    pass

    # ════════════════════════════════════════════════════════════════════
    #  H) COPYCAT — .ct / .ctb
    # ════════════════════════════════════════════════════════════════════

    # ── .ct — COPYCAT (user) ─────────────────────────────────────────────
    # reply + .ct → replied text/sticker SAME dobara | .ct on/off → mode
    @_on(r"^\.ct(?:\s+(on|off|status))?\s*$")
    async def _ct(event):
        mode = (event.pattern_match.group(1) or "").strip().lower()
        reply = await event.get_reply_message()
        if not mode and reply is not None:
            # one-shot copy: replied message EXACT wapas
            chat = await event.get_input_chat()
            ok = await _copy_send(client, chat, reply,
                                  os.path.join(BC_DIR, f"ct_{event.id}"))
            if ok:
                return await event.edit("🪞 **Copied** — same message dobara gaya")
            return await event.edit("❌ Copy nahi ho paya (text/sticker/media?)")
        if mode == "on":
            CT_STATE["user"] = True
            _ct_save_state()
            await event.edit(
                "🪞 **COPYCAT ON (user)**\n"
                "┃ ab tum jo bhi text/sticker bhejoge (`.commands` chhod ke)\n"
                "┃ wahi SAME cheez dobara usi chat me jayegi\n"
                "┃ ⛔ band: `.ct off`")
        elif mode == "off":
            CT_STATE["user"] = False
            _ct_save_state()
            await event.edit("🪞 **COPYCAT OFF (user)**")
        else:  # status / no-arg
            await event.edit(
                f"🪞 **COPYCAT STATUS**\n"
                f"┃ 👤 User: {'🟢 ON' if CT_STATE['user'] else '🔴 OFF'}\n"
                f"┃ 🤖 Bots: {'🟢 ON' if CT_STATE['bots'] else '🔴 OFF'}"
                + (f" (slots: {CT_STATE['bot_slots']})" if CT_STATE.get("bot_slots") else "") +
                "\n📖 reply+`.ct` ek baar copy · `.ct on/off` mode · `.ctb` bots")

    # ── .ctb [slots] — COPYCAT BOTS ───────────────────────────────────────
    # reply + .ctb → bots replied content bhejein | .ctb on/off → mode
    @_on(r"^\.ctb(\d+(?:-\d+)?)?(?:\s+(on|off|status))?\s*$")
    async def _ctb(event):
        data = _bc_load()
        bots = data["bots"]
        mode = (event.pattern_match.group(2) or "").strip().lower()
        slots_arg = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        if not mode and reply is not None:
            # one-shot: bots replied message ka copy bhejein
            if not bots:
                return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
            slots = _parse_slots(slots_arg, len(bots))
            if not slots:
                return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
            pairs = await _connect_bots(client, slots, data)
            if not pairs:
                return await event.edit("❄️ Koi bot connect nahi hua. `.monitorb` dekho.")
            tmp = os.path.join(BC_DIR, f"ctb_{event.id}")
            chat_id = event.chat_id
            sent, rows = 0, []
            for slot, bc in pairs:
                if await _copy_send(bc, chat_id, reply, tmp):
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
                f"🪞 **Bots ne copy bheja** — `{sent}/{len(pairs)}`\n" + "\n".join(rows))
        if mode == "off":
            CT_STATE["bots"] = False
            CT_STATE["bot_slots"] = None
            _ct_save_state()
            return await event.edit("🪞 **COPYCAT OFF (bots)**")
        if not bots and mode != "status":
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        if slots_arg or mode == "on":
            slots = _parse_slots(slots_arg, len(bots))
            if not slots:
                return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
            CT_STATE["bots"] = True
            CT_STATE["bot_slots"] = slots
            _ct_save_state()
            return await event.edit(
                f"🪞 **COPYCAT ON (bots)**\n"
                f"┃ 🤖 Bots: {', '.join(_ord(s) for s in slots)}\n"
                "┃ ab tum jo bhi text/sticker bhejoge (commands chhod ke)\n"
                "┃ wahi bot bhi usi chat me bhejenge\n"
                "┃ ⛔ band: `.ctb off`")
        # status / no-arg
        await event.edit(
            f"🪞 **COPYCAT STATUS**\n"
            f"┃ 👤 User: {'🟢 ON' if CT_STATE['user'] else '🔴 OFF'}\n"
            f"┃ 🤖 Bots: {'🟢 ON' if CT_STATE['bots'] else '🔴 OFF'}"
            + (f" (slots: {CT_STATE['bot_slots']})" if CT_STATE.get("bot_slots") else "") +
            "\n📖 reply+`.ctb` ek baar bots se · `.ctb on` · `.ctb2-3 on` · `.ctb off`")

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
                    await _copy_send(bc, chat_id, msg, tmp_path)
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
            "💡 Bot sessions saved — `.spamb` / `.raidb` dobara turant chalega.")

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
            f"⏹ **{killed}** raid task(s) stopped · RRT band: `{n_r}` 🛡️\n"
            "💡 `.drraid` wala system hata diya gaya — ab `.rrt` use karo")

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

    # ── .stopall — sab kuch band (tasks + RRT + CopyCat) ──────────────────
    @_on(r"^\.stopall\s*$")
    async def _stopall(event):
        killed = _kill_tasks(client, lambda k: True)
        n_r = len(RRT_USERS) + len(RRT_BOTS)
        RRT_USERS.clear()
        RRT_BOTS.clear()
        CT_STATE["user"] = False
        CT_STATE["bots"] = False
        CT_STATE["bot_slots"] = None
        _ct_save_state()
        await event.edit(
            f"⏹ **FULL STOP** 🛑\n"
            f"┃ Tasks killed: `{killed}`\n"
            f"┃ RRT band: `{n_r}` · CopyCat: OFF\n"
            "✦ sab shaant — ID safe")

    # ════════════════════════════════════════════════════════════════════
    #  J) UX — AUTODELETE (default ON) + SUDO management
    # ════════════════════════════════════════════════════════════════════

    # ── AUTODELETE LISTENER — naya command = pichla output khud delete ───
    # Default ON: `.help` likha → output aaya → `.help 1` likha → pichla
    # wala output khud delete ho gaya. Har chat me alag-alag track hota hai.
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.[A-Za-z]"))
    async def _autodel_listener(event):
        try:
            chat_id = event.chat_id
            # v7.4.2: protect_id — current command ka apna output kabhi delete nahi
            await _ad_delete_previous(client, chat_id, protect_id=event.id)
            if _AD.get("on"):
                _ad_track(chat_id, event.id)
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
                "┃ naya command likhoge toh pichle command ka output\n"
                "┃ usi chat me KHUD delete ho jayega — chat hamesha saaf")
        if mode == "off":
            _ad_set(False)
            _AD_LAST.clear()
            return await event.edit(
                "🧹 **AUTO-DELETE OFF** — ab outputs chat me rukenge")
        await event.edit(
            f"🧹 **AUTO-DELETE: {'🟢 ON' if _AD.get('on') else '🔴 OFF'}** (default ON)\n"
            "┃ `.help` → output → `.help 1` → pichla output auto-delete\n"
            "📖 `.autodelete on` / `.autodelete off`")

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
                "📖 Reply karke `.addsudo` ya `.addsudo <user_id>`\n"
                "🤝 SUDO user bhi sab BOT ARMY commands chala sakta hai")
        ids = set(_sudo_ids())
        if uid in ids:
            return await event.edit(f"ℹ️ `{uid}` **pehle se sudo** hai.")
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
            "🤖 Ab ye bhi `.spamb` `.raidb` `.cloneb` sab chala sakta hai")

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
            return await event.edit("📖 Reply karke `.delsudo` ya `.delsudo <user_id>`")
        ids = set(_sudo_ids())
        if uid not in ids:
            return await event.edit(f"ℹ️ `{uid}` sudo list me hai hi nahi.")
        ids.discard(uid)
        _sudo_save(ids)
        await event.edit(
            f"✅ **SUDO removed:** `{uid}`\n┃ 🧩 Baaki sudos: `{len(ids)}`")

    # ── .listsudo — sab sudo users (owner only) ───────────────────────────
    @_on(r"^\.listsudo\s*$", sudo_ok=False)
    async def _listsudo(event):
        ids = sorted(_sudo_ids())
        if not ids:
            return await event.edit(
                "👥 **Koi sudo user nahi.**\n"
                "📖 Reply karke `.addsudo` — phir wo bhi bots control karega")
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
            rows.append("┃ 🤖 Bots: `0` ❗ — pehle `.addbottoken <token>` "
                        "ya `.addnewbotauto` chalao")

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
        rows.append(f"┃ 📜 Raid slots: `{len(_rm_load())}` · "
                    f"Autodelete: {'🟢 ON' if _AD.get('on') else '🔴 off'} · "
                    f"Sudo: `{len(_sudo_ids())}`")
        try:
            n_tasks = len(client.stop_processes or {})
        except Exception:
            n_tasks = 0
        rows.append(f"┃ ⏳ Active tasks: `{n_tasks}`")

        await event.edit(
            "✦ ━━━〔 🩺 **BOTCONTROLLER SELF-CHECK** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n┃ 💡 Agar sab ✅ hai → commands chal rahe hain. Jo ❌ hai"
            "\n┃    uska hint usi line me likha hai."
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .bchelp — full help card ──────────────────────────────────────────
    @_on(r"^\.(?:bchelp|bch|bothelp)$")
    async def _bchelp(event):
        await event.edit(
            "✦ ━━━〔 🤖 **BOTCONTROLLER v7.4.1** 〕━━━ ✦\n"
            "**📐 Setup**\n"
            "┃ `.addbottoken <token>` — bot add (1st/2nd/3rd…)\n"
            "┃ `.addnewbotauto [n]` — BotFather se KHUD naya bot banao\n"
            "┃ `.delbottoken` / `.delbot <n>` — delete (slots auto-shift)\n"
            "┃ `.listbots` · `.monitorb` · `.refreshb` — status\n"
            "**📥 Group**\n"
            "┃ `.addallb [slots]` — bots add (sab ya `.addallb1-3`)\n"
            "┃ `.addall 1-3` — specific bots · `.removeallb` — sab remove\n"
            "**🚀 Attack**\n"
            "┃ `.spamb <n> <sec> <text>` — spam (interval NO limit: 0.1 ok)\n"
            "┃ `.sspam <n> <sec>` — user sticker · `.sspamb` — bots sticker\n"
            "┃ `.raidb [slots] <n> <txt>` — bot raid (reply optional)\n"
            "**🎭 Profile**\n"
            "┃ `.cloneb [slots]` — bots victim ka clone (BotFather engine)\n"
            "┃ `.revertb [slots]` — bots ORIGINAL me wapas\n"
            "┃ `.loadprofileb [slots] <name>` — saved profile bots par\n"
            "┃ `.botsay [slots] <text>` · `.<anim>b [slots]` (.roseb .hackb1-2)\n"
            "**📜 Raid Messages**\n"
            "┃ `.saverm <text>` — slot save (1st, 2nd, 3rd… auto)\n"
            "┃ `.listrm` · `.delrm <n>` (auto-shift) · `.delallrm`\n"
            "**📡 RRT**\n"
            "┃ `.rrt` / `.rrtb [slots]` — reply-raid turbo (user + bots)\n"
            "┃ `.stoprrt` — sab RRT band\n"
            "**🪞 CopyCat**\n"
            "┃ reply+`.ct` — same message wapas · `.ct on/off` mode\n"
            "┃ reply+`.ctb [slots]` — bots copy · `.ctb2-3 on` custom bots\n"
            "**⏹ Stop System**\n"
            "┃ `.stop` · `.stopall` · `.stopb` · `.animstop`\n"
            "┃ `.spamstop` · `.sspamstop` · `.stopraid`/`.raidstop`\n"
            "┃ `.raidbstop` / `.stopraidb`\n"
            "**🛠 UX**\n"
            "┃ `.bccheck` — self-diagnosis (kya kharab hai, ek card me)\n"
            "┃ `.autodelete on/off` — pichla output auto-delete (default ON)\n"
            "┃ `.addsudo`/`.delsudo`/`.listsudo` — bots ka control sudo ko do\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)


COMMANDS_BOTCONTROLLER = {
    "description": "🤖 BotController — Multi-Bot Army Command Center",
    "commands": [
        # setup
        (".addbottoken <token>", "bot register + token verify (1st/2nd/3rd slots)"),
        (".addnewbotauto [n]", "BotFather se khud naya bot banao (name: worker, auto username, 2 try)"),
        (".delbottoken / .delbot <n>", "bot delete — slots auto-shift"),
        (".listbots / .botlist", "sab bots + frozen status"),
        (".monitorb", "LIVE online/frozen check + sab ka naam"),
        (".refreshb", "sab bots reconnect + frozen clear attempt"),
        # group
        (".addallb [slots] / .addall 1-3", "bots group me add (sab / specific) — ImportError FIXED"),
        (".removeallb", "sab bots group se remove"),
        # attack
        (".spamb <n> <sec> <txt>", "sab bots text spam — interval NO lower limit"),
        (".spamb1-2 <n> <sec> <txt>", "sirf specific bots spam"),
        (".sspam <n> <sec>", "user sticker spam (reply)"),
        (".sspamb <n> <sec>", "bots sticker spam (reply)"),
        (".raidb [slots] <n> <txt>", "bot raid — reply optional + saved slots rotate"),
        # profile
        (".cloneb [slots]", "bots replied-user ka profile clone karein (BotFather engine)"),
        (".revertb / .uncloneb [slots]", "bots wapas pre-clone (original) state me"),
        (".loadprofileb [slots] <name>", ".saveprofile wala saved profile bots par load"),
        (".botsay [slots] <txt>", "bots se message bulwao"),
        (".<anim>b [slots] [sec]", "koi bhi animation bots par (.roseb, .hackb1-2)"),
        # raid messages
        (".saverm <text>", "raid message slot save (reply se bhi · 1st, 2nd…)"),
        (".listrm / .delrm <n> / .delallrm", "raid message slots (auto-shift + sab delete)"),
        # rrt
        (".rrt", "reply-raid turbo — target ka har message reply me saved slots se ek-ek"),
        (".rrtb [slots]", "BOTS bhi reply-raid karein (custom slots ok)"),
        (".stoprrt", "sab RRT band (user + bots)"),
        # copycat
        (".ct (reply) / .ct on/off", "COPYCAT — same message wapas / mode"),
        (".ctb (reply) [slots] / .ctb on/off", "BOTS copycat — custom bots bhi"),
        # stop system
        (".stop / .stopall", "sab tasks / sab kuch band (tasks+RRT+CopyCat)"),
        (".stopb / .animstop", "bot tasks / animations stop"),
        (".spamstop / .sspamstop", "text spam / sticker spam stop"),
        (".stopraid / .raidstop", "raid tasks + RRT band"),
        (".raidbstop / .stopraidb", "sirf bot raid stop"),
        # ux
        (".autodelete on/off", "pichla command output auto-delete — DEFAULT ON"),
        (".addsudo / .delsudo / .listsudo", "bots ka control SUDO users ko do"),
        (".bccheck", "self-diagnosis — versions/API/bots/dirs/st Sab ek card me"),
        (".bchelp / .bch / .bothelp", "ye help card"),
    ],
}

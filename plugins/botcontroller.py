# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: BOTCONTROLLER — 👑 v7.3 MULTI-BOT ARMY COMMAND CENTER
############################################################################
"""
BotController — apne MAIN account se pura BOT ARMY control karo.

  • .addbottoken <token>    — bot register (1st/2nd/3rd… slots)
  • .delbottoken <n>         — nth bot delete (slots auto-shift ho jate hain)
  • .listbots                — sab bots + ❄️ frozen status
  • .monitorb                — LIVE status check (online / frozen)
  • .addallb                 — sab bots current group me add
  • .addall 1-3              — sirf 1st-3rd bots add (single: .addall 2)
  • .removeallb              — sab bots group se remove
  • .spamb <n> <sec> <text>  — sab bots text spam (interval NO lower limit — 0.1/0.5 ok)
  • .spamb1-2 <n> <sec> <txt>— sirf 1st & 2nd bot spam
  • .sspamb <n> <sec>        — bots replied-sticker spam (interval float ok)
  • .sspam <n> <sec>         — USER version sticker spam
  • .raidb [slots] <n> <txt> — bot raid (saved raid messages bhi support)
  • .<anim>b [slots] [sec]   — koi bhi animation bots par (.roseb, .hackb1-2 15)
  • .cloneb [slots]          — bots replied-user ka profile clone karein
  • .revertb [slots]         — bots wapas apne ORIGINAL (pre-clone) state me
  • .botsay [slots] <text>   — bots se message bulwao
  • .saverm <text>           — raid message save (1st, 2nd, 3rd… slots)
  • .listrm / .delrm <n>     — saved raid messages (slots auto-shift)
  • .stopb                   — sab bot tasks STOP
  • .bchelp                  — ye help card

Frozen bot = jiska token dead/revoked/deactivated hai — sab lists me ❄️ dikhta hai.
"""

# ─── stores & dirs ──────────────────────────────────────────────────────
BC_STORE = "botcontroller"          # data/botcontroller.json  (bots + slots)
RM_STORE = "raid_messages"          # data/raid_messages.json (.saverm slots)
BC_DIR = os.path.join(DATA_DIR, "botcontroller")
BOT_SESSIONS_DIR = os.path.join(BC_DIR, "sessions")
BOT_PFP_DIR = os.path.join(BC_DIR, "pfps")

for _d in (BC_DIR, BOT_SESSIONS_DIR, BOT_PFP_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except Exception:
        pass

# runtime: {slot(int 1-based): TelegramClient}
BOT_CLIENTS = {}
_bc_lock = None  # created in register (asyncio.Lock)


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
}


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
#  REGISTRATION
# ═══════════════════════════════════════════════════════════════════════

def register_botcontroller(client):
    global _bc_lock
    _bc_lock = asyncio.Lock()

    if not hasattr(client, "stop_processes"):
        client.stop_processes = {}

    # ── .addbottoken <token> ────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.addbottoken\s+([\s\S]+)$"))
    @client.flood_safe
    async def _addbottoken(event):
        token = (event.pattern_match.group(1) or "").strip()
        if not re.match(r"^\d{5,14}:[A-Za-z0-9_-]{25,}$", token):
            return await event.edit(
                "❌ **Invalid token format.**\n"
                "📖 Usage: `.addbottoken 123456789:AAxxxx...` (from **@BotFather**)")
        async with _bc_lock:
            data = _bc_load()
            if any(b.get("token") == token for b in data["bots"]):
                return await event.edit("⚠️ Ye token **already registered** hai.")
            api_id, api_hash = _api_creds(client)
            if not api_id or not api_hash:
                return await event.edit(
                    "❌ API_ID/API_HASH available nahi — `core/config.py` me bharo.")
            await event.edit("🔍 **Token validate ho raha hai…**")
            probe = TelegramClient(StringSession(), api_id, api_hash)
            me = None
            try:
                await probe.start(bot_token=token)
                me = await probe.get_me()
            except Exception as e:
                if _is_freeze_err(e):
                    return await event.edit(
                        f"❌ **Token DEAD/FROZEN hai** — `{type(e).__name__}`\n"
                        "BotFather se naya token lo ya bot revive karo.")
                return await event.edit(f"❌ Token check fail: `{type(e).__name__}: {e}`")
            finally:
                try:
                    await probe.disconnect()
                except Exception:
                    pass
            if me is None:
                return await event.edit("❌ Token se connect nahi hua.")
            if any(b.get("id") == me.id for b in data["bots"]):
                return await event.edit(
                    f"⚠️ @{me.username or me.id} **already registered** hai.")
            data["bots"].append({
                "token": token,
                "id": me.id,
                "username": me.username or "",
                "first_name": me.first_name or "Bot",
                "added_at": time.time(),
                "frozen": False,
                "pre_clone": None,
            })
            _bc_save(data)
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

    # ── .delbottoken / .delbot <n> — delete + slots auto-shift ──────────
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.(?:delbottoken|delbot)\s+(\d+)$"))
    @client.flood_safe
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
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:botlist|listbots)$"))
    @client.flood_safe
    async def _listbots(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit(
                "🤖 **Koi bot registered nahi.**\n"
                "📖 `.addbottoken <token>` — @BotFather se token lo.")
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

    # ── .monitorb — LIVE online/frozen status ────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.monitorb$"))
    @client.flood_safe
    async def _monitorb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit(
                "🤖 Koi bot nahi — `.addbottoken <token>` se add karo.")
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

    # ── group add/remove helpers ──────────────────────────────────────────

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
        """Ek bot ko current chat me add. Returns (ok, why)."""
        entity = await _resolve_bot_entity(main_client, rec)
        if entity is None:
            return False, "not found — pehle bot ko /start karo"
        try:
            from telethon.tl.functions.channels import InviteToChannelRequest
            await main_client(InviteToChannelRequest(input_chat, [entity]))
            return True, "added ✅"
        except Exception as e1:
            n1 = type(e1).__name__
            if "Already" in n1:
                return True, "already in group"
            try:
                from telethon.tl.functions.messages import AddChatMembersRequest
                await main_client(AddChatMembersRequest(chat_id, [entity]))
                return True, "added ✅"
            except Exception as e2:
                n2 = type(e2).__name__
                if "Already" in n2:
                    return True, "already in group"
                return False, n2[:28]

    async def _do_addall(event, arg):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot registered nahi — `.addbottoken <token>`.")
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
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.addallb(\d+(?:-\d+)?)?\s*$"))
    @client.flood_safe
    async def _addallb(event):
        slots_arg = (event.pattern_match.group(1) or "").strip() or None
        await _do_addall(event, slots_arg)

    # ── .addall 1-3 — specific bots add ──────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.addall(?:\s+(\S+))?\s*$"))
    @client.flood_safe
    async def _addall(event):
        arg = (event.pattern_match.group(1) or "").strip() or None
        if arg is None:
            return await event.edit(
                "📖 Usage: `.addall <slots>`\n"
                "e.g. `.addall 1-3` (1st-3rd) · `.addall 2` (sirf 2nd) · "
                "`.addall 1,3` — sab ke liye `.addallb`")
        await _do_addall(event, arg)

    # ── .removeallb — sab bots group se hatao ─────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.removeallb$"))
    @client.flood_safe
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
                rows.append(f"┃ {_ord(i)} @{uname} ❌ {type(e).__name__[:24]}")
        await event.edit(
            "✦ ━━━〔 📤 **BOTS KICKED** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── parse helper: "<count> [interval] …" ─────────────────────────────

    def _parse_count_interval(arg, need_text=False):
        """Returns (count, interval, text, error)."""
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

    # ── .spamb [slots] <count> <interval> <text> — bot army spam ──────────
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.spamb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _spamb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
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
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sspam(?:\s+([\s\S]+))?$"))
    @client.flood_safe
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
            "⛔ `.stop` se roko")
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
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.sspamb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$"))
    @client.flood_safe
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
            total = sum(r for r in res if isinstance(r, int))
            try:
                hint = "" if total else "\n💡 0? Pehle `.addallb` se bots group me add karo."
                await event.reply(
                    f"✅ **Bot sticker spam done** — `{total}/{count * len(pairs)}`{hint}")
            except Exception:
                pass
            try:
                if os.path.exists(fallback_path):
                    os.remove(fallback_path)
            except OSError:
                pass
            for slot, _bc in pairs:
                client.stop_processes.pop(f"bc_sspam_{event.id}_{slot}", None)

        client.stop_processes[f"bc_gather_{event.id}"] = asyncio.create_task(_gatherer())

    # ── .raidb [slots] [count] [text] — BOT RAID ─────────────────────────
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.raidb(\d+(?:-\d+)?)?(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _raidb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit(
                "↩️ **Reply to the victim** — `.raidb [slots] <count> <text>`")
        try:
            tent = await reply.get_input_sender()
            u = await client.get_entity(tent)
        except Exception:
            return await event.edit("❌ Target resolve nahi hua.")
        uid = u.id
        uname = (getattr(u, "first_name", None) or getattr(u, "title", None)
                 or "User")
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
        await event.edit(
            f"💥 **BOT RAID STARTED** on **{uname}**\n"
            f"┃ 🤖 Bots: `{len(pairs)}` · 💬 `{count}` each · 📜 text: `{src[:40]}`\n"
            f"⛔ `.stop` / `.stopb`")

        async def _one(slot, bc):
            key = f"bc_raid_{event.id}_{slot}"
            sent = 0
            fails = 0
            try:
                for i in range(count):
                    raw = text if text else saved[i % len(saved)]
                    try:
                        msg_i = _builder(raw, uid, uname)
                    except Exception:
                        msg_i = f"{uname} {raw}"
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

    # ── animation delegation engine ──────────────────────────────────────

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
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.([a-z]+)b(?:\s+(\d+))?$"))
    @client.flood_safe
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
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.([a-z]+)b(\d+)(?:-(\d+))?(?:\s+(\d+))?$"))
    @client.flood_safe
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

    # ── .cloneb [slots] — bots replied-user ka profile clone karein ─────
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.cloneb(\d+(?:-\d+)?)?\s*$"))
    @client.flood_safe
    async def _cloneb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit("↩️ **Reply to a user** — `.cloneb [slots]`")
        try:
            tent = await reply.get_input_sender()
        except Exception:
            return await event.edit("❌ Target resolve nahi hua.")
        try:
            u = await client.get_entity(tent)
        except Exception:
            u = None
        first = ((getattr(u, "first_name", None) or "User"))[:64]
        last = ((getattr(u, "last_name", None) or ""))[:64]
        bio = ""
        try:
            full = await client(GetFullUserRequest(tent))
            bio = (getattr(full.full_user, "about", None) or "")[:70]
        except Exception:
            pass
        # target ka DP (ek baar download)
        await event.edit("🎭 **Bots cloning profile…**")
        os.makedirs(BOT_PFP_DIR, exist_ok=True)
        target_pfp = os.path.join(BOT_PFP_DIR, f"target_{event.id}.jpg")
        has_photo = False
        try:
            photos = await client.get_profile_photos(tent, limit=1)
            if photos:
                p = await client.download_media(photos[0], file=target_pfp)
                has_photo = bool(p and os.path.exists(p))
        except Exception:
            pass
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            try:
                if os.path.exists(target_pfp):
                    os.remove(target_pfp)
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
            # pre-clone backup (sirf pehli baar — original state kabhi overwrite nahi)
            if not rec.get("pre_clone"):
                pre = {"first_name": "", "last_name": "", "bio": "",
                       "has_photo": False, "pfp_file": None}
                try:
                    bme = await bc.get_me()
                    pre["first_name"] = bme.first_name or ""
                    pre["last_name"] = bme.last_name or ""
                except Exception:
                    pass
                try:
                    bfull = await bc(GetFullUserRequest("me"))
                    pre["bio"] = (getattr(bfull.full_user, "about", None) or "")[:70]
                except Exception:
                    pass
                try:
                    bphotos = await bc.get_profile_photos("me", limit=1)
                    if bphotos:
                        fn = f"bot{s}_orig_{event.id}.jpg"
                        pp = await bc.download_media(bphotos[0],
                                                     file=os.path.join(BOT_PFP_DIR, fn))
                        if pp and os.path.exists(pp):
                            pre["has_photo"] = True
                            pre["pfp_file"] = fn
                except Exception:
                    pass
                rec["pre_clone"] = pre
            done = []
            try:
                await bc(UpdateProfileRequest(first_name=first or "User",
                                             last_name=last, about=bio))
                done.append("name+bio")
            except Exception as e:
                done.append(f"name❌ {type(e).__name__[:18]}")
            if has_photo:
                try:
                    await _bc_clear_bot_photos(bc)
                    up = await bc.upload_file(target_pfp)
                    await bc(UploadProfilePhotoRequest(file=up))
                    done.append("pfp")
                except Exception as e:
                    done.append(f"pfp❌ {type(e).__name__[:18]}")
            rows.append(f"┃ {_ord(s)} @{uname} ✅ {', '.join(done)}")
        _bc_save(data)
        try:
            if os.path.exists(target_pfp):
                os.remove(target_pfp)
        except OSError:
            pass
        await event.edit(
            "✦ ━━━〔 🎭 **BOT CLONE** 〕━━━ ✦\n"
            f"┃ 👤 Target: `{first} {last}`".rstrip() + "\n" + "\n".join(rows) +
            "\n┃ ↩️ Wapas asli roop me: `.revertb`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .revertb [slots] — bots pahle jaise (pre-clone restore) ──────────
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.(?:revertb|uncloneb)(\d+(?:-\d+)?)?\s*$"))
    @client.flood_safe
    async def _revertb(event):
        data = _bc_load()
        bots = data["bots"]
        if not bots:
            return await event.edit("🤖 Koi bot nahi — `.addbottoken <token>`.")
        slots = _parse_slots(event.pattern_match.group(1), len(bots))
        if not slots:
            return await event.edit(f"❌ Invalid bot slot (total `{len(bots)}`).")
        await event.edit("↩️ **Bots revert ho rahe hain…**")
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
            try:
                await bc(UpdateProfileRequest(
                    first_name=(pre.get("first_name") or "Bot")[:64],
                    last_name=(pre.get("last_name") or "")[:64],
                    about=(pre.get("bio") or "")[:70]))
                done.append("name+bio")
            except Exception as e:
                done.append(f"name❌ {type(e).__name__[:18]}")
            if pre.get("has_photo") and pre.get("pfp_file"):
                fp = os.path.join(BOT_PFP_DIR, pre["pfp_file"])
                if os.path.exists(fp):
                    try:
                        await _bc_clear_bot_photos(bc)
                        up = await bc.upload_file(fp)
                        await bc(UploadProfilePhotoRequest(file=up))
                        done.append("pfp")
                    except Exception as e:
                        done.append(f"pfp❌ {type(e).__name__[:18]}")
                else:
                    done.append("pfp⚠️ file missing")
            rows.append(f"┃ {_ord(s)} @{uname} ✅ reverted ({', '.join(done)})")
        _bc_save(data)
        await event.edit(
            "✦ ━━━〔 ↩️ **BOTS REVERTED** 〕━━━ ✦\n" + "\n".join(rows) +
            "\n✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ── .botsay [slots] <text> — bots se message bulwao ───────────────────
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.botsay(\d+(?:-\d+)?)?\s+([\s\S]+)$"))
    @client.flood_safe
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

    # ── .saverm <text> — raid message slots (1st, 2nd, 3rd…) ─────────────
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.saverm(?:\s+([\s\S]+))?$"))
    @client.flood_safe
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
        n_ord = _ord(n)
        await event.edit(
            f"✅ **Raid message saved — {n_ord} slot**\n"
            f"┃ `{text[:80]}`\n"
            f"┃ 🧩 Total slots: `{n}`\n"
            f"💡 `.listrm` dekho · `.delrm {n}` se delete (slots auto-shift)",
            link_preview=False)

    # ── .listrm — saved raid message slots ────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.listrm$"))
    @client.flood_safe
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
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.delrm\s+(\d+)$"))
    @client.flood_safe
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

    # ── .stopb — sab bot tasks STOP ───────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stopb\s*$"))
    @client.flood_safe
    async def _stopb(event):
        killed = 0
        for k, t in list(client.stop_processes.items()):
            if not k.startswith("bc_"):
                continue
            if t is not None and not t.done():
                t.cancel()
                killed += 1
            client.stop_processes.pop(k, None)
        await event.edit(
            f"⏹ **{killed}** bot task(s) stopped.\n"
            "💡 Bot sessions saved — `.spamb` / `.raidb` dobara turant chalega.")

    # ── .bchelp — full help card ──────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:bchelp|bch|bothelp)$"))
    @client.flood_safe
    async def _bchelp(event):
        await event.edit(
            "✦ ━━━〔 🤖 **BOTCONTROLLER** 〕━━━ ✦\n"
            "**📐 Setup**\n"
            "┃ `.addbottoken <token>` — bot add (1st/2nd/3rd…)\n"
            "┃ `.delbottoken` / `.delbot <n>` — delete (slots auto-shift)\n"
            "┃ `.listbots` / `.botlist` — sab bots + ❄️ frozen\n"
            "┃ `.monitorb` — LIVE online check\n"
            "**📥 Group**\n"
            "┃ `.addallb [slots]` — bots add (sab ya `.addallb1-3`)\n"
            "┃ `.addall 1-3` — specific bots add\n"
            "┃ `.removeallb` — sab bots remove\n"
            "**🚀 Attack**\n"
            "┃ `.spamb <n> <sec> <text>` — text spam (interval NO limit)\n"
            "┃ `.spamb1-2 <n> <sec> <text>` — specific bots\n"
            "┃ `.sspam <n> <sec>` — user sticker spam (reply)\n"
            "┃ `.sspamb <n> <sec>` — bots sticker spam (reply)\n"
            "┃ `.raidb [slots] <n> <text>` — bot raid\n"
            "**🎭 Profile & Fun**\n"
            "┃ `.cloneb [slots]` — bots victim ka clone banein\n"
            "┃ `.revertb` / `.uncloneb [slots]` — bots pahle jaise ho jayein\n"
            "┃ `.botsay [slots] <text>` — bots se bolo\n"
            "┃ `.<anim>b [slots] [sec]` — animation bots par (.roseb .hackb1-2)\n"
            "**📜 Raid Messages**\n"
            "┃ `.saverm <text>` — slot save (reply se bhi · 1st, 2nd, 3rd…)\n"
            "┃ `.listrm` / `.delrm <n>` — list / delete (auto-shift)\n"
            "┃ ⚡ `.raid` ab: reply optional + custom text + slots rotate\n"
            "**⏹ Control**\n"
            "┃ `.stopb` / `.stop` — sab tasks stop\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦"
            "_aliases: `.bch` · `.bothelp` · `.delbot` · `.uncloneb` \n",
            link_preview=False)


COMMANDS_BOTCONTROLLER = {
    "description": "🤖 BotController — Multi-Bot Army Command Center",
    "commands": [
        (".addbottoken <token>", "bot register (1st/2nd/3rd slots)"),
        (".delbottoken / .delbot <n>", "bot delete — slots auto-shift"),
        (".listbots / .botlist", "sab bots + frozen status"),
        (".monitorb", "LIVE online/frozen check"),
        (".addallb [slots] / .addall 1-3", "bots group me add (sab / specific)"),
        (".removeallb", "sab bots group se remove"),
        (".spamb <n> <sec> <txt>", "sab bots text spam — interval NO lower limit"),
        (".spamb1-2 <n> <sec> <txt>", "sirf specific bots spam"),
        (".sspam <n> <sec>", "user sticker spam (reply)"),
        (".sspamb <n> <sec>", "bots sticker spam (reply)"),
        (".raidb [slots] <n> <txt>", "bot raid — saved messages bhi"),
        (".cloneb [slots]", "bots replied-user ka profile clone karein"),
        (".revertb / .uncloneb [slots]", "bots wapas pre-clone state me"),
        (".botsay [slots] <txt>", "bots se message bulwao"),
        (".<anim>b [slots] [sec]", "koi bhi animation bots par (.roseb, .hackb1-2)"),
        (".saverm <text>", "raid message slot save (reply se bhi · 1st, 2nd…)"),
        (".listrm / .delrm <n>", "raid message slots (auto-shift)"),
        (".stopb", "sab bot tasks stop"),
        (".bchelp / .bch / .bothelp", "ye help card"),
    ],
}

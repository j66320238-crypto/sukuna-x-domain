# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine (events, ChatBannedRights, EditBannedRequest, json/os/time/re …)

############################################################################
#  SECTION: MUTE  —  global auto-delete mute engine
############################################################################
"""
🔇 MUTE — global auto-delete mute engine (v7.11)

Kya karta hai?
  • `.mute` se kisi user ko mute karo (reply / uid / @username)
  • Muted user ka har message AUTO-DELETE ho jaata hai:
      - DM me  → hamesha delete (received PM delete karne ka rights hamesha hota hai)
      - GC me  → delete SIRF jab userbot us GC me ADMIN ho
                 (admin nahi → wo chat 10 min ke liye skip — har message par
                  failed API call spam nahi hota)
  • Bonus: agar us GC me userbot admin hai to mute karte waqt Telegram
    native mute (EditBannedRequest) bhi lag jaata hai — muted user wahan
    likh bhi nahi paayega. `.unmute` par wo native mute bhi hatt jaata hai
    (har us GC me jo entry ke "native" list me yaad hai).
  • Persistent storage: mute_data.json — restart ke baad bhi mute list zinda.
  • Deletes BILKUL SILENT hote hain — koi count nahi, koi notice nahi.
  • Confirm messages minimal: sirf naam + uid.

Commands:
  .mute            (reply)  → mute replied user
  .mute <uid>               → mute by user id
  .mute @username           → mute by username
  .mute list                → mute list (alias of .mutelist)
  .unmute          (reply)  → unmute replied user
  .unmute <uid>             → unmute by user id
  .unmute @username         → unmute by username
  .mutelist                 → muted users list
  .unmuteall                → poora mute list clear (+ native mutes hatao)

NOTE: purana group-only `.mute <minutes>` (admin.py) hata diya gaya hai —
      ye global engine uska strict superset hai.
"""

# ---------------------------------------------------------------------------
#  Persistence  (module-level helpers — antipm pattern, no client dependency)
# ---------------------------------------------------------------------------

MUTE_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "mute_data.json"
)

_DEFAULT_DATA = {
    "muted":   {},   # { "uid": {"name": str, "how": str, "ts": float, "native": [chat_id, …]} }
}


def _load_data():
    """Load persisted data — corrupt/missing file par clean defaults."""
    try:
        with open(MUTE_DATA_FILE, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        if not isinstance(d, dict):
            d = {}
    except Exception:
        d = {}
    return {
        "muted":   d.get("muted", {})   if isinstance(d.get("muted", {}), dict)   else {},
    }


def _save_data(data):
    """Atomic write — tmp file + os.replace, kabhi half-written JSON na chhode."""
    try:
        tmp = MUTE_DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, MUTE_DATA_FILE)
    except Exception:
        pass


# native mute rights — user GC dekh sakta hai par likh nahi sakta
_MUTE_RIGHTS = ChatBannedRights(
    until_date=0,
    view_messages=False,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
    send_polls=True,
)
_FREE_RIGHTS = ChatBannedRights(until_date=0)

_NO_RIGHTS_TTL = 600    # GC me admin nahi → itne sec tak delete-try skip
_LIST_LIMIT = 25        # .mutelist display cap


def register_mute(client):
    """
    Register all MUTE commands + the auto-delete listener on *client*.
    Everything is a closure over *client* — clean load/unload.
    """

    data = _load_data()
    _mset = set(int(k) for k in data["muted"].keys())   # fast lookup set
    _state = {"me": None}
    _no_rights = {}   # chat_id → ts of last admin-delete failure (is GC me rights nahi)

    # ---------------- small helpers ----------------

    def save():
        """Data file me likho (sirf mute/unmute actions par — deletes bilkul silent)."""
        _save_data(data)

    async def me_id():
        """Own user id — ek baar resolve, phir cache."""
        if _state["me"] is None:
            try:
                _state["me"] = (await client.get_me()).id
            except Exception:
                return None
        return _state["me"]

    def _disp(ent):
        """Pretty name from a Telethon entity (user/channel)."""
        if ent is None:
            return None
        try:
            t = getattr(ent, "title", None)
            if t:
                return t
            n = " ".join(x for x in ((getattr(ent, "first_name", "") or ""),
                                     (getattr(ent, "last_name", "") or "")) if x)
            if n:
                return n
            u = getattr(ent, "username", None)
            if u:
                return "@" + u
        except Exception:
            pass
        return None

    async def _resolve(event, arg):
        """Target resolve — reply > uid > @username.
        Returns (uid:int, name:str, how:str)
             ya  (None, errmsg:str, None)  resolve fail par
             ya  (None, None, None)        koi target hi nahi → usage dikhao
        """
        try:
            reply = await event.get_reply_message()
        except Exception:
            reply = None
        if reply is not None and reply.sender_id:
            s = None
            try:
                s = await reply.get_sender()
            except Exception:
                pass
            return int(reply.sender_id), (_disp(s) or f"User {reply.sender_id}"), "reply"
        if arg:
            a = arg.strip().lstrip("@")
            # numeric uid (user/bot ids 4+ digits hote hain)
            if re.fullmatch(r"\d{4,}", a):
                uid = int(a)
                name = None
                try:
                    name = _disp(await client.get_entity(uid))
                except Exception:
                    pass                       # entity cache me nahi — raw uid par bhi mute chalega
                return uid, (name or f"User {uid}"), "uid"
            # username
            try:
                ent = await client.get_entity(a)
                return int(ent.id), (_disp(ent) or f"User {ent.id}"), "username"
            except Exception:
                return None, (f"❌ `{a}` resolve nahi hua — uid ya @username check karo."), None
        return None, None, None

    async def _native_unmute(uid, chat_ids):
        """Best-effort native unmute on remembered chats. → kitne me success."""
        ok = 0
        try:
            user_ent = await client.get_input_entity(int(uid))
        except Exception:
            return 0
        for cid in (chat_ids or [])[:20]:
            try:
                chat_ent = await client.get_input_entity(int(cid))
                await client(EditBannedRequest(
                    channel=chat_ent, user_id=user_ent, banned_rights=_FREE_RIGHTS))
                ok += 1
            except Exception:
                pass
        return ok

    async def _show_list(event):
        if not data["muted"]:
            await event.reply(
                "🔇 **Mute list khali hai.**\n"
                "┃ Mute karne ke liye: `.mute` (reply) ya `.mute <uid>`")
            return
        items = sorted(data["muted"].items(), key=lambda kv: -kv[1].get("ts", 0))
        lines = [f"🔇 **MUTED ({len(data['muted'])})**\n"]
        for uid_s, info in items[:_LIST_LIMIT]:
            nm = info.get("name") or f"User {uid_s}"
            lines.append(f"• {nm} — `{uid_s}`")
        if len(items) > _LIST_LIMIT:
            lines.append(f"…+{len(items) - _LIST_LIMIT} more")
        await event.reply("\n".join(lines))

    # ==================================================================
    #  Commands
    # ==================================================================

    # ── .mute (reply | <uid> | @user | list) ─────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^[\.!]mute(?:\s+(\S+))?$"))
    @client.flood_safe
    async def mute_cmd(event):
        try:
            arg = event.pattern_match.group(1)
            if arg and arg.lower() == "list":
                return await _show_list(event)

            uid, name, how = await _resolve(event, arg)
            if uid is None:
                if name:                      # resolve error message
                    return await event.reply(name)
                return await event.reply(
                    "🔇 **MUTE — usage**\n"
                    "┃ `.mute` (reply) · `.mute <uid>` · `.mute @user`\n"
                    "┃ `.unmute` (reply) · `.unmute <uid>` · `.unmute @user`\n"
                    "┃ `.mutelist` · `.unmuteall`\n"
                    "┃ Muted user ki DM + admin-GC messages auto-delete 🗑️"
                )

            me = await me_id()
            if me and uid == me:
                return await event.reply("🙃 Khud ko mute karoge to apne hi messages gayab honge — nahi.")

            uid_s = str(uid)
            entry = {"name": name, "how": how, "ts": time.time()}

            # bonus: is GC me admin hai to native mute bhi laga do
            native = False
            if event.is_group:
                try:
                    chat = await event.get_input_chat()
                    tgt = await client.get_input_entity(uid)
                    await client(EditBannedRequest(
                        channel=chat, user_id=tgt, banned_rights=_MUTE_RIGHTS))
                    native = True
                    ch_id = event.chat_id
                    lst = entry.setdefault("native", [])
                    if ch_id not in lst:
                        lst.append(ch_id)
                    _no_rights.pop(ch_id, None)
                except Exception:
                    native = False            # admin nahi / rights nahi — auto-delete mode hi chalega

            data["muted"][uid_s] = entry
            _mset.add(uid)
            save()

            # minimal confirm — sirf naam + uid, bas
            await event.reply(f"🔇 **MUTED** — {name} (`{uid}`)")
        except Exception:
            pass

    # ── .unmute (reply | <uid> | @user) ──────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^[\.!]unmute(?:\s+(\S+))?$"))
    @client.flood_safe
    async def unmute_cmd(event):
        try:
            arg = event.pattern_match.group(1)
            uid, name, how = await _resolve(event, arg)
            if uid is None:
                if name:
                    return await event.reply(name)
                return await event.reply(
                    "🔊 **UNMUTE — usage**\n"
                    "┃ `.unmute` (reply) · `.unmute <uid>` · `.unmute @user`\n"
                    "┃ `.mutelist` — kaun kaun muted hai")

            uid_s = str(uid)
            entry = data["muted"].pop(uid_s, None)

            if entry is None:
                # list me nahi tha — par native unmute phir bhi try (purane
                # admin.py .mute ya manual TG mute se laga ho sakta hai)
                nat = 0
                if event.is_group:
                    try:
                        chat = await event.get_input_chat()
                        tgt = await client.get_input_entity(uid)
                        await client(EditBannedRequest(
                            channel=chat, user_id=tgt, banned_rights=_FREE_RIGHTS))
                        nat = 1
                    except Exception:
                        pass
                msg = f"ℹ️ **{name}** (`{uid}`) mute list me tha hi nahi."
                if nat:
                    msg += " Is GC ka native mute hata diya ✅"
                return await event.reply(msg)

            _mset.discard(uid)
            # yaad ras native mutes hatao (jo GC me humne lagaye the)
            nat = await _native_unmute(uid, entry.get("native"))
            if event.is_group:
                try:
                    chat = await event.get_input_chat()
                    tgt = await client.get_input_entity(uid)
                    await client(EditBannedRequest(
                        channel=chat, user_id=tgt, banned_rights=_FREE_RIGHTS))
                    nat += 1
                except Exception:
                    pass
            save()

            # minimal confirm — sirf naam + uid, bas
            await event.reply(f"🔊 **UNMUTED** — {name} (`{uid}`)")
        except Exception:
            pass

    # ── .mutelist ────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^[\.!]mutelist$"))
    @client.flood_safe
    async def mutelist_cmd(event):
        try:
            await _show_list(event)
        except Exception:
            pass

    # ── .unmuteall ───────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^[\.!]unmuteall$"))
    @client.flood_safe
    async def unmuteall_cmd(event):
        try:
            if not data["muted"]:
                return await event.reply("ℹ️ Mute list pehle se khali hai.")
            total = len(data["muted"])
            nat = 0
            for uid_s, info in list(data["muted"].items()):
                nat += await _native_unmute(int(uid_s), info.get("native"))
            data["muted"].clear()
            _mset.clear()
            save()
            await event.reply(f"🔊 **UNMUTED ALL** — {total} users")
        except Exception:
            pass

    # ==================================================================
    #  Auto-delete listener  (fast-exit: mute set me nahi → 1 set-lookup)
    # ==================================================================

    @client.on(events.NewMessage(incoming=True))
    @client.flood_safe
    async def mute_listener(event):
        uid = event.sender_id
        if uid is None or int(uid) not in _mset:
            return

        # broadcast channel posts — sender channel khud hota hai, skip
        if event.is_channel and not event.is_group:
            return

        try:
            # GC: agar pichli koshish me rights nahi mile the to 10 min tak skip
            if not event.is_private:
                nr = _no_rights.get(event.chat_id)
                if nr and (time.time() - nr) < _NO_RIGHTS_TTL:
                    return

            await event.delete()
            # bilkul silent — koi count nahi, koi disk-write nahi, koi reply nahi
        except Exception as e:
            en = type(e).__name__
            # admin-rights wale errors → is chat ko TTL ke liye cache, no API spam
            if any(s in en for s in ("Admin", "Forbidden", "Rights", "Invalid")):
                try:
                    _no_rights[event.chat_id] = time.time()
                except Exception:
                    pass


COMMANDS_MUTE = {
    "description": "Mute — global silent auto-delete mute (DM + admin GC)",
    "commands": [
        (".mute (reply)", "mute user — DM/GC messages silently auto-delete"),
        (".mute <uid|@user>", "mute by user id ya username"),
        (".unmute (reply)", "unmute user"),
        (".unmute <uid|@user>", "unmute by user id ya username"),
        (".mutelist", "muted users list"),
        (".unmuteall", "poora mute list clear"),
    ],
}

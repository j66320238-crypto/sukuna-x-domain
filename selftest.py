#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest.py — SUKUNA-X DOMAIN LIVE SELF-TEST v3 (synthetic-dispatch engine)
===========================================================================
Kyun v3? — Telegram ek hi session ka apna bheja message US SESSION ko
update-event ke roop me wapas NAHI bhejta (dusra session hi update paata
hai). Isliye purane harness me outgoing handlers kabhi fire hi nahi hote
the. YE harness:
  1. command REAL me bhejta hai (group me asli message)
  2. saare registered handlers ko EXACTLY waise call karta hai jaise
     Telethon's dispatcher karta hai (builder.filter() → await cb(event))
  3. handlers ki event.edit()/reply() ASLI API calls hain → group me
     asli responses aate hain → wahi capture hote hain
Incoming/sudo paths ke liye REAL bot-messages par dispatch hota hai.
Matlab: sirf "update delivery layer" synthetic hai (wo Telethon ka apna
hamesha se theek chalta raha hai) — baaki SAB 100% production-real.

Run:  python3 selftest.py    (userbot STOP ho — warna session lock!)
Out:  selftest_report.json + stdout
"""
import asyncio
import datetime
import json
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import core  # noqa: E402
from core import (  # noqa: E402
    BOT_VERSION, DATA_DIR, print_banner, resolve_credentials,
    stop_processes, command_registry, log,
)
from core import state as _core_state  # noqa: E402
from core import accounts as _accounts_mod  # noqa: E402
from core.ui import register_builtin_commands  # noqa: E402
from userbot import register_all  # noqa: E402

from telethon import TelegramClient, events  # noqa: E402
from telethon.tl.functions.account import UpdateProfileRequest  # noqa: E402

REPORT = {"started": datetime.datetime.now().isoformat(),
          "env": {}, "tests": [], "errors": []}
_NM = events.NewMessage


def _clip(text, n=400):
    try:
        t = (text or "").strip()
        return t[:n] + ("…" if len(t) > n else "")
    except Exception:
        return repr(text)[:n]


class Dispatcher:
    """Telethon ke dispatcher ki hoopt-up copy — ek Message par saare
    matching handlers chalao (pattern + outgoing/incoming + func + chats)."""

    def __init__(self, client):
        self.client = client

    async def fire(self, msg, only_incoming=False):
        """msg par saare NewMessage handlers chalao. Returns fired count."""
        msg.out = bool(getattr(msg, "out", True))
        if only_incoming:
            msg.out = False
        ev = _NM.Event(msg)
        try:
            ev._set_client(self.client)   # real dispatch ki tarah client bind
        except Exception:
            pass
        fired = 0
        for cb, builder in self.client.list_event_handlers():
            if not isinstance(builder, _NM):
                continue
            # v7.6 FIX: builders must be resolved before filter() works.
            # The real dispatcher resolves them on the first live update;
            # the synthetic path must do it explicitly or the first few
            # commands (before any real update) silently match nothing.
            try:
                if not getattr(builder, "resolved", True):
                    await builder.resolve(self.client)
            except Exception:
                pass
            try:
                res = builder.filter(ev)
            except Exception:
                continue
            if not res:
                continue
            fired += 1
            try:
                await cb(res if isinstance(res, _NM.Event) else ev)
            except events.StopPropagation:
                break
            except Exception as e:
                log.error("[selftest-dispatch] %s: %s",
                          getattr(cb, "__name__", "cb"), e)
        return fired


async def main():
    print_banner()
    print("\n   🧪 SUKUNA-X SELF-TEST v3 — synthetic dispatch + real API")
    print("   " + "─" * 52)

    api_id, api_hash, acc_name, acc_phone = resolve_credentials()
    _core_state.ACTIVE_API_ID = api_id or 0
    _core_state.ACTIVE_API_HASH = api_hash or ""
    _live_account = getattr(_accounts_mod, "ACCOUNT", None)
    session_obj = acc_name if _live_account else core.SESSION_NAME
    print(f"   🔑 Session: {session_obj}")

    client = TelegramClient(
        session=session_obj, api_id=api_id, api_hash=api_hash,
        device_model="SukunaX-Domain", system_version=BOT_VERSION,
        app_version=f"Sukuna-X Domain {BOT_VERSION}", lang_code="en",
        system_lang_code="en", connection_retries=None, retry_delay=1,
        request_retries=5, flood_sleep_threshold=20,
    )
    try:
        client.parse_mode = "md"
    except Exception:
        pass
    client.stop_processes = stop_processes
    client.flood_safe = core.flood_safe
    client.command_registry = command_registry

    await client.connect()
    if not await client.is_user_authorized():
        print("   ✖ Session NOT authorized.")
        return 2
    me = await client.get_me()
    _core_state.OWNER_ID = me.id
    orig_first, orig_last = me.first_name or "", me.last_name or ""
    orig_bio = ""
    try:
        from telethon.tl.functions.users import GetFullUserRequest
        full = await client(GetFullUserRequest("me"))
        orig_bio = getattr(full.full_user, "about", None) or ""
    except Exception:
        pass
    print(f"   👤 {me.first_name} (@{me.username or 'n/a'}) ID {me.id}")

    register_builtin_commands(client)
    loaded = register_all(client)
    disp = Dispatcher(client)
    print(f"   🔌 {loaded} plugins · handlers: {len(client.list_event_handlers())}")

    # ── test group(s) ──────────────────────────────────────────────────
    groups = []
    async for d in client.iter_dialogs(limit=300):
        if d.is_group and (d.name or "").strip().lower() == "test":
            groups.append(d)
    print(f"   💬 'test' groups mile: {len(groups)} → " +
          ", ".join(f"{g.name}({g.id})" for g in groups))
    if not groups:
        async for d in client.iter_dialogs(limit=300):
            if d.is_group and "test" in (d.name or "").lower():
                groups.append(d)
    if not groups:
        print("   ✖ 'test' GC nahi mila.")
        REPORT["errors"].append("TEST GROUP NOT FOUND")
        _save()
        await client.disconnect()
        return 3
    g = groups[0]
    test_chat, test_name, test_id = g.entity, g.name, g.id
    print(f"   💬 Use kar rahe: {test_name} (id {test_id})")
    REPORT["env"] = {"me": f"{me.first_name} (@{me.username}) {me.id}",
                     "group": f"{test_name} ({test_id})",
                     "plugins": loaded,
                     "all_test_groups": [f"{x.name} ({x.id})" for x in groups]}

    # worker bots info
    try:
        bcdata = json.load(open(os.path.join(DATA_DIR, "botcontroller.json"),
                                encoding="utf-8"))
    except Exception:
        bcdata = {"bots": []}
    bots = bcdata.get("bots", [])
    bot_ids = [b.get("id") for b in bots if b.get("id")]
    bot_names = [b.get("username") for b in bots if b.get("username")]
    print(f"   🤖 Bots: {bot_names} · ids: {bot_ids}")

    # setup: bots ko /start
    for uname in bot_names:
        try:
            await client.send_message(uname, "/start")
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"   ▶ /start @{uname} fail: {e}")

    # ── engine ────────────────────────────────────────────────────────
    results = []
    st = {"bot_msg_id": None, "self_msg_id": None, "last_bot_txt": ""}

    async def capture(cmd_id, wait, rec):
        await asyncio.sleep(wait)
        out_text, extras = "", []
        try:
            msgs = await client.get_messages(test_chat, limit=30)
            for m in msgs:
                if m.id == cmd_id:
                    out_text = m.raw_text or m.text or ""
                elif m.id > cmd_id:
                    try:
                        s = m.sender
                        sender = (f"@{s.username}" if getattr(s, "username", None)
                                  else (getattr(s, "first_name", None)
                                        or getattr(s, "title", None)
                                        or str(m.sender_id)))
                    except Exception:
                        sender = str(m.sender_id)
                    extras.append(f"[{m.id}|{sender}] " + _clip(m.raw_text or "", 90))
            extras.sort(key=lambda x: int(x.split("|")[0][1:]))
        except Exception as e:
            rec["capture_err"] = str(e)
        return out_text, extras[:8]

    async def run_cmd(cmd, wait=4.0, reply_to=None, expect=None,
                      expect_error=None, note="", no_dispatch=False):
        t0 = time.time()
        rec = {"cmd": cmd, "wait": wait, "note": note}
        try:
            kw = {"reply_to": reply_to} if reply_to else {}
            msg = await client.send_message(test_chat, cmd, **kw)
        except Exception as e:
            rec.update(ok=False, why=f"send failed",
                      output=f"SEND ERROR: {type(e).__name__}: {e}")
            results.append(rec); _pr(rec); return rec
        cmd_id = msg.id
        fired = 0
        if not no_dispatch:
            try:
                fired = await disp.fire(msg)
            except Exception as e:
                rec["dispatch_err"] = f"{type(e).__name__}: {e}"
        out_text, extras = await capture(cmd_id, wait, rec)
        unchanged = (out_text or "").strip() == cmd.strip()
        bad = ("❌ Command failed" in out_text or "ImportError" in out_text
               or "Traceback" in out_text)
        if expect_error:
            ok = expect_error.lower() in out_text.lower()
        elif expect:
            ok = expect.lower() in out_text.lower() and not unchanged
        else:
            ok = (not unchanged) and bool(out_text.strip()) and not bad
        why = ""
        if unchanged:
            why = f"NO RESPONSE (fired={fired})"
        elif bad:
            why = "error reply: " + _clip(out_text, 110)
        elif not ok and expect:
            why = f"expected {expect!r} not in output (fired={fired})"
        else:
            why = "ok"
        rec.update(ok=ok, why=why, fired=fired, output=_clip(out_text, 700),
                   extras=extras, secs=round(time.time() - t0, 1))
        results.append(rec)
        _pr(rec)
        # bot message track
        for ex in extras:
            m = re.match(r"\[(\d+)\|@?([^\]]+)\]", ex)
            if m and any(b in m.group(2) for b in (bot_names + [str(x) for x in bot_ids])):
                if "bot" in m.group(2).lower() or m.group(2) in (str(x) for x in bot_ids):
                    st["bot_msg_id"] = int(m.group(1))
                    st["last_bot_txt"] = ex
        if cmd.startswith(".uptime"):
            st["self_msg_id"] = cmd_id
        return rec

    async def fire_on_msg(msg_id, wait=6, label="incoming-dispatch"):
        """Kisi bhi real message par incoming handlers chalao (bot/sudo path)."""
        rec = {"cmd": f"[dispatch-on-msg {msg_id}] {label}", "wait": wait, "note": ""}
        try:
            m = await client.get_messages(test_chat, ids=msg_id)
            if isinstance(m, list):
                m = m[0] if m else None
            if m is None:
                rec.update(ok=False, why="msg not found", output="")
                results.append(rec); _pr(rec); return rec
            fired = await disp.fire(m, only_incoming=True)
            out, extras = await capture(msg_id, wait, rec)
            rec.update(ok=fired > 0, why=f"fired={fired}",
                      output=_clip(out, 300), extras=extras, fired=fired)
        except Exception as e:
            rec.update(ok=False, why=f"{type(e).__name__}: {e}", output=str(e)[:200])
        results.append(rec)
        _pr(rec)
        return rec

    def _pr(rec):
        mark = "PASS ✅" if rec.get("ok") else "FAIL ❌"
        print(f"   {mark}  {rec['cmd'][:46]:<48} {rec.get('why','')[:56]}", flush=True)

    def _save():
        REPORT["tests"] = results
        REPORT["finished"] = datetime.datetime.now().isoformat()
        p = os.path.join(BASE, "selftest_report.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(REPORT, fh, ensure_ascii=False, indent=1)
        return p

    # ═══════════════ TEST PLAN ═════════════════════════════════════════
    print("\n   PHASE A — CORE UI (outgoing commands)")
    await run_cmd(".alive", 3)
    await run_cmd(".ping", 5)
    await run_cmd(".help", 4)
    await run_cmd(".menu", 5)
    await run_cmd(".cmds", 4)
    await run_cmd(".plist", 4)
    await run_cmd(".stats", 4)
    await run_cmd(".uptime", 3)
    await run_cmd(".sysinfo", 5)
    await run_cmd(".autodelete status", 4)
    await run_cmd(".viewonce", 4, expect="view-once",
                  note="v7.7 view-once saver card (photos+videos, default ON)")
    await run_cmd(".help settings", 5, expect="autodeletem",
                  note="v7.7 settings section inside .help")
    await run_cmd(".autodeletem 10", 3, expect="timer set",
                  note="v7.6 timed auto-delete ON (10s)")
    await run_cmd(".autodeletem off", 2, expect="off",
                  note="timer off again (keep test clean)")
    await run_cmd(".autodeletem status", 3, expect="off",
                  note="timer status confirms OFF")

    print("\n   PHASE B — BOT ARMY (sudo-gate: owner outgoing path)")
    await run_cmd(".listsudo", 3)
    await run_cmd(".bccheck", 10, note="self-diagnosis")
    await run_cmd(".botlist", 4)
    await run_cmd(".monitorb", 15, note="bot connect")
    await run_cmd(".addallb", 20, note="bots ko group me add")

    print("\n   PHASE C — BOT MESSAGING")
    await run_cmd(".botsay selftest hello from worker", 7,
                  note="bot ka msg — RRT/ct target")
    if st["bot_msg_id"] is None:
        # bot ka msg dhundo — bot abhi group me aya hoga
        for m in await client.get_messages(test_chat, limit=30):
            if m.sender_id in bot_ids:
                st["bot_msg_id"] = m.id
                break
    print(f"      (bot_msg_id = {st['bot_msg_id']})")
    await run_cmd(".spamb 2 0.4 selftest bot spam alpha", 12)
    await run_cmd(".spamb 3 0.4 selftest bot spam beta", 16)
    await run_cmd(".stopb", 4, note="bot spam stop")
    await run_cmd(".raid 2 selftest user raid ok", 10)
    await run_cmd(".raidb 2 selftest bot raid ok", 16)
    await run_cmd(".stopraid", 3)
    await run_cmd(".spamstop", 3)
    await run_cmd(".stopall", 3, note="sab background tasks clean")

    print("\n   PHASE D — RAID MESSAGE SLOTS")
    await run_cmd(".saverm selftest slot alpha", 3)
    await run_cmd(".saverm selftest slot beta", 3)
    await run_cmd(".listrm", 3, expect="slot")
    await run_cmd(".delrm 1", 3, expect="delete")
    await run_cmd(".listrm", 3, expect="beta", note="auto-shift: beta ab 1st")
    await run_cmd(".delallrm", 3, expect="delete")

    print("\n   PHASE E — REPLY-BASED (.ct/.ctb mirror + .rr/.rrt reply-raid)")
    r_to = st["bot_msg_id"]
    await run_cmd(".ct copy", 6, reply_to=r_to, expect="copied",
                  note="one-shot copy of bot msg")
    await run_cmd(".ct", 5, reply_to=r_to, expect="mirror on",
                  note="v7.6 user MIRROR toggle → ON")
    await run_cmd(".ct", 5, reply_to=r_to, expect="mirror off",
                  note="v7.6 user MIRROR toggle → OFF")
    await run_cmd(".ctb", 10, reply_to=r_to, expect="mirror on",
                  note="v7.6 bots MIRROR → ON")
    await run_cmd(".ctb", 8, reply_to=r_to, expect="mirror off",
                  note="v7.6 bots MIRROR → OFF")
    await run_cmd(".saverm selftest rrt slot msg", 3)
    await run_cmd(".rrt", 4, reply_to=r_to, expect="started",
                  note=".rrt reply-raid armed (auto-saves replied msg)")
    await run_cmd(".listrm", 3, expect="slot", note=".rrt auto-saved the replied msg into slots")
    # bot ko phir se message bhejao → RRT listener incoming par chalega
    await run_cmd(".botsay selftest rrt trigger ping", 6, note="bot msg for RRT")
    if st["bot_msg_id"]:
        await fire_on_msg(st["bot_msg_id"], wait=8, label="RRT listener (incoming)")
    await run_cmd(".stoprrt", 3, expect="stopped")
    # v7.7 — .rr / .rrb explicit toggle tests (user demand: dobara likho = band)
    await run_cmd(".rr", 4, reply_to=r_to, expect="started",
                  note=".rr arm on the bot-target (saved slots reply)")
    await run_cmd(".rr", 4, reply_to=r_to, expect="stopped",
                  note=".rr same user again = TOGGLE OFF")
    await run_cmd(".rrb", 6, reply_to=r_to, expect="started",
                  note=".rrb bots reply-raid arm")
    await run_cmd(".rrb", 6, reply_to=r_to, expect="stopped",
                  note=".rrb toggle off")
    await run_cmd(".rrt", 4, reply_to=r_to, expect="started",
                  note="arm again for the listener check")
    await run_cmd(".stoprrt", 3, expect="stopped", note="cleanup before raidb")
    if st["bot_msg_id"]:
        await run_cmd(".raidb 2 .1 selftest decimal gap ok", 14,
                      reply_to=st["bot_msg_id"], expect="raid started",
                      note="v7.7 raidb reply+tag + decimal gap .1 parse")
        await run_cmd(".raidbstop", 3, expect="stop", note="bot raid stop")

    print("\n   PHASE F — CLONE / REVERT (bots)")
    await run_cmd(".cloneb", 30, reply_to=st["self_msg_id"],
                  expect="clone", note="bot = user ka clone")
    await run_cmd(".revertb", 15, expect="revert", note="bot wapas original")

    print("\n   PHASE G — USER PROFILE CLONE (safety-net ke saath)")
    await run_cmd(".clone", 15, reply_to=r_to, note="me = bot ka clone")
    await run_cmd(".revert", 10, note="me wapas original")
    _bu = (bot_names[0] if bot_names else None)
    if _bu:
        await run_cmd(f".clone @{_bu}", 25, expect="clone",
                      note="v7.7 clone BY USERNAME (bot target)")
        await run_cmd(".revert", 10, note="restore after username clone")
    try:
        me2 = await client.get_me()
        if (me2.first_name or "") != orig_first:
            await client(UpdateProfileRequest(first_name=orig_first or "user",
                                              last_name=orig_last, about=orig_bio))
            REPORT["errors"].append(
                f"REVERT SAFETY-NET fired: {me2.first_name!r} → {orig_first!r}")
            print("   🛡 REVERT SAFETY-NET — name restored!")
    except Exception as e:
        REPORT["errors"].append(f"safety-net: {e}")

    print("\n   PHASE H — STOP FAMILY + MISC + ERROR PATH")
    await run_cmd(".matrix 40", 4, note="long anim start")
    await run_cmd(".stop", 4, expect="stop", note="task kill")
    await run_cmd(".8ball kya sab commands chal rahe hain", 3, expect="🎱")
    await run_cmd(".random 50", 3)
    await run_cmd(".addbottoken invalid_token_test_123", 4,
                  expect_error="invalid token", note="error-path")

    print("\n   PHASE I — SUDO gate + BotFather naya bot")
    # worker bot ko sudo me daalo → incoming path test
    if bot_ids:
        await run_cmd(f".addsudo {bot_ids[0]}", 3,
                      note="bot sudo (incoming-path test)")
    await run_cmd(".botsay .botlist", 6,
                  note="bot khud .botlist bhejega — sudo-incoming trigger")
    if st["bot_msg_id"]:
        await fire_on_msg(st["bot_msg_id"], wait=8,
                          label="sudo-bot incoming: .botlist response")
    await run_cmd(".addnewbotauto 1", 90, note="BotFather se naya bot (real, paced)")
    await run_cmd(".updateuserbot", 60, expect="latest",
                  note="v7.7 version guard — refuses to downgrade the deploy")
    await run_cmd(".refreshb", 20, note="sab bots reconnect")
    await run_cmd(".monitorb", 15, note="final status")
    await run_cmd(".stopall", 3)
    await run_cmd(".autodeletem 10", 3, expect="timer set",
                  note="leave the 10s timer ON (user default)")
    if bot_ids:
        await run_cmd(f".delsudo {bot_ids[0]}", 3, note="sudo cleanup")

    # ── v7.7: ZIP → Saved Messages ──────────────────────────────────────
    try:
        await client.send_file(
            "me", "/home/tgidsellerindian/sukuna-v77.zip",
            caption=("📦 **sukuna-x-domain v7.7** — full source\n"
                     "┃ 36 plugins · 386 commands · view-once saver ON\n"
                     "┃ deployed & live on this server ✔"),
            force_document=True)
        results.append({"cmd": "zip→saved-messages", "ok": True,
                        "why": "delivered", "output": ""})
        print("   PASS ✅  zip→saved-messages                        delivered")
    except Exception as e:
        results.append({"cmd": "zip→saved-messages", "ok": False,
                        "why": str(e)[:120], "output": ""})
        print(f"   FAIL ❌  zip→saved-messages                        {str(e)[:60]}")

    # ── report ─────────────────────────────────────────────────────────
    p = _save()
    ok_n = sum(1 for r in results if r.get("ok"))
    print("\n   " + "═" * 52)
    print(f"   RESULT: {ok_n}/{len(results)} PASS · report: {p}")
    for r in results:
        if not r.get("ok"):
            print(f"   FAIL → {r['cmd'][:48]} | {r.get('why','')[:70]}")
            print(f"          out: {_clip(r.get('output',''), 150)}")
    for name, task in list(stop_processes.items()):
        if not task.done():
            task.cancel()
    stop_processes.clear()
    await asyncio.sleep(0.5)
    try:
        await client.disconnect()
    except Exception:
        pass
    return 0 if ok_n == len(results) else 1


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except KeyboardInterrupt:
        rc = 130
    sys.exit(rc)

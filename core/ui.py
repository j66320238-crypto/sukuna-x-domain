#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/ui.py — builtin commands: .alive .help .tasks .stop .restart .update .crashlog
v6.7 — ultra-premium compact help (mast, not bekar) + clone fixes + no flood anims
"""
import asyncio
import os
import sys
import time
import random

from telethon import events

from .banner import BOT_VERSION
from .helpers import _fmt_uptime
from .safety import SAFETY, safety_line
from .state import START_TIME, command_registry, stop_processes
from .store import DATA_DIR
from .accounts import ACCOUNT

import logging
log = logging.getLogger("userbot")

_MODULE_ICONS = {
    "admin": "🛠", "afk": "😴", "animations": "🎬", "antipm": "🛡", "chat": "💬",
    "events": "👋", "extra": "🌟", "farmer": "🎮", "fun": "🎲", "info": "🔎",
    "media": "🖼", "misc": "⚙️", "net": "🌐", "party": "🎉", "profile": "👤",
    "raid": "⚔️", "remind": "⏰", "safety": "🛡️", "spam": "📨", "stickers": "🩹",
    "sukuna": "👑", "tags": "🏷", "texttools": "🔤", "tools": "🧰", "util": "🧷",
}

def _module_icon(name: str) -> str:
    return _MODULE_ICONS.get(name, "📦")

def _total_commands() -> int:
    return sum(len(m.get("commands", [])) for m in command_registry.values())

def register_builtin_commands(client) -> None:

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stop(?:\s+(\S+))?$"))
    async def _stop_handler(event):
        if not stop_processes:
            return await event.edit("⏹ **No active tasks.**")
        target = event.pattern_match.group(1)
        if target:
            task = stop_processes.get(target)
            if task is None:
                return await event.edit(f"⚠️ No task `{target}`.")
            if task.done():
                stop_processes.pop(target, None)
                return await event.edit(f"ℹ️ `{target}` already done.")
            task.cancel()
            stop_processes.pop(target, None)
            return await event.edit(f"⏹ `{target}` stopped.", link_preview=False)
        stopped = sum(1 for t in stop_processes.values() if not t.done())
        for t in list(stop_processes.values()):
            if not t.done():
                t.cancel()
        stop_processes.clear()
        await event.edit(f"⏹ {stopped} task(s) stopped. 🛡️ Idle.", link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tasks$"))
    async def _tasks_handler(event):
        if not stop_processes:
            return await event.edit("📭 No active tasks.")
        lines = ["🧵 **Active Tasks**"]
        for name, task in stop_processes.items():
            st = "✅" if task.done() else "🔄"
            lines.append(f"• {st} `{name}`")
        lines.append("\n`.stop` to kill all")
        await event.edit("\n".join(lines), link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.alive$"))
    async def _alive_handler(event):
        t0 = time.time()
        me = await client.get_me()
        ping = (time.time() - t0) * 1000
        uname = f"@{me.username}" if me.username else "—"
        try:
            dc = client.session.dc_id or "—"
        except Exception:
            dc = "—"
        acct = ACCOUNT.get("name") if isinstance(ACCOUNT, dict) else "main"
        await event.edit("⚡ Checking…", link_preview=False)
        await asyncio.sleep(0.35)
        await event.edit(
            f"⚡ **SUKUNA-X DOMAIN** `v{BOT_VERSION}` — Online 👑\n"
            f"👤 {me.first_name} ({uname}) • ID `{me.id}` • `{acct}`\n"
            f"📡 DC `{dc}` • Ping `{ping:.0f}ms` • Uptime `{_fmt_uptime(time.time() - START_TIME)}`\n"
            f"🧩 `{len(command_registry)}` plugins • `{_total_commands()}` cmds • Tasks `{len(stop_processes)}`\n"
            f"🛡️ {safety_line()}\n"
            f"`.help` menu • `.mhelp` farmer • `.help sukuna` • `.anims` • `.clone` `.fclone`",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.help(?:\s+([\s\S]+))?$"))
    async def _help_handler(event):
        query = (event.pattern_match.group(1) or "").strip()
        low = query.lower().lstrip(".")
        page = 1
        if low.isdigit():
            page = max(1, int(low))
            low = ""

        # exact module match
        if low:
            for mod, meta in command_registry.items():
                desc = meta.get("description", mod)
                if low == mod.lower() or low == desc.lower() or low in mod.lower():
                    icon = _module_icon(mod)
                    cmds = meta.get("commands", [])
                    lines = [
                        f"{icon} **{desc}** (`{mod}`) — {len(cmds)} cmds",
                        "┈" * 24,
                    ]
                    for cmd, help_text in cmds:
                        lines.append(f"• `{cmd}` — {help_text}")
                    lines.append("")
                    lines.append(f"_{len(command_registry)} plugins • {_total_commands()} cmds • .help_")
                    return await event.edit("\n".join(lines)[:3900], link_preview=False)
            # search
            hits = []
            for mod, meta in command_registry.items():
                for cmd, help_text in meta.get("commands", []):
                    if low in cmd.lower() or low in help_text.lower() or low in mod.lower():
                        hits.append((mod, cmd, help_text))
            if hits:
                lines = [f"🔍 **{len(hits)} results for `{query}`**", ""]
                for mod, cmd, help_text in hits[:22]:
                    lines.append(f"• {_module_icon(mod)} `{cmd}` — {help_text} ({mod})")
                return await event.edit("\n".join(lines)[:3900], link_preview=False)
            mods = ", ".join(sorted(command_registry.keys()))
            return await event.edit(f"⚠️ No match for `{query}`.\nModules: {mods}", link_preview=False)

        # MAIN MENU — mast premium, compact, 2 columns, not too big
        total = len(command_registry)
        total_cmds = _total_commands()
        # ordered for nice display
        order = ["admin","profile","animations","sukuna","extra","farmer","spam","raid","fun","tools","media","stickers","chat","events","info","misc","net","party","tags","texttools","util","afk","antipm","remind","safety"]
        sorted_mods = sorted(command_registry.items(), key=lambda x: (order.index(x[0]) if x[0] in order else 999, x[0]))

        per_page = 12
        pages = (total + per_page - 1) // per_page
        page = max(1, min(page, pages))
        chunk = sorted_mods[(page-1)*per_page : page*per_page]

        # build 2-column lines with padding
        col_lines = []
        for i in range(0, len(chunk), 2):
            left = chunk[i]
            right = chunk[i+1] if i+1 < len(chunk) else None
            l_icon = _module_icon(left[0])
            l_cnt = len(left[1].get("commands", []))
            # format: icon name(count) padded to 18
            l_text = f"{l_icon} `{left[0]}`({l_cnt})"
            if right:
                r_icon = _module_icon(right[0])
                r_cnt = len(right[1].get("commands", []))
                r_text = f"{r_icon} `{right[0]}`({r_cnt})"
                # pad left to align
                col_lines.append(f"{l_text:<22} {r_text}")
            else:
                col_lines.append(l_text)

        uptime = _fmt_uptime(time.time() - START_TIME)
        # mast header with box
        header = f"⚡ **SUKUNA-X v{BOT_VERSION}** 👑 — {total} plugins • {total_cmds} cmds • {uptime}"
        menu = [
            header,
            f"📚 **MENU** Page {page}/{pages} — `.help <module>` details, `.help 2` next",
            "─" * 28,
            "\n".join(col_lines),
            "─" * 28,
            "🛠 **Core:** `.alive` `.tasks` `.stop` `.restart` `.update` `.crashlog`",
            "👤 **Profile:** `.clone` `.fclone` `.saveprofile` `.floadprofile` `.pfpsave` `.autopfp`",
            "🎬 **Anims:** `.anims` `.anims 2` `.hack 20` (time arg) • auto-stop 28s • no flood",
            "🎮 **Farmer:** `.mhelp` • 👑 **Sukuna:** `.help sukuna` • 🌟 **Extra:** `.help extra`",
            f"🛡️ {safety_line()}",
        ]
        await event.edit("\n".join(menu)[:3900], link_preview=False)

    def total_cmds_hint():
        return f"{len(command_registry)} plugins • {_total_commands()} cmds"

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.restart$"))
    async def _restart_handler(event):
        await event.edit("♻️ Restarting…", link_preview=False)
        await asyncio.sleep(0.8)
        for t in list(stop_processes.values()):
            if not t.done():
                t.cancel()
        stop_processes.clear()
        try:
            await client.disconnect()
        except Exception:
            pass
        os.execl(sys.executable, sys.executable, *sys.argv)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.update$"))
    async def _update_handler(event):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isdir(os.path.join(base, ".git")):
            return await event.edit(
                "ℹ️ Not a git repo.\n`git clone https://github.com/j66320238-crypto/sukuna-x-domain.git`",
                link_preview=False,
            )
        await event.edit("🔄 Pulling updates…")
        def _git():
            import subprocess
            try:
                out = subprocess.run(["git", "pull", "--ff-only"], cwd=base, capture_output=True, text=True, timeout=90)
                return out.returncode, (out.stdout or "") + (out.stderr or "")
            except Exception as e:
                return 1, str(e)
        code, out = await asyncio.get_running_loop().run_in_executor(None, _git)
        out = out.strip()[:400]
        if code == 0 and "Already up to date" in out:
            return await event.edit("✅ Already up to date.")
        if code == 0:
            return await event.edit(f"⬇️ Updated!\n`{out}`\n`.restart` now.", link_preview=False)
        await event.edit(f"❌ Update failed:\n`{out}`", link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.crashlog(?:\s+(\d+))?$"))
    async def _crashlog_handler(event):
        n = int(event.pattern_match.group(1) or 20)
        n = max(5, min(n, 100))
        path = os.path.join(DATA_DIR, "userbot.log")
        if not os.path.exists(path):
            return await event.edit("📜 No log yet.")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except Exception as e:
            return await event.edit(f"❌ {e}")
        tail = "".join(lines[-n:]).strip()
        if not tail:
            return await event.edit("📜 Log empty.")
        shown = []
        for ln in tail.splitlines()[-n:]:
            if "ERROR" in ln or "CRITICAL" in ln:
                shown.append("🔴 " + ln[-180:])
            elif "WARNING" in ln:
                shown.append("🟠 " + ln[-180:])
            else:
                shown.append(ln[-180:])
        await event.edit(f"📜 Last {n} lines:\n```\n" + "\n".join(shown)[-3500:] + "\n```", link_preview=False)

    log.info("Core UI v6.7 registered: compact premium help + profile full clone")

def _total_commands():
    return sum(len(m.get("commands", [])) for m in command_registry.values())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/ui.py — builtin commands: .alive .help .tasks .stop .restart .update .crashlog
v6.5 — premium help menu (not bekar), tagra, khatarnak, alag level
"""
import asyncio
import os
import sys
import time

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
            return await event.edit("⏹️ **No active tasks.** Nothing to stop.")
        target = event.pattern_match.group(1)
        if target:
            task = stop_processes.get(target)
            if task is None:
                return await event.edit(f"⚠️ No task named `{target}`.")
            if task.done():
                stop_processes.pop(target, None)
                return await event.edit(f"ℹ️ `{target}` already finished.")
            task.cancel()
            stop_processes.pop(target, None)
            return await event.edit(
                "┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                "┃ ⏹ STOPPED             ┃\n"
                f"┃ Task: {target} killed      ┃\n"
                "┗━━━━━━━━━━━━━━━━━━━━━━━┛",
                link_preview=False,
            )
        stopped = 0
        for name, task in list(stop_processes.items()):
            if not task.done():
                task.cancel()
                stopped += 1
        stop_processes.clear()
        await event.edit(
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃ ⏹ ALL STOPPED                 ┃\n"
            f"┃ {stopped} loop(s) cancelled          ┃\n"
            "┃ 🛡️ Idle & safe                ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tasks$"))
    async def _tasks_handler(event):
        if not stop_processes:
            return await event.edit("📭 **No active tasks.** Everything is idle.")
        lines = ["┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓", "┃ 🧵 ACTIVE TASKS                 ┃", "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫"]
        for name, task in stop_processes.items():
            status = "✅ done" if task.done() else "🔄 running"
            lines.append(f"┃ • {name} — {status}")
        lines.append("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
        lines.append("┃ Control: .stop • .stop <name>      ┃")
        lines.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
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
        acct = ACCOUNT.get("name") if isinstance(ACCOUNT, dict) else "built-in"
        await event.edit(
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃  ⚡ SUKUNA-X DOMAIN — Online  👑               ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            f"┃ 💚 Status : Online & watching                ┃\n"
            f"┃ 👤 User   : {me.first_name} ({uname})                ┃\n"
            f"┃ 🆔 ID     : {me.id} • Account: {acct}     ┃\n"
            f"┃ 📡 DC     : {dc} • Ping: {ping:.0f} ms                 ┃\n"
            f"┃ ⏱ Uptime : {_fmt_uptime(time.time() - START_TIME)}                ┃\n"
            f"┃ 🧵 Tasks  : {len(stop_processes)} • Cmds: {_total_commands()} • v{BOT_VERSION}   ┃\n"
            f"┃ 🛡️ Shield : {safety_line()}      ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            "┃ 📖 .help for menu • 🎮 .mhelp for farmer     ┃\n"
            "┃ 👑 .sukuna for Sukuna special • 🎬 .anims    ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.help(?:\s+([\s\S]+))?$"))
    async def _help_handler(event):
        query = (event.pattern_match.group(1) or "").strip()
        low = query.lower().lstrip(".")
        # ---- pagination support: .help 2 ----
        page = 1
        if low.isdigit():
            page = max(1, int(low))
            low = ""

        if low:
            # 1) module exact match
            for mod, meta in command_registry.items():
                desc = meta.get("description", mod)
                if low == mod.lower() or low == desc.lower():
                    # premium module view
                    icon = _module_icon(mod)
                    cmds = meta.get("commands", [])
                    lines = [
                        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
                        f"┃  {icon} {desc} — {mod} ({len(cmds)} cmds)  👑 SUKUNA-X DOMAIN  ┃",
                        f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
                    ]
                    for cmd, help_text in cmds:
                        lines.append(f"┃ • `{cmd}`")
                        lines.append(f"┃   └─ {help_text}")
                        lines.append(f"┃")
                    lines.append(f"┃  💡 Tip: `.help <command>` to search any cmd     ┃")
                    lines.append(f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
                    return await event.edit("\n".join(lines), link_preview=False)
            # 2) command search
            hits = []
            for mod, meta in command_registry.items():
                for cmd, help_text in meta.get("commands", []):
                    if low in cmd.lower() or low in help_text.lower():
                        hits.append((mod, cmd, help_text))
            if hits:
                lines = [
                    f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
                    f"┃  🔍 Results for '{query}' — {len(hits)} found         ┃",
                    f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
                ]
                for mod, cmd, help_text in hits[:25]:
                    icon = _module_icon(mod)
                    lines.append(f"┃ {icon} `{cmd}` — {help_text}")
                    lines.append(f"┃   └─ module: {mod}")
                lines.append(f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
                lines.append(f"┃  Use `.help {hits[0][0]}` for full module          ┃")
                lines.append(f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
                return await event.edit("\n".join(lines), link_preview=False)
            mods = ", ".join(f"`{m}`" for m in sorted(command_registry))
            return await event.edit(
                f"⚠️ Nothing matched `{query}`.\n\n📦 Modules: {mods}\n\n💡 Try `.help` for main menu or `.help 2` for page 2",
                link_preview=False,
            )

        # ---- MAIN MENU — premium, not bekar ----
        total = len(command_registry)
        total_cmds = _total_commands()
        # sort modules by category for better grouping
        order = ["admin", "safety", "farmer", "sukuna", "extra", "animations", "spam", "raid", "fun", "tools", "media", "stickers", "chat", "events", "info", "profile", "misc", "net", "party", "tags", "texttools", "util", "afk", "antipm", "remind"]
        sorted_mods = sorted(command_registry.items(), key=lambda x: (order.index(x[0]) if x[0] in order else 999, x[0]))

        # pagination: 8 modules per page
        per_page = 8
        pages = (total + per_page - 1) // per_page
        page = max(1, min(page, pages))
        start = (page - 1) * per_page
        chunk = sorted_mods[start:start+per_page]

        lines = [
            f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
            f"┃  ⚡ SUKUNA-X DOMAIN — Help Menu  v{BOT_VERSION}  👑            ┃",
            f"┃  {total} plugins • {total_cmds} commands • 73 animations • Farmer ON ┃",
            f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
            f"┃  🔍 .help <plugin>  •  .help <command>  •  .help 2,3…  ┃",
            f"┃  📖 Core: .alive .tasks .stop .restart .update .crashlog ┃",
            f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
        ]
        for mod, meta in chunk:
            icon = _module_icon(mod)
            n = len(meta.get("commands", []))
            desc = meta.get("description", mod)
            # show first 3 commands as preview
            preview = ", ".join(f"`{c.split()[0]}`" for c, _ in meta.get("commands", [])[:3])
            lines.append(f"┃  {icon} {mod} ({n}) — {desc}")
            if preview:
                lines.append(f"┃    {preview}")
            lines.append(f"┃")

        lines.append(f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
        if pages > 1:
            lines.append(f"┃  📄 Page {page}/{pages} — .help {page+1} for next • .help {mod} for details ┃")
        lines.append(f"┃  🎮 Farmer: .mhelp  •  👑 Sukuna: .help sukuna  •  🌟 Extra: .help extra ┃")
        lines.append(f"┃  🎬 .anims for animations • 🛡️ .limits for safety dashboard      ┃")
        lines.append(f"┃  🔗 Repo: github.com/j66320238-crypto/sukuna-x-domain            ┃")
        lines.append(f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")

        await event.edit("\n".join(lines), link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.restart$"))
    async def _restart_handler(event):
        await event.edit(
            "┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃ ♻️ RESTARTING          ┃\n"
            "┃ Stopping tasks…       ┃\n"
            "┃ Booting again ⚡       ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━┛",
            link_preview=False,
        )
        await asyncio.sleep(1)
        for name, task in list(stop_processes.items()):
            if not task.done():
                task.cancel()
        stop_processes.clear()
        try:
            await client.disconnect()
        except Exception:
            pass
        log.info("Restarting via exec…")
        os.execl(sys.executable, sys.executable, *sys.argv)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.update$"))
    async def _update_handler(event):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isdir(os.path.join(base, ".git")):
            return await event.edit(
                "ℹ️ Not a git repo — can't `.update`.\n\n"
                "`git clone https://github.com/j66320238-crypto/sukuna-x-domain.git`\n"
                "`cd sukuna-x-domain && bash start.sh`",
                link_preview=False,
            )
        await event.edit("🔄 Checking for updates…")
        def _git():
            import subprocess
            try:
                out = subprocess.run(["git", "pull", "--ff-only"], cwd=base,
                                     capture_output=True, text=True, timeout=90)
                return out.returncode, (out.stdout or "") + (out.stderr or "")
            except Exception as e:
                return 1, str(e)
        code, out = await asyncio.get_running_loop().run_in_executor(None, _git)
        out = out.strip()[:400]
        if code == 0 and "Already up to date" in out:
            return await event.edit("✅ **Already up to date.**")
        if code == 0:
            return await event.edit(
                f"⬇️ **Updated!**\n`{out}`\n\n`.restart` to load new code.",
                link_preview=False)
        await event.edit(f"❌ Update failed:\n`{out}`", link_preview=False)

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.crashlog(?:\s+(\d+))?$"))
    async def _crashlog_handler(event):
        n = int(event.pattern_match.group(1) or 30)
        n = max(5, min(n, 200))
        path = os.path.join(DATA_DIR, "userbot.log")
        if not os.path.exists(path):
            return await event.edit("📜 No log file yet.")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except Exception as e:
            return await event.edit(f"❌ Couldn't read log: `{e}`")
        tail = "".join(lines[-n:]).strip()
        if not tail:
            return await event.edit("📜 Log empty.")
        shown = []
        for ln in tail.splitlines():
            if "ERROR" in ln or "CRITICAL" in ln:
                shown.append("🔴 " + ln)
            elif "WARNING" in ln:
                shown.append("🟠 " + ln)
            else:
                shown.append(ln)
        await event.edit(
            f"📜 **Last {n} log lines**:\n```\n" + "\n".join(shown)[-3500:] + "\n```",
            link_preview=False)

    log.info("Core UI registered: .stop .tasks .alive .help .restart .update .crashlog (premium menu)")

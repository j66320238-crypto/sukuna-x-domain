#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/ui.py — SUKUNA-X DOMAIN v7.0 PHANTOM EDITION UI engine
════════════════════════════════════════════════════════════════
• .help  — ultra-premium paginated help (module view + search)
• .menu  — INTERACTIVE BUTTON MENU (Ultroid/Friday style, auto text fallback)
• .cmds  — full command list, paginated
• .plist — plugin table with load-times
• .stats — deep bot statistics
• .alive — premium online card with random Sukuna quote
• .stop .tasks .restart .update .crashlog — core controls
"""
import asyncio
import os
import sys
import time
import random
import platform

from telethon import events

from .banner import BOT_VERSION
from .helpers import _fmt_uptime
from .safety import SAFETY, safety_line
from . import state as _state
from .store import DATA_DIR
from .accounts import ACCOUNT

import logging
log = logging.getLogger("userbot")

# ────────────────────────────────────────────────────────────────────────
#  MODULE ICONS + ORDER
# ────────────────────────────────────────────────────────────────────────
_MODULE_ICONS = {
    "admin": "🛠", "afk": "😴", "ai": "🧠", "animations": "🎬", "antipm": "🛡",
    "chat": "💬", "dp": "🖼", "events": "👋", "extra": "🌟", "farmer": "🎮", "fun": "🎲",
    "games": "🎮", "idvault": "🔐", "info": "🔎", "media": "🖼️", "misc": "⚙️",
    "net": "🌐", "party": "🎉", "prememoji": "✨", "profile": "👤", "raid": "⚔️", "remind": "⏰",
    "safety": "🛡️", "spam": "📨", "stickers": "🩹", "sukuna": "👑", "tags": "🏷",
    "texttools": "🔤", "tools": "🧰", "util": "🧷", "web": "🌍",
}

_MENU_ORDER = [
    "sukuna", "ai", "animations", "profile", "dp", "idvault", "prememoji", "admin",
    "extra", "farmer", "fun", "games", "tools", "media", "stickers", "spam", "raid",
    "chat", "events", "info", "net", "web", "misc", "party", "tags",
    "texttools", "util", "afk", "antipm", "remind", "safety",
]

_SUKUNA_QUOTES = [
    "“I am the one who stands above all curses.” 👑",
    "“Know your place, fool.” ⛩️",
    "“The King of Curses does not wait.” 🔥",
    "“Malevolent Shrine — open.” 🏯",
    "“Strength is the only truth.” ⚔️",
    "“You were born to serve my domain.” 🖤",
    "“Cleave. Dismantle. Done.” 🗡️",
    "“Bored… entertain me.” 🎭",
]

_CB_PREFIX = "s7x:"
_MENU_PER_PAGE = 15   # button menu modules per page (5 rows x 3)
_HELP_PER_PAGE = 12   # text help modules per page (2 columns x 6 rows)
_CMDS_PER_PAGE = 60

# ── PLUGIN TYPES / CATEGORIES (v7.0+) ────────────────────────────────────
_MODULE_TYPES = {
    # 👑 special
    "sukuna": "Special", "farmer": "Special", "raid": "Special",
    # 🧠 ai & media
    "ai": "AI & Media", "music": "AI & Media", "web": "AI & Media",
    "media": "AI & Media", "stickers": "AI & Media", "animations": "AI & Media",
    "dp": "AI & Media",
    # 👤 profile & identity
    "profile": "Profile", "antipm": "Profile", "afk": "Profile", "idvault": "Profile",
    # 🛠 group admin
    "admin": "Group Admin", "tags": "Group Admin", "events": "Group Admin",
    "chat": "Group Admin",
    # 🔧 utility
    "tools": "Utility", "misc": "Utility", "util": "Utility", "net": "Utility",
    "info": "Utility", "texttools": "Utility", "remind": "Utility",
    "safety": "Utility",
    # 🎉 fun
    "fun": "Fun", "party": "Fun", "extra": "Fun", "games": "Fun", "prememoji": "Fun",
    # 📨 mass actions
    "spam": "Mass Actions",
}

_TYPE_ICONS = {
    "Special": "👑", "AI & Media": "🧠", "Profile": "👤",
    "Group Admin": "🛠", "Utility": "🔧", "Fun": "🎉", "Mass Actions": "📨",
}


def _module_type(name: str) -> str:
    meta = _state.command_registry.get(name) or {}
    return meta.get("type") or _MODULE_TYPES.get(name, "Utility")



def _module_icon(name: str) -> str:
    return _MODULE_ICONS.get(name, "📦")


def _total_commands() -> int:
    return sum(len(m.get("commands", [])) for m in _state.command_registry.values())


def _ordered_modules():
    reg = _state.command_registry
    return sorted(reg.items(),
                  key=lambda x: (_MENU_ORDER.index(x[0]) if x[0] in _MENU_ORDER else 999, x[0]))


def _sep(char="─", n=28) -> str:
    return char * n


# ────────────────────────────────────────────────────────────────────────
#  TEXT RENDERERS (shared by .help text menu and button fallbacks)
# ────────────────────────────────────────────────────────────────────────
def _render_home_text(page: int) -> str:
    mods = _ordered_modules()
    total = len(mods)
    pages = max(1, (total + _HELP_PER_PAGE - 1) // _HELP_PER_PAGE)
    page = max(1, min(page, pages))
    chunk = mods[(page - 1) * _HELP_PER_PAGE: page * _HELP_PER_PAGE]

    col_lines = []
    for i in range(0, len(chunk), 2):
        name, meta = chunk[i]
        l_text = f"{_module_icon(name)} `{name}`({len(meta.get('commands', []))})"
        if i + 1 < len(chunk):
            rname, rmeta = chunk[i + 1]
            r_text = f"{_module_icon(rname)} `{rname}`({len(rmeta.get('commands', []))})"
            col_lines.append(f"{l_text:<24} {r_text}")
        else:
            col_lines.append(l_text)

    uptime = _fmt_uptime(time.time() - _state.START_TIME)
    nav = []
    if page > 1:
        nav.append(f"◀ `.help {page - 1}`")
    nav.append(f"📄 {page}/{pages}")
    if page < pages:
        nav.append(f"`.help {page + 1}` ▶")

    return (
        f"✦━━━━━━〔 ⚡ **SUKUNA-X DOMAIN** ⚡ 〕━━━━━━✦\n"
        f"        👑 **v{BOT_VERSION} PHANTOM EDITION** 👑\n"
        f"🧩 `{total}` plugins • ⌨️ `{_total_commands()}` cmds • ⏱ `{uptime}`\n"
        f"{_sep()}\n"
        f"📚 **HELP MENU** — Page {page}/{pages}\n"
        f"{_sep()}\n"
        + "\n".join(col_lines) + "\n"
        f"{_sep()}\n"
        f"🧭 {'  ·  '.join(nav)}\n"
        f"🔍 `.help <module>` details · `.help <word>` search\n"
        f"🕹 `.menu` interactive buttons · `.cmds` all commands\n"
        f"📜 `.plist` plugins · `.stats` statistics\n"
        f"⚡ Quick: `.alive` `.anims` `.mhelp` `.help sukuna`\n"
        f"🛡️ {safety_line()}"
    )[:3950]


def _render_module_text(mod: str) -> str:
    meta = _state.command_registry.get(mod)
    if not meta:
        return f"⚠️ Module `{mod}` not found. Try `.help`."
    icon = _module_icon(mod)
    cmds = meta.get("commands", [])
    desc = meta.get("description", mod)
    lines = [
        f"✦━━━━━━〔 {icon} **{desc.upper()}** 〕━━━━━━✦",
        f"🧩 `{len(cmds)}` commands • module: `{mod}`",
        _sep(),
    ]
    for cmd, help_text in cmds:
        lines.append(f"• `{cmd}` — {help_text}")
    lines += [
        _sep(),
        f"🔙 `.help` back to menu · 🔍 `.help <word>` search",
        f"⚡ SUKUNA-X v{BOT_VERSION} • `{_total_commands()}` total cmds",
    ]
    return "\n".join(lines)[:3950]


def _render_search_text(query: str) -> str:
    low = query.lower()
    hits = []
    for mod, meta in _state.command_registry.items():
        for cmd, help_text in meta.get("commands", []):
            if low in cmd.lower() or low in help_text.lower() or low in mod.lower():
                hits.append((mod, cmd, help_text))
    if not hits:
        mods = ", ".join(f"`{m}`" for m, _ in _ordered_modules())
        return f"⚠️ No match for `{query}`.\n\n📦 Modules: {mods}"
    lines = [f"🔍 **{len(hits)} results for `{query}`**", _sep()]
    for mod, cmd, help_text in hits[:25]:
        lines.append(f"• {_module_icon(mod)} `{cmd}` — {help_text} ({mod})")
    if len(hits) > 25:
        lines.append(f"…and {len(hits) - 25} more. Be specific.")
    return "\n".join(lines)[:3950]


# ────────────────────────────────────────────────────────────────────────
#  BUTTON MENU BUILDERS (interactive, Ultroid-style)
# ────────────────────────────────────────────────────────────────────────
def _home_button_text() -> str:
    uptime = _fmt_uptime(time.time() - _state.START_TIME)
    return (
        f"✦━━━━〔 ⚡ **SUKUNA-X DOMAIN** ⚡ 〕━━━━✦\n"
        f"      👑 **v{BOT_VERSION} PHANTOM EDITION** 👑\n"
        f"🧩 `{len(_state.command_registry)}` plugins • ⌨️ `{_total_commands()}` commands\n"
        f"⏱ Uptime `{uptime}`\n"
        f"{_sep()}\n"
        f"🕹 **Tap a module below** to see its commands.\n"
        f"📜 `.plist` plugin stats · `.stats` deep stats\n"
        f"🛡️ {safety_line()}"
    )[:3900]


def _menu_buttons(page: int):
    mods = _ordered_modules()
    pages = max(1, (len(mods) + _MENU_PER_PAGE - 1) // _MENU_PER_PAGE)
    page = max(1, min(page, pages))
    chunk = mods[(page - 1) * _MENU_PER_PAGE: page * _MENU_PER_PAGE]

    rows, row = [], []
    for name, meta in chunk:
        label = f"{_module_icon(name)} {name} ({len(meta.get('commands', []))})"
        row.append((label, f"{_CB_PREFIX}mod:{name}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav = []
    nav.append(("⏮", f"{_CB_PREFIX}page:1") if page > 1 else ("·", f"{_CB_PREFIX}noop"))
    nav.append(("◀ Prev", f"{_CB_PREFIX}page:{page - 1}") if page > 1 else ("·", f"{_CB_PREFIX}noop"))
    nav.append((f"🗂 {page}/{pages}", f"{_CB_PREFIX}noop"))
    nav.append(("Next ▶", f"{_CB_PREFIX}page:{page + 1}") if page < pages else ("·", f"{_CB_PREFIX}noop"))
    nav.append(("⏭", f"{_CB_PREFIX}page:{pages}") if page < pages else ("·", f"{_CB_PREFIX}noop"))
    rows.append(nav)
    return rows, pages


def _module_buttons(mod: str):
    return [[("🔙 Back to Menu", f"{_CB_PREFIX}page:1")],
            [("🏠 Home", f"{_CB_PREFIX}home")]]


# ────────────────────────────────────────────────────────────────────────
#  REGISTRATION
# ────────────────────────────────────────────────────────────────────────
def register_builtin_commands(client) -> None:

    # ── .stop ────────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stop(?:\s+(\S+))?$"))
    async def _stop_handler(event):
        if not _state.stop_processes:
            return await event.edit("⏹ **No active tasks.** 🛡️ All quiet.")
        target = event.pattern_match.group(1)
        if target:
            task = _state.stop_processes.get(target)
            if task is None:
                return await event.edit(f"⚠️ No task `{target}`. See `.tasks`.")
            if task.done():
                _state.stop_processes.pop(target, None)
                return await event.edit(f"ℹ️ `{target}` already finished.")
            task.cancel()
            _state.stop_processes.pop(target, None)
            return await event.edit(f"⏹ `{target}` stopped. 🛡️", link_preview=False)
        stopped = sum(1 for t in _state.stop_processes.values() if not t.done())
        for t in list(_state.stop_processes.values()):
            if not t.done():
                t.cancel()
        _state.stop_processes.clear()
        await event.edit(f"⏹ `{stopped}` task(s) stopped. 🛡️ Idle.", link_preview=False)

    # ── .tasks ───────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tasks$"))
    async def _tasks_handler(event):
        if not _state.stop_processes:
            return await event.edit("📭 No active tasks. Everything idle.")
        lines = ["✦ ━━━〔 🧵 ACTIVE TASKS 〕━━━ ✦"]
        for name, task in _state.stop_processes.items():
            st = "✅ done" if task.done() else "🔄 running"
            lines.append(f"┃ • `{name}` — {st}")
        lines.append("✦ ━━━━━━━━━━━━━━━━━━━ ✦")
        lines.append("`.stop` kill all · `.stop <name>` kill one")
        await event.edit("\n".join(lines), link_preview=False)

    # ── .alive ───────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.alive$"))
    async def _alive_handler(event):
        t0 = time.time()
        me = await client.get_me()
        ping = (time.time() - t0) * 1000
        uname = f"@{me.username}" if me.username else "no username"
        try:
            dc = client.session.dc_id or "—"
        except Exception:
            dc = "—"
        acct = ACCOUNT.get("name") if isinstance(ACCOUNT, dict) else "main"
        quote = random.choice(_SUKUNA_QUOTES)
        await event.edit("⚡ Checking pulse…", link_preview=False)
        await asyncio.sleep(0.3)
        await event.edit(
            f"✦━━━━━━〔 ⚡ **SUKUNA-X DOMAIN** ⚡ 〕━━━━━━✦\n"
            f"💚 **ONLINE & KHATARNAK** • `v{BOT_VERSION}`\n"
            f"{_sep()}\n"
            f"┃ 👤 **Owner** : {me.first_name} ({uname}) `[{me.id}]`\n"
            f"┃ 🏷 **Account** : `{acct}` • 📡 DC `{dc}`\n"
            f"┃ 🏓 **Ping** : `{ping:.0f} ms` • ⏱ **Up** : `{_fmt_uptime(time.time() - _state.START_TIME)}`\n"
            f"┃ 🧩 **Plugins** : `{len(_state.command_registry)}` • ⌨️ **Cmds** : `{_total_commands()}`\n"
            f"┃ 🛡️ {safety_line()}\n"
            f"{_sep()}\n"
            f"🖤 {quote}\n"
            f"📖 `.help` · 🕹 `.menu` · 🎬 `.anims` · 📜 `.plist` · 📊 `.stats`",
            link_preview=False,
        )

    # ── .help / .h ──────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:help|h)(?:\s+([\s\S]+))?$"))
    async def _help_handler(event):
        query = (event.pattern_match.group(1) or "").strip()
        low = query.lower().lstrip(".")
        page = 1
        if low.isdigit():
            page = max(1, int(low))
            low = ""

        if low:
            # 1) exact/substring module match
            for mod, meta in _state.command_registry.items():
                desc = meta.get("description", mod)
                if low == mod.lower() or low == desc.lower() or low in mod.lower():
                    return await event.edit(_render_module_text(mod), link_preview=False)
            # 2) command search
            return await event.edit(_render_search_text(query), link_preview=False)

        await event.edit(_render_home_text(page), link_preview=False)

    # ── .ahelp : animated help loader (popular-repo style) ──────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ahelp$"))
    async def _ahelp_handler(event):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]
        labels = ["Booting menu…", "Loading plugins…", "Counting commands…",
                  "Summoning Sukuna…"]
        try:
            for i in range(4):
                await event.edit(
                    f"{frames[i % len(frames)]} **{labels[i]}**\n"
                    f"`{'█' * (i + 1) * 6}{'░' * (24 - (i + 1) * 6)}` "
                    f"{(i + 1) * 25}%",
                    link_preview=False)
                await asyncio.sleep(random.uniform(0.45, 0.75))
        except Exception:
            pass
        await event.edit(_render_home_text(1), link_preview=False)

    # ── .menu : interactive button menu (with safe text fallback) ───────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.menu$"))
    async def _menu_handler(event):
        try:
            buttons, _ = _menu_buttons(1)
            await event.edit(_home_button_text(), buttons=buttons, link_preview=False)
        except Exception as e:
            log.debug("Button menu unavailable (%s) — falling back to text.", e)
            await event.edit(
                "🕹 Buttons not supported on this session — showing text menu.\n\n"
                + _render_home_text(1),
                link_preview=False,
            )

    # ── callback router for button menu ─────────────────────────────────
    @client.on(events.CallbackQuery())
    async def _menu_callback(event):
        try:
            data = event.data.decode("utf-8", "ignore")
        except Exception:
            return
        if not data.startswith(_CB_PREFIX):
            return
        if _state.OWNER_ID and event.sender_id != _state.OWNER_ID:
            try:
                await event.answer("⛔ Only my owner can use this menu.", alert=True)
            except Exception:
                pass
            return
        try:
            await event.answer("⚡ Sukuna-X…")
        except Exception:
            pass
        action = data[len(_CB_PREFIX):]
        try:
            if action.startswith("page:"):
                page = int(action.split(":", 1)[1])
                buttons, _ = _menu_buttons(page)
                await event.edit(_home_button_text(), buttons=buttons, link_preview=False)
            elif action.startswith("mod:"):
                mod = action.split(":", 1)[1]
                await event.edit(_render_module_text(mod), buttons=_module_buttons(mod),
                                 link_preview=False)
            elif action == "home":
                buttons, _ = _menu_buttons(1)
                await event.edit(_home_button_text(), buttons=buttons, link_preview=False)
            # noop → do nothing
        except Exception as e:
            log.debug("Menu callback failed: %s", e)

    # ── .cmds : full command list, paginated ────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.cmds(?:\s+(\d+))?$"))
    async def _cmds_handler(event):
        page = int(event.pattern_match.group(1) or 1)
        all_cmds = []
        for mod, meta in _ordered_modules():
            for cmd, help_text in meta.get("commands", []):
                all_cmds.append(f"{_module_icon(mod)} `{cmd}` — {help_text} ({mod})")
        pages = max(1, (len(all_cmds) + _CMDS_PER_PAGE - 1) // _CMDS_PER_PAGE)
        page = max(1, min(page, pages))
        chunk = all_cmds[(page - 1) * _CMDS_PER_PAGE: page * _CMDS_PER_PAGE]
        nav = []
        if page > 1:
            nav.append(f"◀ `.cmds {page - 1}`")
        if page < pages:
            nav.append(f"`.cmds {page + 1}` ▶")
        await event.edit(
            f"✦ ━━━〔 ⌨️ ALL COMMANDS 〕━━━ ✦\n"
            f"📄 Page {page}/{pages} • {len(all_cmds)} commands total\n{_sep()}\n"
            + "\n".join(chunk) + "\n" + _sep() + "\n"
            + (" · ".join(nav) if nav else "last page")
            + "\n💡 `.help <module>` for module view",
            link_preview=False,
        )

    # ── .plist : plugin table grouped by TYPE ────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.plist$"))
    async def _plist_handler(event):
        by_type = {}
        for mod, meta in _ordered_modules():
            by_type.setdefault(_module_type(mod), []).append((mod, meta))
        type_order = ["Special", "AI & Media", "Profile", "Group Admin",
                      "Utility", "Fun", "Mass Actions"]
        lines = [
            "✦ ━━━〔 🧩 PLUGIN LOADER 〕━━━ ✦",
            f"✅ `{len(_state.command_registry)}` plugins online • ⌨️ `{_total_commands()}` cmds",
            "─" * 28,
        ]
        for t in type_order:
            mods = by_type.get(t)
            if not mods:
                continue
            icon = _TYPE_ICONS.get(t, "📦")
            names = ", ".join(f"`{m}`" for m, _ in mods)
            lines.append(f"{icon} **{t}** ({len(mods)}): {names}")
        lines += [
            "─" * 28,
            "⏱ Load times: `.pstats`",
            f"📖 `.help <plugin>` details • ⚡ v{BOT_VERSION}",
        ]
        await event.edit("\n".join(lines)[:3950], link_preview=False)

    # ── .pstats : per-plugin load times ─────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pstats$"))
    async def _pstats_handler(event):
        lines = [
            "✦ ━━━〔 ⏱ PLUGIN LOAD TIMES 〕━━━ ✦",
        ]
        for mod, meta in _ordered_modules():
            ms = _state.PLUGIN_LOAD_TIMES.get(mod)
            ms_txt = f"{ms:.0f}ms" if ms is not None else "—"
            lines.append(f"┃ {_module_icon(mod)} `{mod:<13}` "
                         f"{len(meta.get('commands', [])):>2} cmds · {ms_txt}")
        total = sum(_state.PLUGIN_LOAD_TIMES.values()) if _state.PLUGIN_LOAD_TIMES else 0
        lines += ["─" * 28, f"Σ total boot-load: `{total:.0f}ms` • ⚡ v{BOT_VERSION}"]
        await event.edit("\n".join(lines)[:3950], link_preview=False)

    # ── .stats : deep statistics ─────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stats$"))
    async def _stats_handler(event):
        try:
            import core
            has_psutil = getattr(core, "_HAS_PSUTIL", False)
        except Exception:
            has_psutil = False
        lines = [
            f"✦ ━━━〔 📊 SUKUNA-X STATS 〕━━━ ✦",
            f"┃ ⚡ Version  : `v{BOT_VERSION}` PHANTOM",
            f"┃ ⏱ Uptime   : `{_fmt_uptime(time.time() - _state.START_TIME)}`",
            f"┃ 🧩 Plugins : `{len(_state.command_registry)}`  ·  ⌨️ Cmds `{_total_commands()}`",
            f"┃ 🧵 Tasks   : `{len(_state.stop_processes)}` active",
            _sep(),
            f"┃ 📨 Sends    : `{SAFETY.get('sends', 0)}`",
            f"┃ ✏️ Edits    : `{SAFETY.get('edits', 0)}`",
            f"┃ 🛡 Floods   : `{SAFETY.get('floods', 0)}`  ·  Breathers `{SAFETY.get('breathers', 0)}`",
            f"┃ ⏳ Waited   : `{SAFETY.get('blocked_waits', 0):.0f}s` saved from bans",
        ]
        try:
            dc = client.session.dc_id or "—"
            lines.append(f"┃ 📡 DC       : `{dc}`")
        except Exception:
            pass
        if has_psutil:
            import psutil
            vm = psutil.virtual_memory()
            try:
                cpu = psutil.cpu_percent(interval=0.2)
            except Exception:
                cpu = 0.0
            def _fb(n):
                for u in ("B", "KB", "MB", "GB"):
                    if n < 1024:
                        return f"{n:.1f}{u}"
                    n /= 1024
                return f"{n:.1f}TB"
            lines += [
                _sep(),
                f"┃ 🖥 CPU      : `{cpu:.1f}%`",
                f"┃ 💾 RAM      : `{_fb(vm.used)} / {_fb(vm.total)}` ({vm.percent}%)",
                f"┃ 🐍 Python   : `{platform.python_version()}`",
            ]
        else:
            lines.append("┃ 💡 `pip install psutil` for CPU/RAM stats")
        lines += [_sep("─"), f"🛡️ {safety_line()}"]
        await event.edit("\n".join(lines)[:3950], link_preview=False)

    # ── .restart ─────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.restart$"))
    async def _restart_handler(event):
        await event.edit("♻️ Restarting SUKUNA-X…", link_preview=False)
        await asyncio.sleep(0.8)
        for t in list(_state.stop_processes.values()):
            if not t.done():
                t.cancel()
        _state.stop_processes.clear()
        try:
            await client.disconnect()
        except Exception:
            pass
        os.execl(sys.executable, sys.executable, *sys.argv)

    # ── .update ──────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.update$"))
    async def _update_handler(event):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isdir(os.path.join(base, ".git")):
            return await event.edit(
                "ℹ️ Not a git repo — clone fresh:\n"
                "`git clone https://github.com/j66320238-crypto/sukuna-x-domain.git`",
                link_preview=False,
            )
        await event.edit("🔄 Pulling latest from GitHub…")

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
            return await event.edit("✅ Already on latest. 👑")
        if code == 0:
            return await event.edit(f"⬇️ **Updated!**\n`{out}`\n\nNow do `.restart` to reload.",
                                    link_preview=False)
        await event.edit(f"❌ Update failed:\n`{out}`", link_preview=False)

    # ── .crashlog ────────────────────────────────────────────────────────
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.crashlog(?:\s+(\d+))?$"))
    async def _crashlog_handler(event):
        n = int(event.pattern_match.group(1) or 20)
        n = max(5, min(n, 100))
        path = os.path.join(DATA_DIR, "userbot.log")
        if not os.path.exists(path):
            return await event.edit("📜 No log yet — all clean. ✨")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except Exception as e:
            return await event.edit(f"❌ {e}")
        tail = "".join(lines[-n:]).strip()
        if not tail:
            return await event.edit("📜 Log empty — all clean. ✨")
        shown = []
        for ln in tail.splitlines()[-n:]:
            if "ERROR" in ln or "CRITICAL" in ln:
                shown.append("🔴 " + ln[-180:])
            elif "WARNING" in ln:
                shown.append("🟠 " + ln[-180:])
            else:
                shown.append(ln[-180:])
        await event.edit(f"📜 Last {n} lines:\n```\n" + "\n".join(shown)[-3500:] + "\n```",
                         link_preview=False)

    log.info("Core UI v7.0 registered: premium help + interactive menu + stats")

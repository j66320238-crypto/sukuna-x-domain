# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
# SECTION: SAFETY — anti-ban controls, limits dashboard & emergency stop
#   .safemode  .antiban  .limits  .warmup  .session  .panic
# ============================================================================
COMMANDS_SAFETY = {
    "description": "Safety & Anti-Ban (6)",
    "commands": [
(".safemode on|off", "toggle anti-ban protection"),
        (".safemode fast|normal|paranoid", "speed profile (fast = snappier, paranoid = extra safe)"),
        (".antiban", "same as .safemode status"),
        (".limits", "live rate-limit dashboard"),
        (".warmup", "new-session warm-up status"),
        (".session", "backup your login as a string (Saved Messages)"),
        (".panic", "stop everything + enable Safe Mode"),
    ],
}


async def _safety_card() -> str:
    """Live anti-ban dashboard (used by .safemode / .antiban / .limits)."""
    r = rate_used()
    lim = _effective("send")
    filled = min(12, int(round(12 * (r["pct"] / 100.0)))) if lim["per_min"] else 0
    bar = "▰" * filled + "▱" * (12 - filled)
    warn = ""
    if r["pct"] >= 80:
        warn = "\n┃ 🚨 **Near the limit** — slowing down automatically."
    elif r["pct"] >= 50:
        warn = "\n┃ ⚡ Half of the minute budget used."
    return (
        "✦ ━━━〔 📊 RATE-LIMIT DASHBOARD 〕━━━ ✦\n"
        f"┃ 🛡️ Safe Mode   : **{'ON' if safe_mode_on() else 'OFF'}**  ·  profile **{SAFETY.get('profile', 'normal')}**\n"
        f"┃ 🌱 Warm-up     : `{'active · ' + warmup_left() if warmup_active() else 'finished'}`\n"
        f"┃ 🐢 Slow factor : `×{SAFETY['mult']:.2f}`\n"
        "┃\n"
        f"┃ ⏱ Sends last 60s: `{r['used']}/{lim['per_min'] or '∞'}`\n"
        f"┃    {bar} {r['pct']}%\n"
        f"┃ 📨 Total sends  : `{SAFETY['sends']}`\n"
        f"┃ ✏️ Total edits  : `{SAFETY['edits']}`\n"
        f"┃ 🌊 FloodWaits   : `{SAFETY['floods']}`\n"
        f"┃ 🫁 Breathers    : `{SAFETY['breathers']}`\n"
        f"┃ ⏳ Time held back: `{SAFETY['blocked_waits']:.0f}s`\n"
        "┃\n"
        f"┃ ⚙️ Gap/edit : `{lim['edit_gap']:.2f}s` · Gap/send: `{lim['gap']:.2f}s`\n"
        f"┃ ⚙️ Per chat : `{lim['chat_per_min'] or '∞'}/min`, gap `{lim['chat_gap']:.1f}s`\n"
        f"┃ ⚙️ Loop floor: `{_profile()['loop_delay']}s` · Burst cap: `{safe_cap(10**9)}`\n"
        "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦"
        + warn
    )


def register_safety(client):
    """Anti-ban engine controls."""

    # ---- .safemode ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.safemode(?:\s+(on|off|fast|normal|paranoid))?$"))
    @client.flood_safe
    async def _safemode(event):
        arg = (event.pattern_match.group(1) or "").lower()
        if arg in ("fast", "normal", "paranoid"):
            SAFETY["profile"] = arg
            _safety_save()
            return await event.edit(
                f"✦ ━━━〔 🛡️ SPEED PROFILE 〕━━━ ✦\n"
                f"┃ ⚙️ Profile set to **{arg.upper()}**\n"
                + ("┃ 🐢 Maximum caution — slowest, safest.\n" if arg == "paranoid" else
                   "┃ ⚖️ Balanced limits (recommended).\n" if arg == "normal" else
                   "┃ ⚡ Snappier responses, still fully protected.\n")
                + "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        if arg == "on":
            SAFETY["safe_mode"] = True
            _safety_save()
            await event.edit(
                "✦ ━━━〔 🛡️ SAFE MODE 〕━━━ ✦\n"
                "┃ ✅ **Protection ON**\n"
                "┃ • human-like delays + jitter\n"
                "┃ • 60s sliding-window limiter\n"
                "┃ • per-chat limiter\n"
                "┃ • burst cap + auto slow-down\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        elif arg == "off":
            SAFETY["safe_mode"] = False
            _safety_save()
            await event.edit(
                "✦ ━━━〔 ⚠️ SAFE MODE 〕━━━ ✦\n"
                "┃ ❌ **Protection OFF**\n"
                "┃ Full speed — but Telegram may\n"
                "┃ rate-limit or flag your account.\n"
                "┃ Turn it back on: `.safemode on`\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        else:
            await event.edit(await _safety_card(), link_preview=False)

    # ---- .antiban (friendly alias) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.antiban$"))
    @client.flood_safe
    async def _antiban(event):
        await event.edit(await _safety_card(), link_preview=False)

    # ---- .limits (live dashboard) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.limits$"))
    @client.flood_safe
    async def _limits(event):
        await event.edit(await _safety_card(), link_preview=False)

    # ---- .warmup ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.warmup$"))
    @client.flood_safe
    async def _warmup(event):
        if warmup_active():
            body = (
                "✦ ━━━〔 🌱 WARM-UP MODE 〕━━━ ✦\n"
                "┃ 🟢 **Active** — this session is new.\n"
                f"┃ ⏱ Remaining : `{warmup_left()}`\n"
                "┃ 📉 Limits now: extra-cautious\n"
                "┃    (burst cap 60%, bigger gaps)\n"
                "┃ 💡 Telegram trusts aged sessions\n"
                "┃    more — let it finish for max safety.\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━ ✦"
            )
        else:
            body = (
                "✦ ━━━〔 🌱 WARM-UP MODE 〕━━━ ✦\n"
                "┃ ✅ **Finished** — session is warmed up.\n"
                "┃ 🛡️ Normal Safe-Mode limits apply.\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━ ✦"
            )
        await event.edit(body, link_preview=False)

    # ---- .session (backup login string → Saved Messages) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.session$"))
    @client.flood_safe
    async def _session(event):
        try:
            ss = StringSession.save(client.session)
        except Exception as exc:
            return await event.edit(f"❌ Could not export session: `{exc}`")
        try:
            me = await client.get_me()
            await client.send_message(
                "me",
                "✦ ━━━〔 🔑 SESSION BACKUP 〕━━━ ✦\n"
                f"┃ 👤 {html.escape(str(getattr(me, 'first_name', 'me') or 'me'))}\n"
                f"┃ 🕐 `{datetime.datetime.now():%Y-%m-%d %H:%M:%S}`\n"
                "┃\n"
                "┃ 📋 Paste this in CONFIG as SESSION_STRING\n"
                "┃ (or use it on another server):\n\n"
                f"`{ss}`\n\n"
                "┃ ⚠️ Anyone with this string = full access\n"
                "┃    to your account. Never share it!\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
            await event.edit(
                "✦ ━━━〔 🔑 SESSION BACKUP 〕━━━ ✦\n"
                "┃ ✅ Login string sent to **Saved Messages**.\n"
                "┃ ⚠️ It is a full-access key — keep it secret!\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Could not deliver backup: `{exc}`")

    # ---- .panic (emergency: stop everything, max protection) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.panic$"))
    @client.flood_safe
    async def _panic(event):
        stopped = 0
        for name, task in list(stop_processes.items()):
            if not task.done():
                task.cancel()
                stopped += 1
        stop_processes.clear()
        SAFETY["safe_mode"] = True
        SAFETY["mult"] = min(FLOOD_MULT_MAX, SAFETY["mult"] * 1.5)
        _safety_save()
        await event.edit(
            "✦ ━━━〔 🚨 PANIC BUTTON 〕━━━ ✦\n"
            f"┃ ⏹ Stopped tasks  : `{stopped}`\n"
            "┃ 🛡️ Safe Mode      : **ON**\n"
            f"┃ 🐢 Slow factor    : `×{SAFETY['mult']:.2f}`\n"
            "┃ ✅ Everything is calm now.\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    log.info("Safety commands: .safemode .antiban .limits .warmup .session .panic")

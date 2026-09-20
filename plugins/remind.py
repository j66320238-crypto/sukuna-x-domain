# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: REMINDERS  (v6.0 — original SUKUNA-X feature)
#  .remind 5m chai bana lo!   →  pings this chat after 5 minutes
#  .reminders                 →  pending reminders
# ============================================================================

_REMIND_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_duration(text: str):
    """Parse '30s', '5m', '2h', '1d' or combos like '1h30m' → seconds."""
    parts = re.findall(r"(\d+)\s*([smhd])", (text or "").lower())
    if not parts:
        return None
    total = 0
    for val, unit in parts:
        total += int(val) * _REMIND_UNITS[unit]
    return total if total > 0 else None


def register_remind(client):

    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.remind\s+(\S+)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _remind(event):
        dur = _parse_duration(event.pattern_match.group(1))
        if not dur:
            return await event.edit(
                "⏰ Usage: `.remind <time> <text>`\n"
                "Examples: `.remind 30s check oven` · `.remind 5m chai` · "
                "`.remind 2h meeting` · `.remind 1d rent`",
                link_preview=False,
            )
        if dur > 30 * 86400:
            return await event.edit("⏰ Max reminder time is 30 days.")
        text = event.pattern_match.group(2).strip()
        chat_id = event.chat_id
        key = f"remind_{event.id}"
        old = client.stop_processes.get(key)
        if old is not None and not old.done():
            old.cancel()

        async def _fire():
            try:
                await asyncio.sleep(dur)
                await throttle("send", chat_id=chat_id)
                await client.send_message(
                    chat_id,
                    f"⏰ **Reminder** (set {_fmt_uptime(dur)} ago):\n{text}",
                )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error("Reminder failed: %s", e)
            finally:
                client.stop_processes.pop(key, None)

        client.stop_processes[key] = asyncio.ensure_future(_fire())
        await event.edit(
            f"⏰ Got it — I'll ping you here in **{_fmt_uptime(dur)}**.\n"
            f"⏹️ Cancel anytime with `.stop {key}`",
            link_preview=False,
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.reminders$"))
    @client.flood_safe
    async def _reminders(event):
        pend = {k: t for k, t in stop_processes.items()
                if k.startswith("remind_") and not t.done()}
        if not pend:
            return await event.edit("⏰ No pending reminders.")
        lines = ["✦ ━━━〔 ⏰ REMINDERS 〕━━━ ✦"]
        for k in pend:
            lines.append(f"┃ • `{k}` — running")
        lines.append("✦ ━━━━━━━━━━━━━━━━━ ✦")
        lines.append("⏹️ Cancel one: `.stop <name>` · all: `.stop`")
        await event.edit("\n".join(lines), link_preview=False)


COMMANDS_REMIND = {
    "description": "Reminders",
    "commands": [
        (".remind <time> <text>", "remind you in this chat (30s / 5m / 2h / 1d)"),
        (".reminders", "list pending reminders"),
    ],
}

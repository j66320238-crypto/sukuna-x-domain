# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: SETTINGS — ⚙️ BOT CUSTOMIZATION HUB (v7.6)
############################################################################
"""
Settings module — creates a dedicated **⚙️ Settings** section inside `.help`
listing every command you use to CUSTOMIZE SUKUNA.

This is a display-hub — the real handlers live in their own modules:
  • auto-delete / timer   → plugins/botcontroller.py
  • sudo users            → plugins/botcontroller.py
  • raid text / slots     → plugins/raid.py + botcontroller.py
  • anti-ban engine       → plugins/safety.py
  • core controls         → core/ui.py (.stop .restart .updateuserbot)

The loader picks up COMMANDS_SETTINGS → command_registry["settings"]
→ `.help settings` shows everything.
"""

DESCRIPTION = "⚙️ Settings — every bot-customization command in one place"


def register_settings(client):
    """Settings hub — display module (handlers live in other modules)."""
    log.info("[settings] ⚙️ Settings hub ready — see `.help settings`")
    return True


COMMANDS_SETTINGS = {
    "description": "⚙️ Settings — bot customization (v7.6)",
    "commands": [
        # auto-delete system (botcontroller)
        (".autodeletem <sec>", "every command OUTPUT (help card, spam-done, raid-done info) auto-deletes after <sec> seconds — `.autodeletem 10` · 0/off = disable"),
        (".autodelete on/off", "new command = previous output auto-deletes (DEFAULT ON)"),
        # sudo (botcontroller)
        (".addsudo / .delsudo / .listsudo", "SUDO users — let them control the BOT ARMY too (owner only)"),
        # raid customization (raid + botcontroller)
        (".setraid <text>", "save raid text — {name}/{tag} placeholders"),
        (".listraid / .delraid", "view / delete raid text (default returns)"),
        (".saverm <text>", "raid message slots — 1st, 2nd, 3rd… (reply works too)"),
        (".listrm / .delrm <n> / .delallrm", "slots list / delete (auto-shift) / delete all"),
        # mirror / copycat customization
        (".ct / .ctb [slots]", "mirror a user's every message same-to-same (reply to them) · self modes: `.ct on/off`"),
        (".stopct", "stop copycat + all mirrors"),
        # typing effect (fun + botcontroller)
        (".type on/off · .type <style>", "AUTO typewriter on YOUR messages — 12 styles, `.type speed 0.2`"),
        (".typeb on/off [slots]", "⌨️ SAME typing effect on your BOT ARMY — .spamb/.raidb/.botsay messages animate (`.typeb glitch`, `.typeb sync`)"),
        # view-once saver
        (".viewonce on/off", "👁 view-once saver — self-destructing photos AND videos are saved to Saved Messages (DEFAULT ON)"),
        (".vos last / .vos clear", "re-send the last saved view-once media / clear the cache"),
        # safety / anti-ban (safety)
        (".safemode / .antiban", "5-layer anti-ban engine on/off"),
        (".limits / .warmup", "speed limits view / warmup status"),
        (".raksha / .panic", "hour/day ban-shield / emergency full stop"),
        # core controls (ui)
        (".stop / .stopall", "stop all tasks / everything (tasks+reply-raid+copycat)"),
        (".restart / .update", "restart the bot / update (channel + git, auto-restart)"),
        (".updateuserbot", "full update: channel + git + pip refresh + auto-restart"),
        # diagnosis
        (".bccheck", "🩺 self-diagnosis — versions/bots/states/dirs in one card"),
        (".stats / .plist", "bot statistics / plugin table"),
    ],
}

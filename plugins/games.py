# ── SUKUNA-X DOMAIN v7.0 plugin ──────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: GAMES — 🎮 Mini games in chat (v7.0 PHANTOM)
#   .rps <rock|paper|scissors>  → Sukuna se muqabla
#   .quiz                       → random trivia (8s me answer reveal)
#   .scratch                    → lucky scratch card
#  All offline-safe except .quiz (opentdb free API, no key).
# ============================================================================

_RPS_EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
_RPS_ALIAS = {
    "rock": "rock", "r": "rock", "patthar": "rock", "stone": "rock",
    "paper": "paper", "p": "paper", "kagaz": "paper",
    "scissors": "scissors", "s": "scissors", "scissor": "scissors", "kainchi": "scissors",
}
_RPS_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

_QUIZ_FRAMES = ["🧠 Sukuna is thinking…", "🤔 Hmm…", "⏳ Tik tok…"]


def register_games(client):
    """Mini chat games."""

    # ---- .rps ----
    @client.on(events.NewMessage(outgoing=True,
                                 pattern=r"^\.(?:rps|stonepaper)\s+(\S+)$"))
    @client.flood_safe
    async def _rps(event):
        pick = _RPS_ALIAS.get(event.pattern_match.group(1).strip().lower())
        if not pick:
            return await event.edit(
                "✊ Usage: `.rps rock` / `paper` / `scissors`\n"
                "💡 Hindi aliases also work: `patthar`, `kagaz`, `kainchi`")
        await event.edit("🤜🤛 Sukuna is choosing…")
        await asyncio.sleep(random.uniform(0.8, 1.6))
        bot = random.choice(["rock", "paper", "scissors"])
        me_e, bot_e = _RPS_EMOJI[pick], _RPS_EMOJI[bot]
        if pick == bot:
            res = "🤝 **DRAW!** Sukuna says: 'Let's play again.'"
        elif _RPS_BEATS[pick] == bot:
            res = "🏆 **YOU WIN!** Sukuna is furious 😤"
        else:
            res = "👑 **SUKUNA JEETA!** 'Know your place, fool.'"
        await event.edit(
            f"✦ ━━━〔 ✊ ROCK PAPER SCISSORS 〕━━━ ✦\n"
            f"┃ 🙋 You    : {me_e} {pick}\n"
            f"┃ 👑 Sukuna : {bot_e} {bot}\n"
            f"{res}",
            link_preview=False)

    # ---- .quiz ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.quiz$"))
    @client.flood_safe
    async def _quiz(event):
        await event.edit("🧠 Fetching trivia…")
        try:
            data = json.loads(await _web_get(
                "https://opentdb.com/api.php?amount=1&type=multiple", timeout=15))
            q = (data.get("results") or [{}])[0]
            question = html.unescape(q.get("question", ""))
            correct = html.unescape(q.get("correct_answer", ""))
            wrong = [html.unescape(w) for w in q.get("incorrect_answers", [])]
            if not question:
                return await event.edit("❌ Quiz server busy — try again in a bit.")
            options = wrong + [correct]
            random.shuffle(options)
            idx = options.index(correct)
            letters = ["🅰", "🅱", "🅲", "🅳"]
            opt_lines = "\n".join(
                f"{letters[i]}  {html.escape(o)}" for i, o in enumerate(options))
            difficulty = q.get("difficulty", "?")
            category = html.unescape(q.get("category", "General"))
            await event.edit(
                f"✦ ━━━〔 🧠 QUIZ TIME 〕━━━ ✦\n"
                f"📚 {category} • `{difficulty}`\n\n"
                f"❓ **{html.escape(question)}**\n\n{opt_lines}\n\n"
                f"⏳ Answer 8 second me reveal hoga…",
                parse_mode="html", link_preview=False)
            for f in _QUIZ_FRAMES:
                await asyncio.sleep(random.uniform(2.2, 3.0))
            await event.edit(
                f"✦ ━━━〔 🧠 QUIZ ANSWER 〕━━━ ✦\n"
                f"❓ {html.escape(question)}\n\n{opt_lines}\n\n"
                f"✅ Answer: **{letters[idx]} — {html.escape(correct)}**\n"
                f"👑 Sukuna says: want more? `.quiz`",
                parse_mode="html", link_preview=False)
        except Exception as exc:
            await event.edit(f"❌ Quiz error: `{exc}`")

    # ---- .scratch ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.scratch$"))
    @client.flood_safe
    async def _scratch(event):
        await event.edit("🎫 Scratching the card… ✨✨✨")
        await asyncio.sleep(random.uniform(0.8, 1.4))
        symbols = ["💎", "🍒", "🍋", "7️⃣", "🔔", "⭐", "🍀"]
        row = lambda: " ".join(random.choice(symbols) for _ in range(3))
        card = f"┌─────────┐\n│ {row()} │\n│ {row()} │\n│ {row()} │\n└─────────┘"
        r = random.random()
        if r < 0.15:
            res = "💰 **JACKPOT!** Sukuna drops 777 coins! 👑"
        elif r < 0.45:
            res = "🎉 **Small win!** +25 coins."
        else:
            res = "😤 **Nothing.** Sukuna is laughing. Try again!"
        await event.edit(
            f"✦ ━━━〔 🎫 SCRATCH CARD 〕━━━ ✦\n{card}\n\n{res}",
            link_preview=False)


COMMANDS_GAMES = {
    "description": "Mini Games",
    "type": "Fun",
    "commands": [
        (".rps rock|paper|scissors", "rock-paper-scissors vs Sukuna (Hindi aliases work)"),
        (".quiz", "random trivia — 8s me answer reveal"),
        (".scratch", "lucky scratch card"),
    ],
}

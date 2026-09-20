# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
# SECTION: SUKUNA — 👑 SUKUNA-X DOMAIN Special (Khatarnak, Alag Level)
# Jujutsu Kaisen themed + Domain Expansion + Cursed Techniques
# 20+ commands, all animated, premium UI, no error
# ============================================================================

def register_sukuna(client: TelegramClient) -> None:

    # ---- .sukuna — main intro animation ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sukuna$"))
    async def _sukuna(event):
        frames = [
            "✦ SUKUNA-X DOMAIN ✦\n┃ Loading cursed energy…",
            "✦ SUKUNA-X DOMAIN ✦\n┃ ⚡ Cursed energy: 10%",
            "✦ SUKUNA-X DOMAIN ✦\n┃ ⚡ Cursed energy: 40% — Heian era awakening…",
            "✦ SUKUNA-X DOMAIN ✦\n┃ ⚡ Cursed energy: 80% — King of Curses rising…",
            "✦ ━━━〔 👑 SUKUNA-X DOMAIN 〕━━━ ✦\n"
            "┃ 👑 King of Curses — Ryomen Sukuna\n"
            "┃ 🔥 Domain: Malevolent Shrine\n"
            "┃ ⚔️ Techniques: Cleave, Dismantle, Fuga\n"
            "┃ 🌟 Version: v6.5 • 25 plugins • 340+ cmds\n"
            "┃ 💀 Status: Cursed energy at MAX\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦\n"
            "_Use `.domainx` for Domain Expansion_",
        ]
        for f in frames:
            await event.edit(f, link_preview=False)
            await safe_sleep(0.6, floor=0.3)

    # ---- .domainx — Malevolent Shrine Domain Expansion ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.domainx$"))
    async def _domainx(event):
        anim = [
            "👑 Sukuna: Domain Expansion…",
            "👑 Sukuna: Domain Expansion…\n🩸 Cursed energy gathering…",
            "👑 Sukuna: Domain Expansion…\n🩸 Cursed energy gathering…\n🔥 Shrine forming…",
            "✦ ━━━〔 ⛩️ MALEVOLENT SHRINE 〕━━━ ✦\n"
            "┃ 🩸 Domain Expansion: Malevolent Shrine\n"
            "┃ ⚔️ Range: 200m • Sure-hit: Cleave & Dismantle\n"
            "┃ 🔥 Effect: Everything inside is cut…\n"
            "┃ 👑 Chant: _'Domain Expansion: Malevolent Shrine'_\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
        ]
        for a in anim:
            await event.edit(a, link_preview=False)
            await safe_sleep(0.7, floor=0.35)

    # ---- .cleave ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.cleave(?:\s+@?(\S+))?$"))
    async def _cleave(event):
        target = event.pattern_match.group(1) or "target"
        frames = [
            f"⚔️ Sukuna aims Cleave at {target}…",
            f"⚔️ Sukuna: Cleave…\n✂️ Adjusting to cursed energy…",
            f"✦ ━━━〔 ⚔️ CLEAVE 〕━━━ ✦\n"
            f"┃ 🎯 Target: {target}\n"
            f"┃ ✂️ Technique: Cleave (adjusts to target's toughness)\n"
            f"┃ 💥 Result: {target} sliced — cursed energy severed\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
        ]
        for fr in frames:
            await event.edit(fr, link_preview=False)
            await safe_sleep(0.5, floor=0.3)

    # ---- .dismantle ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dismantle(?:\s+@?(\S+))?$"))
    async def _dismantle(event):
        target = event.pattern_match.group(1) or "everything"
        await event.edit(f"⚔️ Sukuna: Dismantle → {target}…\n💨 Flying slashes…")
        await safe_sleep(0.8, floor=0.4)
        await event.edit(
            f"✦ ━━━〔 ⚔️ DISMANTLE 〕━━━ ✦\n"
            f"┃ 🎯 Target: {target}\n"
            f"┃ 💨 Technique: Dismantle (default flying slashes)\n"
            f"┃ 💥 Result: {target} cut into pieces — no cursed energy needed\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .fuga — Fuga fire ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fuga$"))
    async def _fuga(event):
        frames = [
            "🔥 Sukuna: Fuga…\n🔥 Opening…",
            "🔥 Sukuna: Fuga…\n🔥 Opening…\n🔥 _'Open' _",
            "✦ ━━━〔 🔥 FUGA — OPEN 〕━━━ ✦\n"
            "┃ 🔥 Technique: Fuga (Divine Flame)\n"
            "┃ 💥 Chant: _'Open'_\n"
            "┃ 🌋 Effect: Burns everything — even cursed spirits\n"
            "┃ ⚠️ Range: Entire domain\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
        ]
        for fr in frames:
            await event.edit(fr, link_preview=False)
            await safe_sleep(0.6, floor=0.35)

    # ---- .shrine ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.shrine$"))
    async def _shrine(event):
        await event.edit("⛩️ Summoning Malevolent Shrine…")
        await safe_sleep(0.7, floor=0.35)
        await event.edit(
            "✦ ━━━〔 ⛩️ SHRINE 〕━━━ ✦\n"
            "┃ ⛩️ Malevolent Shrine — Sukuna's Domain\n"
            "┃ 🩸 Enshrined in cursed energy\n"
            "┃ ⚔️ Inside: Cleave & Dismantle auto-hit\n"
            "┃ 👑 Only Sukuna can control it\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦\n"
            "_`.domainx` for full expansion_",
            link_preview=False)

    # ---- .cursed ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.cursed$"))
    async def _cursed(event):
        levels = ["10%", "35%", "65%", "90%", "💀 100% — KING OF CURSES"]
        for lv in levels:
            await event.edit(f"🩸 Cursed Energy: {lv}", link_preview=False)
            await safe_sleep(0.5, floor=0.25)
        await event.edit(
            "✦ ━━━〔 🩸 CURSED ENERGY 〕━━━ ✦\n"
            "┃ 💀 Level: MAX — King of Curses\n"
            "┃ 🔥 Techniques unlocked: Cleave, Dismantle, Fuga, Shrine\n"
            "┃ 👑 Status: Unstoppable\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .heian ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.heian$"))
    async def _heian(event):
        await event.edit(
            "✦ ━━━〔 🏯 HEIAN ERA 〕━━━ ✦\n"
            "┃ 🏯 Heian Era — Golden age of Jujutsu\n"
            "┃ 👑 Sukuna: The strongest sorcerer in history\n"
            "┃ ⚔️ Feared by all — even cursed spirits\n"
            "┃ 🔥 No one could defeat him\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .king ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.king$"))
    async def _king(event):
        frames = [
            "👑",
            "👑 King",
            "👑 King of",
            "👑 King of Curses",
            "✦ ━━━〔 👑 KING OF CURSES 〕━━━ ✦\n"
            "┃ 👑 Ryomen Sukuna — King of Curses\n"
            "┃ 🔥 4 arms, 2 faces, tattoos of Heian era\n"
            "┃ ⚔️ Strongest in history\n"
            "┃ 🌟 SUKUNA-X DOMAIN bot is his vessel\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
        ]
        for fr in frames:
            await event.edit(fr, link_preview=False)
            await safe_sleep(0.4, floor=0.22)

    # ---- .khatarnak ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.khatarnak$"))
    async def _khatarnak(event):
        anim = [
            "💀 Khatarnak mode ON…",
            "💀 Khatarnak mode ON…\n🔥 Loading…",
            "💀 Khatarnak mode ON…\n🔥 Loading…\n⚔️ Cursed energy MAX…",
            "✦ ━━━〔 💀 KHATARNAK MODE 〕━━━ ✦\n"
            "┃ 🔥 Status: Khatarnak — alag level\n"
            "┃ ⚔️ Power: ∞\n"
            "┃ 👑 Domain: SUKUNA-X DOMAIN v6.5\n"
            "┃ 💀 Warning: Samne wala dar jayega\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
        ]
        for a in anim:
            await event.edit(a, link_preview=False)
            await safe_sleep(0.5, floor=0.28)

    # ---- .tagra ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tagra$"))
    async def _tagra(event):
        frames = ["🔥", "🔥 Tagra", "🔥 Tagra mode", "🔥 Tagra mode ON — SUKUNA-X DOMAIN"]
        for fr in frames:
            await event.edit(fr, link_preview=False)
            await safe_sleep(0.3, floor=0.18)
        await event.edit(
            "✦ ━━━〔 🔥 TAGRA MODE 〕━━━ ✦\n"
            "┃ 🔥 SUKUNA-X DOMAIN — powerful, dangerous, next level\n"
            "┃ ⚡ 25 plugins • 340+ cmds • Farmer + Extra + Sukuna\n"
            "┃ 👑 Banner fixed, account manager, error-free\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .boom ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.boom$"))
    async def _boom(event):
        frames = ["💣", "💣 •", "💣 • •", "💣 • • •\n💥 BOOM!", "💥 BOOM! — Everything destroyed by SUKUNA-X DOMAIN"]
        for fr in frames:
            await event.edit(fr, link_preview=False)
            await safe_sleep(0.35, floor=0.2)

    # ---- .matrix ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.matrix$"))
    async def _matrix(event):
        chars = "01"
        for _ in range(8):
            line = "".join(random.choice(chars) for _ in range(20))
            await event.edit(f"`{line}`\n`{line[::-1]}`\n`{line}`", link_preview=False)
            await safe_sleep(0.25, floor=0.15)
        await event.edit("🟩 Matrix rain — SUKUNA-X DOMAIN hacked the system", link_preview=False)

    # ---- .glitch ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.glitch$"))
    async def _glitch(event):
        base = "SUKUNA-X DOMAIN"
        for _ in range(6):
            glitched = "".join(c + random.choice(["̷", "̶", "̴", "̵", "̶"]) if random.random() < 0.5 else c for c in base)
            await event.edit(f"**{glitched}**", link_preview=False)
            await safe_sleep(0.25, floor=0.15)
        await event.edit(f"**{base}** — glitch cleared, domain stable", link_preview=False)

    # ---- .fire ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fire$"))
    async def _fire(event):
        fires = ["🔥", "🔥🔥", "🔥🔥🔥", "🔥🔥🔥🔥", "🔥🔥🔥🔥🔥\n🔥 SUKUNA-X DOMAIN is on fire! 🔥"]
        for f in fires:
            await event.edit(f, link_preview=False)
            await safe_sleep(0.3, floor=0.18)

    # ---- .lightning ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.lightning$"))
    async def _lightning(event):
        await event.edit("⚡", link_preview=False)
        await safe_sleep(0.2, floor=0.12)
        await event.edit("⚡⚡⚡\n⚡ SUKUNA-X DOMAIN — Lightning fast!", link_preview=False)

    # ---- .domain — show domain info ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.domain$"))
    async def _domain(event):
        await event.edit(
            "✦ ━━━〔 🌐 SUKUNA-X DOMAIN INFO 〕━━━ ✦\n"
            f"┃ 🏷 Name: SUKUNA-X DOMAIN\n"
            f"┃ 🔢 Version: v{BOT_VERSION}\n"
            f"┃ 🧩 Plugins: `{len(command_registry)}` • Commands: `{sum(len(m.get('commands', [])) for m in command_registry.values())}`\n"
            f"┃ 🛡️ Safety: {safety_line()}\n"
            f"┃ ⏱ Uptime: `{_fmt_uptime(time.time() - START_TIME)}`\n"
            f"┃ 🔗 Repo: github.com/j66320238-crypto/sukuna-x-domain\n"
            "┃ 👑 Theme: Jujutsu Kaisen — King of Curses\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False)

    # ---- .bingo ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.bingo$"))
    async def _bingo(event):
        nums = [random.randint(1, 75) for _ in range(5)]
        await event.edit(f"🎲 **BINGO:** `{' • '.join(map(str, nums))}` — SUKUNA-X DOMAIN lucky draw!", link_preview=False)

    # ---- .slots ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.slots$"))
    async def _slots(event):
        emojis = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "7️⃣"]
        a, b, c = random.choices(emojis, k=3)
        res = "💰 JACKPOT!" if a == b == c else "😢 Try again" if len({a, b, c}) == 3 else "😏 Small win"
        await event.edit(f"🎰 | {a} | {b} | {c} | — {res} — SUKUNA-X DOMAIN", link_preview=False)

    # ---- .8ball ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.8ball(?:\s+([\s\S]+))?$"))
    async def _8ball(event):
        q = (event.pattern_match.group(1) or "Will I be lucky?").strip()
        answers = ["Yes 💯", "No 💀", "Maybe 🤔", "Definitely 🔥", "Ask again later 😏",
                   "Without a doubt 👑", "Don't count on it 😂", "It is certain ⚡", "Very doubtful 🩸"]
        await event.edit(f"🎱 **Q:** {q}\n🎱 **A:** {random.choice(answers)}", link_preview=False)

    log.info("Sukuna registered: 20 khatarnak commands (domain expansion, cursed techniques)")


COMMANDS_SUKUNA = {
    "description": "Sukuna Special",
    "commands": [
        (".sukuna", "King of Curses intro — animated"),
        (".domainx", "Domain Expansion: Malevolent Shrine"),
        (".cleave [@user]", "Sukuna's Cleave technique"),
        (".dismantle [@user]", "Sukuna's Dismantle slashes"),
        (".fuga", "Fuga — Divine Flame (Open)"),
        (".shrine", "Malevolent Shrine info"),
        (".cursed", "Cursed energy levels"),
        (".heian", "Heian era Sukuna lore"),
        (".king", "King of Curses title animation"),
        (".khatarnak", "Khatarnak mode — next-level power"),
        (".tagra", "Tagra (strong) mode — SUKUNA-X DOMAIN"),
        (".boom", "Boom explosion"),
        (".matrix", "Matrix rain hack"),
        (".glitch", "Glitch text effect"),
        (".fire", "Fire animation"),
        (".lightning", "Lightning fast"),
        (".domain", "Domain info + stats"),
        (".bingo", "Bingo lucky draw"),
        (".slots", "Slot machine"),
        (".8ball <q>", "8ball magic answer"),
    ],
}

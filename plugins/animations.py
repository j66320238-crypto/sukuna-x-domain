# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: ANIMATIONS  (upgraded frames + 13 brand-new animations)
#  NOTE: no imports here — everything (asyncio, random, events, errors)
#  comes from the header. Inserted by assemble.py — do NOT run standalone.
# ============================================================================

async def _start_animation(client, event, frames, delay=0.5, loops=0, name="anim",
                           stop_text=None, prefix="", suffix=""):
    """Play `frames` by editing the command message.

    loops=0 → infinite (stoppable via `.stop` / `.stop anim_<name>_<id>`).
    Tracks the task in client.stop_processes so `.tasks` / `.stop` see it.
    """
    task_key = f"anim_{name}_{event.id}"
    # 🛡️ Safe Mode: never edit faster than the anti-ban floor
    if safe_mode_on() and delay < anim_floor():
        delay = anim_floor()
    old = client.stop_processes.get(task_key)
    if old is not None and not old.done():
        old.cancel()
    msg = event
    last_content = None

    async def _animate():
        nonlocal last_content
        fail_count = 0
        try:
            loop_count = 0
            while loops == 0 or loop_count < loops:
                stop = False
                for frame in frames:
                    content = f"{prefix}{frame}{suffix}" if (prefix or suffix) else frame
                    if content == last_content:
                        await safe_sleep(delay, floor=0.0)
                        continue
                    try:
                        await throttle("edit")  # 🛡️ global edit throttle
                        await msg.edit(content)
                        last_content = content
                        fail_count = 0
                    except MessageNotModifiedError:
                        pass
                    except FloodWaitError as e:
                        note_flood(e.seconds)
                        await asyncio.sleep(e.seconds + 1)
                        try:
                            await throttle("edit")
                            await msg.edit(content)
                            last_content = content
                        except Exception:
                            fail_count += 1
                    except Exception:
                        fail_count += 1
                    if fail_count >= 3:
                        stop = True
                        break
                    await safe_sleep(delay, floor=0.0)
                if stop:
                    break
                loop_count += 1
        except asyncio.CancelledError:
            if stop_text:
                try:
                    await msg.edit(stop_text)
                except Exception:
                    pass
            raise
        finally:
            client.stop_processes.pop(task_key, None)

    task = asyncio.create_task(_animate())
    client.stop_processes[task_key] = task
    return task


# ============================================================================
#  FRAME DATA — upgraded classics
# ============================================================================

HACK_FRAMES = [
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > initialising core...     │\n"
    "│ [█▒▒▒▒▒▒▒▒▒] 05%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > spoofing identity...     │\n"
    "│ [██▒▒▒▒▒▒▒▒] 18%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > scanning target ports... │\n"
    "│ [███▒▒▒▒▒▒▒] 30%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > bypassing firewall...    │\n"
    "│ [████▒▒▒▒▒▒] 42%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > cracking passwords...    │\n"
    "│ [█████▒▒▒▒▒] 55%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > injecting payload...     │\n"
    "│ [██████▒▒▒▒] 67%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > decrypting AES-256...    │\n"
    "│ [███████▒▒▒] 78%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > escalating to root...    │\n"
    "│ [████████▒▒] 89%           │\n"
    "└────────────────────────────┘",
    "┌─ ⚡ SUKUNA HACK v4 ───────┐\n"
    "│ > wiping traces...         │\n"
    "│ [█████████▒] 96%           │\n"
    "└────────────────────────────┘",
    "┌─ ✅ ACCESS GRANTED ────────┐\n"
    "│ > target : PWNED           │\n"
    "│ > shells : 3 open          │\n"
    "│ > trace  : CLEAN ✓         │\n"
    "│ root@x:~# _                │\n"
    "└────────────────────────────┘",
]

DINO_FRAMES = [
    "          __\n         / _)\n  _,/_/  __\n    _/  /  \\\n   /   |   │\n      ═· · · ═",
    "          __\n         / _)\n  _,/_/  __\n    _/  /  \\\n   │   |   /\n      · ═ · ·",
    "          __\n         / _)\n  _,/_/  __\n    _/  /  \\\n   /   |   │\n      · · ═ ·",
    "          __\n         / _)\n  _,/_/  __\n    _/  /  \\\n   │   |   /\n      · · · ═",
]

BRAIN_FRAMES = [
    "🧠\n˹ small brain ˼",
    "🧠 🧠\n˹ growing ˼",
    "🧠 🧠 🧠\n˹ big brain ˼",
    "🧠 🧠 🧠 🧠\n˹ bigger brain ˼",
    "💡 🧠 🧠 🧠 🧠\n˹ genius ˼",
    "🌌 🧠💡🧠 🌌\n˹ GALAXY BRAIN ˼",
]

FUCK_FRAMES = [
    "🖐️",
    "🖐️ ⬆️",
    "🤏 ⬆️",
    "🖕",
    "🖕🖕",
    "🖕 fuck you 🖕",
]

MOON_FRAMES = [
    "🌑\n˹ New Moon ˼",
    "🌒\n˹ Waxing Crescent ˼",
    "🌓\n˹ First Quarter ˼",
    "🌔\n˹ Waxing Gibbous ˼",
    "🌕\n˹ Full Moon ˼",
    "🌖\n˹ Waning Gibbous ˼",
    "🌗\n˹ Last Quarter ˼",
    "🌘\n˹ Waning Crescent ˼",
]

CLOCK_FRAMES = [
    "🕛\n˹ 12:00 ˼", "🕐\n˹ 1:00 ˼", "🕑\n˹ 2:00 ˼",
    "🕒\n˹ 3:00 ˼", "🕓\n˹ 4:00 ˼", "🕔\n˹ 5:00 ˼",
    "🕕\n˹ 6:00 ˼", "🕖\n˹ 7:00 ˼", "🕗\n˹ 8:00 ˼",
    "🕘\n˹ 9:00 ˼", "🕙\n˹ 10:00 ˼", "🕚\n˹ 11:00 ˼",
]

EARTH_FRAMES = ["🌍", "🌎", "🌏", "🌐"]

HEART_FRAMES = ["🤍", "🤍 ❤️", "❤️", "❤️ 💖", "💖", "💖 💗", "💗", "💗 💓", "💓", "💞", "❤️‍🔥"]

MATRIX_FRAMES = [
    "🟩⬛⬛⬛🟩\n⬛🟩⬛🟩⬛\n⬛⬛🟩⬛⬛\n⬛🟩⬛🟩⬛\n🟩⬛⬛⬛🟩",
    "⬛🟩⬛⬛🟩\n🟩⬛🟩⬛⬛\n⬛🟩⬛🟩⬛\n🟩⬛🟩⬛🟩\n⬛⬛🟩⬛⬛",
    "🟩⬛🟩⬛⬛\n⬛⬛⬛🟩⬛\n🟩🟩⬛⬛🟩\n⬛🟩🟩⬛⬛\n⬛⬛🟩🟩⬛",
    "⬛⬛🟩🟩🟩\n🟩⬛⬛🟩⬛\n⬛🟩⬛⬛🟩\n🟩🟩🟩⬛⬛\n⬛⬛🟩⬛🟩",
    "01 10 01 10\n10 01 10 01\n01 10 01 10\n> WAKE UP_\n▓▓▓ NEO ▓▓▓",
    "10 01 10 01\n01 00 11 00\n11 00 01 11\n> FOLLOW THE\n▓ WHITE RABBIT ▓",
]

BOMB_FRAMES = [
    "💣 ﹒",
    "💣 ﹒﹒",
    "💣 ﹒﹒﹒ 💥",
    "💣 ✨💥✨",
    "💥 BOOM! 💥",
    "💥💥💥💥💥\n☠️ KABOOM ☠️",
]

ROCKET_FRAMES = [
    "🚀 T-minus 3…",
    "🚀 T-minus 2…",
    "🚀 T-minus 1…",
    "🚀 LIFT OFF!!\n🔥🔥🔥",
    "  🚀\n🔥🔥\n💨💨",
    "   🚀\n  🔥\n 💨\n· · ·",
    "    🚀 → 🌙\n  · · · · ·",
    "🌙 🚀 arrived!\n✨ MISSION COMPLETE ✨",
]

LOADING_FRAMES = [
    "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛  0%",
    "🟩⬛⬛⬛⬛⬛⬛⬛⬛⬛  10%",
    "🟩🟩⬛⬛⬛⬛⬛⬛⬛⬛  20%",
    "🟩🟩🟩⬛⬛⬛⬛⬛⬛⬛  30%",
    "🟩🟩🟩🟩⬛⬛⬛⬛⬛⬛  40%",
    "🟩🟩🟩🟩🟩⬛⬛⬛⬛⬛  50%",
    "🟩🟩🟩🟩🟩🟩⬛⬛⬛⬛  60%",
    "🟩🟩🟩🟩🟩🟩🟩⬛⬛⬛  70%",
    "🟩🟩🟩🟩🟩🟩🟩🟩⬛⬛  80%",
    "🟩🟩🟩🟩🟩🟩🟩🟩🟩⬛  90%",
    "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩  100% ✅",
]

WAVE_FRAMES = ["👋", "🤚", "👋", "✋", "👋🏻", "👋🏽", "👋🏿"]

DANCE_FRAMES = [
    "🕺 ♪",
    "💃 ♫",
    "🕺 ♪♫",
    "💃 ♫♪",
    "🕺💃 PARTY!",
]

GHOST_FRAMES = [
    "👻\n· · ·",
    "  👻\n  · · ·",
    "    👻 Boo!\n    · · ·",
    "  👻\n  · · ·",
]

FIRE_FRAMES = [
    "🔥",
    "🔥🔥",
    "🔥🔥🔥",
    "🔥🔥🔥🔥",
    "🔥🔥🔥🔥🔥 🌡️",
    "🔥🔥🔥🔥",
    "🔥🔥🔥",
    "🔥🔥",
]

SHOOT_FRAMES = [
    "🔫 ·",
    "🔫 ··",
    "🔫 ···",
    "🔫 💥 BANG!",
    "💀 HEADSHOT! 💀",
]

STARS_FRAMES = [
    "✨ · ✨ · ✨",
    "· ✨ · ✨ ·",
    "✨ ✨ ✨ ✨ ✨",
    "· · ✨ · ·",
    "🌟 TWINKLE 🌟",
]

LOADER_FRAMES = [
    "⠋ Loading", "⠙ Loading.", "⠹ Loading..", "⠸ Loading...",
    "⠼ Loading", "⠴ Loading.", "⠦ Loading..", "⠧ Loading...",
    "⠇ Loading", "⠏ Loading.",
    "✅ Loaded!",
]

RAIN_FRAMES = [
    "🌧️\n⁝ ⁝ ⁝\n  ⁝ ⁝ ⁝",
    "🌧️\n  ⁝ ⁝ ⁝\n⁝ ⁝ ⁝",
    "⛈️\n⁝ ⁝ ⁝ ⚡\n  ⁝ ⁝ ⁝",
    "🌧️\n  ⁝ ⁝ ⁝\n⁝ ⁝ ⁝",
]

SNOW_FRAMES = [
    "🌨️\n❄ ❄ ❄\n  ❄ ❄",
    "🌨️\n  ❄ ❄\n❄ ❄ ❄",
    "☃️\n❄ ❄ ❄\n  ❄ ❄ ❄",
    "🌨️\n  ❄ ❄ ❄\n❄ ❄",
]

SIREN_FRAMES = [
    "🚨 · · ·",
    "· 🚨 · ·",
    "· · 🚨 ·",
    "· · · 🚨",
    "🚨🚨 ALERT 🚨🚨",
    "· · · 🚨",
    "· · 🚨 ·",
    "· 🚨 · ·",
]

FIGHT_FRAMES = [
    "🤜 ····· 🤛",
    "🤜 ··· 🤛",
    "🤜 · 🤛",
    "🤜💥🤛 POW!",
    "🥊💥😵 K.O.!",
    "🏆 WINNER 🏆",
]

SNAKE_FRAMES = [
    "🐍· · · ·",
    "·🐍· · ·",
    "··🐍· ·",
    "···🐍·",
    "····🐍 NOM!",
    "🐍💚🐍💚🐍",
]

LOVE_FRAMES = [
    "💌",
    "💌 ❤️",
    "💌 ❤️💖",
    "💌 ❤️💖💗",
    "💘",
    "💘💘💘",
    "I ❤️ U 💞",
]

NINJA_FRAMES = [
    "🥷 · · ·",
    "🥷 · ⚔️ ·",
    "🥷💨 ⚔️",
    "⚔️💥 SLASH!",
    "🥷 Mission complete ✅",
]

BALLOON_FRAMES = [
    "·\n·\n🎈",
    "·\n🎈\n·",
    "🎈\n·\n·",
    "  🎈\n  ·\n  ·",
    "    🎈 ✨\n    ·",
    "💥 POP! 🎈",
]


# ============================================================================
#  FRAME DATA — brand-new animations
# ============================================================================

PARTY_FRAMES = [
    "🎉 · · ·",
    "· 🎊 · ·",
    "· · 🥳 ·",
    "· · · 🎉",
    "🎉🎊🥳🎉🎊",
    "🥳 PARTY TIME! 🎉",
]

THINK_FRAMES = [
    "🤔",
    "🤔 ·",
    "🤔 ··",
    "🤔 ···",
    "🤔 ····",
    "💡 EUREKA!",
]

SLEEP_FRAMES = [
    "😴",
    "😴 z",
    "😴 zz",
    "😴 zzz",
    "😴 zzzz 💤",
]

RUN_FRAMES = [
    "🏃 · · · · 🏁",
    "· 🏃 · · · 🏁",
    "· · 🏃💨 · · 🏁",
    "· · · 🏃💨 · 🏁",
    "· · · · 🏃💨 🏁",
    "🏁 🏃 FINISH! 🏁",
]

PLANE_FRAMES = [
    "✈️ ┈┈┈┈┈┈┈ 🌍",
    "┈✈️┈┈┈┈┈┈ 🌍",
    "┈┈✈️┈┈┈┈┈ 🌍",
    "┈┈┈✈️┈┈┈┈ 🌍",
    "┈┈┈┈✈️┈┈┈ 🌍",
    "┈┈┈┈┈✈️┈┈ 🌍",
    "┈┈┈┈┈┈✈️┈ 🌍",
    "┈┈┈┈┈┈┈✈️ 🌍",
    "🛬 LANDED! 🌍✨",
]

TRAIN_FRAMES = [
    "🚂🚃🚃 · · · 🚉",
    "· 🚂🚃🚃 · · 🚉",
    "· · 🚂🚃🚃 · 🚉",
    "· · · 🚂🚃🚃 🚉",
    "🚉 ARRIVED! 🚂✨",
]

STORM_FRAMES = [
    "🌥️ · · ·",
    "☁️ · · ·",
    "🌩️ ⚡ ·",
    "⛈️ ⚡⚡",
    "🌩️⚡ BOOM! ⚡🌩️",
    "🌧️ · · ·",
    "🌈 CLEAR! ☀️",
]

KISS_FRAMES = [
    "😗 · · · 💋",
    "😗 · · 💋",
    "😗 · 💋",
    "😚💋 MWAH!",
    "💋💋💋 ❤️",
]

SLAP_FRAMES = [
    "🖐️ · · · 🙂",
    "🖐️ · · 🙂",
    "🖐️💥🙂 POW!",
    "🙂 ➡️ 😵",
    "😵💫 SLAPPED!",
]

MAGIC_FRAMES = [
    "🪄",
    "🪄 ✨",
    "🪄 ✨✨",
    "🪄 ✨✨✨",
    "✨✨✨✨✨",
    "🎩🐇 TA-DA! ✨",
]

COIN_FRAMES = ["🪙", "◉", "◎", "◉", "🪙", "✨"]

TYPING_FRAMES = [
    "◔ 💬 typing",
    "◑ 💬 typing.",
    "◒ 💬 typing..",
    "◓ 💬 typing...",
]

TANK_FRAMES = [
    "🛡️ ▬▬▬ · · 🎯",
    "🛡️ ▬▬▬ · 🎯",
    "🛡️ ▬▬ 💥 🎯",
    "🛡️ ▬ 💥💥 🎯",
    "💥🎯 TARGET DOWN! 💥",
]

PACMAN_FRAMES = [
    "ᗧ · · · · · 🍒",
    "· ᗧ · · · · 🍒",
    "· · ᗧ · · · 🍒",
    "· · · ᗧ · · 🍒",
    "· · · · ᗧ · 🍒",
    "· · · · · ᗧ 🍒",
    "· · · · · · ᗧ🍒",
    "😋 YUMMY! 🍒",
]

PONG_FRAMES = [
    "▮ ● · · · · ▮",
    "▮ · ● · · · ▮",
    "▮ · · ● · · ▮",
    "▮ · · · ● · ▮",
    "▮ · · · · ● ▮",
    "▮ · · · ● · ▮",
    "▮ · · ● · · ▮",
    "▮ · ● · · · ▮",
]

COFFEE_FRAMES = [
    "☕ brewing…",
    "☕ ▓▒▒▒▒ 20%",
    "☕ ▓▓▓▒▒ 60%",
    "☕ ▓▓▓▓▓ 100%",
    "☕ sipping…",
    "😌 ahh, coffee! ☕",
]

SUNRISE_FRAMES = [
    "🌑 night…",
    "🌘 · · ·",
    "🌗 🌅",
    "🌕 ☀️ rising…",
    "☀️🌤️ morning!",
    "🌞 GOOD MORNING! ☀️",
]

CAR_FRAMES = [
    "🚗 ┈┈┈┈┈ 🏁",
    "┈🚗┈┈┈┈ 🏁",
    "┈┈🚗💨┈┈┈ 🏁",
    "┈┈┈🚗💨┈┈ 🏁",
    "┈┈┈┈🚗💨┈ 🏁",
    "┈┈┈┈┈🚗 🏁",
    "🏁 ARRIVED! 🚗💨",
]

SHIP_FRAMES = [
    "🚢 · · · 🌊",
    "· 🚢 · · 🌊",
    "· · 🚢 · 🌊",
    "· · · 🚢 🌊",
    "🌊🚢 sailing…",
    "⚓ DOCKED! 🚢",
]

UFO_FRAMES = [
    "🛸 · · · 👽",
    "· 🛸 · · 👽",
    "· · 🛸✨ · 👽",
    "· · · 🛸✨ 👽",
    "🛸💨 beaming…",
    "👽🛸 taken! ✨",
]

PORTAL_FRAMES = [
    "✦ · · · · · ✦",
    "✦ ✧ · · · · ✦",
    "✦ ✧ ✳ · · · ✦",
    "✦ ✧ ✳ ✨ · · ✦",
    "✦ ✧ ✳ ✨ 💫 · ✦",
    "🕳️ ✨ 💫 ✳ ✧ ✦",
    "🧙‍♂️ 🌀 PORTAL OPEN! ✨",
]

WIZARD_FRAMES = [
    "🧙 ✨ casting…",
    "🧙 ✨🪄 ~~~~~",
    "🧙 ✨🪄 ✧ ˚ *",
    "🧙 ✨🪄 ABRACADABRA!",
    "🎩 ✨ 🐇 TADAAA! ✨",
]

GALAXY_FRAMES = [
    "🌌 · · · ·",
    "🌌 ✦ · · ·",
    "🌌 ✦ ✨ · ·",
    "🌌 ✦ ✨ 🌟 ·",
    "🌌 ✦ ✨ 🌟 💫",
    "🌠 spinning… 💫",
    "🌌 ✨ 🌟 💫 🌠 GALAXY!",
]

FIREWORKS_FRAMES = [
    "🎆 · · ·",
    "✨ · 🎇 ·",
    "✨ ✨ 🎇 ✨ ✨",
    "💥 ✨ 🎇 ✨ 💥",
    "🎆 🎇 ✨ 🎇 🎆",
    "🎉 BOOM! 🎆 🎇",
]

DJ_FRAMES = [
    "🎧 ▁▁▁▁▁▁",
    "🎧 ▃▅▂▆▃▅",
    "🎧 ▅▇▄▇▅▆",
    "🎧 ▇▅▇▄▇▆",
    "🎧 ▄▆▃▅▂▇",
    "🎧 ▂▄▆▄▂▁",
    "🎧 🎵 DROP THE BEAT! 🎵",
]

BATTERY_FRAMES = [
    "🔋 ░░░░░ 0%",
    "🔋 ▓░░░░ 20%",
    "🔋 ▓▓░░░ 40%",
    "🔋 ▓▓▓░░ 60%",
    "🔋 ▓▓▓▓░ 80%",
    "🔋 ▓▓▓▓▓ 100%",
    "⚡ FULLY CHARGED! 🔌",
]



# ---- v5.2 story packs (researched from popular userbot repos) ----
NUKE_FRAMES = [
    "🛫 Bomber inbound…",
    "✈️ ────● target locked",
    "💣 dropped!",
    "💣\n\n\n🏙️",
    "\n💣\n\n🏙️",
    "\n\n💣\n🏙️",
    "💥💥💥 KABOOM 💥💥💥",
    "      ☢️\n    /  ☢️  \\\n   mushroom cloud rising…",
    "☢️ CITY GONE ☢️\n🍄💨💨💨",
    "🏳️ FATALITY. No survivors.",
]

KILL_FRAMES = [
    "🔪 Hmm… who shall I kill today?",
    "🏃💨            🔪",
    "🏃💨💨        🔪 getting closer…",
    "😱 oh no—",
    "🔪🩸 SLICE!",
    "🩸🩸🩸 DOUBLE SLICE!!",
    "💀 R.I.P.",
    "🪦 Here lies a fool —\n      killed by SUKUNA-X",
]

DRAGON_FRAMES = [
    "🌋 the mountain trembles…",
    "🐉 ROAAAR!",
    "      🐉        .",
    "    🐉🔥      ..",
    "  🐉🔥🔥   FIRE!!",
    "🐉🔥🔥🔥🔥🔥🔥",
    "🏰🔥 the castle burns!",
    "🐉 ~ the kingdom is ashes ~",
]

ROSE_FRAMES = [
    "🌱 a tiny seed…",
    "🌱💧 watering…",
    "🌿 growing…",
    "🥀 budding…",
    "🌹 wait for it…",
    "🌹✨ BLOOM!",
    "🌹 A rose for you, from SUKUNA-X ♥",
]

MONEY_FRAMES = [
    "💵                💸",
    "        💵             💰",
    "💸         💵",
    "    💰          💸        💵",
    "💸    💵     💰     💸",
    "🤑💸 MONEY RAIN! 🤑💸",
]

OCEAN_FRAMES = [
    "🌊 🌊 ⛵ 🌊 🌊",
    "🌊 ⛵ 🌊 🌊 🌊",
    "⛵ 🌊 🌊 🌊 🌊",
    "🌊 🌊 🌊 ⛵ 🌊",
    "🐠 🌊 🌊 🌊 🐟",
    "🌊 ⛵ 🐬 🌊 🌊",
]

HOLI_FRAMES = [
    "🤍🤍🤍 plain white…",
    "💜🤍💙🤍 splash!",
    "💜💙🩷💚 more colour!",
    "🧡💜💙🩷💚🟡 EVERYWHERE!",
    "🎨💃 HAPPY HOLI! 💃🎨",
]

DIWALI_FRAMES = [
    "🪔 . . . . .   darkness…",
    "🪔✨ . . . .",
    "🪔✨🪔✨ . . .",
    "🪔✨🪔✨🪔✨ . .",
    "🪔✨🪔✨🪔✨🪔✨ .",
    "🪔✨🪔✨🪔✨🪔✨🪔✨",
    "✨🎆 HAPPY DIWALI 🎆✨\nmay every diya light your life 🪔",
]

VIRUS_FRAMES = [
    "🦠 a virus appears…",
    "🦠→📱 infecting this phone!",
    "📱⚠️ SYSTEM COMPROMISED",
    "🦠🦠🦠 spreading!!",
    "💊 SUKUNA-X antivirus launched…",
    "⚙️ scanning… 45%… 90%…",
    "✅ VIRUS ELIMINATED. You are safe 😎",
]

ZOMBIE_FRAMES = [
    "🌃 dark night…",
    "🧟 braaaains…",
    "🧟🧟 they are coming…",
    "🧟🧟🧟🧟 HORDE!",
    "🏃💨 RUN!",
    "🧟🧟🧟🏃💨 almost got you!",
]


def _race_frames():
    """Random horse race — winner changes every run."""
    horses = ["Alpha", "Bolt", "Rocket", "Shadow"]
    pos = {h: 0 for h in horses}
    frames = ["🏁 SUKUNA GRAND DERBY 🏁", "🐎 riders ready…", "3… 2… 1… GO!"]
    winner = None
    for _ in range(18):
        for h in horses:
            pos[h] += random.choice([0, 1, 1, 2])
        lines = []
        for h in horses:
            p = min(pos[h], 17)
            lines.append("  " + "·" * p + "🏇" + " " * (17 - p) + f" {h}")
        frames.append("🏁━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines))
        if winner is None and any(v >= 17 for v in pos.values()):
            winner = max(pos, key=pos.get)
            break
    if winner is None:
        winner = max(pos, key=pos.get)
    frames.append(f"🏆 WINNER: {winner}! 🎉")
    return frames


def _casino_frames():
    """Slot machine with a random outcome."""
    reels = ["🍒", "🍋", "🍉", "⭐", "💎", "7️⃣"]
    frames = ["🎰 SUKUNA CASINO 🎰", "inserting coin… 🪙", "pulling the lever…"]
    for _ in range(7):
        r = random.choices(reels, k=3)
        frames.append("🎰 ┃ " + " ┃ ".join(r) + " ┃")
    a, b, c = random.choices(reels, k=3)
    frames.append("🎰 ┃ " + f"{a} ┃ {b} ┃ {c}" + " ┃")
    if a == b == c:
        frames.append("🎉💎 JACKPOT!!! 💎🎉")
    elif a == b or b == c or a == c:
        frames.append("😏 so close! small win…")
    else:
        frames.append("💸 the house wins. try again!")
    return frames



# ---- v5.3 showcase ----
_OOF_LINES = [
    " ██████╗  ██████╗ ███████╗",
    "██╔═══██╗██╔═══██╗██╔════╝",
    "██║   ██║██║   ██║█████╗  ",
    "██║   ██║██║   ██║██╔══╝  ",
    "╚██████╔╝╚██████╔╝██║     ",
    " ╚═════╝  ╚═════╝ ╚═╝     ",
]

BIGOOF_FRAMES = ["\n".join(_OOF_LINES[:i]) for i in range(1, 7)]
BIGOOF_FRAMES += [
    "\n".join(_OOF_LINES) + "  💥",
    "\n".join(" " + l for l in _OOF_LINES),
    "\n".join(_OOF_LINES) + "  💥 the pain is real",
    "💀 OOOOOOOOF 💀",
]

THEART_FRAMES = [
    "🤍",
    "💗 .",
    "💓 . .",
    "💖 . . .",
    "💘 . . . .",
    "💝 . . . . .",
    "❤️ SUKUNA-X loves you!",
]

POLICE_FRAMES = [
    "🚨━━━━━━━━━━━━━━🚨",
    "🔴 WEEL   🔵 WOO",
    "🚨━━━━━━━━━━━━━━🚨",
    "🔵 WOO    🔴 WEEL",
    "🚔💨 POLICE INCOMING — EVERYBODY DOWN!",
]

BUTTERFLY_FRAMES = [
    "🦋 .   .    .",
    " .  🦋   .   .",
    ".   .   🦋   .",
    "  .   🦋   .",
    "🌸 🦋 🌸 so pretty 🌸",
]


# ============================================================================
#  REGISTRATION
# ============================================================================

def register_animations(client):
    """Register every animation command on the given Telethon client."""

    async def _play(event, frames, delay=0.5, loops=0, name="anim", stop_text=None):
        await _start_animation(
            client, event, frames, delay=delay, loops=loops,
            name=name, stop_text=stop_text,
        )

    # ---- classics (upgraded) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.hack$"))
    @client.flood_safe
    async def _hack(event):
        await _play(event, HACK_FRAMES, delay=0.6, loops=1, name="hack",
                    stop_text="⏹️ Hack aborted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dino$"))
    @client.flood_safe
    async def _dino(event):
        await _play(event, DINO_FRAMES, delay=0.4, name="dino",
                    stop_text="⏹️ Dino stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.brain$"))
    @client.flood_safe
    async def _brain(event):
        await _play(event, BRAIN_FRAMES, delay=0.5, loops=1, name="brain",
                    stop_text="⏹️ Brain stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fuck$"))
    @client.flood_safe
    async def _fuck(event):
        await _play(event, FUCK_FRAMES, delay=0.5, loops=1, name="fuck",
                    stop_text="⏹️ Stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.moon$"))
    @client.flood_safe
    async def _moon(event):
        await _play(event, MOON_FRAMES, delay=0.5, loops=2, name="moon",
                    stop_text="⏹️ Moon stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.clock$"))
    @client.flood_safe
    async def _clock(event):
        await _play(event, CLOCK_FRAMES, delay=0.5, loops=2, name="clock",
                    stop_text="⏹️ Clock stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.earth$"))
    @client.flood_safe
    async def _earth(event):
        await _play(event, EARTH_FRAMES, delay=0.6, name="earth",
                    stop_text="⏹️ Earth stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.heart$"))
    @client.flood_safe
    async def _heart(event):
        await _play(event, HEART_FRAMES, delay=0.35, name="heart",
                    stop_text="⏹️ Heart stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.matrix$"))
    @client.flood_safe
    async def _matrix(event):
        await _play(event, MATRIX_FRAMES, delay=0.5, name="matrix",
                    stop_text="⏹️ Matrix stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.bomb$"))
    @client.flood_safe
    async def _bomb(event):
        await _play(event, BOMB_FRAMES, delay=0.5, loops=1, name="bomb",
                    stop_text="⏹️ Bomb defused. 💣")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rocket$"))
    @client.flood_safe
    async def _rocket(event):
        await _play(event, ROCKET_FRAMES, delay=0.6, loops=1, name="rocket",
                    stop_text="⏹️ Launch aborted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.loading$"))
    @client.flood_safe
    async def _loading(event):
        await _play(event, LOADING_FRAMES, delay=0.35, loops=1, name="loading",
                    stop_text="⏹️ Loading cancelled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.wave$"))
    @client.flood_safe
    async def _wave(event):
        await _play(event, WAVE_FRAMES, delay=0.4, name="wave",
                    stop_text="⏹️ Wave stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dance$"))
    @client.flood_safe
    async def _dance(event):
        await _play(event, DANCE_FRAMES, delay=0.4, name="dance",
                    stop_text="⏹️ Dance stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ghost$"))
    @client.flood_safe
    async def _ghost(event):
        await _play(event, GHOST_FRAMES, delay=0.5, name="ghost",
                    stop_text="⏹️ Ghost vanished.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fire$"))
    @client.flood_safe
    async def _fire(event):
        await _play(event, FIRE_FRAMES, delay=0.4, name="fire",
                    stop_text="⏹️ Fire out.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.shoot$"))
    @client.flood_safe
    async def _shoot(event):
        await _play(event, SHOOT_FRAMES, delay=0.5, loops=1, name="shoot",
                    stop_text="⏹️ Shot cancelled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stars$"))
    @client.flood_safe
    async def _stars(event):
        await _play(event, STARS_FRAMES, delay=0.4, name="stars",
                    stop_text="⏹️ Stars faded.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.loader$"))
    @client.flood_safe
    async def _loader(event):
        await _play(event, LOADER_FRAMES, delay=0.25, loops=1, name="loader",
                    stop_text="⏹️ Loader stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.cointoss$"))
    @client.flood_safe
    async def _cointoss(event):
        result = random.choice(["👑 HEADS!", "🌙 TAILS!"])
        frames = [
            "🪙 tossing…",
            "🪙 ·",
            "🪙 ··",
            "🪙 ···",
            "🪙 ✨",
            f"🪙 → {result}",
        ]
        await _play(event, frames, delay=0.4, loops=1, name="cointoss",
                    stop_text="⏹️ Toss cancelled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dice$"))
    @client.flood_safe
    async def _dice(event):
        result = random.choice(["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"])
        frames = [
            "🎲 rolling…",
            "🎲 ·",
            "🎲 ··",
            "🎲 ···",
            result,
            f"🎲 ROLLED → {result}",
        ]
        await _play(event, frames, delay=0.35, loops=1, name="dice",
                    stop_text="⏹️ Roll cancelled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rain$"))
    @client.flood_safe
    async def _rain(event):
        await _play(event, RAIN_FRAMES, delay=0.5, name="rain",
                    stop_text="⏹️ Rain stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.snow$"))
    @client.flood_safe
    async def _snow(event):
        await _play(event, SNOW_FRAMES, delay=0.5, name="snow",
                    stop_text="⏹️ Snow stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.siren$"))
    @client.flood_safe
    async def _siren(event):
        await _play(event, SIREN_FRAMES, delay=0.35, name="siren",
                    stop_text="⏹️ Siren off.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fight$"))
    @client.flood_safe
    async def _fight(event):
        await _play(event, FIGHT_FRAMES, delay=0.5, loops=1, name="fight",
                    stop_text="⏹️ Fight stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.snake$"))
    @client.flood_safe
    async def _snake(event):
        await _play(event, SNAKE_FRAMES, delay=0.4, name="snake",
                    stop_text="⏹️ Snake stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.love$"))
    @client.flood_safe
    async def _love(event):
        await _play(event, LOVE_FRAMES, delay=0.5, loops=1, name="love",
                    stop_text="⏹️ Love stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ninja$"))
    @client.flood_safe
    async def _ninja(event):
        await _play(event, NINJA_FRAMES, delay=0.5, loops=1, name="ninja",
                    stop_text="⏹️ Ninja vanished.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.countdown$"))
    @client.flood_safe
    async def _countdown(event):
        nums = ["🔟", "9️⃣", "8️⃣", "7️⃣", "6️⃣",
                "5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣", "⭕"]
        frames = [f"{n}\n˹ get ready ˼" for n in nums] + ["🚀 GO!! 🚀"]
        await _play(event, frames, delay=0.8, loops=1, name="countdown",
                    stop_text="⏹️ Countdown aborted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.typewriter$"))
    @client.flood_safe
    async def _typewriter(event):
        text = "⚡ Sukuna-X Userbot ⚡"
        frames = [text[:i] + "▌" for i in range(1, len(text) + 1)] + [text]
        await _play(event, frames, delay=0.18, loops=1, name="typewriter",
                    stop_text="⏹️ Typing stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.balloon$"))
    @client.flood_safe
    async def _balloon(event):
        await _play(event, BALLOON_FRAMES, delay=0.5, loops=1, name="balloon",
                    stop_text="⏹️ Balloon popped. 🎈")

    # ---- brand-new animations ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.party$"))
    @client.flood_safe
    async def _party(event):
        await _play(event, PARTY_FRAMES, delay=0.4, name="party",
                    stop_text="⏹️ Party over.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.think$"))
    @client.flood_safe
    async def _think(event):
        await _play(event, THINK_FRAMES, delay=0.5, loops=1, name="think",
                    stop_text="⏹️ Stopped thinking.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sleep$"))
    @client.flood_safe
    async def _sleep(event):
        await _play(event, SLEEP_FRAMES, delay=0.6, name="sleep",
                    stop_text="⏹️ Woke up!")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.run$"))
    @client.flood_safe
    async def _run(event):
        await _play(event, RUN_FRAMES, delay=0.45, loops=1, name="run",
                    stop_text="⏹️ Stopped running.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.plane$"))
    @client.flood_safe
    async def _plane(event):
        await _play(event, PLANE_FRAMES, delay=0.4, loops=1, name="plane",
                    stop_text="⏹️ Flight cancelled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.train$"))
    @client.flood_safe
    async def _train(event):
        await _play(event, TRAIN_FRAMES, delay=0.5, loops=1, name="train",
                    stop_text="⏹️ Train halted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.storm$"))
    @client.flood_safe
    async def _storm(event):
        await _play(event, STORM_FRAMES, delay=0.5, loops=1, name="storm",
                    stop_text="⏹️ Storm passed.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.kiss$"))
    @client.flood_safe
    async def _kiss(event):
        await _play(event, KISS_FRAMES, delay=0.5, loops=1, name="kiss",
                    stop_text="⏹️ Kiss stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.slap$"))
    @client.flood_safe
    async def _slap(event):
        await _play(event, SLAP_FRAMES, delay=0.5, loops=1, name="slap",
                    stop_text="⏹️ Slap dodged.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.magic$"))
    @client.flood_safe
    async def _magic(event):
        await _play(event, MAGIC_FRAMES, delay=0.45, loops=1, name="magic",
                    stop_text="⏹️ Magic fizzled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.coin$"))
    @client.flood_safe
    async def _coin(event):
        await _play(event, COIN_FRAMES, delay=0.3, name="coin",
                    stop_text="⏹️ Coin stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.typing$"))
    @client.flood_safe
    async def _typing(event):
        await _play(event, TYPING_FRAMES, delay=0.35, name="typing",
                    stop_text="⏹️ Typing stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tank$"))
    @client.flood_safe
    async def _tank(event):
        await _play(event, TANK_FRAMES, delay=0.5, loops=1, name="tank",
                    stop_text="⏹️ Tank retreated.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pacman$"))
    @client.flood_safe
    async def _pacman(event):
        await _play(event, PACMAN_FRAMES, delay=0.4, loops=1, name="pacman",
                    stop_text="⏹️ Pacman stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pong$"))
    @client.flood_safe
    async def _pong(event):
        await _play(event, PONG_FRAMES, delay=0.35, name="pong",
                    stop_text="⏹️ Pong stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.coffee$"))
    @client.flood_safe
    async def _coffee(event):
        await _play(event, COFFEE_FRAMES, delay=0.5, loops=1, name="coffee",
                    stop_text="⏹️ Coffee spilled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sunrise$"))
    @client.flood_safe
    async def _sunrise(event):
        await _play(event, SUNRISE_FRAMES, delay=0.6, loops=1, name="sunrise",
                    stop_text="⏹️ Sunrise stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.car$"))
    @client.flood_safe
    async def _car(event):
        await _play(event, CAR_FRAMES, delay=0.4, loops=1, name="car",
                    stop_text="⏹️ Car parked.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ship$"))
    @client.flood_safe
    async def _ship(event):
        await _play(event, SHIP_FRAMES, delay=0.5, name="ship",
                    stop_text="⏹️ Ship anchored.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ufo$"))
    @client.flood_safe
    async def _ufo(event):
        await _play(event, UFO_FRAMES, delay=0.45, loops=1, name="ufo",
                    stop_text="⏹️ UFO escaped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.portal$"))
    @client.flood_safe
    async def _portal(event):
        await _play(event, PORTAL_FRAMES, delay=0.45, loops=1, name="portal",
                    stop_text="⏹️ Portal closed.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.wizard$"))
    @client.flood_safe
    async def _wizard(event):
        await _play(event, WIZARD_FRAMES, delay=0.6, loops=1, name="wizard",
                    stop_text="⏹️ The wizard vanished.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.galaxy$"))
    @client.flood_safe
    async def _galaxy(event):
        await _play(event, GALAXY_FRAMES, delay=0.5, name="galaxy",
                    stop_text="⏹️ Galaxy stopped spinning.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fireworks$"))
    @client.flood_safe
    async def _fireworks(event):
        await _play(event, FIREWORKS_FRAMES, delay=0.35, name="fireworks",
                    stop_text="⏹️ Fireworks over.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dj$"))
    @client.flood_safe
    async def _dj(event):
        await _play(event, DJ_FRAMES, delay=0.3, name="dj",
                    stop_text="⏹️ Music stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.battery$"))
    @client.flood_safe
    async def _battery(event):
        await _play(event, BATTERY_FRAMES, delay=0.45, loops=1, name="battery",
                    stop_text="⏹️ Unplugged.")

    # ---- .anims : aesthetic gallery ----

    # ---- v5.2 story packs ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.nuke$"))
    @client.flood_safe
    async def _nuke(event):
        await _play(event, NUKE_FRAMES, delay=0.55, loops=1, name="nuke",
                    stop_text="⏹️ Nuke aborted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.kill$"))
    @client.flood_safe
    async def _kill(event):
        await _play(event, KILL_FRAMES, delay=0.5, loops=1, name="kill",
                    stop_text="⏹️ Kill aborted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dragon$"))
    @client.flood_safe
    async def _dragon(event):
        await _play(event, DRAGON_FRAMES, delay=0.45, name="dragon",
                    stop_text="⏹️ Dragon stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rose$"))
    @client.flood_safe
    async def _rose(event):
        await _play(event, ROSE_FRAMES, delay=0.55, loops=1, name="rose",
                    stop_text="⏹️ Rose stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.moneyrain$"))
    @client.flood_safe
    async def _moneyrain(event):
        await _play(event, MONEY_FRAMES, delay=0.4, name="moneyrain",
                    stop_text="⏹️ Money rain stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ocean$"))
    @client.flood_safe
    async def _ocean(event):
        await _play(event, OCEAN_FRAMES, delay=0.4, name="ocean",
                    stop_text="⏹️ Ocean stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.holi$"))
    @client.flood_safe
    async def _holi(event):
        await _play(event, HOLI_FRAMES, delay=0.45, loops=2, name="holi",
                    stop_text="⏹️ Holi stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.diwali$"))
    @client.flood_safe
    async def _diwali(event):
        await _play(event, DIWALI_FRAMES, delay=0.55, loops=1, name="diwali",
                    stop_text="⏹️ Diwali stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.virus$"))
    @client.flood_safe
    async def _virus(event):
        await _play(event, VIRUS_FRAMES, delay=0.5, loops=1, name="virus",
                    stop_text="⏹️ Virus scan stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.zombie$"))
    @client.flood_safe
    async def _zombie(event):
        await _play(event, ZOMBIE_FRAMES, delay=0.45, loops=2, name="zombie",
                    stop_text="⏹️ Zombie horde stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.race$"))
    @client.flood_safe
    async def _race(event):
        await _play(event, _race_frames(), delay=0.5, loops=1, name="race",
                    stop_text="⏹️ Race cancelled.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.casino$"))
    @client.flood_safe
    async def _casino(event):
        await _play(event, _casino_frames(), delay=0.42, loops=1, name="casino",
                    stop_text="⏹️ Casino closed.")

    # ---- v5.3 showcase ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.bigoof$"))
    @client.flood_safe
    async def _bigoof(event):
        await _play(event, BIGOOF_FRAMES, delay=0.35, loops=1, name="bigoof",
                    stop_text="⏹️ OOF aborted.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.theart$"))
    @client.flood_safe
    async def _theart(event):
        await _play(event, THEART_FRAMES, delay=0.4, name="theart",
                    stop_text="⏹️ Heart stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.police$"))
    @client.flood_safe
    async def _police(event):
        await _play(event, POLICE_FRAMES, delay=0.35, name="police",
                    stop_text="⏹️ Police stopped.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.butterfly$"))
    @client.flood_safe
    async def _butterfly(event):
        await _play(event, BUTTERFLY_FRAMES, delay=0.4, name="butterfly",
                    stop_text="⏹️ Butterfly flew away.")
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.anims$"))
    @client.flood_safe
    async def _anims(event):
        await event.edit(
            "✦ ━━━━〔 🎬 ANIMATIONS · 73 〕━━━━ ✦\n"
            "┃ ⚡ `.hack` `.matrix` `.loading` `.loader`\n"
            "┃ 🌙 `.moon` `.clock` `.earth` `.stars`\n"
            "┃ ❤️ `.heart` `.love` `.kiss` `.slap`\n"
            "┃ 🔥 `.fire` `.bomb` `.rocket` `.shoot`\n"
            "┃ 🎭 `.dance` `.wave` `.ghost` `.party`\n"
            "┃ 🌧️ `.rain` `.snow` `.storm` `.siren`\n"
            "┃ 🐍 `.snake` `.dino` `.ninja` `.fight`\n"
            "┃ ✈️ `.plane` `.train` `.tank` `.run`\n"
            "┃ 🎲 `.dice` `.cointoss` `.coin` `.magic`\n"
            "┃ 🧠 `.brain` `.think` `.sleep` `.typing`\n"
            "┃ 🎈 `.balloon` `.fuck` `.countdown`\n"
            "┃ ⌨️ `.typewriter`\n"
            "┃ 🕹️ `.pacman` `.pong` `.coffee` `.sunrise`\n"
            "┃ 🚗 `.car` `.ship` `.ufo`\n"
            "┃ 🌀 `.portal` `.wizard` `.galaxy`\n"
            "┃ 🎆 `.fireworks` `.dj` `.battery`\n"
            "┃ 💣 `.nuke` `.kill` `.dragon` `.zombie`\n"
            "┃ 🌹 `.rose` `.moneyrain` `.ocean` `.holi`\n"
            "┃ 🪔 `.diwali` `.virus` `.race` `.casino`\n"
            "┃ 🎪 `.bigoof` `.theart` `.police` `.butterfly`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦\n"
            "⏹️ Stop any loop with `.stop`",
            link_preview=False,
        )


COMMANDS_ANIMATIONS = {
    "description": "Animations (73)",
    "commands": [
        (".hack .matrix .bomb .shoot", "terminal / action"),
        (".moon .clock .earth .stars", "sky loops"),
        (".heart .love .kiss .slap", "love & fun"),
        (".fire .rocket .loading .loader", "energy / progress"),
        (".dance .wave .ghost .party", "party loops"),
        (".rain .snow .storm .siren", "weather / alert"),
        (".snake .dino .ninja .fight", "characters"),
        (".plane .train .tank .run", "vehicles"),
        (".dice .cointoss .coin .magic", "games & magic"),
        (".brain .think .sleep .typing", "mind & chat"),
        (".typewriter .balloon .fuck", "text / fun"),
        (".countdown", "10 → GO countdown"),
        (".pacman .pong .coffee .sunrise", "games & morning vibes"),
        (".car .ship .ufo", "more vehicles"),
        (".portal .wizard .galaxy", "magic & space"),
        (".fireworks .dj .battery", "party vibes"),
        (".nuke .kill .dragon .zombie", "action stories"),
        (".rose .moneyrain .ocean .holi", "vibes"),
        (".diwali .virus .race .casino", "desi & games"),
        (".bigoof .theart .police .butterfly", "v5.3 showcase"),
        (".anims", "this gallery"),
    ],
}

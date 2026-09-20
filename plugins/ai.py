# ── SUKUNA-X DOMAIN v7.0 plugin ──────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: AI — 🧠 Artificial Intelligence tools (100% free, no API keys)
#  • .ai / .gpt   → chat with an AI (Pollinations text engine)
#  • .imagine     → AI image generation (Pollinations image engine)
#  • .fact        → random mind-blowing fact
#  • .advice      → random life advice
#  Inspired by popular userbot repos (CatUserbot / Ultroid AI addons).
# ============================================================================

_AI_ENDPOINT = "https://text.pollinations.ai/"
_IMG_ENDPOINT = "https://image.pollinations.ai/prompt/"


def register_ai(client):
    """AI chat + image generation commands."""

    # ---- .ai / .gpt ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:ai|gpt)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _ai(event):
        prompt = event.pattern_match.group(1).strip()
        await event.edit("🧠 Sukuna is thinking…", link_preview=False)
        try:
            url = _AI_ENDPOINT + urllib.parse.quote(prompt[:1500]) + "?model=openai"
            reply = (await _web_get(url, timeout=45)).strip()
            if not reply:
                return await event.edit("❌ AI returned nothing. Try again.")
            reply = reply[:3500]
            await event.edit(
                f"✦ ━━━〔 🧠 SUKUNA AI 〕━━━ ✦\n"
                f"🙋 **You:** {prompt[:300]}\n\n"
                f"🤖 **AI:** {reply}\n"
                f"✦ ━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ AI error: `{exc}`\n💡 Free endpoint — retry in a few seconds.")

    # ---- .imagine : AI image generation ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:imagine|imgai)\s+([\s\S]+)$"))
    @client.flood_safe
    async def _imagine(event):
        prompt = event.pattern_match.group(1).strip()
        await event.edit("🎨 Generating image with AI… (10-60 sec)", link_preview=False)
        dest = os.path.join(DATA_DIR, f"ai_img_{int(time.time())}.jpg")
        try:
            seed = random.randint(1, 999999)
            url = (_IMG_ENDPOINT + urllib.parse.quote(prompt[:800])
                   + f"?width=768&height=768&nologo=true&seed={seed}")
            await _web_dl(url, dest, timeout=120)
            if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
                return await event.edit("❌ Image generation failed. Try again.")
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), dest,
                caption=f"🎨 **AI Art:** {prompt[:300]}\n⚡ Sukuna-X v" + BOT_VERSION,
                reply_to=event.id,
            )
            await event.delete()
        except Exception as exc:
            try:
                await event.edit(f"❌ Imagine error: `{exc}`\n💡 Retry — free servers get busy.")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .fact ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.fact$"))
    @client.flood_safe
    async def _fact(event):
        await event.edit("🤯 Fetching a fact…")
        try:
            data = json.loads(await _web_get(
                "https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=15))
            fact = (data.get("text") or "").strip()
            if not fact:
                return await event.edit("❌ No fact right now.")
            await event.edit(
                f"✦ ━━━〔 🤯 RANDOM FACT 〕━━━ ✦\n{fact}\n✦ ━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Fact error: `{exc}`")

    # ---- .advice ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.advice$"))
    @client.flood_safe
    async def _advice(event):
        await event.edit("🧙 Asking the wise one…")
        try:
            data = json.loads(await _web_get("https://api.adviceslip.com/advice", timeout=15))
            tip = ((data.get("slip") or {}).get("advice") or "").strip()
            if not tip:
                return await event.edit("❌ No advice right now.")
            await event.edit(
                f"✦ ━━━〔 🧙 ADVICE 〕━━━ ✦\n“{tip}”\n✦ ━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        except Exception as exc:
            await event.edit(f"❌ Advice error: `{exc}`")


COMMANDS_AI = {
    "description": "AI Tools",
    "type": "AI & Media",
    "commands": [
        (".ai <prompt>", "chat with AI (free, no key)"),
        (".gpt <prompt>", "alias of .ai"),
        (".imagine <prompt>", "AI image generation"),
        (".imgai <prompt>", "alias of .imagine"),
        (".fact", "random mind-blowing fact"),
        (".advice", "random life advice"),
    ],
}

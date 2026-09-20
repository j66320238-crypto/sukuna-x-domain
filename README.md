# ⚡ SUKUNA-X DOMAIN v7.0 — PHANTOM EDITION 👑

**32 plugins · 420 handlers · 306 cmds · 88 animations · PREMIUM EMOJIS · v7.1 BAN-PROOF SHIELD · JioSaavn music · ID Backup/Restore · interactive button menu · AI tools · DP Auto-Rotator · plugin categories · zero-flood engine**

```
✦━━━━━━〔 ⚡ SUKUNA-X DOMAIN ⚡ 〕━━━━━━✦
        👑 v7.0 PHANTOM EDITION 👑
   Premium Help • Interactive Menu • AI Tools
🛡️ 5-layer anti-ban shield · human delays · no flood
✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦
```

---

## 🔥 What's New in v7.0 (bada upgrade)

### 🔐 ID BACKUP & RESTORE — "pehle jaisa ID wapas" system
- `.pbsave [name]` → current **ID ka full snapshot** (name + bio + DP) save
- `.pblist` → saare snapshots with date/time
- `.pbload <name>` → **wo ID wapas restore** — name, bio, DP sab kuch (human delays + FloodWait retry ke saath, ID pe koi khatra nahi)
- `.pbdel <name>` → snapshot delete
- `.undp` / `.prevdp` → **last DP change UNDO** — har `.setdp`/`.nextdp`/rotator change se pehle purana DP auto-backup hota hai

### ️ v7.1 BAN-PROOF SHIELD — "ID BAN NA HO" autopilot
- `.raksha on|off|status` (alias `.banshield`) — master ban-protection switch (default ON)
- **Flood-storm autopilot**: 3 FloodWaits in 10 min → instant **paranoid profile + ×3 slow + 30 min cooldown**, phir auto-restore — storm me premium-emoji auto & DP rotator bhi pause
- **Hard caps**: 150 sends/rolling-hour, 900/day — cap cross hote hi 45–90s brake
- Storm me send gaps ×2 + per-minute budget half
- `.limits` dashboard ab storm/raksha/hour-day counters dikhata hai
- `.panic` emergency stop (existing) — sab tasks kill + safe mode

### ✨ PREMIUM EMOJI SYSTEM — OkEmojiBot killer (apne account se, NO bot tag!)
- `.premiumsticker on` → **AUTO mode**: har outgoing message ke emojis automatic premium/animated ho jate hain — delete+resend invisible, koi "via @bot" NAHI
- `.premiumsticker off` → auto band
- `.premiumsticker <text>` / `.pemoji <text>` → one-time premium message
- `.pestatus` → mode + cached emoji documents
- Tech: Telegram `SearchCustomEmoji` RPC se emoji→document mapping (permanent cache), `MessageEntityCustomEmoji` with correct UTF-16 offsets, ZWJ/flags/VS16 support, flood-safe

### 🎮 NEW: Mini Games plugin
- `.rps rock|paper|scissors` — Sukuna se muqabla (hindi bhi: `patthar`/`kagaz`/`kainchi`)
- `.quiz` — random trivia, 8 second me answer reveal (free opentdb API)
- `.scratch` — lucky scratch card

### 🎬 Animations → 88 total (+5 new)
`.quickheal` `.heartbeat` `.spinner` `.energy` `.shield`

### 🪄 Animated help loader
- `.ahelp` — spinner + progress bar animation ke baad full menu (popular-repo style)

### 🎵 MUSIC — JioSaavn direct in chat (3-API fallback, kabhi fail nahi)
- `.song <name>` / `.gaana <name>` → **full 320kbps song** chat me direct, album art + metadata (title/artist/duration) ke saath
- `.songs <name>` / `.songlist` → top-5 results card
- **Fallback chain:** ① saavn-api.vercel.app (JioSaavn 320k) → ② saavn.dev API → ③ iTunes previews — sab tested

### 🧩 PLUGIN TYPES / CATEGORIES (better structure)
- Har plugin ab ek type me: 👑 Special · 🧠 AI & Media · 👤 Profile · 🛠 Group Admin · 🔧 Utility · 🎉 Fun · 📨 Mass Actions
- `.plist` → types ke groups me clean view
- `.pstats` → per-plugin load times + total boot ms
- Naye plugins apna `"type"` khud declare kar sakte hain (COMMANDS dict me)

### 🖼 DP POOL SYSTEM + AUTO ROTATOR (Ultroid/CatUserbot research ke baad)
Numbered DP pool — images 1, 2, 3, 4, 5… save karo aur auto-rotate karo:
- `.adddp [n]` — photo pe reply → pool me save (number auto ya apna choose karo)
- `.dplist` — saare pool DPs numbers ke saath + rotator status
- `.getdp <n>` — DP number n chat me dekho (e.g. `.getdp 5`)
- `.setdp <n>` — DP number n profile pe lagao
- `.curdp` — **current DP pool ka kaunsa number hai?** (smart pixel-match, Pillow se)
- `.nextdp` — instant manual rotate
- `.deldp <n|all>` — delete + numbers auto re-align (1..N hamesha sequential)
- `.autodp 2h` / `.autodp 45m` / `.autodp 6h shuffle` — auto rotator (min 10 min, ban-safe)
- `.dptime 4h` — **timer LIVE change** (rotator auto-restart with new timing)
- `.dpstatus` — full status card: interval, mode, current DP, last set, **next ETA**
- `.stopautodp` — rotator band

Protection: har upload se pehle throttle + human delay, FloodWait pe auto-sleep + retry, images auto-resize (1080px JPEG, kabhi upload fail nahi), state disk pe saved, 3 fails pe auto-backoff.

### 🧹 Optimisation commands
- `.gc` — memory sweep (freed objects + RAM report)
- `.speed` — event-loop + Telegram speed test with grade

### 🕹 Interactive Button Menu (Ultroid/Friday style)
- `.menu` → **tap-able inline button menu** — modules as buttons, tap = command list, back/home buttons
- Auto text fallback if the session can't render buttons — kabhi break nahi hota
- Owner-locked callbacks (dusra banda tap kare to ⛔)

### 📖 Help Menu — full premium redesign
- `.help` → clean 2-column module grid, pagination `.help 2`, uptime + shield footer
- `.help <module>` → module card with full command list
- `.help <word>` → global search across every command
- `.cmds [page]` → ALL 275+ commands paginated
- `.plist` → plugin table with per-plugin load times (ms)
- `.stats` → deep stats: sends/edits/floods/breathers, CPU/RAM (psutil), DC, uptime
- `.alive` → premium online card + random Sukuna quote
- `.h` alias for `.help`

### 🧠 NEW: AI Plugin (no API keys, 100% free)
- `.ai <prompt>` / `.gpt` — chat with AI (Pollinations engine)
- `.imagine <prompt>` — **AI image generation**, sends the art in chat
- `.fact` — random facts · `.advice` — random life advice

### 🌍 NEW: Web & Media Tools (CatUserbot/Ultroid classics)
- `.img <query> [1-6]` — multi-image search (DuckDuckGo engine), sends album
- `.telegraph` — reply media/text → telegra.ph link
- `.carbon <code>` — code → beautiful carbon.png
- `.define <word>` — dictionary (2 fallback sources)
- `.pypi <pkg>` — Python package card
- `.yt <query>` — YouTube search, top 6 results with links (no API key)
- `.country <name>` — country info card with photo (Wikipedia REST)
- `.xkcd [num]` · `.shiba` · `.fox` — comics & cute animals
- `.json` — dump replied message as JSON · `.getid` — chat/user/message ids

### 🎬 10 NEW Animations (total 83)
`.deploy` `.os` `.solarsystem` `.music` `.charging` `.wifi` `.download` `.server` `.radar` `.gamer`
- All flood-safe: auto-stop 28s, human jitter, throttle, `.stop` kills any anim
- `.anims [page]` — full paginated gallery

### 🖥 UI / Boot upgrades
- New PHANTOM banner (colourised on real terminals)
- Plugin loader shows `[n/27] ✓ name (ms)` live progress
- Startup card bug fixed (stray `\n`), dynamic self-check
- SSL fallback for broken CA bundles (Termux-safe web calls)

### 🛡 Protection engine (unchanged, still tagra)
5-layer anti-ban: min gap → sliding window → per-chat limiter → human breather → adaptive backoff + 48h warmup. Animations throttled + jittered + auto-stop. FloodWait auto-sleep & retry everywhere.

---

## 📦 Structure
```
sukuna-x-domain/
├── userbot.py          # bootstrapper only
├── core/               # engine — config, safety (5-layer), accounts, ui (v7), banner…
├── plugins/ (29)       # drop-in auto-load: profile, animations, ai, web, sukuna, farmer…
├── data/ (gitignored)  # sessions, logs, profiles, pfps — never overwritten on git pull
├── start.sh            # one-command launcher
└── termux-setup.sh     # Termux one-command setup
```

## 🚀 Install & Run

**VPS / Alwaysdata / PC:**
```bash
git clone https://github.com/j66320238-crypto/sukuna-x-domain.git
cd sukuna-x-domain
pip install telethon tgcrypto pillow psutil
bash start.sh          # NOT "python start.sh"
# first run: API_ID, API_HASH (my.telegram.org) → phone → OTP → done
```

**Termux:**
```bash
pkg update -y && pkg install -y git python
git clone https://github.com/j66320238-crypto/sukuna-x-domain.git
cd sukuna-x-domain && bash termux-setup.sh
```

**Update:**
```
.update        # inside Telegram — git pull
.restart       # reload new code
```

## ⚡ Quick Commands
| Command | What it does |
|---|---|
| `.alive` | premium online card |
| `.help` / `.h` | premium help menu |
| `.menu` | **interactive button menu** |
| `.cmds` | full command list |
| `.plist` / `.stats` | plugin table / deep stats |
| `.song <name>` / `.songs <name>` | **JioSaavn music** direct chat me (3-API fallback) |
| `.adddp` / `.dplist` / `.getdp n` | DP pool system |
| `.autodp 2h` / `.dptime` / `.dpstatus` | auto-rotator / live timer / full status |
| `.ai <q>` / `.imagine <q>` | AI chat / AI image |
| `.img <q> [n]` | image search album |
| `.gc` / `.speed` | memory sweep / speed test |
| `.anims` | 83-animation gallery |
| `.mhelp` | farmer engine help |
| `.help sukuna` | Sukuna special |
| `.safemode fast\|normal\|paranoid` | anti-ban profile |

## ✅ Tested
32 plugins · 420 handlers · 306 cmds in registry · 83 anims · **JioSaavn live test: search + 320kbps download + artwork + iTunes fallback chain** · flood-storm autopilot unit test (3 floods → paranoid + ×3 + cooldown) · raksha persistence · premium-emoji regex (7 cases: ZWJ/flags/VS16) + UTF-16 entity offsets unit-tested · idvault snapshot save/list helpers unit-tested · games RPS logic · 88 anims · DP pool add/list/get/set/delete/renumber unit-tested · smart pixel-match current-DP detection (recompression-safe) · live timer change (.dptime restart logic) · plugin type grouping · interval parser edge cases · all help renders <4096 chars · button menu + fallback · AI text+image endpoints · DDG image search · YouTube search regex · dictionary (2 sources) · PyPI · xkcd · dog.ceo · randomfox · compile + registration suite green.

Repo: https://github.com/j66320238-crypto/sukuna-x-domain.git

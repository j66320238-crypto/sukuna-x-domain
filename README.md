# ⚡ SUKUNA-X DOMAIN v7.3.1 — PHANTOM EDITION + BOTCONTROLLER 👑🤖

**34 plugins · 460+ handlers · 350+ cmds · 88 animations · BOTCONTROLLER MULTI-BOT ARMY 🤖 · TYPE-X auto-typewriter · 13 naye API commands · v7.2 BAN-PROOF SHIELD+ · JioSaavn music · ID Backup/Restore · interactive button menu · AI tools · DP Auto-Rotator · zero-flood engine**

```
✦━━━━━━〔 ⚡ SUKUNA-X DOMAIN ⚡ 〕━━━━━━✦
        👑 v7.3 PHANTOM + BOTCONTROLLER 🤖
   Multi-Bot Army · .revert pahle-jaisa fix
🛡️ 6-layer anti-ban shield · human delays · no flood
✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦
```

---

## 🤖👑 What's New in v7.3 — BOTCONTROLLER (sabse bada feature!)

**Ek main account se pura BOT ARMY control karo** — @BotFather se jitne chahe bot tokens add karo, sab **1st / 2nd / 3rd** slots me manage hote hain:

| Command | Kya karta hai |
|---|---|
| `.addbottoken <token>` | bot register — token live validate hota hai, dead token reject |
| `.delbottoken <n>` | nth bot delete — **slots automatic shift** (3rd → 2nd ban jata hai) |
| `.listbots` | sab bots list + ❄️ frozen (dead-token) bots mark |
| `.monitorb` | LIVE status — kaun online 💚, kaun frozen ❄️ |
| `.addallb` | **sab bots current group me add** (jo ho sake, add ho jata hai) |
| `.addall 1-3` | sirf 1st-3rd bots add (single: `.addall 2`) |
| `.removeallb` | sab bots group se remove |
| `.spamb <n> <sec> <text>` | sab bots text spam — **interval float, NO lower limit** (0.1 / 0.5 / 0 sab ok) |
| `.spamb1-2 <n> <sec> <txt>` | sirf specific bots spam |
| `.sspam <n> <sec>` | USER sticker spam (reply to sticker) |
| `.sspamb <n> <sec>` | BOTS sticker spam (reply to sticker) |
| `.raidb [slots] <n> <txt>` | bot raid — bina text diye to saved slots rotate hote hain |
| `.cloneb [slots]` | bots replied-user ka profile clone (name + bio + DP) |
| `.revertb [slots]` | **bots pahle jaise** — pre-clone state restore |
| `.botsay [slots] <text>` | bots se message bulwao |
| `.<anim>b [slots] [sec]` | **koi bhi animation bots par** — `.roseb`, `.hackb1-2 15`, `.stormb2` |
| `.saverm <text>` | raid message slots — 1st, 2nd, 3rd… save |
| `.listrm / .delrm <n>` | slots list / delete (delete pe slots auto-shift) |
| `.stopb` | sab bot tasks STOP (`.stop` bhi kaam karta hai) |
| `.rrt` | 🆕 **Reply-Raid Turbo** — target ka har message → reply me saved slots se ek-ek (rotation) |
| `.rrtb [slots]` | 🆕 BOTS bhi reply-raid karein (`.rrtb2-3` custom slots) |
| `.stoprrt` | 🆕 sab RRT band (user + bots) |
| `.ct on/off` | 🆕 **COPYCAT** — jo text/sticker bhejoge wahi SAME dobara jayega |
| `.ctb [slots] on/off` | 🆕 BOTS copycat — bots tumhare messages ka copy bhejein (custom slots) |
| `.refreshb` | 🆕 sab bots reconnect + frozen flags clear attempt |
| `.delallrm` | 🆕 sab saved raid slots ek saath delete |
| `.bchelp` | poora help card |

**Frozen bot system:** token dead/revoked hone par bot ❄️ FROZEN mark hota hai — `.listbots` / `.monitorb` me dikhta hai, kabhi crash nahi hota.

### ↩️ `.revert` FIX — ab sach me "pahle jaisa"
- **Pehle:** `.revert` sirf default "Userbot" naam pe set karta tha — tumhara asli profile LOST hota tha.
- **Ab:** `.clone` / `.fclone` / `.rclone` se **pehle** tumhara original naam + bio + DP auto-backup hota hai — `.revert` likho aur **bilkul pahle jaisa** ho jao (naam + bio + DP sab wapas).
- Chain-of-clones safe: `.clone A → .clone B → .revert` = original (backup kabhi overwrite nahi hota)
- `.revertb [slots]` — bots ka bhi same system (pre-clone state saved rehta hai)

### 💥 `.raid` UPGRADE — saved message slots
- `.saverm <text>` se jitne chahe raid messages save karo (1st, 2nd, 3rd…)
- `.raid` ab **har message agli slot se** bhejta hai — ek hi text repeat nahi hota
- `.delrm 3` karo → 4th slot automatically 3rd ban jata hai
- Purana `.setraid` system bhi waise kaam karta hai (agar koi slot save nahi)

---

## 🔥 What's New in v7.2 (is update me)

### ⌨️ TYPE-X — AUTO TYPEWRITER SYSTEM (sabse bada feature!)
- `.type on` → ab tumhara **har message** automatic typewriter animation me jayega — bilkul `.type` jaisa, bas auto!
- `.type off` (ya `.type of`) → auto mode band
- **12 alag-alag styles** — `.type styles` dekho:
  - `classic` ▌ cursor · `wave` bold wave · `glitch` ░▒▓ blocks resolve · `scramble` random letters decode · `matrix` binary bits · `pulse` 💓 · `fire` 🔥 · `hearts` ❤️ · `zoom` spacing se zoom-in · `eraser` type→erase→retype · `reverse` ulta type · `random` har message naya style
- `.type glitch` → style set · `.type speed 0.2` → frame speed (0.05–1.0s) · `.type status` → full card
- `.type <text>` → one-shot animation (purana behaviour, ab styles ke saath)
- **Flood-proof design:** ≤48 frames/message cap, edit throttle + jitter, ek-waqt-me-ek-animation lock, storm/flood me auto-skip, bot-sent messages (raid/spam/echo) kabhi animate nahi hote, final frame me user ka exact original text wapas
- Restart-proof — `data/typex.json` me state save hota hai
- Premium-emoji auto mode ke saath conflict-free (dono ek saath ON rakh sakte ho)

### 🌐 13 NAYE API COMMANDS (sab free, NO API keys, sab live-tested)
| Command | Kya karta hai |
|---|---|
| `.age <name>` | naam se age guess (census data) |
| `.gender <name>` | naam se gender probability |
| `.nat <name>` | naam ke top nationalities |
| `.horo <sign>` | daily horoscope — **desi naam bhi**: `.horo singh` `.horo mesh` |
| `.news [topic]` | top headlines / topic search (BBC + Google News) |
| `.dns <domain> [a\|aaaa\|mx\|txt]` | DNS records lookup |
| `.riddle` | riddle + 10 second baad answer reveal |
| `.catfact` | random cat fact |
| `.uselessfact` | random useless fact |
| `.kanye` | Kanye West quote |
| `.duck` | random duck pic |
| `.cafe` | random coffee pic |
| `.nasa` | NASA astronomy picture of the day |

### 🛡 FLOODWAIT PROTECTION v7.2 — ab aur tagra
- **flood_safe retry-cap (5)**: pehle infinite retry loop tha jo hang kar sakta tha — ab 5 attempts ke baad graceful skip
- **Big-flood guard**: 120s+ ka FloodWait aate hi **instant paranoid mode** (×2.5 slow + 10–60 min cooldown) — storm ka intezar nahi
- **flood_sleep_threshold 60→20**: bade floods (20s+) ab Telethon se raise hoke hamare engine me aate hain → storm detection + adaptive backoff turant active
- 900s+ flood pe bail-out — bot kabhi permanently block nahi hota

### 🔧 BUG FIXES
- **File logging fix**: `userbot.py` me `logging` import missing tha → rotating file log (data/userbot.log) silently kabhi kaam nahi karta tha. Ab fix.
- **pytest fix**: `tests/conftest.py` add hua — `pytest tests/` ab async tests bhi chalata hai (pehle "async def not supported" error aata tha). Ab `pytest` = 15/15 pass
- Sab purane commands waise ke waise — **kuch bhi remove NAHI hua** (306 → 320+ cmds, sirf add hua)

---

## 🔥 What's New in v7.0.1 (fix update)

### ⚔️ RAID FIX — saved message + naam wala format
- `.raid [n]` ab target ke **naam ke saath** saved message bhejta hai — bilkul **"Mintu kya kar rhe ho Mintu"** style (mention clickable)
- `.setraid` bina kiye bhi chalega — default text `kya kar rhe ho` built-in
- Placeholders: `{name}` = plain naam, `{tag}` / `{mention}` = clickable tag
  - `.setraid kya kar rhe ho {name}` → "kya kar rhe ho Mintu"
  - `.setraid {name} oye {tag}` → "Mintu oye Mintu"
- `.drraid` (auto reply-raid) bhi same format use karta hai

### 📜 SG FIX — name history ab reliably copy hoke aata hai
- Purana bug: query bhejne ke baad conversation start hoti thi — fast reply miss ho jati thi. Ab pehle listen, phir send
- Multi-message support: "please wait" ping filter + saari history messages (names + usernames) collect hote hain
- Result apne message ke roop me aata hai — **source bot ka naam/branding kahin nahi dikhta** (status, errors, output — sab clean)
- Media reply aaye to copy hoke chat me jata hai

### 🖼 AUTO DP FIX — restart-proof rotator
- `.autodp` start karne ke baad bot **restart ho jaye to bhi rotation auto-resume** hoti hai (state disk pe saved)
- `.stopautodp` ab flag bhi clear karta hai — restart ke baad wapas start NAHI hoti jab tak tum na kaho
- Pool < 2 DPs ho to rotator khud band + state clean

### 🎲 NEW: `.rclone` — RANDOM GROUP CLONE
- Group me `.rclone` chalao → kisi bhi **random member ka profile clone** (name + bio + DP) — reply ki zaroorat nahi
- `.rclone full` → random member ka FULL clone (saare photos)
- Bots aur khud ke account ko random me se exclude kiya jata hai

### 🔧 Other
- `.revert` ab sirf revert ke liye (pehle `.rclone` galati se revert se bind tha)
- raid_data.json clean (purana "6" text reset)

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
- `.petest` → verify premium rendering on your account · `.pereset` → clear cached emoji docs (fixes black-dot emojis)
- Emoji docs with `free=True` preferred — renders for every account, no placeholders
- 1.5s anti-conflict cooldown + skips messages that already have custom entities
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
├── core/               # engine — config, safety (6-layer), accounts, ui (v7), banner…
├── plugins/ (33)       # drop-in auto-load: profile, animations, ai, web, apis, sukuna, farmer…
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
| `.type on` / `.type off` | **AUTO typewriter — har message animated!** |
| `.type styles` / `.type glitch` | 12 animation styles |
| `.menu` | **interactive button menu** |
| `.cmds` | full command list |
| `.plist` / `.stats` | plugin table / deep stats |
| `.song <name>` / `.songs <name>` | **JioSaavn music** direct chat me (3-API fallback) |
| `.adddp` / `.dplist` / `.getdp n` | DP pool system |
| `.autodp 2h` / `.dptime` / `.dpstatus` | auto-rotator (restart-proof) / live timer / full status |
| `.rclone [full]` | **group me random member ka clone** |
| `.raid [n]` / `.setraid <text>` | raid (naam + saved text) / custom raid text |
| `.sg` / `.namehistory` | name + username history (reply) |
| `.ai <q>` / `.imagine <q>` | AI chat / AI image |
| `.img <q> [n]` | image search album |
| `.gc` / `.speed` | memory sweep / speed test |
| `.anims` | 83-animation gallery |
| `.mhelp` | farmer engine help |
| `.help sukuna` | Sukuna special |
| `.safemode fast\|normal\|paranoid` | anti-ban profile |

## ✅ Tested
33 plugins · 440+ handlers · 320+ cmds in registry · 88 anims · **JioSaavn live test: search + 320kbps download + artwork + iTunes fallback chain** · tests/test_commands.py offline harness: 68 commands × fake client — 68/68 pass, 0 crashes · **TYPE-X: 12 styles frame-valid + 300-char cap + persistence + auto-mode guards (commands/media/entities/bot-sent/OFF skip) + 3-fail break — sab unit-tested** · **APIs: horo resolve (western+desi) + RSS parse (CDATA/entities) + DNS rows mapping unit-tested** · flood-storm autopilot unit test (3 floods → paranoid + ×3 + cooldown) · big-flood guard (120s → instant paranoid) · raksha persistence · premium-emoji regex (7 cases: ZWJ/flags/VS16) + UTF-16 entity offsets unit-tested · idvault snapshot save/list helpers unit-tested · games RPS logic · 88 anims · DP pool add/list/get/set/delete/renumber unit-tested · smart pixel-match current-DP detection (recompression-safe) · live timer change (.dptime restart logic) · plugin type grouping · interval parser edge cases · all help renders <4096 chars · button menu + fallback · AI text+image endpoints · DDG image search · YouTube search regex · dictionary (2 sources) · PyPI · xkcd · dog.ceo · randomfox · 13 naye API endpoints live-verified (agify genderize nationalize catfact uselessfact kanye duck cafe riddle horoscope dns.google BBC-RSS NASA) · compile + registration suite green · pytest 15/15.

Repo: https://github.com/j66320238-crypto/sukuna-x-domain.git

# ⚡ SUKUNA-X DOMAIN v6.7 — Full Clone + Video PFP + AutoPFP Rotate + No Flood

**25 plugins · 355 handlers · 260+ cmds · 73 anims · no flood · full copy**

### 🔥 What's New v6.7 (your requests)

**Profile Full System:**
- `.clone` → main clone (reply): name + bio + main pfp/video
- `.fclone` → **full clone**: ALL photos/videos of target (20 max) — deletes old, uploads all in order (video supported)
- `.clone full` → same as full
- `.saveprofile <name>` → save replied user's **full profile** (all pfps) to `data/profiles/<name>/photos/`
- `.loadprofile <name>` → load main (1 photo + name/bio)
- `.floadprofile <name>` or `.loadprofile <name> full` → **full load** (all photos/videos)
- `.savedprofiles` → list all saved (new dir + legacy)
- `.delprofile <name>` → delete saved

**PFP Tools (new):**
- `.pfpsave` / `.savepfp` → save own or replied user's all pfps to `data/pfps/`
- `.getpfp [n]` → get replied user's pfps (1-20) and send to chat
- `.setpfp` → reply to photo/video to set as your pfp (video supported if square <=10s <=2MB)
- `.pfplist` / `.pfps` → list saved pfp collections
- `.delpfp [n]` → delete all or n pfps
- `.setname <first> [last]` / `.setbio <text>`

**AutoPFP Rotate (human-like, no flood):**
- `.autopfp <hours> [profile_name]` — e.g. `.autopfp 2` rotates every 2h ±15% jitter, min 5min, human delays 1-2.5s between uploads, safe throttle
- `.pfprotate` alias
- `.stopautopfp` → stop
- Source: latest saved pfps or specified profile's photos
- Protection: deletes old all, uploads new 1, FloodWait handled, adaptive backoff

**Animations — No Limit Fix:**
- OLD: loops=0 infinite → flood
- NEW v6.7: loops=0 runs **max 28 sec auto-stop** (not endless), human jitter -0.08 to +0.15s, floor 0.6s, throttle + safe_sleep
- `.hack 20` → run 20 sec (3-120s allowed), `.moon 10`, etc
- `.anims` compact 2-col paginated: `.anims` page1, `.anims 2` page2
- All anims stop via `.stop`

**Help Menu — Mast Premium (not bekar):**
- OLD: big boxed 30+ lines
- NEW v6.7:
```
⚡ SUKUNA-X v6.7 👑 — 25 plugins • 260 cmds • 2h 15m
📚 MENU Page 1/3 — .help <module> details, .help 2 next
────────────────────────────
🛠 admin(12)          😴 afk(5)
🎬 animations(73)     🛡 antipm(6)
👤 profile(16)        👑 sukuna(20)
...
────────────────────────────
🛠 Core: .alive .tasks .stop .restart .update .crashlog
👤 Profile: .clone .fclone .saveprofile .floadprofile .pfpsave .autopfp
🎬 Anims: .anims .anims 2 .hack 20 (time arg) • auto-stop 28s • no flood
🎮 Farmer: .mhelp • 👑 Sukuna: .help sukuna • 🌟 Extra: .help extra
🛡️ Shield ON • No Flood • Human Delays
```
- Module view: icon + desc + `• cmd — help` list
- Search: `.help clone` → 22 results

**Protection — Popular Repos Inspired (Ultroid/CatUserbot):**
- 5-layer anti-ban: min gap, sliding window, per-chat limiter, human breather, adaptive backoff + warmup 47h
- Animations: throttle + jitter + auto-stop 28s
- Profile: safe_sleep 0.6-1.2s between photos, FloodWait catch + retry
- Telethon log spam silenced (Got difference...)
- Banner safe ASCII

### 📦 Structure
```
sukuna-x-domain/
├── userbot.py (entry only)
├── core/ (11 files) — ui (premium help), safety (5-layer), accounts, banner fixed
├── plugins/ (25) — profile v6.7 (full+video+autopfp), animations (no flood), sukuna (20), extra (18), farmer (24) etc
├── data/ (gitignored) — profiles/, pfps/, autopfp/
├── start.sh / termux-setup.sh / bot.py
```

### 📱 Alwaysdata / VPS / Termux
```bash
# Alwaysdata
git clone https://github.com/j66320238-crypto/sukuna-x-domain.git
cd sukuna-x-domain
pip install telethon tgcrypto pillow
bash start.sh   # NOT python start.sh
# first run: API_ID, API_HASH, phone, OTP

# Termux
bash termux-setup.sh

# Update
.update + .restart
```

### ✅ Tested
25 plugins · 355 handlers · 313 fired · 0 exc · clone full+video · autopfp human · anims auto-stop 28s · help compact mast

Repo: https://github.com/j66320238-crypto/sukuna-x-domain.git

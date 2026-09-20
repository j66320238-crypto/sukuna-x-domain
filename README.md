<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Telethon-1.45-229ED9?logo=telegram&logoColor=white" alt="Telethon"/>
  <img src="https://img.shields.io/badge/version-6.5.0-success" alt="version"/>
  <img src="https://img.shields.io/badge/help--menu-premium-brightgreen" alt="help menu"/>
  <img src="https://img.shields.io/badge/banner-fixed-brightgreen" alt="banner"/>
  <img src="https://img.shields.io/badge/account--manager-enhanced-brightgreen" alt="account manager"/>
  <img src="https://img.shields.io/badge/plugins-25-orange" alt="plugins"/>
  <img src="https://img.shields.io/badge/commands-247-orange" alt="commands"/>
</p>

<h1 align="center">⚡ SUKUNA-X DOMAIN</h1>

<p align="center">
  <b>Khatarnak, tagra, alag level — well-structured, premium help, account manager, banner fixed.</b><br/>
  25 plugins · 343 handlers · 247+ commands · 73 animations — fully modular, error-free.<br/>
  New: 👑 Sukuna Special (20 cmds) + 🌟 Extra Addons (18 cmds) + 🎮 Farmer (24 cmds)
</p>

---

## 🆕 v6.5 — Khatarnak Update

### 1. 👑 Sukuna Special — 20 new khatarnak commands (alag level)

Jujutsu Kaisen themed — King of Curses:

```
.sukuna        King of Curses intro animation
.domainx       Domain Expansion: Malevolent Shrine
.cleave [@user] / .dismantle [@user]  Sukuna techniques
.fuga          Divine Flame — Open
.shrine / .cursed / .heian / .king
.khatarnak     Khatarnak mode — alag level
.tagra         Tagra mode — SUKUNA-X DOMAIN
.boom / .matrix / .glitch / .fire / .lightning
.domain        Domain info + stats
.bingo / .slots / .8ball <q>
```

All animated, premium UI, safety engine.

### 2. 📖 Help Menu — Premium, Not Bekar

Old help was simple list. New is **premium, boxed, paginated, with previews**:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⚡ SUKUNA-X DOMAIN — Help Menu  v6.5.0  👑            ┃
┃  25 plugins • 247 commands • 73 animations • Farmer ON ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  🔍 .help <plugin>  •  .help <command>  •  .help 2,3…  ┃
┃  📖 Core: .alive .tasks .stop .restart .update        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  🎮 farmer (24) — Isolation auto-farmer               ┃
┃    .mstart, .msmart, .mhelp                           ┃
┃  👑 sukuna (20) — Khatarnak cursed techniques         ┃
┃    .sukuna, .domainx, .cleave                          ┃
┃  🌟 extra (18) — Addons (figlet, imdb, waifu…)        ┃
┃    .figlet, .imdb, .waifu                              ┃
┃  ... 8 per page, .help 2 for next                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  🎮 Farmer: .mhelp • 👑 Sukuna: .help sukuna           ┃
┃  🔗 Repo: github.com/j66320238-crypto/sukuna-x-domain  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

- `.help` → main menu (paginated, 8 per page)
- `.help 2` → page 2
- `.help sukuna` → full module with `• cmd — help` + `└─ description`
- `.help cleave` → search any command

### 3. 👥 Account Manager at Startup (v6.4)

Shows ALL IDs at boot, last used highlighted, Enter for same:

```
  #  Name   Phone        API_ID  Session  Last Used
  1  main   +91****3210  12345   ✅ Yes   2h ago ← last
  2  second +91****3211  67890   ❌ No    —
  Options: [1-2] choose • [N] new • [D] delete • [L] details • [Enter]=last
```

Single ID → auto-start card. Non-interactive → auto last. Env: `SUKUNA_ACCOUNT=name`. Telegram: `.accounts`

### 4. 🛠 Banner Fixed (your screenshot)

Old `█▀` broke into `SUKUHA : T`. New uses safe `_ / \ |` + `┏━┓` — renders perfect in Termux.

### 5. 🗂 Well-Structured, Easy Upgrade

```
sukuna-x-domain/
├── userbot.py (255 lines) — bootstrapper only
├── core/ (11 files) — config, safety, accounts (manager!), banner (fixed!), ui (premium help!), client, etc
├── plugins/ (25 plugins) — farmer, extra, sukuna new
├── data/ (gitignored)
├── start.sh, termux-setup.sh, bot.py, .gitignore
```

`git pull` or `.update` → easy upgrade, data safe.

## 📱 Termux One-Command

```bash
pkg update -y && pkg install -y git
git clone https://github.com/j66320238-crypto/sukuna-x-domain.git
cd sukuna-x-domain
bash termux-setup.sh
```

## 🔁 Update

```
.update + .restart
git pull + bash start.sh
```

## 📜 Commands

- **Core (7):** .alive .help .tasks .stop .restart .update .crashlog
- **Farmer (24):** .mstart .msmart .mhelp .mjobs .mstatus .mstopall etc
- **Sukuna (20):** .sukuna .domainx .cleave .dismantle .fuga .khatarnak .tagra .boom etc
- **Extra (18):** .figlet .imdb .anime .waifu .pokedex .truth .dare .wiki .covid .qrcode .accounts etc
- **Animations (73):** .anims + .hack .boom .fire etc
- + admin, afk, antipm, chat, events, fun, info, media, misc, net, party, profile, raid, remind, safety, spam, stickers, tags, texttools, tools, util

Total: 247+ commands

## ✅ Tested

25 plugins · 343 handlers · 301 fired · zero exceptions · compile OK · banner OK · account manager OK

Repo: https://github.com/j66320238-crypto/sukuna-x-domain.git
Baka: https://github.com/j66320238-crypto/baka.git

v6.5.0 — khatarnak, tagra, alag level, premium help, banner fixed, account manager, 20+ new cmds, error-free

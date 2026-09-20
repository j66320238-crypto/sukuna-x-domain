# ⚡ SUKUNA-X DOMAIN v7.0 — START HERE (well-structured)

## 0. What changed? (well-structured)

Old versions were single-file `userbot.py` (10k lines). v7.0 is **fully modular**:

- `userbot.py` = 255 lines bootstrapper only
- `core/` = 11 files (config, safety, store, accounts, helpers, decorators, banner, ui, client, state, __init__)
- `plugins/` = 23 plugins (including new `farmer.py` from baka12.py)
- `data/` auto-created, gitignored — sessions & logs never overwritten on `git pull`

**Easy upgrade:** just `git pull` — your data stays safe.

## 1. Termux one-command

```bash
pkg update -y && pkg install -y git
git clone https://github.com/j66320238-crypto/sukuna-x-domain.git
cd sukuna-x-domain
bash termux-setup.sh
```

## 2. PC / VPS

```bash
git clone https://github.com/j66320238-crypto/sukuna-x-domain.git
cd sukuna-x-domain
pip install telethon tgcrypto pillow
python userbot.py
# or bash start.sh
```

First run asks API_ID/HASH from https://my.telegram.org → saved to `data/accounts.json` → OTP → done.

## 3. Updates (easy)

Telegram:
```
.update
.restart
```
Terminal:
```bash
git pull
bash start.sh
```

## 4. Farmer (baka12.py engine)

```
.mstart mixed 100 8 9 7
.mstart smart 6 10 8
.mhelp
.mjobs
.mstatus
.mstop
```

Full list: `.help farmer`

## 5. Core commands

```
.alive
.help
.help farmer
.tasks
.stop
.restart
.update
.crashlog
.anims
.limits
.safemode fast|normal|paranoid
```

## 6. Adding your own plugin (easy)

Create `plugins/hello.py`:

from core import *
def register_hello(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.hello$"))
    async def _h(event):
        await event.edit("Hello ✦ DOMAIN")
COMMANDS_HELLO = {"description": "Hello", "commands": [(".hello", "say hello")]}

Then `.restart` → `.help hello`

## 7. Structure for GitHub

```
sukuna-x-domain/
├── userbot.py (255 lines)
├── core/ (11 files)
├── plugins/ (23 files)
├── data/ (gitignored, auto-created)
├── start.sh, termux-setup.sh, bot.py, requirements.txt, .gitignore
└── README.md, START-HERE.md
```

Push this to https://github.com/j66320238-crypto/sukuna-x-domain.git

## 8. Troubleshooting

- `No module named telethon` → pip install telethon tgcrypto pillow
- Pillow fails Termux → pkg install clang libjpeg-turbo zlib
- `.update` not a git repo → you used zip, clone instead
- FloodWait → normal, engine slows down
- Session expired → rm -rf data/*.session, re-login

Enjoy — SUKUNA-X DOMAIN v7.0 PHANTOM EDITION 👑

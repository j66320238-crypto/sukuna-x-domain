#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  ⚡ SUKUNA-X DOMAIN — FULL AUTO-SETUP for a fresh Termux
#     bash termux-setup.sh        (does everything, then starts)
#     Repo: https://github.com/j66320238-crypto/sukuna-x-domain.git
# ══════════════════════════════════════════════════════════════
set -e
cd "$(dirname "$0")"
R='\033[0;35m'; Y='\033[1;33m'; G='\033[0;32m'; C='\033[0;36m'; N='\033[0m'
echo -e "${R}  ⚡ SUKUNA-X DOMAIN — Termux auto-setup${N}"
echo -e "${C}  Repo: github.com/j66320238-crypto/sukuna-x-domain${N}"

if ! command -v pkg >/dev/null 2>&1; then
    echo "❌ 'pkg' not found — run this inside Termux."
    exit 1
fi

echo -e "${Y}📦 [1/4] Updating Termux packages…${N}"
pkg update -y && pkg upgrade -y

echo -e "${Y}🧰 [2/4] Installing Python + build libs (for Pillow)…${N}"
pkg install -y python clang libjpeg-turbo zlib binutils git termux-tools

echo -e "${Y}🐍 [3/4] Installing Python libraries…${N}"
python -m pip install --upgrade pip
pip install telethon tgcrypto pillow

echo -e "${Y}🔋 [4/4] Keeping Termux awake (wake-lock)…${N}"
termux-wake-lock 2>/dev/null || true
termux-setup-storage 2>/dev/null || true

echo -e "${G}✅ Setup complete! Starting SUKUNA-X DOMAIN…${N}"
echo -e "   (first run will ask for API_ID / API_HASH from my.telegram.org)"
echo -e "   ${C}Tip: .help for menu, .mhelp for farmer${N}"
exec python userbot.py

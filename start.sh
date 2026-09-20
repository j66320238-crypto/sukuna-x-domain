#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  ⚡ SUKUNA-X DOMAIN — one-command launcher
#     bash start.sh            → run the bot
#     bash start.sh --install  → (re)install dependencies first
#     Repo: https://github.com/j66320238-crypto/sukuna-x-domain.git
# ══════════════════════════════════════════════════════════════
set -e
cd "$(dirname "$0")"

R='\033[0;35m'; Y='\033[1;33m'; G='\033[0;32m'; C='\033[0;36m'; N='\033[0m'
echo -e "${R}"
echo "  ✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦"
echo "       ⚡  SUKUNA-X DOMAIN  ·  launcher"
echo "       Repo: github.com/j66320238-crypto/sukuna-x-domain"
echo "  ✦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✦"
echo -e "${N}"

PY=python3
command -v $PY >/dev/null 2>&1 || { echo "❌ python3 not found — install Python 3.8+ first."; exit 1; }

install_deps() {
    echo -e "${Y}📦 Installing dependencies…${N}"
    $PY -m pip install --user --upgrade telethon tgcrypto pillow 2>/dev/null \
      || $PY -m pip install --upgrade telethon tgcrypto pillow
}

if [ "$1" = "--install" ]; then install_deps; fi

# check deps, install automatically if missing
$PY - <<'EOF' >/dev/null 2>&1 || NEED=1
import telethon  # noqa
EOF
if [ "${NEED:-0}" = "1" ]; then
    echo -e "${Y}⚠️  Telethon missing — installing automatically…${N}"
    install_deps
fi

echo -e "${G}🚀 Starting SUKUNA-X DOMAIN… (Ctrl+C to stop cleanly)${N}"
echo -e "${C}   .help for menu · .mhelp for farmer · .anims for animations${N}"
exec $PY userbot.py

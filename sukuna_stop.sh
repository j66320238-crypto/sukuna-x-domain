#!/usr/bin/env bash
# ⏹ SUKUNA-X DOMAIN — poori chain band karo (supervisor + userbot)
cd "$(dirname "$0")"
screen -S sukuna -X quit 2>/dev/null
pkill -f "python userbot.py" 2>/dev/null
sleep 2
if pgrep -f "python userbot.py" > /dev/null; then
    echo "⚠️ abhi bhi chal raha hai — force kill"
    pkill -9 -f "python userbot.py"
fi
echo "✅ Sukuna band. (wapas chalane ke liye: screen -dmS sukuna bash sukuna_run.sh)"

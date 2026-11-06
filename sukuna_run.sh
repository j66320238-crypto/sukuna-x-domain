#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  🛡️ SUKUNA-X DOMAIN — 24/7 supervisor loop
#  Ye script userbot ko crash hone par khud 5s me restart karti hai.
#
#  START :  screen -dmS sukuna bash sukuna_run.sh
#  STOP  :  bash sukuna_stop.sh
#  LIVE LOG DEKHNE KE LIYE:  screen -r sukuna   (detach: Ctrl+A, D)
# ══════════════════════════════════════════════════════════════
cd "$(dirname "$0")"
PY=/usr/alwaysdata/python/3.13/bin/python
command -v $PY >/dev/null 2>&1 || PY=python3

mkdir -p data
echo "[supervisor $(date '+%F %T')] started (pid $$)" >> supervisor.log

while true; do
    echo "[supervisor $(date '+%F %T')] starting userbot…" >> supervisor.log
    $PY userbot.py >> run.out 2>&1
    RC=$?
    echo "[supervisor $(date '+%F %T')] userbot exited (rc=$RC) — restart in 5s" >> supervisor.log
    echo "userbot exited rc=$RC; restarting in 5s…" >&2
    if [ "$RC" -eq 77 ]; then
        # v7.4.2: instance-lock — pehle se ek instance chal raha hai.
        # Turant restart karne ka koi fayda nahi — 60s ruk kar dobara check karo.
        echo "[supervisor $(date '+%F %T')] instance-lock (rc=77) — dusri instance chal rahi hai, 60s backoff" >> supervisor.log
        sleep 55
    fi
    sleep 5
done

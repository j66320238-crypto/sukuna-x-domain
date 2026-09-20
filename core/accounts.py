#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/accounts.py — SUKUNA-X DOMAIN Account Manager (v6.4 enhanced)

Features:
  • Shows ALL saved IDs/accounts at startup with full details
  • Highlights last used account — press Enter to continue same
  • Session file detection (✅ session exists / ❌ will login)
  • Add new account, delete account, list accounts from startup prompt
  • Saves last_used + last_used_at for next boot
  • Works in non-interactive (docker) — auto picks last_used or first
  • Env override: SUKUNA_ACCOUNT=name  (for VPS/docker)
"""
import os
import re
import sys
import time
import json

from .config import API_ID, API_HASH, PHONE as CFG_PHONE, SESSION_NAME
from .store import load_store, save_store, DATA_DIR

ACCOUNT = None
PHONE = CFG_PHONE


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(name or "sukuna")).strip("_") or "sukuna"


def _acc_cfg_load() -> dict:
    d = load_store("accounts")
    if not isinstance(d, dict):
        return {"accounts": []}
    if "accounts" not in d:
        # old format was just list
        if isinstance(d, list):
            return {"accounts": d}
        return {"accounts": []}
    return d


def _acc_cfg_save(cfg: dict) -> bool:
    return save_store("accounts", cfg)


def _session_exists(acc_name: str) -> bool:
    """Check if session file exists for this account in any known location."""
    safe = _safe_name(acc_name)
    candidates = [
        os.path.join(DATA_DIR, f"{safe}.session"),
        os.path.join(DATA_DIR, f"{acc_name}.session"),
        os.path.join(os.getcwd(), f"{safe}.session"),
        os.path.join(os.getcwd(), f"{acc_name}.session"),
        os.path.join(os.path.dirname(DATA_DIR), f"{safe}.session"),
        os.path.join(os.path.dirname(DATA_DIR), "sukuna_data", f"{safe}.session"),
        os.path.join(os.path.dirname(DATA_DIR), "data", f"{safe}.session"),
    ]
    return any(os.path.exists(p) for p in candidates)


def _fmt_ago(ts: float) -> str:
    if not ts:
        return "never"
    diff = time.time() - ts
    if diff < 60:
        return f"{int(diff)}s ago"
    if diff < 3600:
        return f"{int(diff//60)}m ago"
    if diff < 86400:
        return f"{int(diff//3600)}h ago"
    return f"{int(diff//86400)}d ago"


def _mask_phone(phone: str) -> str:
    if not phone:
        return "—"
    p = str(phone)
    if len(p) <= 4:
        return p
    return p[:3] + "****" + p[-4:]


def _show_accounts_table(accs, last_used_name=None, last_used_at=None):
    print("\n  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("  ┃  👥 SUKUNA-X DOMAIN — Account Manager  •  Choose your ID to start   ┃")
    print("  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
    print("  ┃  #   Name        Phone          API_ID     Session     Last Used     ┃")
    print("  ┃  ─────────────────────────────────────────────────────────────────  ┃")
    for i, a in enumerate(accs, 1):
        name = (a.get("name") or "account")[:10]
        phone = _mask_phone(a.get("phone", ""))
        api_id = str(a.get("api_id", "?"))[:8]
        sess = "✅ Yes" if _session_exists(a.get("name", "")) else "❌ No"
        lu = ""
        if a.get("name") == last_used_name and last_used_at:
            lu = _fmt_ago(last_used_at)
        else:
            # check per-account last_used_at if stored
            lu = _fmt_ago(a.get("last_used_at", 0)) if a.get("last_used_at") else "—"
        marker = " ← last" if a.get("name") == last_used_name else ""
        print(f"  ┃  {i:<2}  {name:<10}  {phone:<13}  {api_id:<8}  {sess:<9}  {lu:<10}{marker:<8}┃")
    print("  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
    if last_used_name:
        print(f"  ┃  Last used: {last_used_name} ({_fmt_ago(last_used_at)}) — Press Enter for same        ┃")
    print("  ┃  Options: [1-{}] choose • [N] new • [D] delete • [L] details • [Enter]=last/first ┃".format(len(accs)))
    print("  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")


def _interactive_add_account(cfg: dict) -> dict:
    print("\n  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("  ┃  ➕ Add New Account — SUKUNA-X DOMAIN          ┃")
    print("  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    print("  1. Open https://my.telegram.org and log in")
    print("  2. API development tools → Create app")
    print("  3. Copy api_id + api_hash")
    while True:
        try:
            raw_id = input("\n   📥 API_ID (number): ").strip()
            api_hash = input("   📥 API_HASH: ").strip()
        except EOFError:
            print("\n⛔ Cancelled.")
            return None
        if not (raw_id.isdigit() and int(raw_id) > 0):
            print("   ⚠️  API_ID must be a positive number.")
            continue
        if len(api_hash) < 16:
            print("   ⚠️  API_HASH too short.")
            continue
        try:
            name = input("   👤 Account name [main]: ").strip() or "main"
            phone = input("   📱 Phone with +country (optional, Enter=skip): ").strip() or None
        except EOFError:
            name, phone = "main", None
        # check duplicate name
        existing = [a.get("name") for a in cfg.get("accounts", [])]
        if name in existing:
            print(f"   ⚠️  Name '{name}' already exists — choose another.")
            continue
        new_acc = {"name": name, "api_id": int(raw_id), "api_hash": api_hash, "phone": phone, "created_at": time.time()}
        cfg.setdefault("accounts", []).append(new_acc)
        cfg["last_used"] = name
        cfg["last_used_at"] = time.time()
        _acc_cfg_save(cfg)
        print(f"\n   ✅ Account '{name}' saved to data/accounts.json")
        return new_acc


def _interactive_delete_account(cfg: dict):
    accs = cfg.get("accounts", [])
    if not accs:
        print("   ❌ No accounts to delete.")
        return
    print("\n  🗑  Delete Account — choose number:")
    for i, a in enumerate(accs, 1):
        print(f"   {i}. {a.get('name')} • {a.get('phone','—')} • api_id {a.get('api_id')}")
    try:
        ch = input("   Number to delete (Enter=cancel): ").strip()
    except EOFError:
        ch = ""
    if not ch.isdigit():
        print("   Cancelled.")
        return
    idx = int(ch) - 1
    if 0 <= idx < len(accs):
        name = accs[idx].get("name")
        del accs[idx]
        if cfg.get("last_used") == name:
            cfg["last_used"] = accs[0].get("name") if accs else None
        _acc_cfg_save(cfg)
        print(f"   ✅ Deleted '{name}'. Session file not removed (delete manually if needed).")
    else:
        print("   ❌ Invalid number.")


def resolve_credentials():
    """
    Returns (api_id, api_hash, account_name, phone)
    Enhanced: shows all IDs, last used, session status, add/delete options.
    """
    global ACCOUNT, PHONE

    # 1) Hard-coded in config.py takes priority (old way)
    if API_ID and str(API_HASH).strip():
        ACCOUNT = {"name": _safe_name(SESSION_NAME), "api_id": int(API_ID), "api_hash": str(API_HASH).strip(), "phone": PHONE}
        return int(API_ID), str(API_HASH).strip(), _safe_name(SESSION_NAME), (PHONE or None)

    cfg = _acc_cfg_load()
    accs = [a for a in cfg.get("accounts", []) if a.get("api_id") and a.get("api_hash")]
    last_used = cfg.get("last_used")
    last_used_at = cfg.get("last_used_at", 0)

    # env override for VPS/docker
    env = os.environ.get("SUKUNA_ACCOUNT", "").strip()
    if env:
        for a in accs:
            if str(a.get("name", "")).lower() == env.lower():
                ACCOUNT = a
                if a.get("phone"):
                    PHONE = a["phone"]
                # update last_used
                cfg["last_used"] = a.get("name")
                cfg["last_used_at"] = time.time()
                a["last_used_at"] = time.time()
                _acc_cfg_save(cfg)
                print(f"\n  🔧 Env SUKUNA_ACCOUNT={env} → using account '{a.get('name')}'")
                return int(a["api_id"]), str(a["api_hash"]), _safe_name(a.get("name")), a.get("phone")

    # 2) If accounts exist — show manager
    if accs:
        # non-interactive (no tty) → auto pick last_used or first
        if not sys.stdin.isatty():
            chosen = None
            if last_used:
                for a in accs:
                    if a.get("name") == last_used:
                        chosen = a
                        break
            if not chosen:
                chosen = accs[0]
            ACCOUNT = chosen
            if chosen.get("phone"):
                PHONE = chosen["phone"]
            print(f"\n  🤖 Non-interactive — auto using account '{chosen.get('name')}' (last used: {last_used or 'none'})")
            return int(chosen["api_id"]), str(chosen["api_hash"]), _safe_name(chosen.get("name")), chosen.get("phone")

        # single account → auto use but show nice card
        if len(accs) == 1:
            a = accs[0]
            sess = "✅ session found" if _session_exists(a.get("name","")) else "❌ no session (will login)"
            print("\n  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
            print("  ┃  👤 Single account found — auto-starting       ┃")
            print(f"  ┃  Name: {a.get('name'):<15} Phone: {_mask_phone(a.get('phone','')):<15} ┃")
            print(f"  ┃  API_ID: {a.get('api_id'):<10} {sess:<25} ┃")
            if last_used:
                print(f"  ┃  Last used: {last_used} ({_fmt_ago(last_used_at)}) — continuing same     ┃")
            print("  ┃  Tip: Add more IDs with [N] at next boot or via .accounts ┃")
            print("  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
            ACCOUNT = a
            if a.get("phone"):
                PHONE = a["phone"]
            cfg["last_used"] = a.get("name")
            cfg["last_used_at"] = time.time()
            a["last_used_at"] = time.time()
            _acc_cfg_save(cfg)
            # small pause so user sees card
            time.sleep(1)
            print(f"\n   ✅ Using account '{a.get('name')}' — starting SUKUNA-X DOMAIN…")
            return int(a["api_id"]), str(a["api_hash"]), _safe_name(a.get("name")), a.get("phone")

        # interactive loop for multiple accounts
        while True:
            _show_accounts_table(accs, last_used, last_used_at)
            try:
                ch = input("\n   👉 Choose: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Cancelled. Bye!")
                sys.exit(1)

            if ch == "":
                # Enter → last used or first
                if last_used:
                    for a in accs:
                        if a.get("name") == last_used:
                            chosen = a
                            break
                    else:
                        chosen = accs[0]
                else:
                    chosen = accs[0]
                ACCOUNT = chosen
                if chosen.get("phone"):
                    PHONE = chosen["phone"]
                cfg["last_used"] = chosen.get("name")
                cfg["last_used_at"] = time.time()
                chosen["last_used_at"] = time.time()
                _acc_cfg_save(cfg)
                print(f"\n   ✅ Using account '{chosen.get('name')}' — starting SUKUNA-X DOMAIN…")
                return int(chosen["api_id"]), str(chosen["api_hash"]), _safe_name(chosen.get("name")), chosen.get("phone")

            low = ch.lower()
            if low == "n":
                new_acc = _interactive_add_account(cfg)
                if new_acc:
                    # refresh list
                    cfg = _acc_cfg_load()
                    accs = [a for a in cfg.get("accounts", []) if a.get("api_id") and a.get("api_hash")]
                    last_used = cfg.get("last_used")
                    last_used_at = cfg.get("last_used_at", 0)
                    continue
                else:
                    continue
            if low == "d":
                _interactive_delete_account(cfg)
                cfg = _acc_cfg_load()
                accs = [a for a in cfg.get("accounts", []) if a.get("api_id") and a.get("api_hash")]
                last_used = cfg.get("last_used")
                last_used_at = cfg.get("last_used_at", 0)
                if not accs:
                    print("\n   No accounts left — need to add one.")
                    continue
                continue
            if low == "l":
                print("\n  📋 Detailed Accounts:")
                for a in accs:
                    sess = "✅ session exists" if _session_exists(a.get("name","")) else "❌ no session"
                    print(f"   • {a.get('name')} — phone {a.get('phone','—')} — api_id {a.get('api_id')} — {sess} — created {_fmt_ago(a.get('created_at',0))}")
                input("\n   Press Enter to continue…")
                continue
            if ch.isdigit() and 1 <= int(ch) <= len(accs):
                chosen = accs[int(ch)-1]
                ACCOUNT = chosen
                if chosen.get("phone"):
                    PHONE = chosen["phone"]
                cfg["last_used"] = chosen.get("name")
                cfg["last_used_at"] = time.time()
                chosen["last_used_at"] = time.time()
                _acc_cfg_save(cfg)
                print(f"\n   ✅ Using account '{chosen.get('name')}' — starting SUKUNA-X DOMAIN…")
                return int(chosen["api_id"]), str(chosen["api_hash"]), _safe_name(chosen.get("name")), chosen.get("phone")
            print(f"   ⚠️  Invalid choice '{ch}' — type 1-{len(accs)}, N, D, L, or Enter.")

    # 3) No accounts — first run setup
    print("\n  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("  ┃  ⚙️  FIRST RUN — SUKUNA-X DOMAIN Account Setup  ┃")
    print("  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    print("  1. Open https://my.telegram.org and log in")
    print("  2. API development tools → Create new application")
    print("  3. Copy api_id (number) + api_hash (text)")
    print("  4. Paste below — saved to data/accounts.json for next time")
    print("  ────────────────────────────────────────────────")
    while True:
        try:
            raw_id = input("\n   📥 API_ID (number): ").strip()
            api_hash = input("   📥 API_HASH: ").strip()
        except EOFError:
            print("\n⛔ No input — run in terminal or edit core/config.py")
            sys.exit(2)
        if not (raw_id.isdigit() and int(raw_id) > 0):
            print("   ⚠️  API_ID must be a positive number.")
            continue
        if len(api_hash) < 16:
            print("   ⚠️  API_HASH too short.")
            continue
        try:
            name = input("   👤 Account name [main]: ").strip() or "main"
            phone = input("   📱 Phone with +country (optional, Enter=skip): ").strip() or None
        except EOFError:
            name, phone = "main", None
        cfg = _acc_cfg_load()
        cfg.setdefault("accounts", []).append(
            {"name": name, "api_id": int(raw_id), "api_hash": api_hash, "phone": phone, "created_at": time.time(), "last_used_at": time.time()})
        cfg["last_used"] = name
        cfg["last_used_at"] = time.time()
        _acc_cfg_save(cfg)
        ACCOUNT = {"name": name, "api_id": int(raw_id), "api_hash": api_hash, "phone": phone}
        if phone:
            PHONE = phone
        print(f"\n   ✅ Account '{name}' saved to data/accounts.json — starting…")
        return int(raw_id), api_hash, _safe_name(name), phone

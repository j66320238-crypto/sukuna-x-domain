#!/usr/bin/env python3
"""v7.3 BotController tests — slots, ordinals, freeze-detect, saverm store, raid rotation."""
import asyncio
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from plugins.botcontroller import (  # noqa: E402
    _parse_slots, _ord, _is_freeze_err, _rm_load, _rm_save,
    _anim_frames, DELEG_EXCLUDE_BASES, RM_STORE,
)
from plugins.raid import _load_raid_messages  # noqa: E402
from core.store import DATA_DIR, load_store  # noqa: E402


def test_parse_slots():
    assert _parse_slots(None, 4) == [1, 2, 3, 4], "None → sab slots"
    assert _parse_slots("", 4) == [1, 2, 3, 4], "empty → sab slots"
    assert _parse_slots("1-3", 5) == [1, 2, 3], "range"
    assert _parse_slots("3", 5) == [3], "single"
    assert _parse_slots("1,3", 5) == [1, 3], "comma list"
    assert _parse_slots("2-4", 3) == [2, 3], "range clip total pe"
    assert _parse_slots("9", 3) == [], "out of range → empty"
    assert _parse_slots("abc", 3) == [], "garbage → empty"
    assert _parse_slots("3-1", 5) == [1, 2, 3], "ulta range bhi chalta hai"
    print("  ✓ _parse_slots: ranges, singles, comma, clip, garbage sab ok")


def test_ordinals():
    assert _ord(1) == "1st"
    assert _ord(2) == "2nd"
    assert _ord(3) == "3rd"
    assert _ord(4) == "4th"
    assert _ord(11) == "11th"
    assert _ord(12) == "12th"
    assert _ord(13) == "13th"
    assert _ord(21) == "21st"
    assert _ord(22) == "22nd"
    assert _ord(23) == "23rd"
    assert _ord(101) == "101st"
    print("  ✓ _ord: 1st/2nd/3rd/4th/11th/21st sab sahi")


def test_freeze_detection():
    class AuthKeyUnregisteredError(Exception):
        pass
    class UserDeactivatedError(Exception):
        pass
    class AccessTokenExpiredError(Exception):
        pass
    assert _is_freeze_err(AuthKeyUnregisteredError("KEY_UNREGISTERED")) is True
    assert _is_freeze_err(UserDeactivatedError("user deactivated")) is True
    assert _is_freeze_err(AccessTokenExpiredError("token expired")) is True
    assert _is_freeze_err(Exception("AUTH_KEY_DUPLICATED")) is True
    # normal errors freeze NAHI hain
    assert _is_freeze_err(Exception("peer id invalid")) is False
    assert _is_freeze_err(Exception("chat write forbidden")) is False
    print("  ✓ freeze-detect: authkey/deactivated/token = frozen; baaki normal")


def test_saverm_slots_and_shift():
    # clean start
    _rm_save([])
    _rm_save(["kya kar rhe ho"])
    _rm_save(_rm_load() + ["oye {name}"])
    _rm_save(_rm_load() + ["suno zara"])
    msgs = _rm_load()
    assert msgs == ["kya kar rhe ho", "oye {name}", "suno zara"], msgs
    # 2nd slot delete → 3rd apne aap 2nd ban jata hai
    msgs.pop(1)
    _rm_save(msgs)
    msgs = _rm_load()
    assert msgs == ["kya kar rhe ho", "suno zara"], msgs
    # raid.py same store padhta hai
    assert _load_raid_messages() == ["kya kar rhe ho", "suno zara"]
    # cleanup
    try:
        os.remove(os.path.join(DATA_DIR, f"{RM_STORE}.json"))
    except OSError:
        pass
    assert _rm_load() == []
    print("  ✓ saverm slots: save 1st/2nd/3rd → delrm 2nd → 3rd shift ho ke 2nd")


def test_anim_lookup():
    assert _anim_frames("rose"), "rose frames milne chahiye (user ka example)"
    assert _anim_frames("hack"), "hack frames"
    assert _anim_frames("theart"), "theart frames"
    assert _anim_frames("solarsystem"), "alias SOLAR_FRAMES"
    assert _anim_frames("moneyrain"), "alias MONEY_FRAMES"
    assert _anim_frames("countdown"), "inline countdown"
    assert _anim_frames("typewriter"), "inline typewriter"
    # non-anim → None (silent skip, .bomb/.imdb conflict-safe)
    assert _anim_frames("bom") is None, ".bomb ka base 'bom' → silent"
    assert _anim_frames("imd") is None, ".imdb ka base 'imd' → silent"
    assert _anim_frames("we") is None, ".web ka base 'we' → silent"
    # exclusion bases
    assert "spam" in DELEG_EXCLUDE_BASES and "raid" in DELEG_EXCLUDE_BASES
    print("  ✓ anim lookup: rose/hack/theart + aliases + inline, conflicts silent")


def test_raid_rotation_math():
    saved = ["a", "b", "c"]
    count = 7
    picked = [saved[i % len(saved)] for i in range(count)]
    assert picked == ["a", "b", "c", "a", "b", "c", "a"], picked
    print("  ✓ raid rotation: 7 msgs → a b c a b c a")


def test_bots_slot_shift():
    # bot slots delete pe auto-shift (list semantics)
    bots = [{"id": 1}, {"id": 2}, {"id": 3}]
    bots.pop(1)  # 2nd delete
    assert [b["id"] for b in bots] == [1, 3]
    # ab purana 3rd bot 2nd slot pe hai
    assert _parse_slots("2", len(bots)) == [2] and bots[1]["id"] == 3
    print("  ✓ bot slots: 2nd delete → 3rd bot ab 2nd slot pe")


if __name__ == "__main__":
    test_parse_slots()
    test_ordinals()
    test_freeze_detection()
    test_saverm_slots_and_shift()
    test_anim_lookup()
    test_raid_rotation_math()
    test_bots_slot_shift()
    print("\n✅ ALL BOTCONTROLLER TESTS PASSED")

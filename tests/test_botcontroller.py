#!/usr/bin/env python3
"""v7.4 BotController tests — slots, ordinals, freeze-detect, saverm store,
raid rotation, stop-system, sudo, autodelete, BotFather engine, parser."""
import asyncio
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from plugins.botcontroller import (  # noqa: E402
    _parse_slots, _ord, _is_freeze_err, _rm_load, _rm_save,
    _anim_frames, DELEG_EXCLUDE_BASES, RM_STORE,
    _parse_count_interval, _gen_bot_username, _kill_tasks,
    _sudo_save, _sudo_ids, _ad_set, _ad_load, _load_profile_meta,
    _bf_ok, _TOKEN_RE, _invite_hint, _copy_send,
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


# ═════════════════════════════ v7.4 NEW ═════════════════════════════════

def test_count_interval_parser():
    # .spamb 10 1 hello → count=10 interval=1.0 text=hello
    assert _parse_count_interval("10 1 hello", need_text=True) == (10, 1.0, "hello", None)
    # float interval — NO lower limit (user requirement: 0.1/0.5 allowed)
    assert _parse_count_interval("10 .5 x", need_text=True) == (10, 0.5, "x", None)
    assert _parse_count_interval("50 0 x", need_text=True) == (50, 0.0, "x", None)
    # interval missing → default 0.5
    assert _parse_count_interval("10 hello", need_text=True) == (10, 0.5, "hello", None)
    # sticker spam (no text needed)
    assert _parse_count_interval("20", need_text=False)[:2] == (20, 0.5)
    # errors
    assert _parse_count_interval("abc 1 x", need_text=True)[3] == "count"
    assert _parse_count_interval("-3 1 x", need_text=True)[3] == "positive"
    assert _parse_count_interval("", need_text=True)[3] == "empty"
    assert _parse_count_interval("10", need_text=True)[3] == "text"
    print("  ✓ count/interval parser: floats, no-lower-limit, error cases")


def test_gen_bot_username():
    for _ in range(20):
        u = _gen_bot_username()
        assert u.endswith("bot"), f"{u} should end with 'bot' (TG rule)"
        assert 5 <= len(u) <= 32, f"{u} length 5-32"
        import re as _re
        assert _re.match(r"^worker\d+_bot$", u), u
    # custom base sanitize
    u = _gen_bot_username("My Cool Bot!")
    assert u.startswith("mycoolbot") and u.endswith("bot")
    print("  ✓ username gen: hamesha 'bot' end + unique random digits")


def test_kill_tasks_stop_family():
    class Task:
        def __init__(self):
            self.cancelled = False
            self.done = lambda: False
        def cancel(self):
            self.cancelled = True
    class FC:
        pass
    fc = FC()
    tasks = {
        "spam_101": Task(), "bc_spam_102_1": Task(), "bc_sspam_103_2": Task(),
        "bc_raid_104_1": Task(), "raid_105": Task(), "bc_anim_106_1": Task(),
        "bc_gather_107": Task(),
    }
    fc.stop_processes = dict(tasks)
    # .spamstop → spam but NOT sspam
    k = _kill_tasks(fc, lambda x: "spam" in x and "sspam" not in x)
    assert k == 2 and "spam_101" not in fc.stop_processes
    assert "bc_sspam_103_2" in fc.stop_processes
    # .sspamstop
    k = _kill_tasks(fc, lambda x: "sspam" in x)
    assert k == 1 and "bc_sspam_103_2" not in fc.stop_processes
    # .stopraid
    k = _kill_tasks(fc, lambda x: "raid" in x)
    assert k == 2 and "bc_raid_104_1" not in fc.stop_processes
    assert "raid_105" not in fc.stop_processes
    # .raidbstop → only bc_raid
    k = _kill_tasks(fc, lambda x: "bc_raid" in x)
    assert k == 0  # already killed above
    # .animstop
    k = _kill_tasks(fc, lambda x: "anim" in x)
    assert k == 1 and "bc_anim_106_1" not in fc.stop_processes
    # .stopall
    k = _kill_tasks(fc, lambda x: True)
    assert k == 1 and "bc_gather_107" not in fc.stop_processes
    assert fc.stop_processes == {}
    print("  ✓ stop-family: spamstop/sspamstop/stopraid/animstop/stopall filters")


def test_sudo_store_roundtrip():
    _sudo_save([111, 222, 222])          # dedupe too
    assert _sudo_ids() == {111, 222}
    _sudo_save([333])
    assert _sudo_ids() == {333}
    # cleanup
    _sudo_save([])
    assert _sudo_ids() == set()
    try:
        os.remove(os.path.join(DATA_DIR, "sudo.json"))
    except OSError:
        pass
    print("  ✓ sudo store: add/dedupe/persist round-trip")


def test_autodelete_default_on():
    # default must be ON (user requirement) — blank store → ON
    try:
        os.remove(os.path.join(DATA_DIR, "botcontroller.json"))
    except OSError:
        pass
    _ad_load()
    from plugins.botcontroller import _AD
    assert _AD.get("on") is True, "autodelete DEFAULT ON hona chahiye"
    # toggle off → persists
    _ad_set(False)
    _ad_load()
    assert _AD.get("on") is False
    # toggle back on
    _ad_set(True)
    _ad_load()
    assert _AD.get("on") is True
    print("  ✓ autodelete: default ON + on/off persist")


def test_botfather_engine():
    # token regex — BotFather reply se token extract
    ok = _TOKEN_RE.search(
        "Done! Congratulations on your new bot.\n"
        "Use this token: 123456789:AAHfLk9xQ2w3e4r5t6y7u8i9o0p1a2s3d")
    assert ok and ok.group(1).startswith("123456789:")
    # success/error keyword detection
    assert _bf_ok("Success! Name updated.") is True
    assert _bf_ok("Success! Description updated.") is True
    assert _bf_ok("Invalid name") is False
    assert _bf_ok("That bot doesn't exist") is False
    # invite hints — asli reason dikhna chahiye (ImportError fix follow-up)
    class ChatAdminRequiredError(Exception): pass
    h = _invite_hint(ChatAdminRequiredError("CHAT_ADMIN_REQUIRED"))
    assert "admin" in h.lower()
    class UserAlreadyParticipantError(Exception): pass
    assert "already" in _invite_hint(UserAlreadyParticipantError("")).lower()
    class PeerIdInvalidError(Exception): pass
    assert "/start" in _invite_hint(PeerIdInvalidError("PEER_ID_INVALID"))
    print("  ✓ BotFather engine: token extract + success detect + invite hints")


def test_profile_meta_missing():
    meta, photos, err = _load_profile_meta("aaisa_koi_profile_nahi_hai")
    assert meta is None and photos == [] and "nahi mila" in err
    print("  ✓ loadprofileb: missing profile → clear error (no crash)")


def test_copy_send_text():
    class Cl:
        def __init__(self):
            self.sent = []
        async def send_message(self, chat, text, **kw):
            self.sent.append(text)
            return True
        async def send_file(self, *a, **kw):
            self.sent.append("FILE")
            return True

    class Msg:
        raw_text = "hello yaar"
        media = None
    cl = Cl()
    ok = asyncio.run(_copy_send(cl, 55, Msg(), "/tmp/x"))
    assert ok and cl.sent == ["hello yaar"]
    print("  ✓ copy send (.ct): text exact wapas jata hai")


def test_importerror_fix_real_class():
    # THE BUG: AddChatMembersRequest telethon me EXIST nahi karta tha —
    # isliye .addallb me "❌ ImportError" aata tha. Ab AddChatUserRequest
    # (asli class) module-level import hota hai.
    from plugins import botcontroller as bc
    from telethon.tl.functions.messages import AddChatUserRequest
    assert bc.AddChatUserRequest is AddChatUserRequest or bc.AddChatUserRequest is None
    # aur InviteToChannelRequest core se already imported hai
    import core
    assert core.InviteToChannelRequest is not None
    print("  ✓ ImportError FIX: asli telethon class (AddChatUserRequest) in use")


if __name__ == "__main__":
    test_parse_slots()
    test_ordinals()
    test_freeze_detection()
    test_saverm_slots_and_shift()
    test_anim_lookup()
    test_raid_rotation_math()
    test_bots_slot_shift()
    print("── v7.4 ──")
    test_count_interval_parser()
    test_gen_bot_username()
    test_kill_tasks_stop_family()
    test_sudo_store_roundtrip()
    test_autodelete_default_on()
    test_botfather_engine()
    test_profile_meta_missing()
    test_copy_send_text()
    test_importerror_fix_real_class()
    print("\n✅ ALL BOTCONTROLLER TESTS PASSED")

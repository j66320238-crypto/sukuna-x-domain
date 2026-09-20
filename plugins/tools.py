# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

# ============================================================================
#  SECTION: TOOLS — web utilities + extra group power tools
#  NOTE: no imports here — everything comes from the header (+ _web_get
#  / _web_dl helpers shared from the FUN section, same namespace).
#  Inserted by assemble.py — do NOT run standalone.
# ============================================================================

antilink_state = {}  # {chat_id: True}


def register_tools(client):
    """Web tools + group extras."""

    # ================= WEB TOOLS =================

    # ---- .qr ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.qr\s+([\s\S]+)$"))
    @client.flood_safe
    async def _qr(event):
        text = event.pattern_match.group(1).strip()[:1000]
        if not text:
            return await event.edit("❌ Usage: `.qr <text>`")
        await event.edit("🔍 Generating QR…")
        dest = f"web_{event.id}.png"
        try:
            url = ("https://api.qrserver.com/v1/create-qr-code/"
                   f"?size=600x600&data={quote_plus(text)}")
            await _web_dl(url, dest)
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), dest,
                caption=f"🔳 QR for: `{text[:100]}`", reply_to=event.id,
            )
            await event.delete()
        except Exception:
            try:
                await event.edit("❌ QR generation failed. Try again later.")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .tr ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tr\s+([a-zA-Z-]{2,5})\s+([\s\S]+)$"))
    @client.flood_safe
    async def _tr(event):
        lang = event.pattern_match.group(1).lower()
        text = event.pattern_match.group(2).strip()[:1000]
        await event.edit(f"🔍 Translating to `{lang}`…")
        try:
            url = ("https://translate.googleapis.com/translate_a/single"
                   f"?client=gtx&sl=auto&tl={lang}&dt=t&q={quote_plus(text)}")
            data = json.loads(await _web_get(url))
            out = "".join(seg[0] for seg in data[0] if seg and seg[0])
            src = ""
            try:
                src = f" _(detected: {data[2]})_"
            except Exception:
                pass
            if not out:
                return await event.edit("❌ Translation failed. Check the language code.")
            await event.edit(f"🌐 **[{lang}]**{src}\n\n{out}", link_preview=False)
        except Exception:
            await event.edit("❌ Translation failed. Try again later.\nUsage: `.tr hi hello world`")

    # ---- .paste ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.paste(?:\s+([\s\S]+))?$"))
    @client.flood_safe
    async def _paste(event):
        text = (event.pattern_match.group(1) or "").strip()
        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = (reply.raw_text or "") if reply else ""
        text = text.strip()[:50000]
        if not text:
            return await event.edit("❌ Usage: `.paste <text>` or reply to a message.")
        await event.edit("📤 Uploading…")
        try:
            def _do():
                req = urllib.request.Request(
                    "https://paste.rs", data=text.encode("utf-8"),
                    headers={"User-Agent": "Mozilla/5.0",
                             "Content-Type": "text/plain"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    return r.read().decode("utf-8", "replace").strip()
            url = await asyncio.get_running_loop().run_in_executor(None, _do)
            await event.edit(f"📋 **Pasted!**\n🔗 {url}", link_preview=False)
        except Exception:
            await event.edit("❌ Paste failed. Try again later.")

    # ---- .tts ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tts\s+([\s\S]+)$"))
    @client.flood_safe
    async def _tts(event):
        raw = event.pattern_match.group(1).strip()
        try:
            from gtts import gTTS
        except ImportError:
            return await event.edit("🔊 Needs gTTS: run `pip install gtts`, then `.restart`.")
        parts = raw.split(None, 1)
        lang, text = "en", raw
        if len(parts) == 2 and len(parts[0]) == 2 and parts[0].isalpha():
            lang, text = parts[0].lower(), parts[1]
        text = text.strip()[:800]
        if not text:
            return await event.edit("❌ Usage: `.tts <text>` or `.tts hi <text>`")
        await event.edit("🔊 Speaking…")
        dest = f"tts_{event.id}.mp3"
        try:
            def _do():
                gTTS(text=text, lang=lang).save(dest)
            await asyncio.get_running_loop().run_in_executor(None, _do)
            await throttle("send")
            await client.send_file(
                await event.get_input_chat(), dest,
                caption=f"🔊 `{text[:80]}`", reply_to=event.id,
                voice_note=False,
            )
            await event.delete()
        except Exception as e:
            try:
                await event.edit(f"❌ TTS failed: `{e}`\n_Check language code: `.tts hi namaste`_")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass

    # ---- .dl ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.dl$"))
    @client.flood_safe
    async def _dl(event):
        reply = await event.get_reply_message()
        if not reply or not reply.media:
            return await event.edit("❌ Reply to any media with `.dl`.")
        await event.edit("📥 Downloading…")
        path = f"dl_{event.id}"
        try:
            downloaded = await client.download_media(reply, file=path)
            if not downloaded or not os.path.exists(downloaded):
                return await event.edit("❌ Download failed.")
            size = os.path.getsize(downloaded) / 1024
            await throttle("send")
            await client.send_file(
                "me", downloaded,
                caption=f"💾 **Downloaded**\n📄 `{os.path.basename(downloaded)}`\n📦 `{size:.1f} KB`",
            )
            await event.edit("✅ Sent to **Saved Messages**. 💾")
        finally:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass

    # ---- .save ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.save$"))
    @client.flood_safe
    async def _save(event):
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit("❌ Reply to a message with `.save`.")
        try:
            await client.forward_messages("me", reply)
            await event.edit("✅ Saved to **Saved Messages**. 💾")
        except Exception as e:
            await event.edit(f"❌ Save failed: `{e}`")

    # ================= GROUP EXTRAS =================

    # ---- .zombies ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.zombies$"))
    @client.flood_safe
    async def _zombies(event):
        if event.is_private:
            return await event.edit("❌ Use `.zombies` inside a group.")
        await event.edit("🔍 Scanning for deleted accounts…")
        try:
            users = await client.get_participants(await event.get_input_chat())
        except Exception as e:
            return await event.edit(f"❌ Can't fetch members: `{e}`")
        zom = [u for u in users if u.deleted]
        if not zom:
            return await event.edit("✅ No deleted accounts. Group is clean! 🧹")
        lines = [f"🧟 **Deleted accounts:** `{len(zom)}`", ""]
        for u in zom[:15]:
            lines.append(f"• [{u.first_name or 'Deleted'}](tg://user?id={u.id}) — `{u.id}`")
        if len(zom) > 15:
            lines.append(f"\n_…and {len(zom) - 15} more._")
        lines.append("\n_Remove them with `.cleandeleted`._")
        await event.edit("\n".join(lines), link_preview=False)

    # ---- .cleandeleted ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.cleandeleted$"))
    @client.flood_safe
    async def _cleandeleted(event):
        if event.is_private:
            return await event.edit("❌ Use `.cleandeleted` inside a group.")
        await event.edit("🧹 Cleaning deleted accounts…")
        try:
            chat = await event.get_input_chat()
            users = await client.get_participants(chat)
        except Exception as e:
            return await event.edit(f"❌ Can't fetch members: `{e}`")
        zom = [u for u in users if u.deleted]
        if not zom:
            return await event.edit("✅ No deleted accounts found.")
        ok, fail = 0, 0
        for u in zom:
            try:
                await client(EditBannedRequest(channel=chat, user_id=u.id,
                                               banned_rights=_FULL_BAN_RIGHTS))
                await client(EditBannedRequest(channel=chat, user_id=u.id,
                                               banned_rights=_FULL_FREE_RIGHTS))
                ok += 1
            except Exception:
                fail += 1
            await safe_sleep(0.5)
        await event.edit(f"🧹 **Cleanup done!**\n✅ Removed: `{ok}`\n❌ Failed: `{fail}`")

    # ---- .lockall / .unlockall ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(lockall|unlockall)$"))
    @client.flood_safe
    async def _lockall(event):
        if event.is_private:
            return await event.edit("❌ Use this inside a group.")
        locking = event.pattern_match.group(1) == "lockall"
        v = locking
        try:
            await client(EditChatDefaultBannedRightsRequest(
                peer=await event.get_input_chat(),
                banned_rights=ChatBannedRights(
                    until_date=None, send_messages=v, send_media=v,
                    send_stickers=v, send_gifs=v, send_games=v,
                    send_inline=v, embed_links=v, send_polls=v,
                    invite_users=v, pin_messages=v, change_info=v),
            ))
            await event.edit("🔒 **Group locked** — members can't send anything."
                             if locking else
                             "🔓 **Group unlocked** — members can send again.")
        except (UserAdminInvalidError, ChatAdminRequiredError):
            await event.edit("❌ I need **admin rights** for that.")
        except Exception as e:
            await event.edit(f"❌ Failed: `{e}`")

    # ---- .antilink ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.antilink(?:\s+(on|off|status))?$"))
    @client.flood_safe
    async def _antilink(event):
        if event.is_private:
            return await event.edit("❌ Use `.antilink` inside a group.")
        arg = (event.pattern_match.group(1) or "status").lower()
        cid = event.chat_id
        if arg == "on":
            antilink_state[cid] = True
            await event.edit("🔗 **Anti-Link ON** — link messages will be deleted.")
        elif arg == "off":
            antilink_state.pop(cid, None)
            await event.edit("✅ **Anti-Link OFF**")
        else:
            on = cid in antilink_state
            await event.edit(f"🔗 Anti-Link is **{'ON' if on else 'OFF'}**.")

    @client.on(events.NewMessage())
    async def _antilink_watch(event):
        try:
            if event.out or event.is_private:
                return
            if event.chat_id not in antilink_state:
                return
            text = (event.raw_text or "").lower()
            if not text or ("http://" not in text and "https://" not in text
                            and "t.me/" not in text and "telegram.me" not in text):
                return
            await event.delete()
        except Exception:
            pass

    # ---- .invite ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.invite$"))
    @client.flood_safe
    async def _invite(event):
        if event.is_private:
            return await event.edit("❌ Use `.invite` inside a group (reply to a user).")
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit("❌ Reply to the user you want to invite.")
        try:
            target = await reply.get_input_sender()
            chat = await event.get_input_chat()
            try:
                await client(InviteToChannelRequest(channel=chat, users=[target]))
            except Exception:
                from telethon.tl.functions.messages import AddChatUserRequest
                await client(AddChatUserRequest(chat_id=event.chat_id,
                                                user_id=target, fwd_limit=0))
            await event.edit("✅ **User invited!** 🎉")
        except (UserAdminInvalidError, ChatAdminRequiredError):
            await event.edit("❌ I need **admin rights** (invite users) for that.")
        except Exception as e:
            await event.edit(f"❌ Invite failed: `{e}`")

    # ---- .bots ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.bots$"))
    @client.flood_safe
    async def _bots(event):
        if event.is_private:
            return await event.edit("❌ Use `.bots` inside a group.")
        try:
            bots = await client.get_participants(
                await event.get_input_chat(), filter=ChannelParticipantsBots)
        except Exception as e:
            return await event.edit(f"❌ Can't fetch bots: `{e}`")
        if not bots:
            return await event.edit("✅ No bots in this chat.")
        lines = [f"🤖 **Bots in chat:** `{len(bots)}`", ""]
        for b in bots:
            uname = f"@{b.username}" if b.username else "_no username_"
            lines.append(f"• {b.first_name} ({uname}) — `{b.id}`")
        await event.edit("\n".join(lines), link_preview=False)

    # ---- .ginfo ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ginfo$"))
    @client.flood_safe
    async def _ginfo(event):
        if event.is_private:
            return await event.edit("❌ Use `.ginfo` inside a group/channel.")
        await event.edit("🔍 Fetching chat info…")
        try:
            chat = await event.get_chat()
            title = getattr(chat, "title", "—")
            cid = getattr(chat, "id", event.chat_id)
            uname = f"@{chat.username}" if getattr(chat, "username", None) else "—"
            about, members, admins = "—", "—", "—"
            try:
                from telethon.tl.functions.channels import GetFullChannel
                full = await client(GetFullChannel(channel=chat))
                about = (full.full_chat.about or "—")[:300]
                members = full.full_chat.participants_count or "—"
                admins = full.full_chat.admins_count or "—"
            except Exception:
                try:
                    members = len(await client.get_participants(chat, limit=0)) or "—"
                except Exception:
                    pass
            await event.edit(
                "✦ ━━━〔 👥 CHAT INFO 〕━━━ ✦\n"
                f"┃ 📛 Title    : **{title}**\n"
                f"┃ 🆔 ID       : `{cid}`\n"
                f"┃ 🔗 Username : {uname}\n"
                f"┃ 👥 Members  : `{members}`\n"
                f"┃ 🛡 Admins   : `{admins}`\n"
                f"┃ 📝 About    : {about}\n"
                "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
                link_preview=False,
            )
        except Exception as e:
            await event.edit(f"❌ Failed: `{e}`")

    # ---- .join ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.join\s+(\S+)$"))
    @client.flood_safe
    async def _join(event):
        arg = event.pattern_match.group(1).strip()
        await event.edit("🔍 Joining…")
        try:
            if "/+" in arg or "joinchat" in arg:
                h = arg.split("/+")[-1].split("joinchat/")[-1].strip("/").split("?")[0]
                await client(ImportChatInviteRequest(hash=h))
            else:
                u = arg.split("t.me/")[-1].strip("/@ ").split("?")[0].split("/")[0]
                await client(JoinChannelRequest(channel=u))
            await event.edit("✅ **Joined!** 🎉")
        except Exception as e:
            await event.edit(f"❌ Join failed: `{e}`")

    # ---- .leave ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.leave$"))
    @client.flood_safe
    async def _leave(event):
        if event.is_private:
            return await event.edit("❌ Use `.leave` inside a group/channel.")
        await event.edit("👋 Leaving…")
        await asyncio.sleep(1)
        try:
            await client(LeaveChannelRequest(channel=await event.get_input_chat()))
        except Exception:
            try:
                from telethon.tl.functions.messages import DeleteChatUserRequest
                me = await client.get_me()
                await client(DeleteChatUserRequest(chat_id=event.chat_id,
                                                   user_id=me.id))
            except Exception as e:
                return await event.edit(f"❌ Leave failed: `{e}`")

    # ---- .report ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.report(?:\s+(.*))?$"))
    @client.flood_safe
    async def _report(event):
        if event.is_private:
            return await event.edit("❌ Use `.report` inside a group (reply to a message).")
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit("❌ Reply to the message you want to report.")
        reason = (event.pattern_match.group(1) or "").strip() or "Reported message"
        me = await client.get_me()
        try:
            admins = await client.get_participants(
                await event.get_input_chat(), filter=ChannelParticipantsAdmins)
        except Exception as e:
            return await event.edit(f"❌ Can't fetch admins: `{e}`")
        mentions = " ".join(
            f'<a href="tg://user?id={a.id}">{a.first_name or "Admin"}</a>'
            for a in admins if not getattr(a, "bot", False))
        if not mentions:
            return await event.edit("❌ No human admins found.")
        await throttle("send")
        await reply.reply(f"🚨 <b>Reported</b> by {me.first_name}\n📝 {reason}\n{mentions}",
                          parse_mode="html")

    # ---- .link ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.link$"))
    @client.flood_safe
    async def _link(event):
        if event.is_private:
            return await event.edit("❌ Use `.link` inside a group/channel.")
        try:
            res = await client(ExportChatInviteRequest(
                peer=await event.get_input_chat()))
            await event.edit(f"🔗 **Invite link:**\n`{res.link}`", link_preview=False)
        except (UserAdminInvalidError, ChatAdminRequiredError):
            await event.edit("❌ I need **admin rights** (invite link) for that.")
        except Exception as e:
            await event.edit(f"❌ Failed: `{e}`")

    # ---- .pinned ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pinned$"))
    @client.flood_safe
    async def _pinned(event):
        if event.is_private:
            return await event.edit("❌ Use `.pinned` inside a group/channel.")
        try:
            from telethon.tl.types import InputMessagesFilterPinned
            msgs = await client.get_messages(
                await event.get_input_chat(), filter=InputMessagesFilterPinned, limit=1)
        except Exception as e:
            return await event.edit(f"❌ Failed: `{e}`")
        if not msgs:
            return await event.edit("📌 No pinned message in this chat.")
        m = msgs[0]
        text = (m.raw_text or "[media]").strip()[:600]
        await event.edit(f"📌 **Pinned** (id `{m.id}`):\n\n{text}", link_preview=False)

    # ---- .sysinfo ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sysinfo$"))
    @client.flood_safe
    async def _sysinfo(event):
        await event.edit("🖥️ Reading system stats…")
        try:
            cpu_load = os.getloadavg()[0] if hasattr(os, "getloadavg") else "n/a"
        except Exception:
            cpu_load = "n/a"
        cores = os.cpu_count() or "?"
        ram = "n/a"
        try:
            with open("/proc/meminfo") as fh:
                mi = {}
                for line in fh:
                    k, _, v = line.partition(":")
                    mi[k.strip()] = v.strip()
            tot = int(mi.get("MemTotal", "0 kB").split()[0]) // 1024
            av = int(mi.get("MemAvailable", "0 kB").split()[0]) // 1024
            ram = f"{av} MB free / {tot} MB"
        except Exception:
            pass
        disk = "n/a"
        try:
            st = shutil.disk_usage("/")
            disk = f"{st.free // (1024**3)} GB free / {st.total // (1024**3)} GB"
        except Exception:
            pass
        py = platform.python_version()
        await event.edit(
            "✦ ━━━〔 🖥️ SYSTEM INFO 〕━━━ ✦\n"
            f"┃ 💻 OS      : {html.escape(platform.system() + ' ' + platform.release())}\n"
            f"┃ 🧠 CPU     : `{cores}` cores · load `{cpu_load}`\n"
            f"┃ 🧮 RAM     : `{ram}`\n"
            f"┃ 💾 Disk    : `{disk}`\n"
            f"┃ 🐍 Python  : `{py}`  ·  Telethon `{globals().get('telethon_version', '?')}`\n"
            f"┃ 🤖 Bot     : SUKUNA-X v`{BOT_VERSION}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )



COMMANDS_TOOLS = {
    "description": "Web & Group Tools",
    "commands": [
        (".qr <text>", "generate a QR code image"),
        (".tr <lang> <text>", "translate (auto-detect source)"),
        (".paste <text|reply>", "upload text, get a link"),
        (".tts [lang] <text>", "text → speech audio"),
        (".dl", "download replied media to Saved Msgs"),
        (".save", "forward replied msg to Saved Msgs"),
        (".zombies", "list deleted accounts"),
        (".cleandeleted", "kick deleted accounts"),
        (".lockall / .unlockall", "lock/unlock whole group"),
        (".antilink on|off", "auto-delete link messages"),
        (".invite", "invite replied user (reply)"),
        (".bots", "list bots in chat"),
        (".ginfo", "group/channel info card"),
        (".join <link|@user>", "join a chat"),
        (".leave", "leave current chat"),
        (".report [reason]", "report replied msg to admins"),
        (".link", "get chat invite link"),
        (".pinned", "show pinned message"),
        (".sysinfo", "CPU / RAM / disk / versions"),
    ],
}

# ── SUKUNA-X DOMAIN plugin ─────────────────────────────────────────────
from core import *  # noqa: F401,F403 — shared engine

############################################################################
#  SECTION: MISC  (ported from worker_bot/modules/misc.py)
############################################################################

# worker_bot/modules/misc.py
"""
Misc / Utility Module — small but handy everyday commands.

Commands:
    .ping        — measure round-trip latency to Telegram.
    .uptime      — how long the userbot has been running.
    .sysinfo     — system report (OS, CPU, RAM, Python, Telethon).
    .calc <expr> — safe calculator (no eval, AST-validated).
    .google <q>  — instant Google search link.
    .time        — current server time & date.
    .random      — random number 1-100 (or .random <max>).
    .reverse <t> — reverse any text (𝗺irrored fun).
    .count <t>   — character/word count of the text.
"""



START_TIME = time.time()

# Safe math operators for .calc (NO eval — AST validated)
_SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_SAFE_FUNCS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "floor": math.floor,
    "ceil": math.ceil,
    "abs": abs,
    "round": round,
    "pi": math.pi,
    "e": math.e,
}


def _safe_calc(expr: str):
    """Evaluate a math expression via a whitelist AST walk. Raises on danger."""
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("only numbers allowed")
        if isinstance(node, ast.BinOp):
            op = _SAFE_BINOPS.get(type(node.op))
            if op is None:
                raise ValueError("operator not allowed")
            return op(_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -_eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +_eval(node.operand)
            raise ValueError("unary operator not allowed")
        if isinstance(node, ast.Name):
            if node.id in _SAFE_FUNCS:
                return _SAFE_FUNCS[node.id]
            raise ValueError(f"unknown name: {node.id}")
        if isinstance(node, ast.Call):
            fn = _eval(node.func)
            if fn not in _SAFE_FUNCS.values():
                raise ValueError("function not allowed")
            return fn(*[_eval(a) for a in node.args])
        raise ValueError("expression element not allowed")

    tree = ast.parse(expr, mode="eval")
    return _eval(tree)


def _fmt_uptime(seconds: float) -> str:
    s = int(seconds)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    parts.append(f"{m}m {s}s")
    return " ".join(parts)


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


try:
    import psutil  # optional — used by .sysinfo when available
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

COMMANDS_MISC = {
    "description": "Misc & Utilities",
    "commands": [
        (".ping", "measure Telegram latency"),
        (".uptime", "bot uptime"),
        (".sysinfo", "server system report"),
        (".calc <expr>", "safe calculator"),
        (".google <query>", "Google search link"),
        (".time", "server date & time"),
        (".random [max]", "random number"),
        (".reverse <text>", "reverse text"),
        (".count <text>", "character/word count"),
        (".gc", "memory cleanup + stats (optimise)"),
        (".speed", "event-loop + Telegram speed test"),
    ],
}


def register_misc(client):
    """Register every misc command on the given client."""

    # ---- .ping ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
    async def _ping(event):
        t0 = datetime.datetime.now()
        await event.edit("✦ · · ·")
        await asyncio.sleep(0.25)
        await event.edit("✦ ✦ · ·")
        ms = (datetime.datetime.now() - t0).total_seconds() * 1000
        await event.edit(
            "✦ ━━━〔 🏓 PONG 〕━━━ ✦\n"
            f"┃ 📶 Ping   : `{ms:.0f} ms`\n"
            f"┃ ⏱ Uptime : `{_fmt_uptime(time.time() - START_TIME)}`\n"
            "✦ ━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    # ---- .uptime ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.uptime$"))
    async def _uptime(event):
        up = _fmt_uptime(time.time() - START_TIME)
        await event.edit(
            "✦ ━━━〔 ⏱ UPTIME 〕━━━ ✦\n"
            f"┃ ⚡ Sukuna-X has been online for: `{up}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    # ---- .sysinfo ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sysinfo$"))
    async def _sysinfo(event):
        lines = [
            "🖥  **System Info**",
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"**OS:**       {platform.system()} {platform.release()}",
            f"**Arch:**     {platform.machine()}",
            f"**Python:**   {platform.python_version()}",
            f"**Telethon:** {telethon_version}",
            f"**Uptime:**   {_fmt_uptime(time.time() - START_TIME)}",
        ]
        if _HAS_PSUTIL:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            lines += [
                f"**CPU:**      {psutil.cpu_count()} cores — "
                f"{psutil.cpu_percent(interval=0.3)}% used",
                f"**RAM:**      {_fmt_bytes(vm.used)} / {_fmt_bytes(vm.total)} "
                f"({vm.percent}%)",
                f"**Swap:**     {_fmt_bytes(swap.used)} / {_fmt_bytes(swap.total)}",
            ]
            try:
                load1, load5, load15 = os.getloadavg()
                lines.append(f"**Load:**     {load1:.2f} / {load5:.2f} / {load15:.2f}")
            except Exception:
                pass
        else:
            lines.append("_Install `psutil` for CPU/RAM stats._")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        await event.edit("\n".join(lines), link_preview=False)

    # ---- .calc ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.calc\s+(.+)$"))
    async def _calc(event):
        expr = event.pattern_match.group(1).strip()
        try:
            result = _safe_calc(expr)
            await event.edit(f"🧮 `{expr}` = **{result}**")
        except ZeroDivisionError:
            await event.edit("🧮 ❌ Division by zero.")
        except Exception as e:
            await event.edit(f"🧮 ❌ Invalid expression: `{e}`")

    # ---- .google ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.google\s+(.+)$"))
    async def _google(event):
        from urllib.parse import quote_plus
        q = event.pattern_match.group(1).strip()
        url = f"https://www.google.com/search?q={quote_plus(q)}"
        await event.edit(f"🔍 [Google: **{q}**]({url})")

    # ---- .time ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.time$"))
    async def _time(event):
        now = datetime.datetime.now()
        await event.edit(
            f"🕒 **{now:%Y-%m-%d %H:%M:%S}**\n"
            f" `{now:%A}`"
        )

    # ---- .random ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.random(?:\s+(\d+))?$"))
    async def _random(event):
        top = int(event.pattern_match.group(1) or 100)
        if top < 1:
            return await event.edit("❌ Max must be ≥ 1.")
        await event.edit(f"🎲 **{random.randint(1, top)}** _(1–{top})_")

    # ---- .reverse ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.reverse\s+(.+)$"))
    async def _reverse(event):
        text = event.pattern_match.group(1).strip()
        await event.edit(f"🔁 {text[::-1]}")

    # ---- .count ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.count\s+(.+)$"))
    async def _count(event):
        text = event.pattern_match.group(1).strip()
        words = len(text.split())
        chars = len(text)
        await event.edit(
            f"📊 **Characters:** `{chars}`  |  **Words:** `{words}`"
        )

    # ---- .gc : memory cleanup (optimisation) ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.gc$"))
    async def _gc(event):
        import gc as _gc
        await event.edit("🧹 Cleaning memory…")
        before = len(_gc.get_objects())
        freed = _gc.collect()
        after = len(_gc.get_objects())
        ram_line = ""
        if _HAS_PSUTIL:
            vm = psutil.virtual_memory()
            def _fb(n):
                for u in ("B", "KB", "MB", "GB"):
                    if n < 1024:
                        return f"{n:.1f}{u}"
                    n /= 1024
                return f"{n:.1f}TB"
            ram_line = f"┃ 💾 RAM     : `{_fb(vm.used)}` ({vm.percent}%)\n"
        await event.edit(
            "✦ ━━━〔 🧹 MEMORY SWEEP 〕━━━ ✦\n"
            f"┃ ♻️ Freed   : `{freed}` objects\n"
            f"┃ 📦 Objects : `{before:,}` → `{after:,}`\n"
            f"┃ 🧵 Tasks   : `{len(stop_processes)}` active\n"
            f"{ram_line}"
            "┃ ⚡ Bot optimised & smooth\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

    # ---- .speed : loop + network responsiveness ----
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.speed$"))
    async def _speed(event):
        t0 = time.time()
        # event-loop responsiveness: 20 micro-sleeps should total ~0.2s
        for _ in range(20):
            await asyncio.sleep(0.01)
        loop_ms = (time.time() - t0) * 1000
        t1 = time.time()
        try:
            await client.get_me()
            tg_ms = (time.time() - t1) * 1000
        except Exception:
            tg_ms = -1
        grade = "🚀 KHATARNAK" if loop_ms < 350 else ("✅ Normal" if loop_ms < 800 else "🐢 Slow")
        await event.edit(
            "✦ ━━━〔 ⚡ SPEED TEST 〕━━━ ✦\n"
            f"┃ 🧠 Event loop : `{loop_ms:.0f} ms` ({grade})\n"
            f"┃ 📡 Telegram   : `{tg_ms:.0f} ms`"
            + ("" if tg_ms >= 0 else " (failed)") + "\n"
            f"┃ ⏱ Uptime     : `{_fmt_uptime(time.time() - START_TIME)}`\n"
            "✦ ━━━━━━━━━━━━━━━━━━━━ ✦",
            link_preview=False,
        )

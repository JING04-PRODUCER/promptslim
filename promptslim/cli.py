"""CLI 命令行工具 — promptslim 入口"""

from __future__ import annotations

import sys
import json
from pathlib import Path


def _build_parser():
    import argparse

    p = argparse.ArgumentParser(
        prog="promptslim",
        description="AI 提示词瘦身 — 从源头减少 Token 消耗",
    )
    sub = p.add_subparsers(dest="command")

    # === count ===
    c = sub.add_parser("count", help="统计文本 Token 数量")
    c.add_argument("input", help="文本内容 / 文件路径（用 file: 前缀）")
    c.add_argument("-m", "--model", default="gpt-4o", help="模型名称（默认 gpt-4o）")
    c.add_argument("--json", action="store_true", help="JSON 格式输出")

    # === slim ===
    s = sub.add_parser("slim", help="快速去冗余瘦身")
    s.add_argument("input", help="文本内容 / 文件路径（用 file: 前缀）")
    s.add_argument("-m", "--model", default="gpt-4o", help="模型名称（默认 gpt-4o）")
    s.add_argument("-o", "--output", help="输出文件路径")
    s.add_argument("--json", action="store_true", help="JSON 格式输出")

    # === smart ===
    sm = sub.add_parser("smart", help="调用 LLM 智能压缩（需 API Key）")
    sm.add_argument("input", help="文本内容 / 文件路径（用 file: 前缀）")
    sm.add_argument("-m", "--model", default="gpt-4o-mini", help="压缩用模型（默认 gpt-4o-mini）")
    sm.add_argument("--max-tokens", type=int, default=2048, help="压缩后最大 Token 数（默认 2048）")
    sm.add_argument("-o", "--output", help="输出文件路径")
    sm.add_argument("--json", action="store_true", help="JSON 格式输出")

    # === compare ===
    cm = sub.add_parser("compare", help="对比两个文本的 Token 差异")
    cm.add_argument("a", help="原始文本 / 文件路径")
    cm.add_argument("b", help="对比文本 / 文件路径")
    cm.add_argument("-m", "--model", default="gpt-4o", help="模型名称（默认 gpt-4o）")

    return p


def _read_input(raw: str) -> str:
    if raw.startswith("file:"):
        return Path(raw[5:]).read_text(encoding="utf-8")
    if Path(raw).exists():
        return Path(raw).read_text(encoding="utf-8")
    return raw


def _color_pct(pct: float) -> str:
    if pct <= 0:
        return f"[dim]{pct}%[/]"
    if pct < 10:
        return f"[yellow]{pct}%[/]"
    return f"[green]{pct}%[/]"


def cmd_count(args):
    from .tokenizer import count_tokens, cost_estimate

    text = _read_input(args.input)
    tokens = count_tokens(text, args.model)
    cost = cost_estimate(text, args.model)

    if args.json:
        print(json.dumps({"tokens": tokens, "estimated_cost_usd": cost, "model": args.model}, ensure_ascii=False))
    else:
        from rich.console import Console
        from rich.table import Table
        c = Console()
        t = Table(title=f"Token 统计 — {args.model}")
        t.add_column("指标", style="cyan")
        t.add_column("值", style="green")
        t.add_row("字符数", str(len(text)))
        t.add_row("Token 数", str(tokens))
        t.add_row("估算费用 (输入)", f"${cost:.6f}")
        c.print(t)


def cmd_slim(args):
    from .compressor import quick_slim

    text = _read_input(args.input)
    report = quick_slim(text, args.model)

    if args.output:
        Path(args.output).write_text(report.slimmed, encoding="utf-8")

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False))
    else:
        _print_report(report)


def cmd_smart(args):
    from .compressor import smart_slim

    text = _read_input(args.input)
    report = smart_slim(text, args.model, args.max_tokens)

    if args.output:
        Path(args.output).write_text(report.slimmed, encoding="utf-8")

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False))
    else:
        _print_report(report)


def cmd_compare(args):
    from .tokenizer import count_tokens

    ta = _read_input(args.a)
    tb = _read_input(args.b)
    ta_tok = count_tokens(ta, args.model)
    tb_tok = count_tokens(tb, args.model)

    diff = ta_tok - tb_tok
    pct = round(diff / ta_tok * 100, 1) if ta_tok > 0 else 0

    from rich.console import Console
    from rich.table import Table
    c = Console()
    t = Table(title=f"Token 对比 — {args.model}")
    t.add_column("文本", style="cyan")
    t.add_column("字符数")
    t.add_column("Token 数", style="yellow")
    t.add_row("原始", str(len(ta)), str(ta_tok))
    t.add_row("对比", str(len(tb)), str(tb_tok))
    t.add_row("差异", f"-{abs(len(ta) - len(tb))}", f"-{diff}" if diff > 0 else f"+{abs(diff)}")
    t.add_row("节省比例", "", f"{pct}%")
    c.print(t)


def _print_report(report):
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text

    d = report.to_dict()
    c = Console()

    # 核心指标
    t = Table(title=f"Slim 瘦身报告 — {d['model']}")
    t.add_column("指标", style="cyan")
    t.add_column("原始", style="red")
    t.add_column("瘦身后", style="green")
    t.add_column("节省", style="yellow")
    t.add_row("字符数", str(d["original_chars"]), str(d["slimmed_chars"]), f"-{d['original_chars'] - d['slimmed_chars']}")
    t.add_row("Token 数", str(d["original_tokens"]), str(d["slimmed_tokens"]), f"-{d['tokens_saved']}")
    t.add_row("费用/次", "-", "-", f"${d['cost_per_call_saved_usd']:.6f}")
    c.print(t)

    pct = d["savings_pct"]
    if pct > 20:
        color = "green"
        emoji = "[Great!]"
    elif pct > 5:
        color = "yellow"
        emoji = "[OK]"
    else:
        color = "dim"
        emoji = "[Tip]"

    msg = Text(f"\n{emoji} Token 节省 {pct}%，每次调用节省约 ${d['cost_per_call_saved_usd']:.6f}")
    msg.stylize(color)
    c.print(msg)

    if pct <= 5:
        c.print("[dim]提示：试试 smart 模式，用 LLM 做更激进的压缩[/]")


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cmds = {
        "count": cmd_count,
        "slim": cmd_slim,
        "smart": cmd_smart,
        "compare": cmd_compare,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()

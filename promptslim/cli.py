"""CLI 命令行工具 — promptslim 入口"""

from __future__ import annotations

import json
from pathlib import Path


def _build_parser():
    import argparse

    p = argparse.ArgumentParser(
        prog="promptslim",
        description="AI 提示词瘦身 — 从源头减少 Token 消耗",
    )
    sub = p.add_subparsers(dest="command")

    c = sub.add_parser("count", help="统计文本 Token 数量")
    c.add_argument("input", help="文本内容 / 文件路径（用 file: 前缀）")
    c.add_argument("-m", "--model", default="gpt-4o", help="模型名称（默认 gpt-4o）")
    c.add_argument("--json", action="store_true", help="JSON 格式输出")
    c.add_argument("--cache", metavar="MESSAGES_JSON", help="分析 Prompt Caching 节省潜力（传入 messages JSON 文件路径）")

    s = sub.add_parser("slim", help="快速去冗余瘦身")
    s.add_argument("input", help="文本内容 / 文件路径（用 file: 前缀）")
    s.add_argument("-m", "--model", default="gpt-4o", help="模型名称（默认 gpt-4o）")
    s.add_argument("-o", "--output", help="输出文件路径")
    s.add_argument("--json", action="store_true", help="JSON 格式输出")

    sm = sub.add_parser("smart", help="调用 LLM 智能压缩（需 API Key）")
    sm.add_argument("input", help="文本内容 / 文件路径（用 file: 前缀）")
    sm.add_argument("-m", "--model", default="gpt-4o-mini", help="压缩用模型（默认 gpt-4o-mini）")
    sm.add_argument("--max-tokens", type=int, default=2048, help="压缩后最大 Token 数（默认 2048）")
    sm.add_argument("--base-url", help="自定义 API 地址")
    sm.add_argument("--api-key", help="API 密钥")
    sm.add_argument("-o", "--output", help="输出文件路径")
    sm.add_argument("--json", action="store_true", help="JSON 格式输出")

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


def cmd_count(args):
    from .tokenizer import cost, count

    text = _read_input(args.input)
    tokens = count(text, args.model)
    cost_val = cost(args.model, tokens, 0)

    cache_data = None
    if args.cache:
        try:
            messages = json.loads(Path(args.cache).read_text(encoding="utf-8"))
            from .cache import analyze
            cache_data = analyze(messages, args.model)
        except Exception as e:
            from rich.console import Console
            Console().print(f"[yellow]缓存分析失败: {e}[/]")

    if args.json:
        out = {"tokens": tokens, "estimated_cost_usd": round(cost_val, 6), "model": args.model}
        if cache_data:
            out["cache"] = cache_data.to_dict()
        print(json.dumps(out, ensure_ascii=False))
    else:
        from rich.console import Console
        from rich.table import Table
        c = Console()
        t = Table(title=f"Token 统计 — {args.model}")
        t.add_column("指标", style="cyan")
        t.add_column("值", style="green")
        t.add_row("字符数", str(len(text)))
        t.add_row("Token 数", str(tokens))
        t.add_row("估算费用 (输入)", f"${cost_val:.6f}")
        c.print(t)

        if cache_data:
            _print_cache_table(cache_data)


def cmd_slim(args):
    from .compressor import quick_slim

    text = _read_input(args.input)
    report = quick_slim(text, args.model)

    if args.output:
        Path(args.output).write_text(report.compressed, encoding="utf-8")

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False))
    else:
        _print_report(report)


def cmd_smart(args):
    from .compressor import CompressReport, smart_compress

    text = _read_input(args.input)
    compressed = smart_compress(text, args.model, args.max_tokens,
                                base_url=args.base_url, api_key=args.api_key)
    report = CompressReport(original=text, compressed=compressed, model=args.model)

    if args.output:
        Path(args.output).write_text(report.compressed, encoding="utf-8")

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False))
    else:
        _print_report(report)


def cmd_compare(args):
    from .tokenizer import count

    ta = _read_input(args.a)
    tb = _read_input(args.b)
    ta_tok = count(ta, args.model)
    tb_tok = count(tb, args.model)

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
    from rich.text import Text

    d = report.to_dict()
    c = Console()

    t = Table(title=f"Slim 瘦身报告 — {d['model']}")
    t.add_column("指标", style="cyan")
    t.add_column("原始", style="red")
    t.add_column("瘦身后", style="green")
    t.add_column("节省", style="yellow")
    t.add_row("字符数", str(d["original_chars"]), str(d["compressed_chars"]),
              f"-{d['original_chars'] - d['compressed_chars']}")
    t.add_row("Token 数", str(d["original_tokens"]), str(d["compressed_tokens"]),
              f"-{d['tokens_saved']}")
    t.add_row("费用/次", "-", "-", f"${d['cost_saved_usd']:.6f}")
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

    msg = Text(f"\n{emoji} Token 节省 {pct}%，每次调用节省约 ${d['cost_saved_usd']:.6f}")
    msg.stylize(color)
    c.print(msg)

    if pct <= 5:
        c.print("[dim]提示：试试 smart 模式，用 LLM 做更激进的压缩[/]")


def _print_cache_table(cache_data):
    from rich.console import Console
    from rich.table import Table

    from .cache import CACHE_READ_MULT, CACHE_TTL, CACHE_WRITE_MULT

    d = cache_data.to_dict()
    c = Console()

    t = Table(title="Prompt Caching 缓存分析")
    t.add_column("指标", style="cyan")
    t.add_column("值", style="green")
    t.add_row("可缓存 Token", f"{d['cacheable_tokens']} / {d['total_tokens']} ({d['cacheable_pct']}%)")
    t.add_row("缓存块数", str(d["blocks"]))
    t.add_row("断点使用", f"{d['breakpoints']} / 4")
    t.add_row("无缓存费用", f"${d['cost_without_cache_usd']:.6f}")
    t.add_row("首次写入费用", f"${d['cost_first_call_usd']:.6f} (x{CACHE_WRITE_MULT})")
    t.add_row("缓存命中费用", f"${d['cost_cached_call_usd']:.6f} (x{CACHE_READ_MULT})")
    t.add_row("每次命中节省", f"${d['savings_per_call_usd']:.6f}")
    t.add_row("缓存 TTL", f"{CACHE_TTL}s (5 分钟)")
    c.print(t)

    if d["savings_pct"] > 0:
        c.print(f"\n[green]缓存命中后可再节省 {d['savings_pct']}% input 费用[/]")
    else:
        c.print("\n[dim]当前消息无可缓存部分（system prompt 需 >1024 tokens）[/]")


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

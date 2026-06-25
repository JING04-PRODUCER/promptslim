"""
Generate a terminal-style demo GIF for promptslim.
Uses Pillow — no external recording tools needed.
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Configuration ──────────────────────────────────────────
W, H = 720, 480
BG = "#1e1e2e"
FG = "#cdd6f4"
GREEN = "#a6e3a1"
CYAN = "#89dceb"
YELLOW = "#f9e2af"
RED = "#f38ba8"
MAGENTA = "#cba6f7"
TITLE_BG = "#181825"
PROMPT_COLOR = GREEN
CMD_COLOR = CYAN
DIALOG_BG = "#313244"
FONT_PATH = None  # auto-detect

OUTPUT = Path(__file__).resolve().parent.parent / "demo.gif"

# Frame timing (ms)
FAST = 500
NORMAL = 1200
SLOW = 2000
PAUSE = 3000

# ── Font detection ─────────────────────────────────────────
def _get_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/Cour.ttf",
        "C:/Windows/Fonts/DejaVuSansMono.ttf",
        "C:/Windows/Fonts/JetBrainsMono-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ── Helpers ────────────────────────────────────────────────
def new_frame() -> tuple[Image.Image, ImageDraw.Draw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # Title bar
    draw.rectangle([0, 0, W, 28], fill=TITLE_BG)
    font_sm = _get_font(13)
    draw.text((12, 5), "Terminal — promptslim demo", fill=GREEN, font=font_sm)
    # Window controls
    for i, color in enumerate(["#f38ba8", "#f9e2af", "#a6e3a1"]):
        draw.ellipse([W - 60 + i * 18, 7, W - 48 + i * 18, 21], fill=color)
    return img, draw


def draw_text(draw, x, y, text, color=FG, size=14):
    font = _get_font(size)
    draw.text((x, y), text, fill=color, font=font)


def draw_prompt(draw, x, y, text, size=14):
    """Draw a shell prompt line"""
    font = _get_font(size)
    draw.text((x, y), "$ ", fill=GREEN, font=font)
    w = font.getlength("$ ")
    draw.text((x + w, y), text, fill=CMD_COLOR, font=font)


def draw_output(draw, x, y, lines, color=FG, size=13):
    """Draw multi-line output"""
    font = _get_font(size)
    for i, line in enumerate(lines):
        draw.text((x, y + i * 19), line, fill=color, font=font)


# ── Scene generators ───────────────────────────────────────
def scene_help() -> list[Image.Image]:
    """Scene: promptslim --help"""
    frames = []
    help_lines = [
        "usage: promptslim [-h] {count,slim,smart,compare} ...",
        "",
        "AI Prompt Slimmer — Reduce Token Costs at the Source",
        "",
        "positional arguments:",
        "  {count,slim,smart,compare}",
        "    count        Count tokens in text",
        "    slim         Rule-based redundancy removal",
        "    smart        LLM-powered intelligent compression (needs API key)",
        "    compare      Compare token counts between texts",
        "",
        "options:",
        "  -h, --help     show this help message and exit",
        "  --version      show program's version number and exit",
    ]

    img, draw = new_frame()
    draw_prompt(draw, 12, 36, "promptslim --help")
    draw_output(draw, 12, 62, help_lines)
    frames.append(img)
    return frames


def scene_slim_typing() -> list[Image.Image]:
    """Scene: typing the slim command"""
    frames = []
    cmd = 'promptslim slim "I would like to kindly request that you please help me to analyze the performance bottlenecks in this code..."'

    # Frame 1: just the prompt, no command
    img, draw = new_frame()
    draw_prompt(draw, 12, 36, "")
    frames.append(img)

    # Frame 2: partial command
    img, draw = new_frame()
    draw_prompt(draw, 12, 36, cmd[:40])
    frames.append(img)

    # Frame 3: full command
    img, draw = new_frame()
    draw_prompt(draw, 12, 36, cmd)
    frames.append(img)

    return frames


def scene_slim_result() -> list[Image.Image]:
    """Scene: slim results"""
    frames = []
    img, draw = new_frame()
    cmd = 'promptslim slim "I would like to kindly request that you please help me..."'
    draw_prompt(draw, 12, 36, cmd)

    result_lines = [
        "",
        "  Original :   64 tokens  (364 chars)",
        "  Slimmed  :   60 tokens  (345 chars)",
        "  ──────────────────────────────────",
        "  Saved    :    4 tokens  (6.3% reduction)",
        "  Chars    :   19 chars removed",
        "",
        "  Slimmed text:",
        '  "I kindly request that you please help me to analyze..."',
    ]
    draw_output(draw, 12, 62, result_lines)
    for i, line in enumerate(result_lines):
        if "Saved" in line:
            draw.text((12, 62 + i * 19), line, fill=YELLOW, font=_get_font(13))
        elif "Slimmed" in line:
            draw.text((12, 62 + i * 19), line, fill=GREEN, font=_get_font(13))
    frames.append(img)
    return frames


def scene_python_api() -> list[Image.Image]:
    """Scene: Python API usage"""
    frames = []
    img, draw = new_frame()

    py_lines = [
        "$ python",
        ">>> from promptslim import quick_slim",
        ">>> report = quick_slim(my_long_prompt)",
        ">>> print(f\"Saved {report.tokens_saved} tokens!\")",
        "Saved 4 tokens!",
        ">>> print(f\"Cost reduced by {report.savings_pct:.1f}%\")",
        "Cost reduced by 6.3%",
        ">>>",
    ]
    for i, line in enumerate(py_lines):
        if line.startswith("$"):
            draw.text((12, 36 + i * 19), line, fill=GREEN, font=_get_font(14))
        elif line.startswith(">>>"):
            draw.text((12, 36 + i * 19), line, fill=CMD_COLOR, font=_get_font(14))
        elif line.startswith("Saved") or line.startswith("Cost"):
            draw.text((12, 36 + i * 19), line, fill=YELLOW, font=_get_font(14))
        else:
            draw.text((12, 36 + i * 19), line, fill=FG, font=_get_font(14))
    frames.append(img)
    return frames


def scene_compare() -> list[Image.Image]:
    """Scene: compare command"""
    frames = []
    img, draw = new_frame()

    draw_prompt(draw, 12, 36, 'promptslim compare "verbose text here" "concise text here"')

    lines = [
        "",
        "  Text A :  64 tokens  (364 chars)",
        "  Text B :  12 tokens  ( 58 chars)",
        "  ──────────────────────────────────",
        "  Delta  :  52 tokens  (81.3% fewer)",
        "  B uses only 18.8% of A's tokens!",
        "",
        "  Text A is 5.3x more expensive than Text B.",
    ]
    draw_output(draw, 12, 62, lines)
    for i, line in enumerate(lines):
        if "Delta" in line:
            draw.text((12, 62 + i * 19), line, fill=YELLOW, font=_get_font(13))
        elif "fewer" in line:
            draw.text((12, 62 + i * 19), line, fill=GREEN, font=_get_font(13))
    frames.append(img)
    return frames


def scene_summary() -> list[Image.Image]:
    """Scene: summary with key takeaways"""
    frames = []
    img, draw = new_frame()

    draw_prompt(draw, 12, 36, "promptslim --summary  # Demo complete!")

    summary = [
        "",
        "  ╔══════════════════════════════════════╗",
        "  ║     promptslim — Token Cost Killer   ║",
        "  ╠══════════════════════════════════════╣",
        "  ║                                      ║",
        "  ║   pip install promptslim             ║",
        "  ║   github.com/JING04-PRODUCER/promptslim ║",
        "  ║                                      ║",
        "  ║   ✓  Rule-based slim (no API key)   ║",
        "  ║   ✓  LLM-powered smart compression   ║",
        "  ║   ✓  Python API / CLI                ║",
        "  ║   ✓  10-80% token reduction          ║",
        "  ║                                      ║",
        "  ╚══════════════════════════════════════╝",
    ]
    draw_output(draw, 12, 62, summary, color=GREEN, size=13)
    frames.append(img)
    return frames


# ── GIF Assembly ───────────────────────────────────────────
def generate():
    all_frames = []

    # Timing: each scene gets a number of frames based on desired display time
    def add_scene(frames, display_ms=NORMAL):
        """Add frames with proper duration"""
        # Repeat frames to achieve desired display time
        n_copies = max(1, display_ms // FAST)
        for f in frames:
            for _ in range(n_copies):
                all_frames.append(f.copy())

    # Scene 1: Help (0-3s)
    add_scene(scene_help(), 3000)

    # Scene 2: Typing slim command (3-5s)
    add_scene(scene_slim_typing(), 2000)

    # Scene 3: Slim result (5-10s)
    add_scene(scene_slim_result(), 5000)

    # Scene 4: Python API (10-16s)
    add_scene(scene_python_api(), 6000)

    # Scene 5: Compare (16-22s)
    add_scene(scene_compare(), 6000)

    # Scene 6: Summary (22-28s)
    add_scene(scene_summary(), 6000)

    # Save
    if all_frames:
        all_frames[0].save(
            str(OUTPUT),
            save_all=True,
            append_images=all_frames[1:],
            duration=FAST,
            loop=0,
            optimize=False,
            quality=85,
        )
        print(f"Demo GIF saved to: {OUTPUT}")
        print(f"Frames: {len(all_frames)}, Duration: ~{len(all_frames) * FAST / 1000:.0f}s")
    else:
        print("ERROR: No frames generated!")


if __name__ == "__main__":
    generate()

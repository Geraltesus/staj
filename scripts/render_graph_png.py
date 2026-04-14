"""Render the simplified Interview Mentor graph to a PNG file."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1500
CANVAS_HEIGHT = 980
BACKGROUND = (255, 250, 240)
INK = (23, 33, 27)
MUTED = (89, 103, 92)
ACCENT = (224, 93, 47)
SAGE = (87, 116, 91)
PANEL = (245, 230, 200)
TOOL = (219, 233, 209)
LINE = (90, 77, 57)

NODES = {
    "START": (610, 40, 890, 120, "START", "entry"),
    "ask_question": (110, 220, 410, 320, "ask_question", "LLM asks question"),
    "evaluate_answer": (610, 220, 910, 320, "evaluate_answer", "LLM scores answer"),
    "decide_next": (610, 420, 910, 520, "decide_next", "choose route"),
    "run_tool": (110, 610, 410, 710, "run_tool", "local JSON tool"),
    "final_review": (610, 610, 910, 710, "final_review", "LLM final feedback"),
    "respond": (1080, 420, 1380, 520, "respond", "reply for chat/API"),
    "END": (1080, 790, 1380, 870, "END", "done"),
}

EDGES = [
    ("START", "ask_question", "new session"),
    ("START", "evaluate_answer", "answer"),
    ("START", "final_review", "finish"),
    ("ask_question", "respond", "question"),
    ("evaluate_answer", "decide_next", "evaluation"),
    ("decide_next", "ask_question", "next question"),
    ("decide_next", "run_tool", "tool"),
    ("decide_next", "final_review", "finish"),
    ("decide_next", "respond", "clarify"),
    ("run_tool", "respond", "tool reply"),
    ("final_review", "respond", "summary"),
    ("respond", "END", "response"),
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def center(box: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    return (x1 + x2) // 2, (y1 + y2) // 2


def edge_points(source: str, target: str) -> tuple[tuple[int, int], tuple[int, int]]:
    sx1, sy1, sx2, sy2, *_ = NODES[source]
    tx1, ty1, tx2, ty2, *_ = NODES[target]
    scx, scy = center((sx1, sy1, sx2, sy2))
    tcx, tcy = center((tx1, ty1, tx2, ty2))

    if abs(tcx - scx) > abs(tcy - scy):
        return ((sx2, scy) if tcx > scx else (sx1, scy), (tx1, tcy) if tcx > scx else (tx2, tcy))
    return ((scx, sy2) if tcy > scy else (scx, sy1), (tcx, ty1) if tcy > scy else (tcx, ty2))


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], label: str, font: ImageFont.ImageFont) -> None:
    draw.line([start, end], fill=LINE, width=3)
    ex, ey = end
    sx, sy = start
    if abs(ex - sx) > abs(ey - sy):
        direction = 1 if ex > sx else -1
        arrow = [(ex, ey), (ex - 14 * direction, ey - 8), (ex - 14 * direction, ey + 8)]
    else:
        direction = 1 if ey > sy else -1
        arrow = [(ex, ey), (ex - 8, ey - 14 * direction), (ex + 8, ey - 14 * direction)]
    draw.polygon(arrow, fill=LINE)

    lx = (sx + ex) // 2
    ly = (sy + ey) // 2
    bbox = draw.textbbox((0, 0), label, font=font)
    pad = 5
    draw.rounded_rectangle(
        [lx - (bbox[2] - bbox[0]) // 2 - pad, ly - 12, lx + (bbox[2] - bbox[0]) // 2 + pad, ly + 12],
        radius=8,
        fill=BACKGROUND,
        outline=(220, 203, 170),
    )
    draw.text((lx, ly), label, fill=MUTED, font=font, anchor="mm")


def draw_node(draw: ImageDraw.ImageDraw, data: tuple[int, int, int, int, str, str], title_font: ImageFont.ImageFont, subtitle_font: ImageFont.ImageFont) -> None:
    x1, y1, x2, y2, title, subtitle = data
    fill = TOOL if title == "run_tool" else PANEL
    outline = ACCENT if title in {"decide_next", "final_review"} else SAGE
    draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=fill, outline=outline, width=4)
    draw.text(((x1 + x2) // 2, y1 + 35), title, fill=INK, font=title_font, anchor="mm")
    draw.text(((x1 + x2) // 2, y1 + 68), subtitle, fill=MUTED, font=subtitle_font, anchor="mm")


def render(output_path: Path) -> None:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    title_font = load_font(38, bold=True)
    node_font = load_font(24, bold=True)
    subtitle_font = load_font(18)
    edge_font = load_font(14)

    draw.text((70, 55), "Interview Mentor LangGraph", fill=INK, font=title_font)
    draw.text((70, 105), "6 semantic nodes, Ollama llama3.2:1b + local JSON tools", fill=MUTED, font=subtitle_font)

    for source, target, label in EDGES:
        draw_arrow(draw, *edge_points(source, target), label, edge_font)

    for node in NODES.values():
        draw_node(draw, node, node_font, subtitle_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("graph.png")
    render(destination)
    print(f"Graph PNG written to {destination}")

"""Render the Interview Mentor graph to a PNG file.

This is the first local renderer used in the project: it draws a deterministic
PNG without external services such as mermaid.ink and without Node/Mermaid CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1800
CANVAS_HEIGHT = 1350
BACKGROUND = (255, 250, 240)
INK = (23, 33, 27)
MUTED = (89, 103, 92)
ACCENT = (224, 93, 47)
SAGE = (87, 116, 91)
PANEL = (245, 230, 200)
TOOL = (219, 233, 209)
LINE = (90, 77, 57)

NODES = {
    "START": (760, 40, 1040, 120, "START", "entry"),
    "init_interview": (120, 210, 420, 310, "init_interview", "start session"),
    "generate_question": (590, 210, 910, 310, "generate_question", "LLM asks question"),
    "format_output": (1180, 210, 1500, 310, "format_output", "reply for chat/API"),
    "evaluate_answer": (120, 460, 420, 560, "evaluate_answer", "LLM scores answer"),
    "agent_decision": (590, 460, 910, 560, "agent_decision", "LLM chooses route"),
    "adjust_difficulty": (1180, 430, 1500, 530, "adjust_difficulty", "up / keep / down"),
    "save_round": (1180, 650, 1500, 750, "save_round", "append history"),
    "generate_hint": (120, 760, 420, 860, "generate_hint", "local JSON tool"),
    "get_reference_answer": (590, 760, 910, 860, "get_reference_answer", "local JSON tool"),
    "final_review": (1180, 890, 1500, 990, "final_review", "LLM final feedback"),
    "END": (760, 1150, 1040, 1230, "END", "done"),
}

EDGES = [
    ("START", "init_interview", "new session"),
    ("START", "evaluate_answer", "answer"),
    ("START", "save_round", "finish command"),
    ("init_interview", "generate_question", "interview started"),
    ("generate_question", "format_output", "question ready"),
    ("evaluate_answer", "agent_decision", "answer evaluated"),
    ("agent_decision", "adjust_difficulty", "ask_question"),
    ("agent_decision", "format_output", "clarify"),
    ("agent_decision", "generate_hint", "hint"),
    ("agent_decision", "get_reference_answer", "reference"),
    ("agent_decision", "save_round", "finish"),
    ("adjust_difficulty", "save_round", "difficulty changed"),
    ("save_round", "generate_question", "continue"),
    ("save_round", "final_review", "finish"),
    ("generate_hint", "format_output", "hint reply"),
    ("get_reference_answer", "format_output", "reference reply"),
    ("final_review", "format_output", "summary reply"),
    ("format_output", "END", "response returned"),
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
        start = (sx2, scy) if tcx > scx else (sx1, scy)
        end = (tx1, tcy) if tcx > scx else (tx2, tcy)
    else:
        start = (scx, sy2) if tcy > scy else (scx, sy1)
        end = (tcx, ty1) if tcy > scy else (tcx, ty2)
    return start, end


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
    fill = TOOL if "tool" in subtitle else PANEL
    outline = ACCENT if title in {"agent_decision", "final_review"} else SAGE
    draw.rounded_rectangle([x1, y1, x2, y2], radius=24, fill=fill, outline=outline, width=4)
    draw.text(((x1 + x2) // 2, y1 + 35), title, fill=INK, font=title_font, anchor="mm")
    draw.text(((x1 + x2) // 2, y1 + 68), subtitle, fill=MUTED, font=subtitle_font, anchor="mm")


def render(output_path: Path) -> None:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    title_font = load_font(42, bold=True)
    node_font = load_font(24, bold=True)
    subtitle_font = load_font(18)
    edge_font = load_font(14)

    draw.text((80, 55), "Interview Mentor LangGraph", fill=INK, font=title_font)
    draw.text((80, 110), "10 nodes, 18 edges, Ollama llama3.2:1b + local JSON tools", fill=MUTED, font=subtitle_font)

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

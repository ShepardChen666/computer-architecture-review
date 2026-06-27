from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


SOURCE = Path("计算机体系结构期末复习宝典.md")
TARGET = Path("计算机体系结构期末复习宝典.pdf")
FONT = r"C:\Windows\Fonts\simhei.ttf"
PAGE_W, PAGE_H = A4
LEFT = 42
RIGHT = 42
TOP = 42
BOTTOM = 42
MAX_W = PAGE_W - LEFT - RIGHT


def strip_md(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text


def wrap_text(text: str, font: str, size: float, max_width: float) -> list[str]:
    text = strip_md(text).replace("\t", "    ")
    if not text:
        return [""]
    lines: list[str] = []
    current = ""
    for ch in text:
        test = current + ch
        if pdfmetrics.stringWidth(test, font, size) <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


class Writer:
    def __init__(self) -> None:
        pdfmetrics.registerFont(TTFont("SimHei", FONT))
        self.c = canvas.Canvas(str(TARGET), pagesize=A4)
        self.c.setTitle("计算机体系结构期末复习宝典")
        self.page = 1
        self.y = PAGE_H - TOP
        self.in_code = False

    def footer(self) -> None:
        self.c.setFont("SimHei", 8)
        self.c.setFillColor(colors.HexColor("#777777"))
        self.c.drawCentredString(PAGE_W / 2, 22, f"第 {self.page} 页")
        self.c.setFillColor(colors.black)

    def new_page(self) -> None:
        self.footer()
        self.c.showPage()
        self.page += 1
        self.y = PAGE_H - TOP

    def ensure(self, height: float) -> None:
        if self.y - height < BOTTOM:
            self.new_page()

    def draw_wrapped(
        self,
        text: str,
        size: float = 10.5,
        leading: float = 16,
        color=colors.black,
        indent: float = 0,
        before: float = 0,
        after: float = 0,
    ) -> None:
        lines = wrap_text(text, "SimHei", size, MAX_W - indent)
        self.ensure(before + leading * len(lines) + after)
        self.y -= before
        self.c.setFont("SimHei", size)
        self.c.setFillColor(color)
        for line in lines:
            self.c.drawString(LEFT + indent, self.y, line)
            self.y -= leading
        self.c.setFillColor(colors.black)
        self.y -= after

    def draw_code(self, text: str) -> None:
        lines = wrap_text(text, "SimHei", 8.5, MAX_W - 12)
        height = 12 * len(lines) + 8
        self.ensure(height + 4)
        self.c.setFillColor(colors.HexColor("#f5f7fa"))
        self.c.rect(LEFT, self.y - height + 4, MAX_W, height, stroke=0, fill=1)
        self.c.setFillColor(colors.HexColor("#333333"))
        self.c.setFont("SimHei", 8.5)
        y = self.y - 10
        for line in lines:
            self.c.drawString(LEFT + 6, y, line)
            y -= 12
        self.y -= height + 4
        self.c.setFillColor(colors.black)

    def finish(self) -> None:
        self.footer()
        self.c.save()


def build() -> None:
    writer = Writer()
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    code_buffer: list[str] = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            if writer.in_code:
                writer.draw_code("\n".join(code_buffer))
                code_buffer = []
                writer.in_code = False
            else:
                writer.in_code = True
            continue

        if writer.in_code:
            code_buffer.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            writer.y -= 5
            if writer.y < BOTTOM:
                writer.new_page()
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            if level == 1:
                writer.draw_wrapped(text, 20, 28, colors.HexColor("#14345c"), before=4, after=8)
            elif level == 2:
                writer.draw_wrapped(text, 15, 22, colors.HexColor("#1f4e79"), before=10, after=5)
            else:
                writer.draw_wrapped(text, 12.5, 18, colors.HexColor("#315f8f"), before=7, after=3)
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            writer.draw_code(stripped)
            continue

        bullet = re.match(r"^(\d+\.\s+|[-*]\s+)(.*)$", stripped)
        if bullet:
            prefix = bullet.group(1)
            body = bullet.group(2)
            writer.draw_wrapped(prefix + strip_md(body), 10.2, 15, indent=10, after=1)
            continue

        writer.draw_wrapped(stripped, 10.5, 16, after=1)

    if code_buffer:
        writer.draw_code("\n".join(code_buffer))
    writer.finish()


if __name__ == "__main__":
    build()

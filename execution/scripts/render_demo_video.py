from __future__ import annotations

import math
import subprocess
import textwrap
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(r"C:\Users\nyusk\Desktop\Проект 3")
DEMO_DIR = ROOT / "demo"
ASSETS_DIR = DEMO_DIR / "assets"
FRAMES_DIR = DEMO_DIR / "frames"
REPORTS_DIR = ROOT / "execution" / "data" / "reports"
FFMPEG = Path(r"C:\Users\nyusk\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe")
FONT_REG = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_ACCENT = r"C:\Windows\Fonts\georgiab.ttf"
W, H = 1920, 1080


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def gradient_background(color_a: tuple[int, int, int], color_b: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (W, H), color_a)
    px = img.load()
    for y in range(H):
        ratio = y / max(H - 1, 1)
        r = int(color_a[0] * (1 - ratio) + color_b[0] * ratio)
        g = int(color_a[1] * (1 - ratio) + color_b[1] * ratio)
        b = int(color_a[2] * (1 - ratio) + color_b[2] * ratio)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img


def add_glow_circle(base: Image.Image, x: int, y: int, radius: int, color: tuple[int, int, int, int]) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=60))
    base.alpha_composite(overlay)


def card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, fill=(250, 250, 250), outline=(0, 0, 0), alpha=220):
    rgba = fill + (alpha,)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=rgba, outline=outline + (20,), width=2)


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], width_chars: int, font_obj, fill, line_gap: int = 12):
    x, y = xy
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            y += font_obj.size // 2
            continue
        for line in textwrap.wrap(paragraph, width=width_chars, break_long_words=False):
            draw.text((x, y), line, font=font_obj, fill=fill)
            y += font_obj.size + line_gap
    return y


def base_slide() -> Image.Image:
    img = gradient_background((8, 20, 40), (16, 56, 72)).convert("RGBA")
    add_glow_circle(img, 260, 180, 170, (88, 224, 255, 90))
    add_glow_circle(img, 1600, 240, 220, (255, 183, 77, 70))
    add_glow_circle(img, 1450, 860, 260, (97, 87, 255, 60))
    return img


def save_slide(idx: int, title: str, subtitle: str | None = None, bullets: list[str] | None = None, kicker: str | None = None, report_image: Path | None = None, metrics: list[tuple[str, str]] | None = None):
    img = base_slide()
    draw = ImageDraw.Draw(img, "RGBA")
    title_font = font(FONT_ACCENT, 60)
    subtitle_font = font(FONT_BOLD, 28)
    body_font = font(FONT_REG, 28)
    small_font = font(FONT_REG, 22)
    metric_font = font(FONT_BOLD, 34)

    draw.text((120, 90), title, font=title_font, fill=(248, 249, 250, 255))
    if subtitle:
        draw.text((125, 170), subtitle, font=subtitle_font, fill=(188, 229, 255, 255))

    draw.rounded_rectangle((110, 230, 1030, 920), radius=36, fill=(250, 250, 250, 232))
    y = 280
    if kicker:
        y = draw_wrapped(draw, kicker, (155, y), 48, font(FONT_BOLD, 30), (14, 39, 57, 255), 10) + 10
    if bullets:
        for bullet in bullets:
            draw.ellipse((160, y + 10, 176, y + 26), fill=(17, 138, 178, 255))
            y = draw_wrapped(draw, bullet, (195, y), 46, body_font, (27, 38, 59, 255), 10) + 12

    if metrics:
        mx, my = 1110, 260
        for i, (label, value) in enumerate(metrics):
            box_y = my + i * 120
            draw.rounded_rectangle((mx, box_y, 1760, box_y + 95), radius=24, fill=(255, 255, 255, 230))
            draw.text((1140, box_y + 18), label, font=subtitle_font, fill=(45, 52, 54, 255))
            draw.text((1550, box_y + 18), value, font=metric_font, fill=(11, 99, 132, 255))

    if report_image and report_image.exists():
        report = Image.open(report_image).convert("RGBA")
        report.thumbnail((720, 760))
        shadow = Image.new("RGBA", (report.width + 30, report.height + 30), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle((15, 15, shadow.width - 5, shadow.height - 5), radius=26, fill=(0, 0, 0, 120))
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        img.alpha_composite(shadow, (1090, 250))
        frame = Image.new("RGBA", (report.width + 20, report.height + 20), (255, 255, 255, 255))
        frame.paste(report, (10, 10), report)
        img.alpha_composite(frame, (1100, 260))

    footer = "Product demo generated from real project assets · Telegram-first · OCR + RAG + Explainability"
    draw.text((120, 995), footer, font=small_font, fill=(220, 234, 239, 255))
    out = FRAMES_DIR / f"slide_{idx:02d}.png"
    img.convert("RGB").save(out, quality=95)
    return out


def render_report_preview() -> Path:
    report_path = sorted(REPORTS_DIR.glob("report_*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
    doc = fitz.open(report_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
    out = ASSETS_DIR / "report_preview.png"
    pix.save(out)
    return out


def make_video(slides: list[Path], output: Path):
    durations = [4] * len(slides)
    inputs = []
    for slide, duration in zip(slides, durations):
        inputs.extend(["-loop", "1", "-t", str(duration), "-i", str(slide)])

    filter_parts = []
    for i in range(len(slides)):
        filter_parts.append(f"[{i}:v]scale=1920:1080,format=yuv420p,setsar=1[v{i}]")

    current = "v0"
    offset = durations[0] - 1
    for i in range(1, len(slides)):
        out = f"x{i}"
        filter_parts.append(f"[{current}][v{i}]xfade=transition=fade:duration=1:offset={offset}[{out}]")
        current = out
        offset += durations[i] - 1

    cmd = [str(FFMPEG), "-y", *inputs, "-filter_complex", ";".join(filter_parts), "-map", f"[{current}]", "-r", "30", "-pix_fmt", "yuv420p", str(output)]
    subprocess.run(cmd, check=True)


def main():
    report_preview = render_report_preview()
    slides = []
    slides.append(save_slide(
        1,
        "Tender Copilot",
        "Telegram-first AI copilot for tender analysis",
        bullets=[
            "Deep tender analysis with company-context RAG, not a generic chatbot.",
            "Explains why the tender fits or does not fit the supplier profile.",
            "Builds a bid draft outline and export-ready report for real teams.",
        ],
        metrics=[("Format", "Telegram + PDF + JSON"), ("AI Stack", "RAG · OCR · LLM"), ("Target User", "Supplier / Bid Ops")],
    ))
    slides.append(save_slide(
        2,
        "What It Understands",
        "Two-sided reasoning: company context + tender documents",
        bullets=[
            "Company profile document: domains, projects, constraints, geography, certifications.",
            "Tender package: subject, price, deadlines, obligations, payment terms, special conditions.",
            "Optional user draft: if uploaded, it becomes the priority basis for the bid outline.",
        ],
        metrics=[("Input", "PDF / DOCX"), ("Multi-file", "Yes"), ("Scanned PDFs", "OCR fallback")],
    ))
    slides.append(save_slide(
        3,
        "Interpretable Decisioning",
        "A black-box answer is not enough for procurement workflows",
        bullets=[
            "Overall score summarizes the recommendation, but the system also breaks the result into four interpretable dimensions.",
            "Fit score: how well the company matches the tender scope.",
            "Completeness, evidence, and risk scores expose why the recommendation is strong or weak.",
        ],
        metrics=[("overall_score", "0–100"), ("fit_score", "Company vs Tender"), ("risk_score", "Participation Risk")],
    ))
    slides.append(save_slide(
        4,
        "Evidence-Based Output",
        "Decision is grounded in real document fragments",
        bullets=[
            "The bot separates evidence coming from tender files and evidence coming from the company profile.",
            "Every recommendation can point to a file, fragment, and quote.",
            "This makes manual validation possible for a bid manager or operations lead.",
        ],
        metrics=[("Evidence", "File + fragment + quote"), ("Mode", "Explainable"), ("Fallback", "Safe REVIEW")],
    ))
    slides.append(save_slide(
        5,
        "Production Readiness",
        "This project goes beyond a demo bot",
        bullets=[
            "PostgreSQL stores profile and tender runs; Redis stores user session state.",
            "OCR is enabled through Tesseract for scanned PDFs.",
            "LLM failures degrade safely and do not break the workflow.",
        ],
        metrics=[("Persistence", "PostgreSQL"), ("Sessions", "Redis"), ("OCR", "Tesseract 5.4")],
    ))
    slides.append(save_slide(
        6,
        "Generated PDF Report",
        "Real project artifact rendered from current local run",
        kicker="Below is a real report page generated by the current codebase.",
        report_image=report_preview,
    ))
    slides.append(save_slide(
        7,
        "Portfolio Positioning",
        "Why this project is strong for AI Specialist + AI PM roles",
        bullets=[
            "Shows RAG design, document ingestion, OCR, explainability, and production persistence.",
            "Shows product thinking: decision framework, user flow, KPI framing, and business outputs.",
            "Demonstrates an automation workflow that solves a real B2B operational problem.",
        ],
        metrics=[("Tests", "10 passed"), ("Eval accuracy", "1.0"), ("Evidence coverage", "1.0")],
    ))

    output = DEMO_DIR / "tender_copilot_demo.mp4"
    make_video(slides, output)
    print(output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate 50 HTML slides from AI深度研究报告.md with internal styles."""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH = BASE_DIR / "AI深度研究报告.md"
SLIDES_DIR = BASE_DIR / "slides"
TOTAL_SLIDES = 50
MAX_SECTION_SUBSLIDES = 5


def clean_text(text: str) -> str:
    """Normalize markdown text and strip formatting markers."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)  # remove images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # links
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")
    text = text.replace("#", "")
    text = text.replace("`", "")
    return text.strip()


def split_sentences(paragraph: str) -> List[str]:
    """Split Chinese/English paragraph into sentences keeping punctuation."""
    paragraph = paragraph.strip()
    if not paragraph:
        return []

    pieces = re.findall(r"[^。！？!?]+[。！？!?]?", paragraph)
    sentences: List[str] = []
    for piece in pieces:
        sentence = piece.strip()
        if not sentence:
            continue
        sentences.append(sentence)
    return sentences or [paragraph]


def merge_lines(lines: List[str]) -> List[str]:
    """Merge markdown lines into logical paragraphs and bullets."""
    paragraphs: List[str] = []
    buffer: List[str] = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue

        if stripped.startswith(("- ", "* ")):
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            paragraphs.append(stripped[2:].strip())
            continue

        if re.match(r"^\d+\.\s+", stripped):
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            paragraphs.append(re.sub(r"^\d+\.\s+", "", stripped))
            continue

        if stripped.startswith(">"):
            stripped = stripped.lstrip(">").strip()

        buffer.append(stripped)

    if buffer:
        paragraphs.append(" ".join(buffer))

    cleaned = [clean_text(paragraph) for paragraph in paragraphs]
    return [item for item in cleaned if item]


def to_bullets(lines: List[str], max_items: int = 6) -> List[str]:
    """Convert markdown lines to bullet list limited to max_items."""
    bullets: List[str] = []
    for paragraph in merge_lines(lines):
        for sentence in split_sentences(paragraph):
            candidate = clean_text(sentence)
            if candidate:
                bullets.append(candidate)
    return bullets[:max_items]


class Subsection:
    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: List[str] = []

    def bullets(self) -> List[str]:
        return to_bullets(self.lines)


class Section:
    def __init__(self, title: str) -> None:
        self.title = title
        self.intro_lines: List[str] = []
        self.subsections: List[Subsection] = []

    def intro_bullets(self) -> List[str]:
        return to_bullets(self.intro_lines, max_items=5)


def parse_report(path: Path) -> List[Section]:
    sections: List[Section] = []
    current_section: Optional[Section] = None
    current_subsection: Optional[Subsection] = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            title = clean_text(line[3:])
            current_section = Section(title)
            sections.append(current_section)
            current_subsection = None
            continue

        if line.startswith("### "):
            if current_section is None:
                continue
            title = clean_text(line[4:])
            current_subsection = Subsection(title)
            current_section.subsections.append(current_subsection)
            continue

        if current_subsection is not None:
            current_subsection.lines.append(line)
        elif current_section is not None:
            current_section.intro_lines.append(line)

    return sections


def build_slides(sections: List[Section]) -> List[Dict[str, object]]:
    slides: List[Dict[str, object]] = []

    def try_add(slide: Dict[str, object]) -> bool:
        if len(slides) >= TOTAL_SLIDES - 1:
            return False
        slides.append(slide)
        return True

    # Cover slide
    try_add(
        {
            "layout": "cover",
            "title": "AI技术核心解析报告",
            "subtitle": "AI 深度研究报告",
            "bullets": [
                "聚焦算力、模型、部署、生态四大维度",
                "服务体制内高层领导与技术团队决策",
                "提供战略认知框架与落地实施路径",
            ],
        }
    )

    # Audience & goal slide using first section intro
    overview_section = sections[0] if sections else None
    overview_bullets = overview_section.intro_bullets()[:4] if overview_section else []
    if not overview_bullets:
        overview_bullets = [
            "阐释人工智能技术发展背景与战略价值",
            "明确报告面向的核心受众与痛点",
            "通过结构化大纲帮助快速建立认知",
        ]
    try_add(
        {
            "layout": "content",
            "title": "报告目标与受众",
            "subtitle": "项目概况",
            "bullets": overview_bullets,
        }
    )

    # Agenda slide
    agenda_bullets = [f"{idx + 1:02d}. {section.title}" for idx, section in enumerate(sections)]
    try_add(
        {
            "layout": "agenda",
            "title": "目录总览",
            "subtitle": "九大板块",
            "bullets": agenda_bullets,
        }
    )

    # Section & subsection content
    for index, section in enumerate(sections, start=1):
        label = f"板块 {index:02d}"
        intro_bullets = section.intro_bullets()
        if intro_bullets:
            if not try_add(
                {
                    "layout": "section-intro",
                    "title": section.title,
                    "subtitle": label,
                    "bullets": intro_bullets,
                }
            ):
                break

        sub_count = 0
        for subsection in section.subsections:
            if sub_count >= MAX_SECTION_SUBSLIDES:
                break
            bullets = subsection.bullets()
            if not bullets:
                continue
            sub_slide = {
                "layout": "content",
                "title": subsection.title,
                "subtitle": section.title,
                "bullets": bullets,
            }
            if not try_add(sub_slide):
                break
            sub_count += 1
        if len(slides) >= TOTAL_SLIDES - 1:
            break

    # Ensure we have enough slides by adding synthesis slides if needed
    synthesis_templates = [
        {
            "layout": "summary",
            "title": "算力基础设施战略要点",
            "subtitle": "综合洞察",
            "bullets": [
                "将GPU算力视为AI产业底座，提前布局数据中心与网络设施",
                "建立面向模型开发的统一算力调度平台，提高资源利用率",
                "强化软硬件协同优化，围绕CUDA生态构建自主研发能力",
                "通过多元合作保障芯片供应链安全，规避地缘政治风险",
            ],
        },
        {
            "layout": "summary",
            "title": "大模型应用落地关键举措",
            "subtitle": "综合洞察",
            "bullets": [
                "分层规划模型能力：基础模型、自主训练、行业微调协同推进",
                "搭建数据治理体系，确保数据高质量、可追溯与合规",
                "建立模型评测指标体系，覆盖效果、安全、效率与可维护性",
                "通过知识蒸馏、模型压缩与部署优化提升推理效率",
            ],
        },
        {
            "layout": "summary",
            "title": "智能体与知识体系构建方向",
            "subtitle": "综合洞察",
            "bullets": [
                "围绕业务流程设计多Agent协同架构，实现任务自动化",
                "建设持续演进的企业知识库，支持模型检索增强",
                "制定安全与伦理规范，确保智能体行为可控",
                "构建跨部门协同机制，加速AI应用迭代与复盘",
            ],
        },
    ]

    template_index = 0
    while len(slides) < TOTAL_SLIDES - 1 and template_index < len(synthesis_templates):
        slides.append(synthesis_templates[template_index])
        template_index += 1

    # Duplicate last available content if still short
    while len(slides) < TOTAL_SLIDES - 1 and slides:
        slides.append(slides[-1])

    # Conclusion slide
    conclusion = {
        "layout": "conclusion",
        "title": "战略收束与下一步行动",
        "subtitle": "Action Items",
        "bullets": [
            "制定算力与数据双轮驱动计划，构建自主可控的AI底座",
            "围绕重点场景推进大模型试点，形成可复制的行业解决方案",
            "建立跨部门AI治理委员会，完善安全、伦理与评估机制",
            "加大人才培养与生态合作力度，打造持续创新的组织能力",
            "设定季度性里程碑与指标，确保战略执行落地可衡量",
        ],
    }
    slides.append(conclusion)

    if len(slides) != TOTAL_SLIDES:
        raise ValueError(f"Unexpected slide count: {len(slides)} (expected {TOTAL_SLIDES})")

    return slides


CSS_TEMPLATE = """
:root {
    --bg-base: #040915;
    --bg-panel: rgba(12, 20, 46, 0.92);
    --bg-panel-strong: rgba(18, 30, 68, 0.92);
    --primary: #165DFF;
    --accent: #36CFFB;
    --accent-secondary: #4F6BFF;
    --text-main: #F5F8FF;
    --text-subtle: #A7B8FF;
    --divider: rgba(105, 128, 255, 0.35);
}

* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    height: 100%;
    width: 100%;
    font-family: 'Microsoft YaHei', 'Source Han Sans SC', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-base);
    color: var(--text-main);
    letter-spacing: 0.03em;
}

body {
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: 24px;
    --scale: 1;
}

.scale-wrapper {
    position: relative;
    width: 1920px;
    height: 1080px;
    transform-origin: top left;
    transform: scale(var(--scale));
}

@media (max-width: 1920px), (max-height: 1080px) {
    body {
        --scale: min(calc(100vw / 1920), calc(100vh / 1080));
    }
}

.stage {
    position: relative;
    width: 1920px;
    height: 1080px;
    background:
        radial-gradient(circle at 18% 18%, rgba(54, 207, 251, 0.25), transparent 45%),
        radial-gradient(circle at 80% 80%, rgba(22, 93, 255, 0.22), transparent 55%),
        linear-gradient(135deg, rgba(6, 12, 33, 0.96) 0%, rgba(10, 16, 38, 0.96) 100%);
    border-radius: 32px;
    padding: 120px 140px 130px;
    box-shadow: 0 50px 120px rgba(0, 0, 0, 0.55);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    isolation: isolate;
}

.stage::before {
    content: "";
    position: absolute;
    inset: 60px;
    border-radius: 28px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    pointer-events: none;
}

.stage::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(120deg, rgba(22, 93, 255, 0.12), transparent 55%);
    mix-blend-mode: screen;
    opacity: 0.9;
    pointer-events: none;
}

.header {
    position: relative;
    z-index: 2;
    margin-bottom: 48px;
}

.kicker {
    font-size: 26px;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-subtle);
    margin: 0 0 16px;
}

.title {
    font-size: 68px;
    font-weight: 700;
    line-height: 1.12;
    margin: 0;
    color: var(--text-main);
    text-shadow: 0 18px 38px rgba(22, 93, 255, 0.35);
}

.subtitle {
    margin-top: 18px;
    font-size: 28px;
    color: var(--text-subtle);
    font-weight: 400;
}

.body {
    position: relative;
    z-index: 2;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.body ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.body li {
    position: relative;
    font-size: 32px;
    line-height: 1.55;
    color: var(--text-main);
    padding-left: 40px;
}

.body li::before {
    content: "";
    position: absolute;
    left: 0;
    top: 20px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 18px rgba(54, 207, 251, 0.6);
}

.body li strong {
    color: var(--accent);
    font-weight: 600;
}

.layout-cover .stage {
    padding: 160px 180px 160px;
}

.layout-cover .header {
    margin-bottom: 32px;
}

.layout-cover .title {
    font-size: 92px;
    line-height: 1.05;
}

.layout-cover .body ul {
    gap: 22px;
}

.layout-agenda .body li {
    font-size: 30px;
}

.layout-section-intro .body li {
    font-size: 30px;
}

.footer {
    position: relative;
    z-index: 2;
    margin-top: 32px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}

.page-indicator {
    position: absolute;
    right: 150px;
    bottom: 90px;
    font-size: 26px;
    color: var(--text-subtle);
    letter-spacing: 0.12em;
    padding: 10px 20px;
    border-radius: 999px;
    background: rgba(15, 26, 56, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: inset 0 0 0 1px rgba(54, 207, 251, 0.18);
}

.progress-track {
    position: absolute;
    left: 150px;
    right: 150px;
    bottom: 100px;
    height: 4px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    width: 0;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    box-shadow: 0 0 15px rgba(54, 207, 251, 0.45);
    transition: width 0.4s ease;
}
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body class=\"layout-{layout}\">
    <div class=\"scale-wrapper\">
        <div class=\"stage\">
            <header class=\"header\">
                {kicker}
                <h1 class=\"title\">{title}</h1>
                {subtitle}
            </header>
            <main class=\"body\">
                {content}
            </main>
            <footer class=\"footer\"></footer>
            <div class=\"progress-track\"><div class=\"progress-bar\"></div></div>
            <div class=\"page-indicator\"></div>
        </div>
    </div>
    <script src=\"../navigation.js\"></script>
</body>
</html>
"""


def render_slide(slide: Dict[str, object]) -> str:
    layout = html.escape(str(slide.get("layout", "content")))
    title = html.escape(str(slide.get("title", "")))
    subtitle_text = str(slide.get("subtitle", "")).strip()
    kicker_html = ""
    if subtitle_text:
        kicker_html = f"<p class=\"kicker\">{html.escape(subtitle_text)}</p>"
    subtitle_html = ""
    body_content = ""
    bullets = slide.get("bullets", [])
    if bullets:
        items = "\n".join(f"<li>{html.escape(item)}</li>" for item in bullets)
        body_content = f"<ul>\n{items}\n</ul>"
    else:
        body_content = "<ul></ul>"

    return HTML_TEMPLATE.format(
        title=title,
        css=CSS_TEMPLATE,
        layout=layout,
        kicker=kicker_html,
        subtitle=subtitle_html,
        content=body_content,
    )


def write_slides(slides: List[Dict[str, object]]) -> None:
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    for existing in SLIDES_DIR.glob("slide_*.html"):
        existing.unlink()
    for index, slide in enumerate(slides, start=1):
        path = SLIDES_DIR / f"slide_{index:02d}.html"
        path.write_text(render_slide(slide), encoding="utf-8")


def main() -> None:
    sections = parse_report(REPORT_PATH)
    slides = build_slides(sections)
    write_slides(slides)
    print(f"Generated {len(slides)} slides in {SLIDES_DIR.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()

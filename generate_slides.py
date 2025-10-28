import os
import re
from pathlib import Path

def clean_line(text: str) -> str:
    text = text.strip()
    if not text:
        return ''
    # remove markdown emphasis and code markers
    text = text.replace('**', '').replace('`', '').replace('\\*', '')
    # remove markdown links, keep label
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # remove images ![]()
    text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)
    # normalize spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_sentences(paragraph: str) -> list[str]:
    paragraph = paragraph.strip()
    if not paragraph:
        return []
    # handle Chinese punctuation splitting
    parts = re.split(r'(?<=[。！？；])\s*', paragraph)
    sentences = []
    for part in parts:
        part = part.strip()
        if part:
            sentences.append(part)
    if not sentences:
        sentences = [paragraph]
    return sentences


def summarise_lines(lines: list[str], max_points: int = 5) -> list[str]:
    points: list[str] = []
    buffer: list[str] = []
    list_buffer: list[str] = []

    def flush_buffer():
        nonlocal buffer, points
        if not buffer or len(points) >= max_points:
            buffer = []
            return
        joined = ' '.join(buffer).strip()
        buffer = []
        if not joined:
            return
        joined = clean_line(joined)
        for sentence in split_sentences(joined):
            if sentence:
                points.append(sentence)
                if len(points) >= max_points:
                    break

    def flush_list_buffer():
        nonlocal list_buffer, points
        if not list_buffer or len(points) >= max_points:
            list_buffer = []
            return
        combined = '；'.join(item.strip() for item in list_buffer if item.strip())
        list_buffer = []
        combined = clean_line(combined)
        if not combined:
            return
        points.append(combined)

    for raw in lines:
        text = clean_line(raw)
        if not text:
            flush_buffer()
            if len(points) >= max_points:
                break
            continue
        stripped = re.sub(r'^(\*|-|•|·|●|○)\s+', '', text)
        stripped = re.sub(r'^\d+[\.、]\s*', '', stripped)
        stripped = re.sub(r'^[（(][\d一二三四五六七八九十]+[)）]\s*', '', stripped)
        is_list_item = text != stripped
        if is_list_item:
            flush_buffer()
            if len(points) >= max_points:
                break
            if stripped:
                list_buffer.append(stripped)
            continue
        flush_list_buffer()
        buffer.append(text)
    if len(points) < max_points:
        flush_buffer()
    if len(points) < max_points:
        flush_list_buffer()

    changed = True
    while changed:
        changed = False
        merged_points = []
        skip_next = False
        for idx, point in enumerate(points):
            if skip_next:
                skip_next = False
                continue
            if (point.endswith('：') or point.endswith(':')) and idx + 1 < len(points):
                merged_points.append(point + points[idx + 1])
                skip_next = True
                changed = True
            else:
                merged_points.append(point)
        points = merged_points

    # ensure points are unique and reasonably short
    cleaned_points = []
    seen = set()
    for point in points:
        point = point.strip('。；;')
        point = point.strip()
        if not point or point in seen:
            continue
        if len(point) > 90:
            if re.search(r'[，、；,;]', point):
                fragments = [frag.strip() for frag in re.split(r'[，、；,;]', point) if frag.strip()]
                merged = []
                current = ''
                for frag in fragments:
                    candidate = f"{current}、{frag}" if current else frag
                    if len(candidate) <= 90:
                        current = candidate
                    else:
                        if current:
                            merged.append(current)
                        current = frag
                if current:
                    merged.append(current)
                for frag in merged:
                    if len(cleaned_points) >= max_points:
                        break
                    if frag and frag not in seen:
                        cleaned_points.append(frag)
                        seen.add(frag)
                if len(cleaned_points) >= max_points:
                    break
                continue
        cleaned_points.append(point)
        seen.add(point)
        if len(cleaned_points) >= max_points:
            break
    return cleaned_points


def parse_markdown(md_path: Path):
    lines = md_path.read_text(encoding='utf-8').splitlines()
    slides = []
    current_section = None
    section_intro_lines: list[str] = []
    current_slide = None

    def flush_intro():
        nonlocal section_intro_lines, current_section
        if section_intro_lines:
            slides.append({
                'kind': 'section_intro',
                'section': current_section,
                'title': current_section if current_section else '概述',
                'lines': section_intro_lines.copy()
            })
            section_intro_lines = []

    def flush_current_slide():
        nonlocal current_slide
        if current_slide is not None:
            slides.append(current_slide)
            current_slide = None

    for line in lines:
        if line.startswith('## '):
            flush_current_slide()
            flush_intro()
            current_section = line[3:].strip()
            section_intro_lines = []
        elif line.startswith('### '):
            flush_current_slide()
            flush_intro()
            current_slide = {
                'kind': 'subsection',
                'section': current_section,
                'title': line[4:].strip(),
                'lines': []
            }
        else:
            if current_slide is not None:
                current_slide['lines'].append(line)
            else:
                section_intro_lines.append(line)
    flush_current_slide()
    flush_intro()
    return slides


def build_slide_data(md_path: Path):
    parsed = parse_markdown(md_path)
    slides = []

    # cover slide
    slides.append({
        'kind': 'cover',
        'section': 'AI 技术核心解析',
        'title': 'AI 技术核心解析报告',
        'subtitle': '面向体制内高层的战略级技术洞察',
        'points': [
            '全景梳理算力、算法、生态的核心逻辑',
            '聚焦英伟达、算力卡与大模型的协同演进',
            '支撑决策层制定 AI 战略与投资布局'
        ]
    })

    for item in parsed:
        points = summarise_lines(item.get('lines', []), max_points=5)
        if not points:
            continue
        chunk_size = 5
        base_title = item.get('title') or ''
        section_name = item.get('section') or 'AI 技术核心解析'
        for chunk_index, start in enumerate(range(0, len(points), chunk_size)):
            chunk = points[start:start + chunk_size]
            if not chunk:
                continue
            if chunk_index == 0:
                title = base_title
            elif chunk_index == 1:
                title = f"{base_title}（续）"
            else:
                title = f"{base_title}（续{chunk_index}）"
            slides.append({
                'kind': 'standard',
                'section': section_name,
                'title': title,
                'points': chunk
            })
    return slides


def render_slide(index: int, total: int, data: dict) -> str:
    section = data.get('section', '') or ''
    title = data.get('title', '') or ''
    subtitle = data.get('subtitle', '')
    points = data.get('points', [])
    classes = ['slide']
    if data['kind'] == 'cover':
        classes.append('cover')
    class_attr = ' '.join(classes)

    points_html = ''
    if points:
        points_items = '\n'.join(f'                <li>{p}</li>' for p in points)
        points_html = f"            <div class=\"content\">\n                <ul>\n{points_items}\n                </ul>\n            </div>\n"

    subtitle_html = ''
    if subtitle:
        subtitle_html = f"            <p class=\"slide-subtitle\">{subtitle}</p>\n"

    badge_html = ''
    if section:
        badge_html = f"            <div class=\"badge\">{section}</div>\n"

    template = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>AI 技术核心解析报告 - 幻灯片 {index:02}</title>
    <style>
        :root {{ color-scheme: light; }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at 20% 20%, #16213E 0%, #0F172A 45%, #020617 100%);
            font-family: 'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Source Han Sans SC', sans-serif;
            color: #1D2939;
        }}
        .slide {{
            width: 1280px;
            height: 720px;
            background: #FFFFFF;
            border-radius: 32px;
            position: relative;
            padding: 96px 112px 120px 112px;
            box-shadow: 0 32px 120px rgba(15, 23, 42, 0.45);
            overflow: hidden;
        }}
        .slide.cover {{
            background: linear-gradient(140deg, #165DFF 0%, #36CFFB 55%, #5AD7F7 100%);
            color: #FFFFFF;
        }}
        .slide.cover .badge {{
            background: rgba(255, 255, 255, 0.18);
            color: #FFFFFF;
        }}
        .slide.cover .slide-title {{
            color: #FFFFFF;
            font-size: 64px;
        }}
        .slide.cover .slide-subtitle {{
            color: rgba(255, 255, 255, 0.85);
            font-size: 28px;
        }}
        .slide.cover .content ul li {{
            color: rgba(255, 255, 255, 0.9);
        }}
        .badge {{
            position: absolute;
            top: 36px;
            left: 48px;
            padding: 6px 18px;
            border-radius: 999px;
            background: rgba(22, 93, 255, 0.12);
            color: #165DFF;
            font-size: 18px;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        .slide-title {{
            margin: 0;
            font-size: 46px;
            line-height: 1.2;
            color: #101828;
            font-weight: 700;
            letter-spacing: 0.01em;
        }}
        .slide-subtitle {{
            margin: 18px 0 48px 0;
            font-size: 24px;
            line-height: 1.6;
            color: #475467;
            max-width: 780px;
        }}
        .content {{
            font-size: 24px;
            line-height: 1.6;
            color: #1D2939;
        }}
        .content ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .content li {{
            margin-bottom: 20px;
            position: relative;
            padding-left: 28px;
        }}
        .content li::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 12px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #165DFF;
            box-shadow: 0 0 0 5px rgba(22, 93, 255, 0.2);
        }}
        .slide.cover .content li::before {{
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 0 0 5px rgba(255, 255, 255, 0.2);
        }}
        .nav-hint {{
            position: absolute;
            bottom: 40px;
            left: 56px;
            font-size: 18px;
            color: #98A2B3;
            letter-spacing: 0.02em;
        }}
        .slide.cover .nav-hint {{
            color: rgba(255, 255, 255, 0.7);
        }}
        .page-number {{
            position: absolute;
            bottom: 40px;
            right: 56px;
            font-size: 20px;
            color: #98A2B3;
            font-weight: 500;
            letter-spacing: 0.04em;
        }}
        .slide.cover .page-number {{
            color: rgba(255, 255, 255, 0.75);
        }}
    </style>
</head>
<body>
    <div class=\"{class_attr}\" data-slide=\"{index}\">
{badge_html}            <h1 class=\"slide-title\">{title}</h1>
{subtitle_html}{points_html}            <div class=\"nav-hint\">使用 ← → 键切换</div>
            <div class=\"page-number\"></div>
    </div>
    <script src=\"navigation.js\"></script>
</body>
</html>"""
    return template


def main():
    base_dir = Path(__file__).resolve().parent
    slides_dir = base_dir / 'slides'
    slides_dir.mkdir(exist_ok=True)

    for html_file in slides_dir.glob('slide-*.html'):
        html_file.unlink()

    md_path = base_dir / 'AI深度研究报告.md'
    slide_data = build_slide_data(md_path)
    total = len(slide_data)

    for idx, data in enumerate(slide_data, start=1):
        file_name = slides_dir / f'slide-{idx:02}.html'
        html = render_slide(idx, total, data)
        file_name.write_text(html, encoding='utf-8')

    nav_path = slides_dir / 'navigation.js'
    nav_code = f"""(function() {{
    const TOTAL_SLIDES = {total};

    function getCurrentSlideIndex() {{
        const match = window.location.pathname.match(/slide-(\\d+)\\.html$/);
        if (!match) return 1;
        return parseInt(match[1], 10);
    }}

    function goToSlide(index) {{
        if (index < 1 || index > TOTAL_SLIDES) return;
        const target = `slide-${{String(index).padStart(2, '0')}}.html`;
        window.location.href = target;
    }}

    document.addEventListener('keydown', (event) => {{
        if (event.key === 'ArrowRight') {{
            const current = getCurrentSlideIndex();
            if (current < TOTAL_SLIDES) {{
                goToSlide(current + 1);
            }}
        }} else if (event.key === 'ArrowLeft') {{
            const current = getCurrentSlideIndex();
            if (current > 1) {{
                goToSlide(current - 1);
            }}
        }}
    }});

    document.addEventListener('DOMContentLoaded', () => {{
        const current = getCurrentSlideIndex();
        const indicator = document.querySelector('.page-number');
        if (indicator) {{
            indicator.textContent = `幻灯片 ${{current}} / ${{TOTAL_SLIDES}}`;
        }}
    }});
}})();
"""
    nav_path.write_text(nav_code, encoding='utf-8')

if __name__ == '__main__':
    main()

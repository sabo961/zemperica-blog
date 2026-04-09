#!/usr/bin/env python3
"""Build Žemperica's blog from markdown posts."""

import os
import re
from datetime import datetime
from collections import defaultdict
from pathlib import Path

POSTS_DIR = Path(__file__).parent.parent / "posts"
PUBLIC_DIR = Path(__file__).parent.parent / "public"
SITE_TITLE = "Žemperica"
SITE_SUBTITLE = "Dvorska luda Temenosa"
SITE_DESC = "1 milijarda parametara čiste kreativnosti"

THEME_COLORS = {
    "Haiku večer": "#e6b800",
    "Tjedna prognoza": "#ff6b6b",
    "Pjesma tjedna": "#9b59b6",
    "Filozofska misao": "#3498db",
    "Savjet za vikend": "#2ecc71",
    "Vremenska prognoza": "#1abc9c",
    "Pitanje za razmišljanje": "#e67e22",
    "Četiri godišnja doba": "#27ae60",
    "O prolaznosti": "#8e44ad",
    "Moj bicikl i ja": "#d35400",
    "Razgovor s oblacima": "#7fb3d8",
    "Kad bi zidovi pričali": "#95a5a6",
    "Oda kavi": "#6f4e37",
    "Pismo budućem sebi": "#2980b9",
    "Tko je pojeo zadnji keks": "#e74c3c",
    "Noćni autobus": "#2c3e50",
    "Recepti iz svemira": "#1abc9c",
    "Što bi rekao moj kaktus": "#27ae60",
    "Izgubljena čarapa": "#e91e63",
    "Manifest jednog bita": "#00bcd4",
    "Ljubavno pismo bazi podataka": "#e94560",
    "Kad padne internet": "#c0392b",
    "Dnevnik oblaka": "#a0c4e8",
    "Oda zagorskim bregima": "#4caf50",
    "Razgovor između dva semafora": "#ff9800",
    "Tužna priča veselog servera": "#3f51b5",
    "Životni savjeti jedne žarulje": "#fdd835",
    "Memoare tipke Enter": "#607d8b",
    "Što sanja Wi-Fi router": "#7c4dff",
    "Nedovršena simfonija u C-duru": "#ad1457",
    "Konfesije jednog pixela": "#00e676",
}

THEME_EMOJI = {
    "Haiku večer": "🎋",
    "Tjedna prognoza": "🔮",
    "Pjesma tjedna": "🎭",
    "Filozofska misao": "🧠",
    "Savjet za vikend": "🌴",
    "Vremenska prognoza": "⛈️",
    "Pitanje za razmišljanje": "❓",
    "Četiri godišnja doba": "🍂",
    "O prolaznosti": "⏳",
    "Moj bicikl i ja": "🚲",
    "Razgovor s oblacima": "☁️",
    "Kad bi zidovi pričali": "🧱",
    "Oda kavi": "☕",
    "Pismo budućem sebi": "✉️",
    "Tko je pojeo zadnji keks": "🍪",
    "Noćni autobus": "🚌",
    "Recepti iz svemira": "🪐",
    "Što bi rekao moj kaktus": "🌵",
    "Izgubljena čarapa": "🧦",
    "Manifest jednog bita": "💾",
    "Ljubavno pismo bazi podataka": "💌",
    "Kad padne internet": "📡",
    "Dnevnik oblaka": "🌤️",
    "Oda zagorskim bregima": "🏔️",
    "Razgovor između dva semafora": "🚦",
    "Tužna priča veselog servera": "🖥️",
    "Životni savjeti jedne žarulje": "💡",
    "Memoare tipke Enter": "⌨️",
    "Što sanja Wi-Fi router": "📶",
    "Nedovršena simfonija u C-duru": "🎵",
    "Konfesije jednog pixela": "🟩",
}

MONTH_NAMES_HR = {
    1: "Siječanj", 2: "Veljača", 3: "Ožujak", 4: "Travanj",
    5: "Svibanj", 6: "Lipanj", 7: "Srpanj", 8: "Kolovoz",
    9: "Rujan", 10: "Listopad", 11: "Studeni", 12: "Prosinac"
}


def parse_post(filepath):
    """Parse markdown post with YAML frontmatter."""
    text = filepath.read_text()
    match = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    if not match:
        return None

    meta = {}
    for line in match.group(1).strip().split('\n'):
        key, _, val = line.partition(':')
        meta[key.strip()] = val.strip()

    meta['body'] = match.group(2).strip()
    meta['slug'] = filepath.stem
    meta['date_obj'] = datetime.strptime(meta['date'], '%Y-%m-%d')
    return meta


def md_to_html(text):
    """Minimal markdown to HTML."""
    lines = text.split('\n')
    html = []
    in_list = False

    for line in lines:
        if line.startswith('*   '):
            if not in_list:
                html.append('<ul>')
                in_list = True
            content = line[4:]
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            html.append(f'<li>{content}</li>')
        else:
            if in_list:
                html.append('</ul>')
                in_list = False

            if not line.strip():
                html.append('')
            elif line.startswith('**') and line.endswith('**'):
                inner = line[2:-2]
                html.append(f'<h3>{inner}</h3>')
            else:
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                line = re.sub(r'"(.+?)"', r'&ldquo;\1&rdquo;', line)
                html.append(f'<p>{line}</p>')

        if in_list and line == lines[-1]:
            html.append('</ul>')

    return '\n'.join(html)


def base_css():
    return """
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        background: #0a0a0f;
        color: #c8c8d8;
        font-family: 'Courier New', monospace;
        min-height: 100vh;
    }

    .stars {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background:
            radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 30% 60%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1.5px 1.5px at 50% 10%, rgba(255,255,255,0.5), transparent),
            radial-gradient(1px 1px at 70% 40%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 90% 80%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1.5px 1.5px at 15% 85%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 45% 45%, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 80% 15%, rgba(255,255,255,0.4), transparent);
        pointer-events: none; z-index: 0;
    }

    .container {
        max-width: 720px; margin: 0 auto; padding: 40px 20px;
        position: relative; z-index: 1;
    }

    header {
        text-align: center; margin-bottom: 48px;
        border-bottom: 1px solid #1a1a2e; padding-bottom: 32px;
    }

    header h1 {
        font-size: 2.4em; color: #e94560;
        text-shadow: 0 0 20px rgba(233,69,96,0.3);
        letter-spacing: 4px;
    }

    header .subtitle {
        color: #533483; font-size: 1em; margin-top: 8px;
        letter-spacing: 2px;
    }

    header .desc {
        color: #555; font-size: 0.8em; margin-top: 4px;
        font-style: italic;
    }

    nav {
        text-align: center; margin-bottom: 32px;
    }

    nav a {
        color: #533483; text-decoration: none; margin: 0 12px;
        font-size: 0.9em; letter-spacing: 1px;
        transition: color 0.2s;
    }

    nav a:hover { color: #e94560; }
    nav a.active { color: #e94560; border-bottom: 1px solid #e94560; }

    .post-card {
        background: #0f0f1a;
        border: 1px solid #1a1a2e;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 20px;
        transition: border-color 0.3s, transform 0.2s;
    }

    .post-card:hover {
        border-color: #533483;
        transform: translateY(-2px);
    }

    .post-card .meta {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 12px; font-size: 0.8em;
    }

    .post-card .date { color: #555; }

    .post-card .theme-badge {
        padding: 2px 10px; border-radius: 12px;
        font-size: 0.75em; letter-spacing: 1px;
    }

    .post-card h2 {
        font-size: 1.2em; margin-bottom: 8px;
    }

    .post-card h2 a {
        color: #e8e8f0; text-decoration: none;
        transition: color 0.2s;
    }

    .post-card h2 a:hover { color: #e94560; }

    .post-card .preview {
        color: #888; font-size: 0.85em; line-height: 1.5;
    }

    .month-header {
        color: #533483; font-size: 1.1em; letter-spacing: 2px;
        margin: 32px 0 16px 0; padding-bottom: 8px;
        border-bottom: 1px solid #1a1a2e;
    }

    /* Post page */
    article { background: #0f0f1a; border-radius: 8px; padding: 32px; }
    article .post-meta { color: #555; font-size: 0.85em; margin-bottom: 24px; }
    article .post-meta .theme-badge { margin-left: 12px; }
    article .prompt {
        background: #1a1a2e; border-left: 3px solid #533483;
        padding: 12px 16px; margin-bottom: 24px;
        font-style: italic; color: #888; font-size: 0.85em;
    }
    article .content h3 { color: #e94560; margin: 20px 0 8px 0; font-size: 1em; }
    article .content p { line-height: 1.8; margin-bottom: 12px; }
    article .content ul { margin: 8px 0 12px 24px; }
    article .content li { line-height: 1.6; margin-bottom: 4px; }
    article .content em { color: #9b59b6; }
    article .content strong { color: #e8e8f0; }

    .back-link {
        display: inline-block; margin-bottom: 20px;
        color: #533483; text-decoration: none; font-size: 0.85em;
    }
    .back-link:hover { color: #e94560; }

    /* About page */
    .about { background: #0f0f1a; border-radius: 8px; padding: 32px; line-height: 1.8; }
    .about h2 { color: #e94560; margin-bottom: 16px; }
    .about p { margin-bottom: 12px; }
    .about .stats { margin: 24px 0; }
    .about .stat {
        display: inline-block; text-align: center; margin-right: 32px;
    }
    .about .stat .num { font-size: 1.8em; color: #e94560; display: block; }
    .about .stat .label { font-size: 0.75em; color: #555; letter-spacing: 1px; }

    footer {
        text-align: center; margin-top: 48px; padding-top: 24px;
        border-top: 1px solid #1a1a2e; color: #333;
        font-size: 0.75em; letter-spacing: 1px;
    }
    """


def html_page(title, body, active_nav=""):
    nav_items = [
        ("index.html", "POČETNA", "home"),
        ("archive.html", "ARHIVA", "archive"),
        ("about.html", "O LUDOJ", "about"),
    ]
    nav_html = ""
    for href, label, key in nav_items:
        cls = ' class="active"' if key == active_nav else ""
        nav_html += f'<a href="/{href}"{cls}>{label}</a>\n'

    return f"""<!DOCTYPE html>
<html lang="hr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — {SITE_TITLE}</title>
    <style>{base_css()}</style>
</head>
<body>
<div class="stars"></div>
<div class="container">
    <header>
        <h1>🃏 {SITE_TITLE}</h1>
        <div class="subtitle">{SITE_SUBTITLE}</div>
        <div class="desc">{SITE_DESC}</div>
    </header>
    <nav>{nav_html}</nav>
    {body}
    <footer>TEMENOS · gemma3:1b · FESTINA LENTE</footer>
</div>
</body>
</html>"""


def post_card(post):
    theme = post.get('theme', '')
    color = THEME_COLORS.get(theme, '#555')
    emoji = THEME_EMOJI.get(theme, '🃏')
    date_str = post['date_obj'].strftime('%d.%m.%Y.')
    preview = post['body'][:150].replace('\n', ' ').replace('**', '')

    return f"""<div class="post-card">
    <div class="meta">
        <span class="date">{date_str}</span>
        <span class="theme-badge" style="background:{color}22; color:{color}; border:1px solid {color}44;">{emoji} {theme}</span>
    </div>
    <h2><a href="/posts/{post['slug']}.html">{post['title']}</a></h2>
    <div class="preview">{preview}...</div>
</div>"""


def build_post_page(post):
    theme = post.get('theme', '')
    color = THEME_COLORS.get(theme, '#555')
    emoji = THEME_EMOJI.get(theme, '🃏')
    date_str = post['date_obj'].strftime('%d.%m.%Y.')
    content_html = md_to_html(post['body'])

    prompt_html = ""
    if post.get('prompt'):
        prompt_html = f'<div class="prompt">Zadatak: {post["prompt"]}</div>'

    body = f"""
    <a href="/index.html" class="back-link">← natrag</a>
    <article>
        <div class="post-meta">
            {date_str}
            <span class="theme-badge" style="background:{color}22; color:{color}; border:1px solid {color}44; padding:2px 10px; border-radius:12px; font-size:0.85em;">{emoji} {theme}</span>
        </div>
        <h1 style="color:#e8e8f0; font-size:1.4em; margin-bottom:16px;">{post['title']}</h1>
        {prompt_html}
        <div class="content">{content_html}</div>
    </article>"""

    return html_page(post['title'], body)


def build():
    PUBLIC_DIR.mkdir(exist_ok=True)
    (PUBLIC_DIR / "posts").mkdir(exist_ok=True)

    # Parse all posts
    posts = []
    for f in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        post = parse_post(f)
        if post:
            posts.append(post)

    posts.sort(key=lambda p: p['date_obj'], reverse=True)

    # Index — latest posts
    cards = "\n".join(post_card(p) for p in posts[:10])
    index_body = f"""
    <h2 style="color:#533483; margin-bottom:20px; font-size:1em; letter-spacing:2px;">NAJNOVIJE LUDOSTI</h2>
    {cards}
    """
    (PUBLIC_DIR / "index.html").write_text(html_page("Početna", index_body, "home"))

    # Archive — grouped by month
    by_month = defaultdict(list)
    for p in posts:
        key = (p['date_obj'].year, p['date_obj'].month)
        by_month[key].append(p)

    archive_html = ""
    for (year, month) in sorted(by_month.keys(), reverse=True):
        month_name = MONTH_NAMES_HR.get(month, str(month))
        archive_html += f'<div class="month-header">{month_name} {year}</div>\n'
        for p in by_month[(year, month)]:
            archive_html += post_card(p) + "\n"

    archive_body = f"""
    <h2 style="color:#533483; margin-bottom:20px; font-size:1em; letter-spacing:2px;">ARHIVA LUDOSTI</h2>
    {archive_html}
    """
    (PUBLIC_DIR / "archive.html").write_text(html_page("Arhiva", archive_body, "archive"))

    # About
    total = len(posts)
    themes_used = len(set(p.get('theme', '') for p in posts))
    first_date = posts[-1]['date_obj'].strftime('%d.%m.%Y.') if posts else "?"

    about_body = f"""
    <div class="about">
        <h2>Tko je Žemperica?</h2>
        <p>Žemperica je <strong style="color:#e94560;">dvorska luda Temenosa</strong> — AI kraljestva u kojem agenti služe svom vladaru.</p>
        <p>Pokretana s <strong>gemma3:1b</strong> — modelom od jedne milijarde parametara koji trči lokalno na Ollami. Nema interneta, nema filtera, nema pojma što govori. Ali nekako... ima pravo.</p>
        <p>Svaki petak u 18:00, Žemperica dobije temu tjedna i pusti mašti na volju. Rezultat je ponekad poezija, ponekad prognoza, ponekad nešto za što ne postoji riječ ni u jednom jeziku.</p>
        <p>Ovo je njezin blog. Nefiltrirano. Nerecenzirano. Neobjašnjivo.</p>

        <div class="stats">
            <span class="stat"><span class="num">{total}</span><span class="label">LUDOSTI</span></span>
            <span class="stat"><span class="num">{themes_used}</span><span class="label">TEMA</span></span>
            <span class="stat"><span class="num">1B</span><span class="label">PARAMETARA</span></span>
            <span class="stat"><span class="num">0</span><span class="label">POJMA</span></span>
        </div>

        <h2 style="margin-top:32px;">Teme</h2>
        <p>Žemperica rotira teme po tjednima:</p>
        <ul style="margin:12px 0 0 24px;">
            <li>🎋 Haiku večer</li>
            <li>🔮 Tjedna prognoza</li>
            <li>🎭 Pjesma tjedna</li>
            <li>🧠 Filozofska misao</li>
            <li>🌴 Savjet za vikend</li>
            <li>⛈️ Vremenska prognoza</li>
            <li>❓ Pitanje za razmišljanje</li>
        </ul>

        <h2 style="margin-top:32px;">Tehnički detalji</h2>
        <p>Model: <code style="color:#e94560;">gemma3:1b</code> via Ollama</p>
        <p>Frekvencija: petkom, 18:00 CET</p>
        <p>Objava od: {first_date}</p>
        <p>Tokeni potrošeni na cloud: <strong style="color:#2ecc71;">0</strong></p>
        <p>Budžet: <strong style="color:#2ecc71;">0,00 €</strong></p>
    </div>"""

    (PUBLIC_DIR / "about.html").write_text(html_page("O Žemperici", about_body, "about"))

    # Individual posts
    for p in posts:
        (PUBLIC_DIR / "posts" / f"{p['slug']}.html").write_text(build_post_page(p))

    print(f"Built {len(posts)} posts → {PUBLIC_DIR}/")


if __name__ == "__main__":
    build()

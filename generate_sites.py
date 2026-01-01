import csv
import html
import json
import os
import re
from pathlib import Path
from typing import Dict, List

DATA_FILE = Path("Plumbing Google Maps_KH.csv")
OUTPUT_DIR = Path("docs")
ASSETS_DIR = OUTPUT_DIR / "assets"
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://example.com/plumbing")


def slugify(name: str, index: int, seen: set) -> str:
    base = re.sub(r"[^\w]+", "-", name).strip("-")
    base = re.sub(r"-+", "-", base)
    ascii_base = base.encode("ascii", "ignore").decode()
    ascii_base = ascii_base.strip("-")
    if not ascii_base or not re.search(r"[a-zA-Z0-9]", ascii_base):
        ascii_base = f"store-{index + 1}"
    candidate = ascii_base.lower()
    suffix = 1
    while candidate in seen:
        suffix += 1
        candidate = f"{ascii_base.lower()}-{suffix}"
    seen.add(candidate)
    return candidate


def load_stores() -> List[Dict[str, str]]:
    stores: List[Dict[str, str]] = []
    with DATA_FILE.open(encoding="big5") as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            stores.append({k: (v or "").strip() for k, v in row.items()})
    return stores


def ensure_output_dirs() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def build_page_head(title: str, description: str, url: str, keywords: List[str]) -> str:
    keywords_str = ", ".join(filter(None, keywords))
    head_parts = [
        "    <meta charset=\"utf-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        f"    <title>{html.escape(title)}</title>",
        f"    <meta name=\"description\" content=\"{html.escape(description)}\">",
    ]
    if keywords_str:
        head_parts.append(f"    <meta name=\"keywords\" content=\"{html.escape(keywords_str)}\">")
    if url:
        head_parts.extend([
            f"    <link rel=\"canonical\" href=\"{html.escape(url)}\">",
            f"    <meta property=\"og:url\" content=\"{html.escape(url)}\">",
        ])
    head_parts.extend([
        f"    <meta property=\"og:title\" content=\"{html.escape(title)}\">",
        f"    <meta property=\"og:description\" content=\"{html.escape(description)}\">",
        "    <meta property=\"og:type\" content=\"website\">",
        "    <meta property=\"og:locale\" content=\"zh_TW\">",
        "    <meta property=\"og:site_name\" content=\"高雄水電行專頁\">",
        "    <meta name=\"twitter:card\" content=\"summary\">",
        "    <link rel=\"stylesheet\" href=\"assets/style.css\">",
    ])
    return "\n".join(head_parts)


def render_index(stores: List[Dict[str, str]]) -> str:
    title = "高雄水電行目錄"
    description = "為高雄市水電行打造的獨立網站集合，包含地址、電話與營業資訊。"
    url = f"{SITE_BASE_URL.rstrip('/')}/"
    head = build_page_head(title, description, url, ["高雄水電行", "水電師傅", "水電維修", "電機服務"])
    cards = []
    for store in stores:
        cards.append(
            f"      <article class=\"card\">\n"
            f"        <h2><a href=\"{store['slug']}.html\">{html.escape(store['店家名稱'])}</a></h2>\n"
            f"        <p class=\"type\">{html.escape(store['店家類型'])}</p>\n"
            f"        <p>評分：{html.escape(store['評分'] or '尚無評價')}</p>\n"
            f"        <p>地址：{html.escape(store['地址'])}</p>\n"
            f"        <p>電話：<a href=\"tel:{html.escape(store['電話']).replace(' ', '')}\">{html.escape(store['電話'])}</a></p>\n"
            f"        <p>營業資訊：{html.escape(store['打烊時間'])}</p>\n"
            "      </article>"
        )
    cards_html = "\n".join(cards)
    return f"""<!doctype html>
<html lang=\"zh-Hant\">
  <head>
{head}
  </head>
  <body>
    <header class=\"hero\">
      <div class=\"container\">
        <p class=\"eyebrow\">高雄專區</p>
        <h1>{html.escape(title)}</h1>
        <p>{html.escape(description)}</p>
      </div>
    </header>
    <main class=\"container\">
      <section class=\"grid\">
{cards_html}
      </section>
    </main>
    <footer class=\"footer\">
      <div class=\"container\">
        <p>本頁面為高雄市水電行索引。歡迎來電預約，優先找到離您最近的水電師傅。</p>
      </div>
    </footer>
  </body>
</html>
"""


def render_store_page(store: Dict[str, str]) -> str:
    title = f"{store['店家名稱']}｜高雄水電行"
    description = f"{store['店家名稱']} 提供 {store['店家類型']} 服務，位於 {store['地址']}，電話 {store['電話']}，營業資訊：{store['打烊時間']}。"
    url = f"{SITE_BASE_URL.rstrip('/')}/{store['slug']}.html"
    keywords = [store["店家名稱"], "高雄水電", store["店家類型"], store["地址"].split("號")[0]]
    head = build_page_head(title, description, url, keywords)

    services = [s for s in [store.get("實體和線上"), store.get("其他服務")] if s]
    website_section = ""
    if store.get("網站"):
        website_section = (
            "      <p>官方網站：" f"<a href=\"{html.escape(store['網站'])}\" rel=\"noopener noreferrer\">{html.escape(store['網站'])}</a></p>\n"
        )

    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": url,
        "name": store["店家名稱"],
        "description": description,
        "address": store.get("地址"),
        "telephone": store.get("電話"),
        "url": url,
        "sameAs": [store.get("Google 地圖連結")],
    }
    if store.get("評分"):
        try:
            rating = float(store["評分"])
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": rating,
                "reviewCount": max(1, int(rating)),
            }
        except ValueError:
            pass
    if services:
        schema["knowsAbout"] = services

    services_html = ""
    if services:
        services_html = (
            "      <h3>服務特色</h3>\n" + "\n".join(f"      <p>• {html.escape(service)}</p>" for service in services)
        )

    return f"""<!doctype html>
<html lang=\"zh-Hant\">
  <head>
{head}
    <script type=\"application/ld+json\">{json.dumps(schema, ensure_ascii=False)}</script>
  </head>
  <body>
    <header class=\"hero\">
      <div class=\"container\">
        <p class=\"eyebrow\">高雄水電行</p>
        <h1>{html.escape(store['店家名稱'])}</h1>
        <p class=\"type\">{html.escape(store['店家類型'])}</p>
      </div>
    </header>
    <main class=\"container\">
      <section class=\"content\">
        <p class=\"highlight\">評分：{html.escape(store['評分'] or '尚無評價')}</p>
        <p>地址：{html.escape(store['地址'])}</p>
        <p>電話：<a href=\"tel:{html.escape(store['電話']).replace(' ', '')}\">{html.escape(store['電話'])}</a></p>
        <p>營業資訊：{html.escape(store['打烊時間'])}</p>
        <p>Google 地圖：<a href=\"{html.escape(store['Google 地圖連結'])}\" rel=\"noopener noreferrer\">查看路線</a></p>
{website_section}        {services_html if services_html else ''}
        <p><a class=\"back\" href=\"index.html\">← 回到所有水電行</a></p>
      </section>
    </main>
    <footer class=\"footer\">
      <div class=\"container\">
        <p>本頁面收錄高雄水電行資訊，協助您快速找到合適的師傅。</p>
      </div>
    </footer>
  </body>
</html>
"""


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def build_sitemap(slugs: List[str]) -> str:
    base = SITE_BASE_URL.rstrip("/")
    urls = [f"  <url>\n    <loc>{base}/</loc>\n  </url>"]
    urls.extend(
        f"  <url>\n    <loc>{base}/{html.escape(slug)}.html</loc>\n  </url>" for slug in slugs
    )
    return "\n".join(
        ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">", *urls, "</urlset>"]
    )


def main() -> None:
    ensure_output_dirs()
    stores = load_stores()
    slug_seen: set = set()
    for idx, store in enumerate(stores):
        store_slug = slugify(store["店家名稱"], idx, slug_seen)
        store["slug"] = store_slug
    index_html = render_index(stores)
    write_file(OUTPUT_DIR / "index.html", index_html)

    for store in stores:
        page_html = render_store_page(store)
        write_file(OUTPUT_DIR / f"{store['slug']}.html", page_html)

    sitemap = build_sitemap([store["slug"] for store in stores])
    write_file(OUTPUT_DIR / "sitemap.xml", sitemap)
    write_file(OUTPUT_DIR / "robots.txt", "Sitemap: {base}/sitemap.xml\n".format(base=SITE_BASE_URL.rstrip("/")))

    style = """:root {
  color-scheme: light;
  --bg: #f7f7f7;
  --text: #1c1c1e;
  --muted: #4b5563;
  --accent: #0ea5e9;
  --card: #ffffff;
  --border: #e5e7eb;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}
.container {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 1.25rem 2rem;
}
.hero {
  background: linear-gradient(135deg, #0ea5e9, #22d3ee);
  color: white;
  padding: 2.5rem 0 2rem;
}
.hero h1 { margin: 0.2rem 0 0.4rem; }
.eyebrow {
  letter-spacing: 0.1em;
  font-size: 0.85rem;
  text-transform: uppercase;
  opacity: 0.9;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.2rem;
  box-shadow: 0 6px 18px rgba(0,0,0,0.06);
}
.card h2 {
  margin-top: 0;
  margin-bottom: 0.35rem;
}
.card .type { color: var(--muted); margin: 0 0 0.4rem; }
.card a { color: var(--accent); text-decoration: none; }
.card a:hover { text-decoration: underline; }
.content {
  background: var(--card);
  border-radius: 12px;
  border: 1px solid var(--border);
  margin-top: -2rem;
  padding: 1.5rem;
  box-shadow: 0 10px 24px rgba(0,0,0,0.08);
}
.highlight {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #ecfeff;
  color: #0ea5e9;
  border-radius: 999px;
  font-weight: 600;
}
.footer {
  background: #0f172a;
  color: #e5e7eb;
  padding: 1.5rem 0;
  margin-top: 2rem;
}
.footer a { color: #e0f2fe; }
.back { display: inline-block; margin-top: 1rem; color: var(--accent); }
a { word-break: break-all; }
@media (max-width: 640px) {
  .hero { padding: 2rem 0 1.5rem; }
  .content { margin-top: -1.5rem; }
}
"""
    write_file(ASSETS_DIR / "style.css", style)


if __name__ == "__main__":
    main()

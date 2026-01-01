"""Generate static plumbing business pages for GitHub Pages."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import sys
from typing import Iterable, List, MutableSet, Sequence

DEFAULT_BASE_URL = "https://example.github.io/plumbing"


def slugify(name: str, existing: MutableSet[str]) -> str:
    """Create a filesystem-friendly slug while keeping CJK characters."""
    base = re.sub(r"\s+", "-", name.strip())
    base = re.sub(r"[^\w\-一-龥]", "", base)
    base = base.lower() or "store"
    if len(base) > 80:
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
        base = f"{base[:60]}-{digest}"
    slug = base
    counter = 2
    while slug in existing:
        slug = f"{base}-{counter}"
        counter += 1
    existing.add(slug)
    return slug


def load_stores(csv_path: pathlib.Path) -> List[dict]:
    seen: set[str] = set()
    stores: List[dict] = []

    with csv_path.open(encoding="cp950") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            name = (row.get("店家名稱") or "").strip()
            if not name:
                continue

            slug = slugify(name, seen)
            store = {
                "slug": slug,
                "name": name,
                "map_url": (row.get("Google 地圖連結") or "").strip(),
                "rating": (row.get("評分") or "").strip(),
                "category": (row.get("店家類型") or "").strip(),
                "address": (row.get("地址") or "").strip(),
                "closing": (row.get("打烊時間") or "").strip("· ").strip(),
                "phone": (row.get("電話") or "").strip(),
                "cta": (row.get("R8c4Qb") or "").strip(),
                "services": [
                    text.strip()
                    for text in (
                        row.get("實體和線上") or "",
                        row.get("其他服務") or "",
                    )
                    if text.strip()
                ],
                "website": (row.get("網站") or "").strip(),
            }
            stores.append(store)

    return stores


def meta_description(store: dict) -> str:
    parts = [
        store["name"],
        store.get("category"),
        store.get("address"),
        f"電話：{store['phone']}" if store.get("phone") else "",
        f"評分：{store['rating']}" if store.get("rating") else "",
    ]
    joined = "｜".join(filter(None, parts))
    return f"{joined}．高雄水電行線上資訊與服務"


def keyword_list(store: dict) -> str:
    keywords = [
        store["name"],
        store.get("category", ""),
        "水電行",
        "高雄水電",
        "水電維修",
        "水電工程",
        store.get("address", ""),
    ]
    return ",".join(filter(None, keywords))


def structured_data(store: dict, page_url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Plumber",
        "name": store["name"],
        "url": page_url,
        "address": store.get("address") or None,
        "telephone": store.get("phone") or None,
        "priceRange": "視工程報價",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": store.get("rating") or None,
            "reviewCount": 1,
        },
        "areaServed": "高雄市",
        "sameAs": [url for url in (store.get("website"), store.get("map_url")) if url],
    }
    # Remove empty fields
    cleaned = {k: v for k, v in data.items() if v not in ("", None, [], {})}
    if "aggregateRating" in cleaned and cleaned["aggregateRating"]["ratingValue"] is None:
        cleaned.pop("aggregateRating")
    return json.dumps(cleaned, ensure_ascii=False, indent=2)


def render_index(stores: Sequence[dict], base_url: str, out_dir: pathlib.Path) -> None:
    items_markup = "\n".join(
        f"""
        <article class="card">
          <header>
            <p class="eyebrow">{html.escape(store.get("category") or "水電行")}</p>
            <h2><a href="{html.escape(store['slug'])}.html">{html.escape(store['name'])}</a></h2>
          </header>
          <p class="address">{html.escape(store.get("address") or "地址未提供")}</p>
          <p class="meta">評分 {html.escape(store.get("rating") or "N/A")} · 電話 {html.escape(store.get("phone") or "未提供")}</p>
          <div class="actions">
            <a class="button" href="{html.escape(store.get('map_url') or '#')}" rel="noopener" target="_blank">查看地圖</a>
            <a class="link" href="{html.escape(store['slug'])}.html">查看店家頁面</a>
          </div>
        </article>
        """
        for store in stores
    )

    item_list_schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "高雄水電行列表",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": store["name"],
                "url": f"{base_url}/{store['slug']}.html",
            }
            for index, store in enumerate(stores)
        ],
    }

    html_content = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>高雄水電行 | GitHub Pages 靜態網站</title>
  <meta name="description" content="高雄水電行列表，包含地址、電話與地圖連結，支援 GitHub Pages 展示。">
  <meta name="keywords" content="高雄,水電行,水電維修,水電工程,GitHub Pages">
  <meta property="og:title" content="高雄水電行">
  <meta property="og:description" content="透過 GitHub Pages 快速瀏覽高雄水電行資訊。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{base_url}/">
  <link rel="canonical" href="{base_url}/">
  <link rel="sitemap" type="application/xml" title="Sitemap" href="{base_url}/sitemap.xml">
  <script type="application/ld+json">
{json.dumps(item_list_schema, ensure_ascii=False, indent=2)}
  </script>
  <style>
    :root {{
      --bg: #0f172a;
      --card: #0b1224;
      --accent: #0ea5e9;
      --text: #e2e8f0;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at 20% 20%, rgba(14,165,233,0.15), transparent 25%), var(--bg);
      color: var(--text);
    }}
    header.hero {{
      padding: 48px 16px 24px;
      max-width: 960px;
      margin: 0 auto;
      text-align: center;
    }}
    header.hero h1 {{ margin: 0 0 12px; font-size: 2rem; letter-spacing: 0.5px; }}
    header.hero p {{ margin: 0; color: var(--muted); }}
    main {{ max-width: 960px; margin: 0 auto; padding: 8px 16px 48px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--card);
      padding: 16px;
      border: 1px solid rgba(255,255,255,0.05);
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.35);
    }}
    .card h2 {{ margin: 4px 0 8px; font-size: 1.25rem; }}
    .card a {{ color: var(--text); text-decoration: none; }}
    .card a:hover {{ color: var(--accent); }}
    .eyebrow {{ color: var(--muted); font-size: 0.85rem; margin: 0; letter-spacing: 0.5px; }}
    .address {{ margin: 0 0 4px; color: var(--text); }}
    .meta {{ margin: 0 0 12px; color: var(--muted); font-size: 0.95rem; }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .button {{
      background: linear-gradient(135deg, var(--accent), #38bdf8);
      color: #0f172a;
      padding: 8px 12px;
      border-radius: 8px;
      font-weight: 600;
      border: none;
    }}
    .button:hover {{ opacity: 0.95; }}
    .link {{ color: var(--accent); font-weight: 600; }}
    footer {{ text-align: center; color: var(--muted); padding: 16px; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <header class="hero">
    <p class="eyebrow">GitHub Pages 靜態網站</p>
    <h1>高雄水電行彙整</h1>
    <p>瀏覽水電行的地址、電話、營業資訊，並可點擊前往個別 SEO 友善的店家頁面。</p>
  </header>
  <main>
    <section class="grid">
      {items_markup}
    </section>
  </main>
  <footer>資料來源：Google 地圖 · 產生時間：{dt.date.today().isoformat()}</footer>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_content, encoding="utf-8")


def render_detail(store: dict, base_url: str, out_dir: pathlib.Path) -> None:
    page_url = f"{base_url}/{store['slug']}.html"
    meta_desc = meta_description(store)
    keywords = keyword_list(store)
    services_markup = (
        "".join(f"<li>{html.escape(service)}</li>" for service in store.get("services") or [])
        or "<li>歡迎來電洽詢服務內容</li>"
    )
    cta_label = store.get("cta") or "查看位置"
    map_cta = (
        f'<a class="button" href="{html.escape(store.get("map_url") or "#")}" target="_blank" rel="noopener">{html.escape(cta_label)}</a>'
        if store.get("map_url")
        else ""
    )
    website_link = (
        f'<a class="link" href="{html.escape(store["website"])}" target="_blank" rel="noopener">官方網站</a>'
        if store.get("website")
        else ""
    )

    html_content = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(store['name'])} | 高雄水電行</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <meta name="keywords" content="{html.escape(keywords)}">
  <meta property="og:title" content="{html.escape(store['name'])} | 高雄水電行">
  <meta property="og:description" content="{html.escape(meta_desc)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{page_url}">
  <link rel="canonical" href="{page_url}">
  <link rel="sitemap" type="application/xml" title="Sitemap" href="{base_url}/sitemap.xml">
  <script type="application/ld+json">
{structured_data(store, page_url)}
  </script>
  <style>
    :root {{
      --bg: #0f172a;
      --card: #0b1224;
      --accent: #0ea5e9;
      --text: #e2e8f0;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}
    .layout {{ max-width: 840px; margin: 0 auto; padding: 24px 16px 48px; }}
    nav a {{ color: var(--muted); text-decoration: none; }}
    nav a:hover {{ color: var(--accent); }}
    header.hero {{ padding: 16px 0 12px; }}
    header.hero h1 {{ margin: 4px 0; font-size: 2rem; }}
    header.hero p {{ margin: 4px 0; color: var(--muted); }}
    .card {{
      background: var(--card);
      padding: 16px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.05);
      box-shadow: 0 10px 40px rgba(0,0,0,0.35);
      margin-top: 16px;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }}
    .label {{ color: var(--muted); font-size: 0.95rem; margin: 0 0 4px; letter-spacing: 0.25px; }}
    .value {{ margin: 0; font-size: 1.05rem; }}
    .actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }}
    .button {{
      background: linear-gradient(135deg, var(--accent), #38bdf8);
      color: #0f172a;
      padding: 10px 14px;
      border-radius: 10px;
      font-weight: 700;
      border: none;
      text-decoration: none;
    }}
    .link {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
    .link:hover {{ text-decoration: underline; }}
    ul {{ padding-left: 18px; margin: 6px 0; color: var(--text); }}
    footer {{ color: var(--muted); margin-top: 16px; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="layout">
    <nav><a href="index.html">← 回到店家列表</a></nav>
    <header class="hero">
      <p class="label">{html.escape(store.get("category") or "水電行")}</p>
      <h1>{html.escape(store["name"])}</h1>
      <p>{html.escape(store.get("address") or "地址未提供")}</p>
    </header>
    <section class="card grid">
      <div>
        <p class="label">電話</p>
        <p class="value">{html.escape(store.get("phone") or "未提供")}</p>
      </div>
      <div>
        <p class="label">評分</p>
        <p class="value">{html.escape(store.get("rating") or "尚無評分")}</p>
      </div>
      <div>
        <p class="label">營業狀態</p>
        <p class="value">{html.escape(store.get("closing") or "請來電確認營業時間")}</p>
      </div>
    </section>
    <section class="card">
      <p class="label">提供服務</p>
      <ul>
        {services_markup}
      </ul>
      <div class="actions">
        {map_cta}
        {website_link}
        <a class="link" href="{html.escape(store.get("map_url") or "#")}" target="_blank" rel="noopener">檢視 Google 地圖</a>
      </div>
    </section>
    <footer>此頁面為 GitHub Pages 自動產生，提供 {html.escape(store['name'])} 的基本聯絡資訊與 SEO 友善標記。</footer>
  </div>
</body>
</html>
"""
    (out_dir / f"{store['slug']}.html").write_text(html_content, encoding="utf-8")


def generate_sitemap(stores: Sequence[dict], base_url: str, out_dir: pathlib.Path) -> None:
    today = dt.date.today().isoformat()
    urlset = "\n".join(
        f"""  <url>
    <loc>{base_url}/{html.escape(store['slug'])}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>"""
        for store in stores
    )
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
{urlset}
</urlset>
"""
    (out_dir / "sitemap.xml").write_text(content, encoding="utf-8")


def generate_robots(base_url: str, out_dir: pathlib.Path) -> None:
    content = f"""User-agent: *
Allow: /
Sitemap: {base_url}/sitemap.xml
"""
    (out_dir / "robots.txt").write_text(content, encoding="utf-8")


def generate_pages(csv_path: pathlib.Path, output_dir: pathlib.Path, base_url: str) -> None:
    stores = load_stores(csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    render_index(stores, base_url, output_dir)
    for store in stores:
        render_detail(store, base_url, output_dir)
    generate_sitemap(stores, base_url, output_dir)
    generate_robots(base_url, output_dir)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate plumbing storefront pages.")
    parser.add_argument(
        "--csv-path",
        default="Plumbing Google Maps_KH.csv",
        type=pathlib.Path,
        help="Path to the CSV exported from Google Maps (Big5 encoded).",
    )
    parser.add_argument(
        "--output-dir",
        default=pathlib.Path("docs"),
        type=pathlib.Path,
        help="Directory to write the static pages (GitHub Pages uses docs/ by default).",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Canonical base URL for SEO tags and sitemap (e.g., https://<user>.github.io/plumbing).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    base_url = args.base_url.rstrip("/")
    generate_pages(args.csv_path, args.output_dir, base_url)


if __name__ == "__main__":
    main()

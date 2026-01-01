from __future__ import annotations

import argparse
import csv
import html
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class Shop:
    name: str
    rating: str
    category: str
    address: str
    closing_time: str
    phone: str
    directions_label: str
    physical_online: str
    extra_services: str
    website: str
    map_url: str
    slug: str

    @property
    def structured_rating(self) -> Optional[float]:
        try:
            return float(self.rating)
        except (TypeError, ValueError):
            return None

    @property
    def description(self) -> str:
        parts = [p for p in [self.category, self.address, self.closing_time] if p]
        if not parts:
            return "水電行資訊"
        return " · ".join(parts)


def slugify(name: str, fallback_index: int, existing: set[str]) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(
        c for c in normalized if c.isascii() and (c.isalnum() or c in {" ", "-"})
    )
    ascii_name = re.sub(r"\s+", "-", ascii_name).strip("-").lower()

    if not ascii_name:
        ascii_name = f"shop-{fallback_index}"

    slug = ascii_name or f"shop-{fallback_index}"
    if len(slug) > 80:
        slug = slug[:80]
    counter = 1
    base_slug = slug or f"shop-{fallback_index}"
    slug = base_slug
    while slug in existing or not slug:
        counter += 1
        slug = f"{base_slug}-{counter}"
        if len(slug) > 90:
            slug = slug[:90]
    existing.add(slug)
    return slug


def read_shops(csv_path: Path) -> List[Shop]:
    content = csv_path.read_bytes()
    text = content.decode("cp950")
    reader = csv.DictReader(text.splitlines())
    shops: List[Shop] = []
    existing_slugs: set[str] = set()

    for idx, row in enumerate(reader, start=1):
        slug = slugify(row.get("店家名稱", ""), idx, existing_slugs)
        shop = Shop(
            name=row.get("店家名稱", "").strip(),
            rating=row.get("評分", "").strip(),
            category=row.get("店家類型", "").strip(),
            address=row.get("地址", "").strip(),
            closing_time=row.get("打烊時間", "").strip(),
            phone=row.get("電話", "").strip(),
            directions_label=row.get("R8c4Qb", "").strip() or "規劃路線",
            physical_online=row.get("實體和線上", "").strip(),
            extra_services=row.get("其他服務", "").strip(),
            website=row.get("網站", "").strip(),
            map_url=row.get("Google 地圖連結", "").strip(),
            slug=slug,
        )
        shops.append(shop)
    return shops


def build_base_url(base_url: str) -> str:
    if not base_url.endswith("/"):
        return base_url + "/"
    return base_url


def render_index(shops: List[Shop], base_url: str) -> str:
    list_items = "\n".join(
        f"""
        <article class=\"card\">
            <header>
                <p class=\"eyebrow\">{html.escape(shop.category or '水電行')}</p>
                <h2><a href=\"{shop.slug}.html\">{html.escape(shop.name)}</a></h2>
                <p class=\"rating\">評分：{html.escape(shop.rating or '—')}</p>
            </header>
            <p class=\"meta\">{html.escape(shop.address)}</p>
            <p class=\"meta\">{html.escape(shop.closing_time or '營業時間請來電確認')}</p>
            <div class=\"actions\">
                <a class=\"button primary\" href=\"{shop.slug}.html\">查看資訊</a>
                <a class=\"button\" href=\"{html.escape(shop.map_url)}\" rel=\"noopener\" target=\"_blank\">{html.escape(shop.directions_label)}</a>
            </div>
        </article>
        """
        for shop in shops
    )

    ld_json = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "高雄水電行清單",
        "description": "高雄地區水電行、施工服務商與水電材料行彙整，附地址、電話與營業資訊。",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": idx + 1,
                "name": shop.name,
                "url": f"{base_url}{shop.slug}.html",
            }
            for idx, shop in enumerate(shops)
        ],
    }

    return f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>高雄水電行清單 | Plumbing Directory</title>
    <meta name=\"description\" content=\"高雄地區水電行與水電工程行目錄，提供地址、電話、營業時間與地圖連結。\" />
    <link rel=\"canonical\" href=\"{base_url}\" />
    <link rel=\"stylesheet\" href=\"assets/styles.css\" />
    <script type=\"application/ld+json\">{json.dumps(ld_json, ensure_ascii=False)}</script>
</head>
<body>
    <header class=\"site-header\">
        <div class=\"container\">
            <p class=\"eyebrow\">Kaohsiung Plumbing & Electrical</p>
            <h1>高雄水電行獨立網站專區</h1>
            <p class=\"lead\">每一家水電行都有自己的簡介頁面，方便快速找到聯絡方式與地圖導航。</p>
        </div>
    </header>
    <main class=\"container\">
        <section class=\"grid\" aria-label=\"水電行清單\">
            {list_items}
        </section>
    </main>
    <footer class=\"site-footer\">
        <div class=\"container\">
            <p>資料來源：Plumbing Google Maps_KH.csv。請於 GitHub Pages 部署後更新 canonical 網址以提升 SEO。</p>
        </div>
    </footer>
</body>
</html>"""


def render_shop_page(shop: Shop, base_url: str) -> str:
    canonical_url = f"{base_url}{shop.slug}.html"
    ld_json: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": shop.name,
        "address": shop.address,
        "telephone": shop.phone,
        "url": canonical_url,
        "image": shop.map_url,
        "department": shop.category,
        "sameAs": [link for link in [shop.map_url, shop.website] if link],
    }
    if shop.structured_rating is not None:
        ld_json["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": shop.structured_rating,
            "reviewCount": 1,
        }

    description = shop.description

    return f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{html.escape(shop.name)} | 高雄水電行</title>
    <meta name=\"description\" content=\"{html.escape(description)}\" />
    <link rel=\"canonical\" href=\"{canonical_url}\" />
    <link rel=\"stylesheet\" href=\"assets/styles.css\" />
    <meta property=\"og:title\" content=\"{html.escape(shop.name)}\" />
    <meta property=\"og:description\" content=\"{html.escape(description)}\" />
    <meta property=\"og:type\" content=\"website\" />
    <meta property=\"og:url\" content=\"{canonical_url}\" />
    <script type=\"application/ld+json\">{json.dumps(ld_json, ensure_ascii=False)}</script>
</head>
<body>
    <header class=\"site-header\">
        <div class=\"container\">
            <p class=\"eyebrow\">Kaohsiung Plumbing & Electrical</p>
            <h1>{html.escape(shop.name)}</h1>
            <p class=\"lead\">{html.escape(description)}</p>
            <div class=\"breadcrumb\"><a href=\"index.html\">← 返回清單</a></div>
        </div>
    </header>
    <main class=\"container\">
        <section class=\"detail\">
            <dl>
                <div>
                    <dt>店家類型</dt>
                    <dd>{html.escape(shop.category or '水電行')}</dd>
                </div>
                <div>
                    <dt>評分</dt>
                    <dd>{html.escape(shop.rating or '暫無評分')}</dd>
                </div>
                <div>
                    <dt>地址</dt>
                    <dd>{html.escape(shop.address or '未提供')}</dd>
                </div>
                <div>
                    <dt>營業時間</dt>
                    <dd>{html.escape(shop.closing_time or '請電話確認')}</dd>
                </div>
                <div>
                    <dt>電話</dt>
                    <dd><a href=\"tel:{html.escape(shop.phone.replace(' ', ''))}\">{html.escape(shop.phone or '未提供')}</a></dd>
                </div>
                <div>
                    <dt>服務</dt>
                    <dd>{html.escape(shop.extra_services or shop.physical_online or '請洽詢店家')}</dd>
                </div>
                <div>
                    <dt>地圖</dt>
                    <dd><a class=\"button\" href=\"{html.escape(shop.map_url)}\" rel=\"noopener\" target=\"_blank\">{html.escape(shop.directions_label)}</a></dd>
                </div>
                <div>
                    <dt>網站</dt>
                    <dd>{f'<a href="{html.escape(shop.website)}" rel="noopener" target="_blank">官方網站</a>' if shop.website else '尚無網站資訊'}</dd>
                </div>
            </dl>
        </section>
    </main>
    <footer class=\"site-footer\">
        <div class=\"container\">
            <p>想要修改資訊？請更新 CSV 後重新執行產生腳本。</p>
        </div>
    </footer>
</body>
</html>"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_sitemap(shops: Iterable[Shop], base_url: str) -> str:
    updated = datetime.utcnow().date().isoformat()
    urls = [
        {
            "loc": base_url,
            "lastmod": updated,
        }
    ]
    for shop in shops:
        urls.append({"loc": f"{base_url}{shop.slug}.html", "lastmod": updated})

    urlset = "\n".join(
        f"    <url><loc>{html.escape(u['loc'])}</loc><lastmod>{u['lastmod']}</lastmod></url>"
        for u in urls
    )
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
{urlset}
</urlset>
"""


def render_robots_txt(base_url: str) -> str:
    return f"""User-agent: *
Allow: /
Sitemap: {base_url}sitemap.xml
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static sites for plumbing shops.")
    parser.add_argument("--source", default="Plumbing Google Maps_KH.csv", help="Path to CSV source (cp950)")
    parser.add_argument("--output", default="docs", help="Output directory for GitHub Pages")
    parser.add_argument("--base-url", default="https://<github-username>.github.io/plumbing/", help="Canonical base URL for SEO")
    args = parser.parse_args()

    output_dir = Path(args.output)
    csv_path = Path(args.source)
    base_url = build_base_url(args.base_url)

    shops = read_shops(csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_file(output_dir / "index.html", render_index(shops, base_url))
    for shop in shops:
        write_file(output_dir / f"{shop.slug}.html", render_shop_page(shop, base_url))

    write_file(output_dir / "sitemap.xml", render_sitemap(shops, base_url))
    write_file(output_dir / "robots.txt", render_robots_txt(base_url))

    print(f"Generated {len(shops)} shop pages into {output_dir.resolve()}")


if __name__ == "__main__":
    main()

import csv
import html
import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("Plumbing Google Maps_KH.csv")
OUTPUT_DIR = Path("docs")
STORES_DIR = OUTPUT_DIR / "stores"
ASSETS_DIR = OUTPUT_DIR / "assets"

DEFAULT_BASE_URL = "https://<your-github-username>.github.io/plumbing/"
ENCODING = "cp950"


def slugify(name: str, existing: set[str]) -> str:
    normalized = unicodedata.normalize("NFKC", name).strip()
    candidate = re.sub(r"[\s・／/、]+", "-", normalized)
    candidate = re.sub(r"[^\w一-龥-]", "", candidate)
    candidate = re.sub(r"-+", "-", candidate).strip("-") or "store"
    # Keep slugs file-system friendly
    candidate = candidate[:80]

    slug = candidate
    suffix = 1
    while slug in existing:
        suffix += 1
        slug = f"{candidate}-{suffix}"
    existing.add(slug)
    return slug


def load_rows() -> list[dict[str, str]]:
    with DATA_FILE.open(encoding=ENCODING, newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def ensure_dirs():
    STORES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def build_meta_description(store: dict[str, str]) -> str:
    pieces = [store.get("店家名稱", "").strip()]
    if store.get("評分"):
        pieces.append(f"評分 {store['評分']}")
    if store.get("店家類型"):
        pieces.append(store["店家類型"].strip())
    if store.get("地址"):
        pieces.append(store["地址"].strip())
    if store.get("電話"):
        pieces.append(f"電話 {store['電話'].strip()}")
    return " · ".join(p for p in pieces if p)


def seo_head(title: str, description: str, url: str, asset_prefix: str, extra_meta: str = "") -> str:
    escaped_title = html.escape(title)
    escaped_description = html.escape(description)
    escaped_url = html.escape(url)
    css_path = f"{asset_prefix}style.css"
    return f"""
    <meta charset=\"utf-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n    <title>{escaped_title}</title>\n    <meta name=\"description\" content=\"{escaped_description}\">\n    <meta property=\"og:title\" content=\"{escaped_title}\">\n    <meta property=\"og:description\" content=\"{escaped_description}\">\n    <meta property=\"og:type\" content=\"website\">\n    <meta property=\"og:url\" content=\"{escaped_url}\">\n    <link rel=\"canonical\" href=\"{escaped_url}\">\n    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">\n    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>\n    <link href=\"https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700&display=swap\" rel=\"stylesheet\">\n    <link rel=\"stylesheet\" href=\"{css_path}\">\n    {extra_meta}\n    """


def render_store_page(store: dict[str, str], slug: str, base_url: str) -> str:
    title = f"{store['店家名稱']}｜高雄水電行"
    description = build_meta_description(store)
    url = f"{base_url.rstrip('/')}/stores/{slug}.html"
    structured_data = {
        "@context": "https://schema.org",
        "@type": "Store",
        "name": store.get("店家名稱"),
        "url": url,
        "image": store.get("Google 地圖連結", ""),
        "address": store.get("地址"),
        "telephone": store.get("電話") or None,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": store.get("評分") or None,
            "reviewCount": store.get("評分") and 1 or None,
        },
        "sameAs": [value for value in [store.get("網站"), store.get("Google 地圖連結")] if value],
    }
    json_ld = json.dumps(structured_data, ensure_ascii=False, indent=2)

    def render_item(label: str, value: str) -> str:
        if not value:
            return ""
        display = html.escape(value)
        if isinstance(value, str) and value.startswith("http"):
            display = f'<a href="{html.escape(value)}" target="_blank" rel="noopener">{display}</a>'
        return f'<div class="detail-row"><span class="label">{html.escape(label)}</span><span>{display}</span></div>'

    website_link = store.get("網站") or store.get("Google 地圖連結")
    services = [v for v in [store.get("實體和線上"), store.get("其他服務")] if v]
    services_html = "".join(
        f"<span class=\"chip\">{html.escape(s)}</span>" for s in services
    ) or "<span class=\"chip muted\">尚未提供服務資訊</span>"

    return f"""
<!doctype html>
<html lang=\"zh-Hant\">
<head>
{seo_head(title, description, url, asset_prefix='../assets/', extra_meta=f'<script type="application/ld+json">{json_ld}</script>')}
</head>
<body>
<header class=\"site-header\">
  <div class=\"container\">
    <a href=\"../index.html\" class=\"logo\">高雄水電行導覽</a>
    <nav><a href=\"../index.html#list\">全部店家</a><a href=\"../index.html#faq\">常見問題</a></nav>
  </div>
</header>
<main class=\"container\">
  <section class=\"hero\">
    <p class=\"eyebrow\">高雄在地水電服務</p>
    <h1>{html.escape(store['店家名稱'])}</h1>
    <p class=\"lede\">{html.escape(description)}</p>
    <div class=\"cta-group\">
      <a class=\"button primary\" href=\"{html.escape(store.get('Google 地圖連結', '#'))}\" target=\"_blank\" rel=\"noopener\">查看地圖</a>
      <a class=\"button secondary\" href=\"../index.html\">返回店家列表</a>
    </div>
  </section>

  <section class=\"card-grid\">
    <div class=\"card\">
      <h2>基本資料</h2>
      {render_item('店家類型', store.get('店家類型', ''))}
      {render_item('評分', store.get('評分', ''))}
      {render_item('地址', store.get('地址', ''))}
      {render_item('打烊時間', store.get('打烊時間', ''))}
      {render_item('電話', store.get('電話', ''))}
    </div>
    <div class=\"card\">
      <h2>服務特色</h2>
      <div class=\"chips\">{services_html}</div>
      {render_item('網站', website_link)}
      {render_item('Google 地圖', store.get('Google 地圖連結', ''))}
    </div>
  </section>

  <section id=\"faq\" class=\"faq\">
    <div>
      <h2>快速問答</h2>
      <details open>
        <summary>如何聯絡 {html.escape(store['店家名稱'])}？</summary>
        <p>可撥打 {html.escape(store.get('電話', '')) or '店家未提供電話'}，或透過 Google 地圖頁面洽詢。</p>
      </details>
      <details>
        <summary>有提供哪些服務？</summary>
        <p>{'、'.join(html.escape(s) for s in services) if services else '尚未提供服務資訊'}</p>
      </details>
      <details>
        <summary>是否支援線上預約？</summary>
        <p>若店家提供「線上估價服務」或「門市服務」標記，即可事先詢價或預約。</p>
      </details>
    </div>
  </section>
</main>
<footer class=\"site-footer\">
  <div class=\"container\">
    <p>高雄水電行資料導覽｜自動化產生的在地服務索引。</p>
  </div>
</footer>
<script src=\"../assets/script.js\"></script>
</body>
</html>
"""


def render_index(stores: list[dict[str, str]], slug_map: dict[str, str], base_url: str) -> str:
    title = "高雄水電行地圖與聯絡資訊"
    description = "瀏覽高雄各區水電行、工程行與水匠的地址、評分、營業時間與聯絡方式，快速找到附近的水電服務。"
    url = f"{base_url.rstrip('/')}/index.html"
    structured_data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": title,
        "url": url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{url}?q={{search_term}}",
            "query-input": "required name=search_term",
        },
    }
    json_ld = json.dumps(structured_data, ensure_ascii=False, indent=2)

    cards = []
    for store in stores:
        slug = slug_map[store['店家名稱']]
        services = "、".join(filter(None, [store.get("實體和線上"), store.get("其他服務")]))
        meta = build_meta_description(store)
        cards.append(
            f"<article class=\"store-card\" data-name=\"{html.escape(store['店家名稱'])}\" data-type=\"{html.escape(store.get('店家類型',''))}\" data-address=\"{html.escape(store.get('地址',''))}\">"
            f"<div class=\"card-header\"><p class=\"eyebrow\">{html.escape(store.get('店家類型','商店'))}</p><span class=\"rating\">⭐ {html.escape(store.get('評分','-'))}</span></div>"
            f"<h2><a href=\"./stores/{slug}.html\">{html.escape(store['店家名稱'])}</a></h2>"
            f"<p class=\"meta\">{html.escape(meta)}</p>"
            f"<p class=\"services\">{html.escape(services) if services else '服務資訊待補'}</p>"
            f"<div class=\"card-actions\"><a class=\"button primary\" href=\"./stores/{slug}.html\">查看細節</a>"
            f"<a class=\"button ghost\" href=\"{html.escape(store.get('Google 地圖連結', '#'))}\" target=\"_blank\" rel=\"noopener\">開啟地圖</a></div>"
            f"</article>"
        )
    cards_html = "\n".join(cards)

    return f"""
<!doctype html>
<html lang=\"zh-Hant\">
<head>
{seo_head(title, description, url, asset_prefix='./assets/', extra_meta=f'<script type="application/ld+json">{json_ld}</script>')}
</head>
<body>
<header class=\"site-header\">
  <div class=\"container\">
    <a href=\"./index.html\" class=\"logo\">高雄水電行導覽</a>
    <nav><a href=\"#list\">店家列表</a><a href=\"#faq\">常見問題</a></nav>
  </div>
</header>
<main class=\"container\">
  <section class=\"hero\">
    <p class=\"eyebrow\">GitHub Pages 靜態網站</p>
    <h1>高雄水電行資訊大全</h1>
    <p class=\"lede\">彙整高雄市 96 家水電行與工程行，包含地址、營業時間、評分、電話與地圖連結，方便搜尋附近的專業服務。</p>
    <div class=\"cta-group\">
      <a class=\"button primary\" href=\"#list\">瀏覽全部店家</a>
      <a class=\"button secondary\" href=\"https://www.google.com/maps/search/%E9%AB%98%E9%9B%84+%E6%B0%B4%E9%9B%BB%E8%A1%8C\" target=\"_blank\" rel=\"noopener\">在地圖查看</a>
    </div>
  </section>

  <section id=\"list\" class=\"list\">
    <div class=\"list-header\">
      <div>
        <p class=\"eyebrow\">店家列表</p>
        <h2>高雄 96 家水電行</h2>
      </div>
      <div class=\"filters\">
        <input id=\"search\" type=\"search\" placeholder=\"輸入店名、地址或類型搜尋\" aria-label=\"搜尋店家\">
        <select id=\"type-filter\" aria-label=\"類型篩選\">
          <option value=\"\">全部類型</option>
          <option value=\"水電行\">水電行</option>
          <option value=\"水電承辦商\">水電承辦商</option>
          <option value=\"水匠\">水匠</option>
          <option value=\"商店\">商店</option>
        </select>
      </div>
    </div>
    <div class=\"grid\" id=\"store-grid\">
      {cards_html}
    </div>
  </section>

  <section id=\"faq\" class=\"faq\">
    <div>
      <h2>常見問題</h2>
      <details open>
        <summary>這些資料是否都在高雄？</summary>
        <p>資料來源於 Google 地圖，高雄地區共收錄 96 家水電行與工程行。</p>
      </details>
      <details>
        <summary>如何提升各店家的 SEO？</summary>
        <p>每個店家頁面均包含語意化 HTML 標題、描述、Open Graph 標籤與 Schema.org LocalBusiness JSON-LD，有助於搜尋結果呈現。</p>
      </details>
      <details>
        <summary>網站如何部署？</summary>
        <p>將 docs/ 設定為 GitHub Pages 來源，即可自動呈現靜態網站。</p>
      </details>
    </div>
  </section>
</main>
<footer class=\"site-footer\">
  <div class=\"container\">
    <p>高雄水電行資料導覽｜GitHub Pages 靜態網站。</p>
  </div>
</footer>
<script src=\"./assets/script.js\"></script>
</body>
</html>
"""


def build_sitemap(store_slugs: dict[str, str], base_url: str) -> str:
    base = base_url.rstrip("/")
    urls = [f"{base}/index.html"] + [f"{base}/stores/{slug}.html" for slug in store_slugs.values()]
    now = datetime.utcnow().strftime("%Y-%m-%d")
    entries = "\n".join(
        f"  <url><loc>{html.escape(u)}</loc><lastmod>{now}</lastmod></url>" for u in urls
    )
    return f"""
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
{entries}
</urlset>
"""


def main():
    base_url = os.environ.get("BASE_URL", DEFAULT_BASE_URL)
    rows = load_rows()
    ensure_dirs()

    slug_map: dict[str, str] = {}
    existing_slugs: set[str] = set()
    for row in rows:
        name = row.get("店家名稱", "")
        slug_map[name] = slugify(name, existing_slugs)

    index_html = render_index(rows, slug_map, base_url)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    for row in rows:
        slug = slug_map[row["店家名稱"]]
        page = render_store_page(row, slug, base_url)
        (STORES_DIR / f"{slug}.html").write_text(page, encoding="utf-8")

    sitemap = build_sitemap(slug_map, base_url)
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUTPUT_DIR / "robots.txt").write_text("Sitemap: " + base_url.rstrip("/") + "/sitemap.xml\n", encoding="utf-8")

    print(f"Generated {len(rows)} store pages.")


if __name__ == "__main__":
    main()

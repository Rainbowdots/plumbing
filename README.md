# Plumbing 店家靜態網站

此專案會把 `Plumbing Google Maps_KH.csv` 的 96 間水電行轉成 GitHub Pages 靜態網站，為每間店家生成獨立的 SEO 最佳化頁面與索引頁。

## 使用方式

1. 安裝需求：僅需 Python 3，無額外套件。
2. 產生網站：

   ```bash
   python generate_sites.py
   ```

   如需設定實際部署網址（會用在 canonical、OG 標籤與 sitemap），可加入環境變數：

   ```bash
   BASE_URL="https://<your-github-username>.github.io/plumbing/" python generate_sites.py
   ```

3. 將 repo 的 `docs/` 設為 GitHub Pages 來源即可發布。

## 產出內容

- `docs/index.html`：店家列表，支援店名／地址搜尋與類型篩選。
- `docs/stores/*.html`：每間水電行的獨立頁面，含敘述性標題、描述、Open Graph、Schema.org JSON-LD。
- `docs/sitemap.xml`、`docs/robots.txt`：SEO 基礎設定。
- `docs/assets/`：版面樣式與前端篩選腳本。

如需重新生成或更新資料，修改 `Plumbing Google Maps_KH.csv` 後重新執行 `generate_sites.py` 即可。

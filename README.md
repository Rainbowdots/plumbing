# Plumbing GitHub Pages

利用 Google Maps 匯出的水電行資料，快速在 GitHub Pages 上發佈每間店家的獨立網站，並加入 SEO 標記（meta、Open Graph、JSON-LD、sitemap、robots.txt）。

## 產生靜態網站

1. 安裝 Python 3，並確認 `Plumbing Google Maps_KH.csv` 存在於專案根目錄。
2. 執行產生腳本（記得換成你的 GitHub Pages 網址）：

   ```bash
   python scripts/generate_sites.py --base-url https://<username>.github.io/plumbing
   ```

   產物會寫入 `docs/`，包含：
   - `index.html`：所有水電行列表頁
   - `<店名>.html`：每間店的 SEO 友善獨立頁
   - `sitemap.xml` 與 `robots.txt`

3. 將 `docs/` 推上 GitHub，並在 repo 設定啟用 GitHub Pages（Source 選擇 `docs/`）。靜態檔案即會公開。

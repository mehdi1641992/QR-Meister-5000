# 🚀 QR Meister 5000

A free, privacy-first **QR Code & Barcode generator** that runs **entirely in your browser**.
No server, no database, no sign-up, no tracking — your data never leaves your device.

Hosts perfectly on **GitHub Pages** (free static hosting).

## ✨ Features

### 🎨 QR Code Generation
- **Content types:** Text/URL, WiFi access codes (WPA/WEP/Open), vCard contact cards
- **Pixel styles:** Square, Rounded, Circle (dots), Classy, Extra Rounded
- **Customization:** Foreground color, background color, **transparent background**
- **Logo overlay:** Embed your brand logo in the center (auto-boosts error correction to level H)

### 📊 Barcodes
- **Formats:** Code 128, EAN-13, UPC-A, Code 39 (with human-readable values)

### 📤 Export
- **Formats:** PNG, JPG, SVG (vector — infinitely scalable)
- **Resolutions:** 512px (web) up to **8K** (billboards)
- **Copy to clipboard** with one click

### 🌗 Interface
- **Live preview** with instant rendering as you type
- **Dark / light mode** (remembers your preference)
- **100% client-side** — works offline once loaded, nothing is ever uploaded

---

## 🌐 Deploy to GitHub Pages (free)

1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "QR Meister 5000 static web app"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
2. In your repo, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
4. Select **main** branch and **/(root)** folder, then click **Save**.
5. Wait ~1 minute. Your app is live at:
   `https://<your-username>.github.io/<your-repo>/`

> The included `.nojekyll` file makes GitHub Pages serve files as-is (no Jekyll processing), and `404.html` handles unknown URLs.

---

## 🖥️ Run locally

No build step and no dependencies. Either:

- **Option A:** double-click `index.html` (works from the file system), or
- **Option B:** serve it (recommended):
  ```bash
  python -m http.server 8000
  # then open http://localhost:8000
  ```

---

## 📂 Project Structure

```
/
├── index.html                     # The entire app (single page)
├── 404.html                       # GitHub Pages fallback page
├── .nojekyll                      # Disables Jekyll processing on Pages
├── assets/
│   ├── css/styles.css             # Custom styles (loader, checkerboard, theme)
│   ├── js/app.js                  # Generator engine (render, export, tabs)
│   ├── vendor/                    # Bundled libraries (no CDN dependency)
│   │   ├── qr-code-styling.min.js #   styled QR rendering (MIT)
│   │   └── JsBarcode.all.min.js   #   barcode rendering (MIT)
│   └── img/                       # favicon, logo, social preview images
```

## 🛠️ Tech

- [qr-code-styling](https://github.com/ozdemirburak/qr-code-styling) (MIT) — styled QR rendering
- [JsBarcode](https://github.com/lindell/JsBarcode) (MIT) — barcode rendering
- [Tailwind CSS](https://tailwindcss.com) via CDN + Phosphor Icons + Google Fonts (Inter)

## 📜 License

MIT for the app code. Third-party libraries keep their own licenses.

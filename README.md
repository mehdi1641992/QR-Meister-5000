
# 🚀 State-of-the-Art QR Code Generator (SaaS Edition)

A production-grade QR Code Generator built with Flask. Features a high-performance 16K rendering engine, dynamic URL shortening, analytics dashboard, and a complete Content Management System (CMS) for SEO landing pages.

## ✨ Key Features

### 🎨 Rendering Engine
- **Hyper-Resolution Support:** Generate QR codes up to **16K resolution** (15,360px) for billboards and print.
- **Smart Scaling:** Mathematical dot-size calculation to ensure crisp edges at any size.
- **Logo Overlay:** Intelligent center-logo embedding with transparency support.
- **Formats:** Export to PNG, JPG, and high-DPI PDF.

### 💼 Business Tools
- **Dynamic Short Links:** Create editable short links (e.g., `yourdomain.com/s/summer-sale`) that redirect to changing targets.
- **Bio Link Pages:** Auto-generated "Link-in-Bio" landing pages for Pro users.
- **Analytics:** Track scan counts, device types (Mobile vs Desktop), and daily performance.

### 🛠️ Admin & CMS
- **Dashboard:** Full admin panel to manage users, campaigns, and global settings.
- **Programmatic SEO:** Dynamic landing pages for industries (Restaurants, Real Estate, Retail).
- **Auto-Sitemap:** Dynamic XML sitemap generation for Google indexing.
- **File Manager:** Upload custom Favicons and Logos directly from settings.

---

## ⚙️ Installation

### 1. Clone & Setup
```bash
# Clone the repository
git clone [https://github.com/yourusername/qr-generator.git](https://github.com/yourusername/qr-generator.git)
cd qr-generator

# Create a virtual environment
python -m venv venv

# Activate Virtual Environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

```

### 2. Install Dependencies

Bash

```
pip install -r requirements.txt

```

### 3. Initialize Database

The application automatically creates the SQLite database (`site.db`) on the first run. No manual SQL setup is required.

### 4. Run the Application

Bash

```
python flask_app.py

```

_The app will launch at `http://127.0.0.1:5000`_

----------

## 🔐 Admin Access (Important)

On the very first run, the system automatically creates a **Super Admin** account.

-   **Login URL:** `/login`
    
-   **Default Username:** `admin`
    
-   **Default Password:** `admin123`
    
-   **Master Security PIN:** `123456789`
    

> ⚠️ **Security Notice:** Please change the admin password and Security PIN immediately from the Admin Profile section after logging in.

----------

## 📂 Project Structure

```
/
├── flask_app.py          # Core Application Logic (Routes & Engine)
├── requirements.txt      # Python Dependencies
├── site.db               # SQLite Database (Auto-created)
├── static/
│   ├── uploads/          # User uploaded logos & favicons
│   └── css/              # (Optional) Custom styles if not using CDN
└── templates/
    ├── index.html        # Main Generator Interface
    ├── login.html        # Admin Login
    ├── use_case.html     # Dynamic Industry Landing Pages
    ├── bio_link.html     # User Bio Link Page
    ├── sitemap_template.xml # XML Template for SEO
    └── admin/            # Admin Dashboard Templates
        ├── base.html
        ├── dashboard.html
        ├── settings.html
        ├── campaigns.html
        └── ...

```

## 🚀 Deployment (PythonAnywhere)

1.  Upload all files to your PythonAnywhere file manager.
    
2.  Open a **Bash Console** and run: `pip install -r requirements.txt`
    
3.  Go to the **Web** tab.
    
4.  Set **Source code** path to your folder (e.g., `/home/yourusername/mysite`).
    
5.  Reload the web app.
    

----------

## 📜 License

Proprietary Software. All rights reserved. Powered by **QR Master Engine v2.0**

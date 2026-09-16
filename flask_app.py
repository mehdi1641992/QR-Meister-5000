import os
import re
import base64
import qrcode
import string
import random
import zipfile
import uuid # NEW: For generating API Keys
import requests # NEW: For Geo-IP lookup
from io import BytesIO
from datetime import datetime, timedelta

# Added PIL for Logo Overlay functionality
from PIL import Image

# BARCODE IMPORTS (NEW)
import barcode
from barcode.writer import ImageWriter

from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer
)

# Added 'Response' to imports for Sitemap XML generation
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, MetaData
from flask_migrate import Migrate

app = Flask(__name__)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'w312-key-uwi-c323794esdfk')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'ico'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define the naming convention for SQLite compatibility
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default="QR Generator")
    favicon = db.Column(db.String(100), default="default_favicon.ico")
    total_generated = db.Column(db.Integer, default=0)
    title_font = db.Column(db.String(50), default="Inter")
    title_font_size = db.Column(db.Integer, default=32)
    title_color = db.Column(db.String(20), default="#111827")
    dark_mode = db.Column(db.Boolean, default=False)
    maintenance_mode = db.Column(db.Boolean, default=False)
    footer_text = db.Column(db.String(200), default="Powered by QR Master")
    contact_email = db.Column(db.String(100), default="admin@yourdomain.com")
    whatsapp_number = db.Column(db.String(20), default="8801XXXXXXXXX")
    payment_instructions = db.Column(db.Text, default="Send 1500 BDT via bKash to...")

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(10), unique=True, nullable=False)
    target_url = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    show_in_bio = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scans = db.relationship('ScanLog', backref='campaign', lazy=True, cascade="all, delete-orphan")

class ScanLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    platform = db.Column(db.String(50))
    # NEW: Geo-Location Fields
    ip_address = db.Column(db.String(50))
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(20), unique=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    is_pro = db.Column(db.Boolean, default=False)
    secure_pin = db.Column(db.String(128))
    transaction_id = db.Column(db.String(100))
    amount_paid = db.Column(db.Float, default=0.0)
    pending_update_type = db.Column(db.String(20))
    pending_value = db.Column(db.String(255))
    pending_new_pin = db.Column(db.String(128))
    # NEW: Developer API Key
    api_key = db.Column(db.String(64), unique=True)
    campaigns = db.relationship('Campaign', backref='owner', lazy=True)

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Industry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), default='ph-rocket-launch')
    action_text = db.Column(db.String(50))
    benefit_text = db.Column(db.String(100))
    description = db.Column(db.Text)
    meta_title = db.Column(db.String(150))
    meta_desc = db.Column(db.String(255))

class IndustryScan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    industry_id = db.Column(db.Integer, db.ForeignKey('industry.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    platform = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HELPERS & MIDDLEWARE ---

def get_config():
    config = SiteConfig.query.first()
    if not config:
        config = SiteConfig()
        db.session.add(config)
        db.session.commit()
    return config

@app.before_request
def check_maintenance():
    config = get_config()
    if config.maintenance_mode:
        allowed_paths = ['/login', '/logout', '/static', '/admin']
        is_allowed = any(request.path.startswith(path) for path in allowed_paths)
        if not is_allowed and not (current_user.is_authenticated and current_user.is_superadmin):
            return render_template('maintenance.html'), 503

def generate_slug(length=6):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

@app.context_processor
def inject_global_vars():
    return dict(config=get_config())

def generate_qr_code(data, target_size=1000, fg_color="#000000", bg_color="#FFFFFF", logo_path=None, style='square'):
    """
    Generates QR code with custom Dot Styles (Drawers).
    """
    drawers = {
        'square': SquareModuleDrawer(),
        'gapped': GappedSquareModuleDrawer(),
        'circle': CircleModuleDrawer(),
        'rounded': RoundedModuleDrawer(),
        'vertical': VerticalBarsDrawer(),
        'horizontal': HorizontalBarsDrawer()
    }
    selected_drawer = drawers.get(style, SquareModuleDrawer())

    estimated_box_size = (int(target_size) // 35) + 2

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=estimated_box_size,
        border=2
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=selected_drawer
    ).convert("RGBA")

    datas = img.getdata()
    newData = []

    for item in datas:
        if item[0] == 0 and item[1] == 0 and item[2] == 0:
            h = fg_color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            newData.append(rgb + (255,))
        else:
            if bg_color == 'transparent':
                newData.append((255, 255, 255, 0))
            else:
                h = bg_color.lstrip('#')
                rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                newData.append(rgb + (255,))

    img.putdata(newData)

    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        qr_width, qr_height = img.size
        logo_size = int(qr_width * 0.22)
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        logo_pos = ((qr_width - logo.size[0]) // 2, (qr_height - logo.size[1]) // 2)

        if bg_color == 'transparent':
             bg_square = Image.new("RGBA", logo.size, (255, 255, 255, 255))
             img.paste(bg_square, logo_pos, bg_square)
        else:
             h = bg_color.lstrip('#')
             bg_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255,)
             bg_square = Image.new("RGBA", logo.size, bg_rgb)
             img.paste(bg_square, logo_pos, bg_square)

        img.paste(logo, logo_pos, logo)

    return img.resize((int(target_size), int(target_size)), Image.Resampling.NEAREST)

def generate_barcode_img(data, barcode_type='code128', fg_color="#000000", bg_color="#FFFFFF"):
    """
    Generates a 1D Barcode (EAN, UPC, Code128)
    """
    if barcode_type not in barcode.PROVIDED_BARCODES:
        barcode_type = 'code128'

    # Configure ImageWriter to handle Colors
    # Note: python-barcode ImageWriter is basic. We render then colorize if needed.
    # For robust color, we rely on the PIL image returned.

    BC = barcode.get_barcode_class(barcode_type)

    # Some formats (EAN13) require exactly 12 or 13 digits.
    # We let the library raise error if data is invalid, caught in routes.
    my_barcode = BC(data, writer=ImageWriter())

    # Options for ImageWriter
    options = {
        'module_width': 0.4,
        'module_height': 10,
        'quiet_zone': 1,
        'font_size': 10,
        'text_distance': 3,
        'background': bg_color if bg_color != 'transparent' else 'white',
        'foreground': fg_color
    }

    img = my_barcode.render(writer_options=options).convert("RGBA")

    # Handle Transparency manually since library defaults 'white' for transparent
    if bg_color == 'transparent':
        datas = img.getdata()
        newData = []
        for item in datas:
            # If pixel is white-ish, make transparent
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        img.putdata(newData)

    return img

# --- PUBLIC ROUTES ---

@app.route('/')
def index():
    config, faqs, industries = get_config(), FAQ.query.all(), Industry.query.all()
    return render_template('index.html', config=config, faqs=faqs, industries=industries)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            pw_match = check_password_hash(user.password_hash, request.form.get('password'))
            pin_match = check_password_hash(user.secure_pin, request.form.get('password')) if user.secure_pin else False
            if pw_match or pin_match:
                login_user(user)
                return redirect(url_for('admin_dashboard'))
        flash('Invalid Username or Security Key')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/b/<username>')
def bio_link(username):
    user = User.query.filter_by(username=username, is_pro=True).first_or_404()
    links = Campaign.query.filter_by(user_id=user.id, is_active=True, show_in_bio=True).all()
    return render_template('bio_link.html', user=user, links=links)

@app.route('/contact')
def contact():
    return render_template('contact.html', config=get_config())

@app.route('/upgrade-instructions')
def upgrade_instructions():
    return render_template('upgrade.html')

# --- SEO & LEGAL ROUTES ---

@app.route('/sitemap.xml')
def sitemap():
    pages = []
    lastmod = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d')
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0 and not rule.rule.startswith('/admin'):
            pages.append([url_for(rule.endpoint, _external=True), lastmod])

    industries = Industry.query.all()
    for ind in industries:
        pages.append([url_for('use_case', industry=ind.slug, _external=True), lastmod])

    pro_users = User.query.filter_by(is_pro=True).all()
    for user in pro_users:
        pages.append([url_for('bio_link', username=user.username, _external=True), lastmod])
    return Response(render_template('sitemap_template.xml', pages=pages), mimetype='application/xml')

@app.route('/solutions/<industry>')
def use_case(industry):
    details = Industry.query.filter_by(slug=industry).first_or_404()
    ua = request.headers.get('User-Agent', '').lower()
    platform = "Mobile" if any(x in ua for x in ['iphone', 'android', 'mobile']) else "Desktop"
    db.session.add(IndustryScan(industry_id=details.id, platform=platform))
    db.session.commit()
    return render_template('use_case.html', industry=details.name, details=details)

@app.route('/terms')
def terms():
    page = Page.query.filter_by(slug='terms').first()
    if not page: return render_template('legal/terms.html', now_date=datetime.utcnow().strftime('%Y-%m-%d'))
    return render_template('legal/dynamic_page.html', page=page)

@app.route('/privacy')
def privacy():
    page = Page.query.filter_by(slug='privacy').first()
    if not page: return render_template('legal/privacy.html', now_date=datetime.utcnow().strftime('%Y-%m-%d'))
    return render_template('legal/dynamic_page.html', page=page)

# --- ADMIN ROUTES ---

@app.route('/admin')
@login_required
def admin_dashboard():
    config = get_config()
    if current_user.is_superadmin:
        total_revenue = db.session.query(db.func.sum(User.amount_paid)).scalar() or 0
        stats = {
            'total_qr': config.total_generated,
            'total_faqs': FAQ.query.count(),
            'total_users': User.query.count(),
            'pending_requests': User.query.filter(User.pending_update_type != None).count(),
            'revenue': total_revenue,
            'my_campaigns': Campaign.query.filter_by(user_id=current_user.id).count(),
            'my_scans': sum(len(c.scans) for c in current_user.campaigns) if current_user.campaigns else 0
        }
    else:
        stats = {
            'my_campaigns': Campaign.query.filter_by(user_id=current_user.id).count(),
            'my_scans': sum(len(c.scans) for c in current_user.campaigns) if current_user.campaigns else 0
        }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/generate-bio-qr/<username>')
@login_required
def generate_bio_qr(username):
    """Generates the fixed QR for the Pro user's Digital Business Card."""
    if current_user.username != username and not current_user.is_superadmin:
        return "Unauthorized", 403
    bio_url = f"{request.host_url}b/{username}"
    img = generate_qr_code(bio_url, target_size=600)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    if request.args.get('download'):
        return send_file(buf, mimetype='image/png', as_attachment=True, download_name=f'{username}_bio_qr.png')
    return send_file(buf, mimetype='image/png')

@app.route('/admin/campaigns', methods=['GET', 'POST'])
@login_required
def admin_campaigns():
    if request.method == 'POST':
        name, target = request.form.get('name'), request.form.get('target_url')
        show_bio = 'show_in_bio' in request.form
        if name and target:
            db.session.add(Campaign(name=name, target_url=target, slug=generate_slug(), user_id=current_user.id, show_in_bio=show_bio))
            db.session.commit()
            flash('Dynamic Campaign Created!', 'success')
    return render_template('admin/campaigns.html', campaigns=Campaign.query.filter_by(user_id=current_user.id).all())

@app.route('/admin/campaigns/edit/<int:id>', methods=['POST'])
@login_required
def edit_campaign(id):
    camp = Campaign.query.get_or_404(id)
    if camp.user_id == current_user.id or current_user.is_superadmin:
        camp.name = request.form.get('name')
        camp.target_url = request.form.get('target_url')
        camp.show_in_bio = 'show_in_bio' in request.form
        db.session.commit()
        flash("Campaign destination updated.", "success")
    return redirect(url_for('admin_campaigns'))

@app.route('/admin/campaigns/stats/<int:id>')
@login_required
def campaign_stats(id):
    camp = Campaign.query.get_or_404(id)
    if camp.user_id != current_user.id and not current_user.is_superadmin:
        return jsonify({'error': 'Unauthorized'}), 403

    # 1. Platform Data
    p_data = db.session.query(ScanLog.platform, func.count(ScanLog.id)).filter(ScanLog.campaign_id == id).group_by(ScanLog.platform).all()

    # 2. Timeline Data
    today = datetime.utcnow().date()
    labels = [(today - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
    values = [ScanLog.query.filter(ScanLog.campaign_id == id, func.date(ScanLog.timestamp) == (today - timedelta(days=i))).count() for i in range(6, -1, -1)]

    # 3. Geo Data (NEW)
    geo_data = db.session.query(ScanLog.country, func.count(ScanLog.id)).filter(ScanLog.campaign_id == id).group_by(ScanLog.country).all()
    geo_dict = {country or 'Unknown': count for country, count in geo_data}

    return jsonify({'labels': labels, 'values': values, 'platforms': {p: c for p, c in p_data}, 'geo': geo_dict})

@app.route('/admin/campaigns/delete/<int:id>')
@login_required
def delete_campaign(id):
    camp = Campaign.query.get_or_404(id)
    if camp.user_id != current_user.id and not current_user.is_superadmin:
        flash("Unauthorized access.", "error")
        return redirect(url_for('admin_campaigns'))
    db.session.delete(camp)
    db.session.commit()
    flash("Campaign removed from ledger.", "info")
    return redirect(url_for('admin_campaigns'))

@app.route('/admin/bulk-generate', methods=['GET', 'POST'])
@login_required
def bulk_generate():
    """High-performance batch engine for Pro users."""
    if request.method == 'POST':
        raw_urls = request.form.get('urls', '')
        urls = [u.strip() for u in raw_urls.split('\n') if u.strip()][:100]
        fg = request.form.get('fg_color', '#000000')
        bg = 'transparent' if 'is_transparent' in request.form else '#FFFFFF'

        if not urls:
            flash("Please enter at least one URL.", "error")
            return redirect(url_for('bulk_generate'))

        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            for i, u in enumerate(urls):
                img_buf = BytesIO()
                qr_img = generate_qr_code(u, target_size=1000, fg_color=fg, bg_color=bg)
                qr_img.save(img_buf, 'PNG')
                zf.writestr(f"batch_qr_{i+1}.png", img_buf.getvalue())

        buf.seek(0)
        return send_file(
            buf,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'QR_Batch_{datetime.now().strftime("%Y%m%d")}.zip'
        )

    return render_template('admin/bulk.html')

@app.route('/admin/pages', methods=['GET'])
@login_required
def admin_pages():
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    return render_template('admin/pages.html', pages=Page.query.all())

@app.route('/admin/pages/edit/<slug>', methods=['GET', 'POST'])
@login_required
def edit_page(slug):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    page = Page.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        page.title, page.content = request.form.get('title'), request.form.get('content')
        db.session.commit()
        flash(f'{page.title} Updated!', 'success')
        return redirect(url_for('admin_pages'))
    return render_template('admin/edit_page.html', page=page)

@app.route('/admin/industries', methods=['GET', 'POST'])
@login_required
def admin_industries():
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        name, slug = request.form.get('name'), request.form.get('slug').lower().replace(' ', '-')
        if not Industry.query.filter_by(slug=slug).first():
            db.session.add(Industry(name=name, slug=slug, icon=request.form.get('icon'), action_text=request.form.get('action_text'), benefit_text=request.form.get('benefit_text')))
            db.session.commit()
            flash(f'Industry {name} created!', 'success')
    return render_template('admin/industries.html', industries=Industry.query.all())

@app.route('/admin/industries/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_industry(id):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    ind = Industry.query.get_or_404(id)
    if request.method == 'POST':
        ind.name, ind.icon = request.form.get('name'), request.form.get('icon')
        ind.action_text, ind.benefit_text = request.form.get('action_text'), request.form.get('benefit_text')
        ind.description = request.form.get('description')
        ind.meta_title, ind.meta_desc = request.form.get('meta_title'), request.form.get('meta_desc')
        db.session.commit()
        flash(f'SEO for {ind.name} updated!', 'success')
        return redirect(url_for('admin_industries'))
    return render_template('admin/edit_industry.html', industry=ind)

@app.route('/admin/industries/delete/<int:id>')
@login_required
def delete_industry(id):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    ind = Industry.query.get_or_404(id)
    db.session.delete(ind)
    db.session.commit()
    flash('Industry deleted.', 'info')
    return redirect(url_for('admin_industries'))

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    industry_stats = db.session.query(Industry.name, func.count(IndustryScan.id)).join(IndustryScan).group_by(Industry.name).all()
    mobile_count = IndustryScan.query.filter_by(platform='Mobile').count()
    desktop_count = IndustryScan.query.filter_by(platform='Desktop').count()
    return render_template('admin/analytics.html', industry_stats=industry_stats, mobile_count=mobile_count, desktop_count=desktop_count)

# --- CORE ENGINE (UPDATED WITH GEO) ---

@app.route('/s/<slug>')
def dynamic_redirect(slug):
    camp = Campaign.query.filter_by(slug=slug, is_active=True).first_or_404()

    # 1. Capture Platform
    ua = request.headers.get('User-Agent', '').lower()
    platform = "Mobile" if any(x in ua for x in ['iphone', 'android', 'mobile']) else "Desktop"

    # 2. Capture IP (Handle PythonAnywhere Proxy)
    if 'X-Forwarded-For' in request.headers:
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        ip = request.remote_addr

    # 3. Resolve Geo-Location (Using ip-api.com)
    country, city = None, None
    try:
        # Timeout is crucial to prevent hanging if API is slow
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == 'success':
                country = data.get('country')
                city = data.get('city')
    except:
        pass # Fail silently if API is down, don't stop the redirect!

    # 4. Log Scan
    db.session.add(ScanLog(
        campaign_id=camp.id,
        platform=platform,
        ip_address=ip,
        country=country,
        city=city
    ))
    db.session.commit()

    return redirect(camp.target_url)

@app.route('/preview', methods=['POST'])
def preview():
    data, fg, bg, style, gen_type = request.form.get('qr_data', ''), request.form.get('fg_color', '#000000'), request.form.get('bg_color', '#FFFFFF'), request.form.get('qr_style', 'square'), request.form.get('gen_type', 'qr')
    logo = request.files.get('logo')
    logo_path = None
    if logo:
        fn = secure_filename(logo.filename)
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        logo.save(logo_path)
    config = get_config()
    config.total_generated += 1
    db.session.commit()
    buf = BytesIO()

    if gen_type == 'barcode':
        # Generate Barcode
        b_type = request.form.get('barcode_type', 'code128')
        try:
            img = generate_barcode_img(data, b_type, fg, bg)
            img.save(buf, format="PNG")
        except Exception as e:
            return jsonify({'error': 'Invalid Barcode Data'}), 400
    else:
        # Generate QR
        logo = request.files.get('logo')
        logo_path = None
        if logo:
            fn = secure_filename(logo.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
            logo.save(logo_path)
        img = generate_qr_code(data, 300, fg, '#FFFFFF' if bg == 'transparent' else bg, logo_path, style=style)
        img.save(buf, format="PNG")

    return jsonify({'image': f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}", 'new_count': config.total_generated})

@app.route('/download', methods=['POST'])
def download():
    data, fg, bg, qual, style, gen_type = request.form.get('qr_data'), request.form.get('fg_color', '#000000'), request.form.get('bg_color', '#FFFFFF'), request.form.get('quality', 1000), request.form.get('qr_style', 'square'), request.form.get('gen_type', 'qr')
    try: target_res = min(int(qual), 16000)
    except: target_res = 1000
    img = generate_qr_code(data, target_res, fg, '#FFFFFF' if bg == 'transparent' else bg, style=style)
    buf, fmt = BytesIO(), request.form.get('format', 'png')

    if gen_type == 'barcode':
        b_type = request.form.get('barcode_type', 'code128')
        img = generate_barcode_img(data, b_type, fg, bg)
        # Barcodes are naturally smaller, so we upscale them for print
        if int(qual) > 1000:
            img = img.resize((img.width * 4, img.height * 4), Image.Resampling.NEAREST)
    else:
        try: target_res = min(int(qual), 16000)
        except: target_res = 1000
        img = generate_qr_code(data, target_res, fg, '#FFFFFF' if bg == 'transparent' else bg, style=style)

    if fmt == 'pdf':
        img.save(buf, format="PDF", resolution=300.0)
        m, e = 'application/pdf', 'pdf'
    else:
        if fmt == 'jpg': img = img.convert("RGB")
        img.save(buf, format="JPEG" if fmt == 'jpg' else "PNG", quality=100)
        m, e = ('image/jpeg', 'jpg') if fmt == 'jpg' else ('image/png', 'png')

    buf.seek(0)
    return send_file(buf, mimetype=m, as_attachment=True, download_name=f"code.{e}")

# --- SETTINGS & PROFILE (UPDATED WITH API KEY) ---

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    cfg = get_config()
    if request.method == 'POST':
        for attr in ['site_name', 'footer_text', 'title_font', 'title_color', 'contact_email', 'whatsapp_number', 'payment_instructions']:
            setattr(cfg, attr, request.form.get(attr))
        cfg.title_font_size = int(request.form.get('title_font_size', 32))
        cfg.dark_mode = 'dark_mode' in request.form
        cfg.maintenance_mode = 'maintenance_mode' in request.form
        if 'favicon' in request.files:
            file = request.files['favicon']
            if file and file.filename:
                fn = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                cfg.favicon = fn
        db.session.commit()
        flash('Settings Updated!')
    return render_template('admin/settings.html', config=cfg)

@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    if request.method == 'POST':
        # Password Change Logic
        if 'new_password' in request.form:
            if check_password_hash(current_user.password_hash, request.form.get('current_password')):
                current_user.password_hash = generate_password_hash(request.form.get('new_password'))
                db.session.commit()
                flash('Password Updated!')
            else: flash('Current Password Error', 'error')

        # NEW: Generate API Key Logic
        elif 'generate_key' in request.form:
            if current_user.is_pro or current_user.is_superadmin:
                current_user.api_key = f"sk_{uuid.uuid4().hex}"
                db.session.commit()
                flash('New API Key Generated!', 'success')
            else:
                flash('API Access is for Pro Members only.', 'error')

    return render_template('admin/profile.html')

@app.route('/admin/profile/request-pin', methods=['POST'])
@login_required
def request_pin_change():
    """Allows a user to request a new PIN, which sets a flag for Admin approval."""
    new_pin = request.form.get('new_pin')

    if new_pin and len(new_pin) >= 4:
        # Store the hashed PIN in the temporary 'pending' column
        current_user.pending_new_pin = generate_password_hash(new_pin)
        current_user.pending_update_type = 'pin_change'
        db.session.commit()
        flash('Security PIN change requested. Awaiting Super Admin approval.', 'info')
    else:
        flash('Invalid PIN provided. Request failed.', 'error')

    return redirect(url_for('admin_profile'))

@app.route('/admin/users/approve/<int:id>')
@login_required
def approve_change(id):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))

    user = User.query.get_or_404(id)

    if user.pending_update_type == 'pin_change':
        # Apply the pending PIN as the actual PIN
        user.secure_pin = user.pending_new_pin
        # Clear the pending flags
        user.pending_new_pin = None
        user.pending_update_type = None
        db.session.commit()
        flash(f"PIN change for {user.username} approved.", "success")

    return redirect(url_for('admin_users'))

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    if request.method == 'POST' and 'create_staff' in request.form:
        u, p = request.form.get('username'), request.form.get('password')
        if not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password_hash=generate_password_hash(p)))
            db.session.commit()
            flash(f'Staff {u} created!', 'success')
    return render_template('admin/users.html', users=User.query.all())

# ADD THESE NEW ROUTES BELOW IT:

@app.route('/admin/users/create-pro', methods=['POST'])
@login_required
def create_pro_user():
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    u, e, t, a = request.form.get('username'), request.form.get('email'), request.form.get('txn_id'), request.form.get('amount', 0)
    if not User.query.filter_by(username=u).first():
        uid = f"QR-2025-{random.randint(1000, 9999)}"
        new_pro = User(username=u, email=e, transaction_id=t, amount_paid=float(a), is_pro=True, uid=uid,
                        password_hash=generate_password_hash("12345678"), secure_pin=generate_password_hash("123456789"))
        db.session.add(new_pro)
        db.session.commit()
        flash(f"Pro Member {u} activated! UID: {uid}", "success")
    else:
        flash("Username already exists.", "error")
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    if id == current_user.id:
        flash("Cannot delete owner account.", "error")
        return redirect(url_for('admin_users'))
    user_to_delete = User.query.get_or_404(id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"Identity {user_to_delete.username} wiped.", "info")
    return redirect(url_for('admin_users'))

@app.route('/admin/users/reset-pin/<int:id>')
@login_required
def reset_user_pin(id):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    user = User.query.get_or_404(id)
    user.secure_pin = generate_password_hash("123456789")
    db.session.commit()
    flash(f"PIN for {user.username} reset to default: 123456789", "success")
    return redirect(url_for('admin_users'))

# --- DEVELOPER API (NEW) ---

@app.route('/api/v1/generate', methods=['POST'])
def api_generate():
    """
    B2B API Endpoint.
    Expects params: key, data, bg_color, fg_color, style
    """
    api_key = request.args.get('key') or request.form.get('key')
    if not api_key:
        return jsonify({'error': 'Missing API Key'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user or not user.is_pro:
        return jsonify({'error': 'Invalid Key or Subscription'}), 403

    # If auth passes, generate QR
    data = request.form.get('data') or request.args.get('data')
    if not data: return jsonify({'error': 'No data provided'}), 400

    style = request.form.get('style') or request.args.get('style') or 'square'
    fg = request.form.get('fg_color') or request.args.get('fg_color') or '#000000'
    bg = request.form.get('bg_color') or request.args.get('bg_color') or '#FFFFFF'

    try:
        img = generate_qr_code(data, target_size=1000, fg_color=fg, bg_color=bg, style=style)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- FAQ MANAGEMENT ---

@app.route('/admin/faqs', methods=['GET', 'POST'])
@login_required
def admin_faqs():
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        q = request.form.get('question')
        a = request.form.get('answer')
        if q and a:
            db.session.add(FAQ(question=q, answer=a))
            db.session.commit()
            flash('FAQ Entry Added!', 'success')

    faqs = FAQ.query.all()
    return render_template('admin/faqs.html', faqs=faqs)

@app.route('/admin/faqs/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_faq(id):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    faq = FAQ.query.get_or_404(id)

    if request.method == 'POST':
        faq.question = request.form.get('question')
        faq.answer = request.form.get('answer')
        db.session.commit()
        flash('FAQ Updated successfully!', 'success')
        return redirect(url_for('admin_faqs'))

    return render_template('admin/edit_faq.html', faq=faq)

@app.route('/admin/faqs/delete/<int:id>')
@login_required
def delete_faq(id):
    if not current_user.is_superadmin: return redirect(url_for('admin_dashboard'))
    faq = FAQ.query.get_or_404(id)
    db.session.delete(faq)
    db.session.commit()
    flash('FAQ Deleted.', 'info')
    return redirect(url_for('admin_faqs'))

# --- DATABASE INIT ---

with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        db.session.add(User(username='admin', password_hash=generate_password_hash('admin123'), secure_pin=generate_password_hash('123456789'), is_superadmin=True, is_pro=True, uid="QR-ADMIN-001"))
    elif not admin_user.is_pro:
        admin_user.is_pro = True

    if not Industry.query.first():
        db.session.bulk_save_objects([
            Industry(slug='restaurants', name='Restaurants', icon='ph-fork-knife', action_text='Digital Menu', benefit_text='Contactless Dining'),
            Industry(slug='real-estate', name='Real Estate', icon='ph-house-line', action_text='Virtual Tour', benefit_text='Instant Data'),
            Industry(slug='retail', name='Retail Shops', icon='ph-shopping-bag', action_text='Discount Code', benefit_text='Loyalty')
        ])
    if not Page.query.filter_by(slug='terms').first():
        db.session.add(Page(slug='terms', title='Terms of Service', content='<p>Default terms...</p>'))
    if not Page.query.filter_by(slug='privacy').first():
        db.session.add(Page(slug='privacy', title='Privacy Policy', content='<p>Default privacy...</p>'))
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=False)
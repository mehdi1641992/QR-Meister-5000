/* ===== QR Meister 5000 — client-side generator engine ===== */
/* No server, no database: everything renders in your browser. */

'use strict';

const $ = (id) => document.getElementById(id);

let qrInstance = null;          // qr-code-styling instance (QR preview)
let logoDataUrl = null;         // data URL of uploaded logo overlay
let currentBarcodeCanvas = null;
let previewDebounce = null;

/* ---------------- Data construction (shared with old engine) ---------------- */

function getConstructedData() {
    const genType = $('gen_type').value;
    if (genType === 'barcode') return $('barcode_data').value;

    const type = $('qr_type').value;
    if (type === 'text_url') return $('qr_data').value;
    if (type === 'wifi') {
        const s = $('wifi_ssid').value;
        const p = $('wifi_pass').value;
        const e = $('wifi_type').value;
        return s ? `WIFI:T:${e};S:${s};P:${p};;` : '';
    }
    if (type === 'vcard') {
        const f = $('vc_first').value;
        const l = $('vc_last').value;
        if (!f && !l) return '';
        return `BEGIN:VCARD\nVERSION:3.0\nN:${l};${f};;;\nFN:${f} ${l}\nTEL;TYPE=WORK,VOICE:${$('vc_phone').value}\nEMAIL:${$('vc_email').value}\nORG:${$('vc_org').value}\nEND:VCARD`;
    }
    return '';
}

/* ---------------- Theme ---------------- */

function applyTheme(dark) {
    document.body.classList.toggle('dark', dark);
    $('theme_icon').className = dark ? 'ph ph-sun text-lg' : 'ph ph-moon-stars text-lg';
    try { localStorage.setItem('qr_dark_mode', dark ? 'true' : 'false'); } catch (e) { /* ignore */ }
}

function toggleTheme() {
    applyTheme(!document.body.classList.contains('dark'));
}

function initTheme() {
    let stored = null;
    try { stored = localStorage.getItem('qr_dark_mode'); } catch (e) { /* ignore */ }
    if (stored !== null) applyTheme(stored === 'true');
    else applyTheme(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
}

/* ---------------- QR options ---------------- */

const DOT_TYPES = {
    square: 'square',
    rounded: 'rounded',
    circle: 'dots',
    classy: 'classy',
    extra: 'extra-rounded'
};

function buildQrOptions(size) {
    const transparent = $('bg_transparent').checked;
    const fg = $('fg_color').value;
    const bg = transparent ? 'transparent' : $('bg_color').value;
    const dotType = DOT_TYPES[$('qr_style').value] || 'square';

    return {
        width: size,
        height: size,
        type: 'canvas',
        data: getConstructedData(),
        margin: 2,
        image: logoDataUrl || undefined,
        qrOptions: { errorCorrectionLevel: logoDataUrl ? 'H' : 'Q' },
        imageOptions: { hideBackgroundDots: true, imageSize: 0.4, margin: 4, crossOrigin: 'anonymous' },
        dotsOptions: { color: fg, type: dotType },
        cornersSquareOptions: { color: fg, type: dotType === 'square' ? 'square' : 'extra-rounded' },
        cornersDotOptions: { color: fg, type: dotType === 'dots' ? 'dot' : 'square' },
        backgroundOptions: { color: bg }
    };
}

/* ---------------- Preview ---------------- */

function showPlaceholder(message) {
    const ph = $('placeholder_text');
    $('loader').style.display = 'none';
    $('qr_render').classList.add('hidden');
    $('barcode_render').classList.add('hidden');
    ph.classList.remove('hidden', 'opacity-0');
    if (message) {
        ph.innerHTML = `<i class="ph ph-warning-circle text-5xl mb-4 opacity-20"></i><p class="text-xs font-bold uppercase tracking-widest leading-loose">${message}</p>`;
    }
}

function showRender(which) {
    $('placeholder_text').classList.add('hidden');
    $('loader').style.display = 'none';
    $('qr_render').classList.toggle('hidden', which !== 'qr');
    $('barcode_render').classList.toggle('hidden', which !== 'barcode');
}

function renderBarcodePreview(data) {
    const wrap = $('barcode_render');
    wrap.innerHTML = '';
    const canvas = document.createElement('canvas');
    wrap.appendChild(canvas);
    try {
        JsBarcode(canvas, data, {
            format: $('barcode_type').value,
            lineColor: $('fg_color').value,
            background: $('bg_transparent').checked ? 'transparent' : $('bg_color').value,
            width: 3,
            height: 110,
            displayValue: true,
            fontSize: 18,
            fontOptions: 'bold',
            margin: 12
        });
        currentBarcodeCanvas = canvas;
        showRender('barcode');
    } catch (err) {
        currentBarcodeCanvas = null;
        showPlaceholder('Invalid data for this barcode format');
    }
}

function renderPreview() {
    const data = getConstructedData();
    if (!data || data.trim() === '') {
        $('placeholder_text').innerHTML =
            '<i class="ph ph-qr-code text-5xl mb-4 opacity-20"></i><p class="text-xs font-bold uppercase tracking-widest leading-loose">Live Render Engine</p>';
        showPlaceholder(null);
        return;
    }

    const isBarcode = $('gen_type').value === 'barcode';
    if (isBarcode) {
        renderBarcodePreview(data);
        return;
    }

    $('loader').style.display = 'block';
    try {
        if (!qrInstance) {
            qrInstance = new QRCodeStyling(buildQrOptions(512));
            $('qr_render').innerHTML = '';
            qrInstance.append($('qr_render'));
        } else {
            qrInstance.update(buildQrOptions(512));
        }
        showRender('qr');
    } catch (err) {
        showPlaceholder('Could not render this content');
    }
}

function triggerPreview() {
    clearTimeout(previewDebounce);
    previewDebounce = setTimeout(renderPreview, 300);
}

/* ---------------- Export helpers ---------------- */

function blobToImage(blob) {
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
        img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('image load failed')); };
        img.src = url;
    });
}

function canvasToJpegBlob(canvas) {
    const out = document.createElement('canvas');
    out.width = canvas.width;
    out.height = canvas.height;
    const ctx = out.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, out.width, out.height);
    ctx.drawImage(canvas, 0, 0);
    return new Promise((resolve) => out.toBlob(resolve, 'image/jpeg', 0.95));
}

async function exportQr(fmt, size) {
    const tmp = new QRCodeStyling(buildQrOptions(size));
    if (fmt === 'svg') return tmp.getRawData('svg');
    const pngBlob = await tmp.getRawData('png');
    if (fmt === 'png') return pngBlob;
    // JPG has no alpha channel: composite over white first
    const img = await blobToImage(pngBlob);
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    canvas.getContext('2d').drawImage(img, 0, 0);
    return canvasToJpegBlob(canvas);
}

async function exportBarcode(fmt, size) {
    const value = getConstructedData();
    const fg = $('fg_color').value;
    const bg = $('bg_transparent').checked ? 'transparent' : $('bg_color').value;
    const scale = Math.max(1, Math.round(size / 400));

    if (fmt === 'svg') {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        JsBarcode(svg, value, {
            format: $('barcode_type').value, lineColor: fg, background: bg,
            width: 3, height: 110, displayValue: true, fontSize: 18, fontOptions: 'bold', margin: 12
        });
        return new Blob([new XMLSerializer().serializeToString(svg)], { type: 'image/svg+xml' });
    }

    const canvas = document.createElement('canvas');
    JsBarcode(canvas, value, {
        format: $('barcode_type').value, lineColor: fg, background: bg,
        width: 3 * scale, height: 110 * scale, displayValue: true,
        fontSize: 18 * scale, fontOptions: 'bold', margin: 12 * scale
    });
    if (fmt === 'png') return new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
    return canvasToJpegBlob(canvas);
}

/* ---------------- Actions ---------------- */

async function downloadQRCode() {
    const data = getConstructedData();
    if (!data || data.trim() === '') return;

    const btn = document.querySelector('button[onclick="downloadQRCode()"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="ph ph-spinner animate-spin"></i> Rendering...';
    btn.disabled = true;

    try {
        const fmt = $('download_format').value;               // png | jpg | svg
        const size = parseInt($('download_quality').value, 10);
        const isBarcode = $('gen_type').value === 'barcode';
        const blob = isBarcode ? await exportBarcode(fmt, size) : await exportQr(fmt, size);
        if (!blob) throw new Error('empty render');

        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `qr-meister-${Date.now()}.${fmt === 'jpeg' ? 'jpg' : fmt}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    } catch (err) {
        alert('Could not export the file. Please check your data.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function copyToClipboard() {
    try {
        let blob;
        if ($('gen_type').value === 'barcode') {
            if (!currentBarcodeCanvas) return;
            blob = await new Promise((r) => currentBarcodeCanvas.toBlob(r, 'image/png'));
        } else {
            if (!qrInstance) return;
            blob = await qrInstance.getRawData('png');
        }
        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
        alert('Copied to clipboard!');
    } catch (err) {
        alert('Copy failed.');
    }
}

function resetGenerator() {
    document.querySelectorAll('input[type="text"], input[type="email"], textarea').forEach(el => el.value = '');
    $('qr_style').value = 'square';
    $('fg_color').value = '#000000';
    $('bg_color').value = '#FFFFFF';
    $('bg_transparent').checked = false;
    removeLogo();
    switchTab('text_url');
}

/* ---------------- Logo overlay ---------------- */

function removeLogo() {
    logoDataUrl = null;
    $('qr_logo').value = '';
    $('logo_filename').innerHTML = '<i class="ph ph-image-square mr-2"></i> Click to upload Logo';
    $('remove_logo_btn').classList.add('hidden');
    triggerPreview();
}

function handleLogoChange() {
    const input = $('qr_logo');
    const removeBtn = $('remove_logo_btn');
    const label = $('logo_filename');

    if (input.files && input.files[0]) {
        label.innerText = input.files[0].name;
        removeBtn.classList.remove('hidden');
        const reader = new FileReader();
        reader.onload = (e) => {
            logoDataUrl = e.target.result;
            triggerPreview();
        };
        reader.readAsDataURL(input.files[0]);
    } else {
        removeLogo();
    }
}

/* ---------------- Toggles / tabs ---------------- */

function toggleTransparent() {
    const isChecked = $('bg_transparent').checked;
    $('bg_color').disabled = isChecked;
    $('bg_disabled_overlay').classList.toggle('hidden', !isChecked);
    triggerPreview();
}

function switchTab(type) {
    ['text_url', 'wifi', 'vcard', 'barcode'].forEach(t => $('input_' + t).classList.add('hidden'));
    $('input_' + type).classList.remove('hidden');

    const isBarcode = (type === 'barcode');
    $('gen_type').value = isBarcode ? 'barcode' : 'qr';

    $('qr_controls').classList.toggle('hidden', isBarcode);
    $('barcode_controls').classList.toggle('hidden', !isBarcode);

    if (!isBarcode) $('qr_type').value = type;

    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    const map = { text_url: 'tab_text', wifi: 'tab_wifi', vcard: 'tab_vcard', barcode: 'tab_barcode' };
    $(map[type]).classList.add('active');
    triggerPreview();
}

/* ---------------- Cookie banner ---------------- */

function checkCookies() {
    let consent = null;
    try { consent = localStorage.getItem('qr_cookie_consent'); } catch (e) { /* ignore */ }
    if (consent) return;
    const banner = $('cookie_banner');
    banner.classList.remove('hidden');
    setTimeout(() => banner.classList.remove('translate-y-full', 'opacity-0'), 100);
}

function acceptCookies() {
    try { localStorage.setItem('qr_cookie_consent', 'true'); } catch (e) { /* ignore */ }
    closeBanner();
}

function closeBanner() {
    const banner = $('cookie_banner');
    banner.classList.add('translate-y-full', 'opacity-0');
    setTimeout(() => banner.classList.add('hidden'), 500);
}

/* ---------------- Init ---------------- */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    document.querySelectorAll('input, textarea, select').forEach(el => {
        el.addEventListener('input', triggerPreview);
        el.addEventListener('change', triggerPreview);
    });
    $('qr_logo').addEventListener('change', handleLogoChange);
    $('theme_toggle').addEventListener('click', toggleTheme);
    switchTab('text_url');
    checkCookies();
});



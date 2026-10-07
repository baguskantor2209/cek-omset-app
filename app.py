import io
import os
import traceback
import requests
from datetime import datetime, timezone
import pytz
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components  # <-- TAMBAHAN IMPORT BARU

# Custom Import untuk Export PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

st.set_page_config(
    page_title="Bagus SDA AB4", layout="wide", page_icon="📊"
)

# Custom CSS
st.markdown(
    """<style>
header { visibility: hidden !important; height: 0px !important; display: none !important; }
#MainMenu { visibility: hidden !important; display: none !important; }
.stAppToolbar { display: none !important; visibility: hidden !important; }
footer { visibility: hidden !important; height: 0px !important; display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { visibility: hidden !important; display: none !important; }
[data-testid="stViewerBadge"] { display: none !important; visibility: hidden !important; }

.stApp { background-color: #f8f9fa; color: #111827; }

/* WARNA TOMBOL DOWNLOAD PDF */
[data-testid="stDownloadButton"] button {
    background-color: #2563eb !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background-color: #1d4ed8 !important;
}
[data-testid="stDownloadButton"] button p {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}

/* Metric Cards */
.metric-card {
    background-color: #ffffff; border-radius: 12px; padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #2563eb; margin-bottom: 12px;
}
.metric-title { color: #4b5563; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }
.metric-value { color: #1e3a8a; font-size: 1.5rem; font-weight: 800; margin: 4px 0; }
.metric-subtitle { font-size: 0.85rem; font-weight: 600; }

/* LEBAR KOLOM TABEL PROPORSIONAL */
.omset-table-container {
    background: #ffffff; padding: 16px; border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 15px; margin-bottom: 25px; overflow-x: auto;
}
.report-table { 
    width: 100%; 
    min-width: 1000px; 
    table-layout: fixed; 
    border-collapse: collapse; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; 
}
.report-table th { background-color: #00c0f0; color: #000000; font-weight: 700; text-align: center; padding: 8px 4px; border: 1px solid #bce8f1; white-space: nowrap; }
.report-table th.blue-header { background-color: #002060; color: #ffffff; }
.report-table td { padding: 6px 8px; border: 1px solid #d1d5db; text-align: right; background-color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.report-table td.center { text-align: center; }
.report-table td.left { text-align: left; font-weight: 600; }
.row-category { background-color: #002060 !important; color: #ffffff !important; font-weight: bold; }
.row-category td { background-color: #002060 !important; color: #ffffff !important; border-color: #001040 !important; }
.row-total { background-color: #d92525 !important; color: #ffffff !important; font-weight: bold; }
.row-total td { background-color: #d92525 !important; color: #ffffff !important; border-color: #b01010 !important; }

/* MENGHILANGKAN LABEL BAWAAN STREAMLIT KARENA KITA PAKAI LABEL MANUAL */
label[data-baseweb="radio"] { display: none; }
</style>""",
    unsafe_allow_html=True,
)

# --- ASSISTIVE TOUCH (iPHONE STYLE - CUSTOM) ---
assistive_touch_html = """
<style>
/* Kontainer AssistiveTouch (Ditambah transition untuk gerakan mulus jika diperlukan, dipindah ke ID untuk JS) */
.assistive-touch-container {
    position: fixed;
    bottom: 35px;
    left: 35px; 
    z-index: 999999;
    font-family: 'Segoe UI', Arial, sans-serif;
    /* transition dihapus dari container agar drag terasa mulus (realtime) */
}

/* Checkbox disembunyikan sebagai trigger klik */
.at-checkbox {
    display: none;
}

/* Tombol bulat (Gradasi Biru Muda) */
.at-button {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #7dd3fc, #3b82f6); /* GRADASI BIRU MUDA */
    border-radius: 50%; /* BULAT SEMPURNA */
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 2px solid rgba(255,255,255,0.6);
    transition: all 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}

/* Lingkaran dalam AssistiveTouch */
.at-button::after {
    content: "";
    width: 42px;
    height: 42px;
    border-radius: 50%;
    border: 3.5px solid rgba(255,255,255,0.9);
    box-sizing: border-box;
    transition: all 0.4s;
}
.at-button::before {
    content: "";
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(255,255,255,0.9);
    position: absolute;
    transition: all 0.4s;
}

/* Menu yang muncul saat diklik */
.at-menu {
    position: absolute;
    bottom: 75px;
    left: 0;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 10px;
    width: 230px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    opacity: 0;
    visibility: hidden;
    transform: scale(0.5) translateY(30px) rotate(-90deg); 
    transform-origin: bottom left; 
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(0,0,0,0.1);
}

/* Animasi ketika AssistiveTouch diklik */
.at-checkbox:checked ~ .at-menu {
    opacity: 1;
    visibility: visible;
    transform: scale(1) translateY(0) rotate(0deg); 
}
.at-checkbox:checked ~ .at-button {
    transform: scale(0.95) rotate(360deg); 
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.6);
}
.at-checkbox:checked ~ .at-button::after, 
.at-checkbox:checked ~ .at-button::before {
    opacity: 0.7;
}

/* List Form/Menu di dalamnya */
.at-item {
    padding: 14px 16px;
    border-radius: 12px;
    background: #ffffff;
    color: #1f2937 !important;
    text-decoration: none !important;
    font-size: 14px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.2s ease;
    border: 1px solid #f3f4f6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.at-item:hover {
    background: #f8fafc;
    transform: scale(1.02);
    color: #2563eb !important;
    border-color: #bfdbfe;
}
</style>

<!-- Ditambahkan id="at-container" dan id="at-handle" untuk dibaca oleh JavaScript -->
<div class="assistive-touch-container" id="at-container">
    <input type="checkbox" id="at-toggle" class="at-checkbox">
    <div class="at-menu">
        <a href="#dashboard-cek-omset-toko" class="at-item" onclick="document.getElementById('at-toggle').checked = false;">📊 Cek Omset Toko</a>
    </div>
    <label for="at-toggle" class="at-button" id="at-handle"></label>
</div>
"""
st.markdown(assistive_touch_html, unsafe_allow_html=True)

# --- SCRIPT JAVASCRIPT UNTUK FITUR DRAG (GESER) & AUTO-SAVE POSISI ---
draggable_js = """
<script>
    // Karena kita menempel JS di Streamlit, kita perlu memanggil element dari window parent
    const doc = window.parent.document;
    const container = doc.getElementById('at-container');
    const handle = doc.getElementById('at-handle');

    if (container && handle && !container.dataset.dragReady) {
        container.dataset.dragReady = 'true';
        
        let isDragging = false;
        let hasMoved = false; // Deteksi apakah beneran digeser atau cuma diklik
        let startX, startY, initialLeft, initialTop;

        // BACA POSISI TERAKHIR DARI MEMORI BROWSER (LocalStorage)
        const savedLeft = localStorage.getItem('at-left');
        const savedTop = localStorage.getItem('at-top');
        if (savedLeft && savedTop) {
            container.style.left = savedLeft;
            container.style.top = savedTop;
            container.style.bottom = 'auto'; // Matikan default bottom
        }

        function onMouseDown(e) {
            isDragging = false;
            hasMoved = false;
            if (e.type === 'touchstart') {
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
            } else {
                startX = e.clientX;
                startY = e.clientY;
            }
            
            const rect = container.getBoundingClientRect();
            initialLeft = rect.left;
            initialTop = rect.top;
            
            doc.addEventListener('mousemove', onMouseMove);
            doc.addEventListener('mouseup', onMouseUp);
            doc.addEventListener('touchmove', onMouseMove, {passive: false});
            doc.addEventListener('touchend', onMouseUp);
        }

        function onMouseMove(e) {
            let currentX, currentY;
            if (e.type === 'touchmove') {
                currentX = e.touches[0].clientX;
                currentY = e.touches[0].clientY;
            } else {
                currentX = e.clientX;
                currentY = e.clientY;
            }

            const dx = currentX - startX;
            const dy = currentY - startY;

            // Jika geseran lebih dari 5 pixel, maka itu sedang di-drag (bukan klik biasa)
            if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                isDragging = true;
                hasMoved = true;
                e.preventDefault(); // Mencegah layar ikut tergulir (scroll) saat digeser di HP
                
                container.style.left = (initialLeft + dx) + 'px';
                container.style.top = (initialTop + dy) + 'px';
                container.style.bottom = 'auto';
            }
        }

        function onMouseUp(e) {
            doc.removeEventListener('mousemove', onMouseMove);
            doc.removeEventListener('mouseup', onMouseUp);
            doc.removeEventListener('touchmove', onMouseMove);
            doc.removeEventListener('touchend', onMouseUp);
            
            // SIMPAN POSISI BARU KE MEMORI BROWSER
            if (hasMoved) {
                localStorage.setItem('at-left', container.style.left);
                localStorage.setItem('at-top', container.style.top);
            }
            setTimeout(() => { isDragging = false; }, 50);
        }

        // Cegah menu terbuka saat sedang di-drag
        handle.addEventListener('click', (e) => {
            if (hasMoved) {
                e.preventDefault(); 
            }
        });

        handle.addEventListener('mousedown', onMouseDown);
        handle.addEventListener('touchstart', onMouseDown, {passive: false});
    }
</script>
"""
# Eksekusi Script JS agar tersembunyi
components.html(draggable_js, height=0, width=0)


# --- FUNGSI LAST UPDATED DARI GITHUB API ---
@st.cache_data(ttl=300) # Refresh tiap 5 menit
def get_github_last_updated():
    """Tarik waktu aktual BDB_AB4.parquet di-commit ke GitHub"""
    url = "https://api.github.com/repos/baguskantor2209/cek-omset-app/commits?path=BDB_AB4.parquet&page=1&per_page=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json

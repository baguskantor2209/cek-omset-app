import io
import os
import math
import traceback
import requests
from datetime import datetime, timezone
import pytz
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
[data-testid="stDownloadButton"] button:hover { background-color: #1d4ed8 !important; }
[data-testid="stDownloadButton"] button p { color: #ffffff !important; font-weight: 700 !important; font-size: 14px !important; }

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
    width: 100%; min-width: 1000px; table-layout: fixed; border-collapse: collapse; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; 
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

# --- ASSISTIVE TOUCH DENGAN DUA MENU (PAGE ROUTING) ---
assistive_touch_html = """
<style>
.assistive-touch-container { position: fixed; bottom: 35px; left: 35px; z-index: 999999; font-family: 'Segoe UI', Arial, sans-serif; }
.at-checkbox { display: none; }
.at-button {
    width: 60px; height: 60px; background: linear-gradient(135deg, #7dd3fc, #3b82f6); border-radius: 50%;
    display: flex; align-items: center; justify-content: center; cursor: pointer;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    border: 2px solid rgba(255,255,255,0.6); transition: all 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}
.at-button::after { content: ""; width: 42px; height: 42px; border-radius: 50%; border: 3.5px solid rgba(255,255,255,0.9); box-sizing: border-box; transition: all 0.4s; }
.at-button::before { content: ""; width: 28px; height: 28px; border-radius: 50%; background: rgba(255,255,255,0.9); position: absolute; transition: all 0.4s; }
.at-menu {
    position: absolute; bottom: 75px; left: 0; background: rgba(255, 255, 255, 0.95); border-radius: 16px; padding: 10px; width: 230px;
    display: flex; flex-direction: column; gap: 8px; opacity: 0; visibility: hidden;
    transform: scale(0.5) translateY(30px) rotate(-90deg); transform-origin: bottom left; 
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 10px 30px rgba(0,0,0,0.15); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); border: 1px solid rgba(0,0,0,0.1);
}
.at-checkbox:checked ~ .at-menu { opacity: 1; visibility: visible; transform: scale(1) translateY(0) rotate(0deg); }
.at-checkbox:checked ~ .at-button { transform: scale(0.95) rotate(360deg); box-shadow: 0 4px 15px rgba(59, 130, 246, 0.6); }
.at-checkbox:checked ~ .at-button::after, .at-checkbox:checked ~ .at-button::before { opacity: 0.7; }
.at-item {
    padding: 14px 16px; border-radius: 12px; background: #ffffff; color: #1f2937 !important; text-decoration: none !important;
    font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 12px; transition: all 0.2s ease; border: 1px solid #f3f4f6; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.at-item:hover { background: #f8fafc; transform: scale(1.02); color: #2563eb !important; border-color: #bfdbfe; }
</style>

<div class="assistive-touch-container" id="at-container">
    <input type="checkbox" id="at-toggle" class="at-checkbox">
    <div class="at-menu">
        <a href="?page=cek_omset" target="_self" class="at-item" onclick="document.getElementById('at-toggle').checked = false;">📊 Cek Omset Toko</a>
        <a href="?page=lintas_divisi" target="_self" class="at-item" onclick="document.getElementById('at-toggle').checked = false;">🔄 Toko Lintas Divisi</a>
    </div>
    <label for="at-toggle" class="at-button" id="at-handle"></label>
</div>
"""
st.markdown(assistive_touch_html, unsafe_allow_html=True)

draggable_js = """<script>
    const doc = window.parent.document; const container = doc.getElementById('at-container'); const handle = doc.getElementById('at-handle');
    if (container && handle && !container.dataset.dragReady) {
        container.dataset.dragReady = 'true'; let isDragging = false; let hasMoved = false; let startX, startY, initialLeft, initialTop;
        const savedLeft = localStorage.getItem('at-left'); const savedTop = localStorage.getItem('at-top');
        if (savedLeft && savedTop) { container.style.left = savedLeft; container.style.top = savedTop; container.style.bottom = 'auto'; }
        function onMouseDown(e) {
            isDragging = false; hasMoved = false;
            if (e.type === 'touchstart') { startX = e.touches[0].clientX; startY = e.touches[0].clientY; } else { startX = e.clientX; startY = e.clientY; }
            const rect = container.getBoundingClientRect(); initialLeft = rect.left; initialTop = rect.top;
            doc.addEventListener('mousemove', onMouseMove); doc.addEventListener('mouseup', onMouseUp);
            doc.addEventListener('touchmove', onMouseMove, {passive: false}); doc.addEventListener('touchend', onMouseUp);
        }
        function onMouseMove(e) {
            let currentX, currentY;
            if (e.type === 'touchmove') { currentX = e.touches[0].clientX; currentY = e.touches[0].clientY; } else { currentX = e.clientX; currentY = e.clientY; }
            const dx = currentX - startX; const dy = currentY - startY;
            if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                isDragging = true; hasMoved = true; e.preventDefault(); 
                container.style.left = (initialLeft + dx) + 'px'; container.style.top = (initialTop + dy) + 'px'; container.style.bottom = 'auto';
            }
        }
        function onMouseUp(e) {
            doc.removeEventListener('mousemove', onMouseMove); doc.removeEventListener('mouseup', onMouseUp);
            doc.removeEventListener('touchmove', onMouseMove); doc.removeEventListener('touchend', onMouseUp);
            if (hasMoved) { localStorage.setItem('at-left', container.style.left); localStorage.setItem('at-top', container.style.top); }
            setTimeout(() => { isDragging = false; }, 50);
        }
        handle.addEventListener('click', (e) => { if (hasMoved) { e.preventDefault(); } });
        handle.addEventListener('mousedown', onMouseDown); handle.addEventListener('touchstart', onMouseDown, {passive: false});
    }
</script>"""
components.html(draggable_js, height=0, width=0)

@st.cache_data(ttl=300) 
def get_github_last_updated():
    url = "https://api.github.com/repos/baguskantor2209/cek-omset-app/commits?path=BDB_AB4.parquet&page=1&per_page=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                date_str = data[0]['commit']['committer']['date']
                dt_utc = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                tz_wib = pytz.timezone('Asia/Jakarta')
                return dt_utc.astimezone(tz_wib).strftime("%d-%m-%Y %H:%M WIB")
    except Exception: pass
    
    bdb_candidates = ["BDB_AB4.parquet", "BDB AB4.parquet", "BDB_AB4.csv.gz", "BDB_AB4.csv", "BDB_AB4.xlsx"]
    target_bdb = next((f for f in bdb_candidates if os.path.exists(f)), None)
    if target_bdb:
        mtime = os.path.getmtime(target_bdb)
        dt_utc = datetime.fromtimestamp(mtime, tz=timezone.utc)
        return dt_utc.astimezone(pytz.timezone('Asia/Jakarta')).strftime("%d-%m-%Y %H:%M WIB")
    return "Sedang memuat..."

def read_file_fast(file_path):
    if file_path.endswith(".parquet"): return pd.read_parquet(file_path)
    elif file_path.endswith(".csv.gz") or file_path.endswith(".csv"): return pd.read_csv(file_path, engine="python", on_bad_lines="skip", encoding='utf-8', sep=None)
    return pd.read_excel(file_path, engine="openpyxl")

def read_grouping_smart(file_path):
    if file_path.endswith(".parquet"): return pd.read_parquet(file_path)
    elif file_path.endswith(".csv"): return pd.read_csv(file_path, engine="python", on_bad_lines="skip")
    try:
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        sheet_target = next((s for s in xls.sheet_names if s.strip().upper() == "DP"), xls.sheet_names[0])
        df_sheet = pd.read_excel(xls, sheet_name=sheet_target, header=1)
        df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
        if "Kode Customer" not in df_sheet.columns and "KDCUST" not in [c.upper() for c in df_sheet.columns]:
            df_sheet = pd.read_excel(xls, sheet_name=sheet_target, header=0)
            df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
        return df_sheet
    except Exception:
        return pd.read_excel(file_path)

def map_wilayah(depo_str):
    val = str(depo_str).upper()
    if pd.isna(depo_str) or val == "NAN" or val == "": return "LAINNYA"
    banten_codes = ["0819", "0820", "0823", "0910", "0921", "0924"]
    dki_codes = ["0107", "0116", "0117", "0118", "0203", "0204", "0208", "0209"]
    bodebek_codes = ["0301", "0303", "0304", "0310", "0602", "0605", "0622"]
    if any(code in val for code in banten_codes): return "BANTEN"
    if any(code in val for code in dki_codes): return "DKI"
    if any(code in val for code in bodebek_codes): return "BODEBEK"
    return "LAINNYA"

# --- OPTIMASI MEMORI: Pemrosesan Angka yang Hemat RAM ---
@st.cache_data
def load_data_from_github():
    bdb_candidates = ["BDB_AB4.parquet", "BDB AB4.parquet", "BDB_AB4.csv.gz", "BDB_AB4.csv", "BDB_AB4.xlsx"]
    target_bdb = next((f for f in bdb_candidates if os.path.exists(f)), None)
    if not target_bdb: raise FileNotFoundError("Data 'BDB_AB4' tidak ditemukan!")
    
    df_bdb = read_file_fast(target_bdb)
    df_bdb.columns = [str(c).strip() for c in df_bdb.columns]
    
    kd_cust_col = next((c for c in df_bdb.columns if c.lower() in ["kdcust", "kode customer", "kode_customer"]), "kdCust")
    cust_name_col = next((c for c in df_bdb.columns if c.lower() in ["cust", "nama customer", "nama toko"]), "cust")
    
    df_bdb["kdCust_orig"] = df_bdb[kd_cust_col].astype(str).str.strip().str.upper()
    df_bdb["kdCust_clean"] = df_bdb["kdCust_orig"].str.replace("-", "", regex=False).str.replace(" ", "", regex=False).str.replace(".", "", regex=False)
    df_bdb["cust"] = df_bdb[cust_name_col].astype(str).str.strip()
    
    if "depo" in df_bdb.columns:
        df_bdb["depo"] = df_bdb["depo"].astype(str).str.strip()
        df_bdb["wilayah"] = df_bdb["depo"].apply(map_wilayah)
    else:
        df_bdb["wilayah"] = "LAINNYA"

    # HANYA convert kolom yang sudah ada dan gunakan 'downcast' agar hemat RAM 50%
    numeric_suffixes = ["TOR", "UCV", "KTD", "RBL", "UCW", "ISO", "EDV", "CZLSN", "CZKRT", "R3", "R06EXC", "ALK", "ALKREG", "ALKNONREG", "MAA", "HC", "AB4", "AB2", "AB3"]
    bln_list_all = ["RT225", "SM225", "JAN26", "FEB26", "MAR26", "APR26", "MEI26", "JUN26", "JUL26", "AGT26", "SEP26", "OKT26"]
    
    for suf in numeric_suffixes:
        for b in bln_list_all:
            col_name = f"{b}_{suf}"
            if col_name in df_bdb.columns:
                # float32 memakan setengah memori dibanding float64 bawaan Pandas
                df_bdb[col_name] = pd.to_numeric(df_bdb[col_name], errors='coerce', downcast='float').fillna(0.0)

    # Khusus untuk kebutuhan Lintas Divisi, pastikan kolom ini ada (buat dengan float32 agar ringan)
    for d in ['AB2', 'AB3', 'AB4']:
        for p in ['JUL26', 'AGT26', 'SEP26', 'OKT26', 'RT225', 'SM225']:
            c = f"{p}_{d}"
            if c not in df_bdb.columns:
                df_bdb[c] = pd.Series(0.0, index=df_bdb.index, dtype='float32')

    group_candidates = ["Grouping_Toko.parquet", "Grouping_Toko.csv", "Grouping_Toko.xlsx", "Grouping Toko.xlsx"]
    target_group = next((f for f in group_candidates if os.path.exists(f)), None)

    if target_group:
        df_group = read_grouping_smart(target_group)
        col_lookup = {str(c).lower().replace("_", " ").strip(): c for c in df_group.columns}
        col_kd_cust = col_lookup.get("kode customer") or col_lookup.get("kdcust")
        col_kd_pemilik = col_lookup.get("kd tk pemilik") or col_lookup.get("kdtkpemilik")
        col_nm_pemilik = col_lookup.get("nama tk pemilik") or col_lookup.get("namatkpemilik")

        if col_kd_cust and col_kd_pemilik and col_nm_pemilik:
            df_group["clean_kd_cust"] = df_group[col_kd_cust].astype(str).str.strip().str.upper().str.replace("-", "", regex=False).str.replace(" ", "", regex=False).str.replace(".", "", regex=False)
            df_group["clean_kd_pemilik"] = df_group[col_kd_pemilik].astype(str).str.strip().str.upper().str.replace("-", "", regex=False).str.replace(" ", "", regex=False).str.replace(".", "", regex=False)
            df_group["clean_nm_pemilik"] = df_group[col_nm_pemilik].astype(str).str.strip()

            map_pemilik_code = df_group.set_index("clean_kd_cust")["clean_kd_pemilik"].to_dict()
            map_pemilik_name = df_group.set_index("clean_kd_cust")["clean_nm_pemilik"].to_dict()

            df_bdb["Kd_Pemilik"] = df_bdb["kdCust_clean"].map(map_pemilik_code).fillna(df_bdb["kdCust_clean"])
            df_bdb["Nama_Pemilik"] = df_bdb["kdCust_clean"].map(map_pemilik_name).fillna(df_bdb["cust"])
            df_bdb["Is_Group"] = df_bdb["kdCust_clean"].isin(map_pemilik_code)
        else:
            df_bdb["Kd_Pemilik"], df_bdb["Nama_Pemilik"], df_bdb["Is_Group"] = df_bdb["kdCust_clean"], df_bdb["cust"], False
    else:
        df_bdb["Kd_Pemilik"], df_bdb["Nama_Pemilik"], df_bdb["Is_Group"] = df_bdb["kdCust_clean"], df_bdb["cust"], False

    df_bdb["search_code"] = df_bdb["Kd_Pemilik"]
    df_bdb["search_name"] = df_bdb.apply(lambda r: f"{r['Nama_Pemilik']} ( Grouping )" if r["Is_Group"] else r["cust"], axis=1)
    
    return df_bdb

def f_num(val): return f"{val:,.0f}" if val and val != 0 else "-"
def f_dec(val): return f"{val:,.1f}" if val and val != 0 else "-"
def format_month_label(bln_code):
    months_map = { "JAN": "Januari", "FEB": "Februari", "MAR": "Maret", "APR": "April", "MEI": "Mei", "JUN": "Juni", "JUL": "Juli", "AGT": "Agustus", "SEP": "September", "OKT": "Oktober"}
    prefix = str(bln_code)[:3].upper()
    return f"{months_map.get(prefix, prefix)} 2026" if "26" in str(bln_code) else months_map.get(prefix, prefix)

# --- OPTIMASI 2: Aggregasi Cepat (Tanpa apply numeric berulang) ---
def aggregate_store_rows(sub_df):
    first_row = sub_df.iloc[0].copy()
    if len(sub_df) == 1: return first_row
    
    numeric_suffixes = ["TOR", "UCV", "KTD", "RBL", "UCW", "ISO", "EDV", "CZLSN", "CZKRT", "R3", "R06EXC", "ALK", "ALKREG", "ALKNONREG", "MAA", "HC", "AB4"]
    
    # Hanya ambil kolom yang benar-benar ada dan bertipe numerik
    num_cols = [c for c in sub_df.columns if any(c.endswith(f"_{suf}") for suf in numeric_suffixes) and pd.api.types.is_numeric_dtype(sub_df[c])]
    
    # Kalkulasi penjumlahan yang cepat
    sums = sub_df[num_cols].sum()
    for c in num_cols:
        first_row[c] = sums[c]
        
    first_row["cust"] = f"{first_row['Nama_Pemilik']} ( Grouping ) [{len(sub_df)} Toko Cabang]"
    return first_row

def generate_pdf_multi_toko(rows_list, bln_list):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=14, alignment=1, textColor=colors.HexColor("#002060"), spaceAfter=6)
    info_style = ParagraphStyle("InfoStyle", parent=styles["Normal"], fontSize=9, alignment=1, spaceAfter=8)
    headers = ["RT2 25", "SM2 25", "No", "KP", "Satuan", "JAN 26", "FEB 26", "MAR 26", "APR 26", "MEI 26", "JUN 26", "JUL 26", "AGT 26", "SEP 26", "OKT 26"]

    for idx, row in enumerate(rows_list):
        elements.append(Paragraph("<b>DASHBOARD LAPORAN OMSET TOKO</b>", title_style))
        info_text = f"<b>Depo:</b> {row.get('depo', '-')} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Kode Cust:</b> {row.get('search_code', row.get('kdCust_orig', '-'))} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Nama Toko:</b> {row.get('cust', '-')}"
        elements.append(Paragraph(info_text, info_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#002060"), spaceAfter=10))
        table_data = [headers]
        def gv(suf, is_num=True): return [f_num(row.get(f"{b}_{suf}", 0)) if is_num else f_dec(row.get(f"{b}_{suf}", 0)) for b in bln_list]

        rows_config = [
            (f_num(row.get("RT225_TOR",0)), f_num(row.get("SM225_TOR",0)), "1", "TOR", "Krt", gv("TOR", True), "item"),
            (f_num(row.get("RT225_UCV",0)), f_num(row.get("SM225_UCV",0)), "2", "UCV", "Krt", gv("UCV", True), "item"),
            (f_num(row.get("RT225_KTD",0)), f_num(row.get("SM225_KTD",0)), "3", "KTD", "Krt", gv("KTD", True), "item"),
            (f_num(row.get("RT225_RBL",0)), f_num(row.get("SM225_RBL",0)), "4", "RBLGOLD", "Krt", gv("RBL", True), "item"),
            (f_num(row.get("RT225_UCW",0)), f_num(row.get("SM225_UCW",0)), "5", "UCW", "Krt", gv("UCW", True), "item"),
            (f_num(row.get("RT225_ISO",0)), f_num(row.get("SM225_ISO",0)), "6", "ISO", "Krt", gv("ISO", True), "item"),
            (f_dec(row.get("RT225_EDV",0)), f_dec(row.get("SM225_EDV",0)), "", "ENERGY DRINK VITAMIN", "Jt Rp", gv("EDV", False), "cat"),
            (f_num(row.get("RT225_CZLSN",0)), f_num(row.get("SM225_CZLSN",0)), "7", "CZ", "Lsn", gv("CZLSN", True), "item"),
            (f_num(row.get("RT225_CZKRT",0)), f_num(row.get("SM225_CZKRT",0)), "", "CZ", "Krt", gv("CZKRT", True), "item"),
            (f_num(row.get("RT225_R3",0)), f_num(row.get("SM225_R3",0)), "", "R3", "Krt", gv("R3", True), "item"),
            (f_num(row.get("RT225_R06EXC",0)), f_num(row.get("SM225_R06EXC",0)), "", "R06", "Krt", gv("R06EXC", True), "item"),
            (f_num(row.get("RT225_ALK",0)), f_num(row.get("SM225_ALK",0)), "8", "ALK", "Krt", gv("ALK", True), "item"),
            (f_num(row.get("RT225_ALKREG",0)), f_num(row.get("SM225_ALKREG",0)), "", "ALK REG", "Krt", gv("ALKREG", True), "item"),
            (f_num(row.get("RT225_ALKNONREG",0)), f_num(row.get("SM225_ALKNONREG",0)), "", "ALK NON REG", "Krt", gv("ALKNONREG", True), "item"),
            (f_num(row.get("RT225_MAA",0)), f_num(row.get("SM225_MAA",0)), "9", "MAA", "Krt", gv("MAA", True), "item"),
            (f_dec(row.get("RT225_HC",0)), f_dec(row.get("SM225_HC",0)), "", "HOME CARE", "Jt Rp", gv("HC", False), "cat"),
            (f_dec(row.get("RT225_AB4",0)), f_dec(row.get("SM225_AB4",0)), "", "DIVISI AB4", "Jt Rp", gv("AB4", False), "total"),
        ]

        t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00c0f0")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ]

        r_idx = 1
        for rt2, sm2, no, kp, sat, vals, r_type in rows_config:
            table_data.append([rt2, sm2, no, kp, sat] + vals)
            if r_type == "cat": t_style.extend([("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#002060")), ("TEXTCOLOR", (0, r_idx), (-1, r_idx), colors.white), ("FONTNAME", (0, r_idx), (-1, r_idx), "Helvetica-Bold"), ("SPAN", (2, r_idx), (3, r_idx))])
            elif r_type == "total": t_style.extend([("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#d92525")), ("TEXTCOLOR", (0, r_idx), (-1, r_idx), colors.white), ("FONTNAME", (0, r_idx), (-1, r_idx), "Helvetica-Bold"), ("SPAN", (2, r_idx), (3, r_idx))])
            r_idx += 1

        pdf_table = Table(table_data, colWidths=[45, 45, 20, 100, 40] + [42]*10, hAlign="CENTER")
        pdf_table.setStyle(TableStyle(t_style))
        elements.append(pdf_table)
        if idx < len(rows_list) - 1: elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# MAIN APP EXECUTION (ROUTING HALAMAN)
# ==========================================

query_params = st.query_params
page = query_params.get("page", "cek_omset")

if page == "cek_omset":
    # ----------------------------------------------------
    # HALAMAN 1: DASHBOARD CEK OMSET TOKO
    # ----------------------------------------------------
    try:
        st.title("📊 Dashboard Cek Omset Toko")
        st.markdown(
            f"<div style='text-align: right; margin-top: -35px; margin-bottom: 20px; color: #4b5563; font-size: 15px;'>"
            f"🕘 Last Updated : &nbsp;<span style='color: #2563eb; font-weight: bold;'>{get_github_last_updated()}</span>"
            f"</div>", unsafe_allow_html=True
        )
        st.markdown("<hr style='margin-top: -10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

        with st.spinner("⚡ Memuat database & Sinkronisasi Grouping Toko..."):
            df = load_data_from_github()

        if "wilayah" in df.columns:
            list_wilayah = sorted([w for w in df["wilayah"].unique() if w != "LAINNYA"])
            if "LAINNYA" in df["wilayah"].unique(): list_wilayah.append("LAINNYA")
        else: list_wilayah = []
            
        list_wilayah.insert(0, "SEMUA WILAYAH")
        
        st.markdown("<div style='font-size:16px; font-weight:600; color:#1f2937; margin-bottom: 8px;'>🌍 Filter By Wilayah</div>", unsafe_allow_html=True)
        selected_wilayah = st.selectbox("label_wilayah", options=list_wilayah, label_visibility="collapsed")

        if selected_wilayah != "SEMUA WILAYAH": df_filtered = df[df["wilayah"] == selected_wilayah]
        else: df_filtered = df

        st.markdown("<br>", unsafe_allow_html=True)

        toko_df = df_filtered[["search_code", "search_name"]].drop_duplicates()
        toko_options = (toko_df["search_code"].astype(str) + " - " + toko_df["search_name"].astype(str)).unique()

        st.markdown("<div style='font-size:16px; font-weight:600; color:#1f2937; margin-bottom: 8px;'>🔍 Cari Toko</div>", unsafe_allow_html=True)
        selected_tokos = st.multiselect("label_toko", options=list(toko_options), max_selections=5, placeholder="Ketik Kode / Nama Toko (Atau Toko Grouping)...", label_visibility="collapsed")

        bln_list = ["JAN26", "FEB26", "MAR26", "APR26", "MEI26", "JUN26", "JUL26", "AGT26", "SEP26", "OKT26"]

        if selected_tokos:
            selected_rows = []
            for selected_toko in selected_tokos:
                selected_code = selected_toko.split(" - ")[0].strip().upper()
                sub_df = df[df["search_code"].astype(str).str.strip().str.upper() == selected_code]
                
                # Menggunakan agregasi cepat
                row = aggregate_store_rows(sub_df)
                selected_rows.append(row)

                omset_okt26, rt225_ab4 = row.get("OKT26_AB4", 0), row.get("RT225_AB4", 0)
                diff_omset = omset_okt26 - rt225_ab4
                pct_omset = (diff_omset / rt225_ab4 * 100) if rt225_ab4 and rt225_ab4 > 0 else 0
                status_arrow, status_color = ("▲", "#10b981") if diff_omset >= 0 else ("▼", "#ef4444")

                jan_jun_cols = ["JAN26_AB4", "FEB26_AB4", "MAR26_AB4", "APR26_AB4", "MEI26_AB4", "JUN26_AB4"]
                sm1_26_total = sum(float(row.get(m, 0) or 0) for m in jan_jun_cols)
                sm1_26_avg = sm1_26_total / 6.0
                
                diff_sm1 = omset_okt26 - sm1_26_avg
                pct_sm1 = (diff_sm1 / sm1_26_avg * 100) if sm1_26_avg > 0 else 0
                status_arrow_sm1, status_color_sm1 = ("▲", "#10b981") if diff_sm1 >= 0 else ("▼", "#ef4444")

                max_val, max_month_code = -1.0, "OKT26"
                for b in bln_list:
                    val = float(row.get(f"{b}_AB4", 0) or 0)
                    if val > max_val: max_val, max_month_code = val, b

                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"""<div class="metric-card" style="border-left-color: #2563eb;"><div class="metric-title">REAL OMSET OKT 26 DIVISI AB4</div><div class="metric-value">Rp {omset_okt26:,.1f} Jt</div><div class="metric-subtitle" style="color: {status_color};">{status_arrow} {abs(pct_omset):,.1f}% vs RT2 25 ({diff_omset:+,.1f} Jt)</div><div class="metric-subtitle" style="color: {status_color_sm1}; margin-top: 5px;">{status_arrow_sm1} {abs(pct_sm1):,.1f}% vs SM1 26 ({diff_sm1:+,.1f} Jt)</div></div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class="metric-card" style="border-left-color: #06b6d4;"><div class="metric-title">OMSET TERBESAR DIVISI AB4</div><div class="metric-value" style="font-size: 1.25rem;">Puncak Omset Pada Bulan <b>{format_month_label(max_month_code)}</b></div><div class="metric-subtitle" style="color: #06b6d4;">Dengan Jumlah Omset Rp {max_val:,.1f} Jt</div></div>""", unsafe_allow_html=True)

                def fmt_v(suf): return "".join([f"<td>{f_num(row.get(f'{b}_{suf}', 0))}</td>" for b in bln_list])
                def fmt_raw(suf): return "".join([f"<td>{f_dec(row.get(f'{b}_{suf}', 0))}</td>" for b in bln_list])

                table_html = f"""<div class="omset-table-container"><div style="font-size: 14px; font-weight: bold; margin-bottom: 10px;">Depo : <span style="background: #e5e7eb; padding: 3px 8px; border-radius: 4px;">{row.get('depo', '-')}</span><br>Kode Cust : <span style="background: #e5e7eb; padding: 3px 8px; border-radius: 4px;">{row['search_code']}</span><br>Nama Toko : <b>{row['cust']}</b></div><table class="report-table"><thead><tr><th class="blue-header" style="width: 55px;">RT2 25</th><th class="blue-header" style="width: 55px;">SM2 25</th><th style="width: 25px;">No</th><th style="text-align: left;">KP</th><th style="width: 45px;">Satuan</th><th>JAN 26</th><th>FEB 26</th><th>MAR 26</th><th>APR 26</th><th>MEI 26</th><th>JUN 26</th><th>JUL 26</th><th>AGT 26</th><th>SEP 26</th><th>OKT 26</th></tr></thead><tbody><tr><td class="center">{f_num(row.get('RT225_TOR',0))}</td><td class="center">{f_num(row.get('SM225_TOR',0))}</td><td class="center bold-col">1</td><td class="left bold-col">TOR</td><td class="center">Krt</td>{fmt_v('TOR')}</tr><tr><td class="center">{f_num(row.get('RT225_UCV',0))}</td><td class="center">{f_num(row.get('SM225_UCV',0))}</td><td class="center bold-col">2</td><td class="left bold-col">UCV</td><td class="center">Krt</td>{fmt_v('UCV')}</tr><tr><td class="center">{f_num(row.get('RT225_KTD',0))}</td><td class="center">{f_num(row.get('SM225_KTD',0))}</td><td class="center bold-col">3</td><td class="left bold-col">KTD</td><td class="center">Krt</td>{fmt_v('KTD')}</tr><tr><td class="center">{f_num(row.get('RT225_RBL',0))}</td><td class="center">{f_num(row.get('SM225_RBL',0))}</td><td class="center bold-col">4</td><td class="left bold-col">RBLGOLD</td><td class="center">Krt</td>{fmt_v('RBL')}</tr><tr><td class="center">{f_num(row.get('RT225_UCW',0))}</td><td class="center">{f_num(row.get('SM225_UCW',0))}</td><td class="center bold-col">5</td><td class="left bold-col">UCW</td><td class="center">Krt</td>{fmt_v('UCW')}</tr><tr><td class="center">{f_num(row.get('RT225_ISO',0))}</td><td class="center">{f_num(row.get('SM225_ISO',0))}</td><td class="center bold-col">6</td><td class="left bold-col">ISO</td><td class="center">Krt</td>{fmt_v('ISO')}</tr><tr class="row-category"><td class="center">{f_dec(row.get('RT225_EDV',0))}</td><td class="center">{f_dec(row.get('SM225_EDV',0))}</td><td colspan="2" class="left bold-col" style="padding-left:10px;">ENERGY DRINK VITAMIN</td><td class="center">Jt Rp</td>{fmt_raw('EDV')}</tr><tr><td class="center">{f_num(row.get('RT225_CZLSN',0))}</td><td class="center">{f_num(row.get('SM225_CZLSN',0))}</td><td class="center bold-col">7</td><td class="left bold-col">CZ</td><td class="center">Lsn</td>{fmt_v('CZLSN')}</tr><tr><td class="center">{f_num(row.get('RT225_CZKRT',0))}</td><td class="center">{f_num(row.get('SM225_CZKRT',0))}</td><td class="center bold-col"></td><td class="left bold-col">CZ</td><td class="center">Krt</td>{fmt_v('CZKRT')}</tr><tr><td class="center">{f_num(row.get('RT225_R3',0))}</td><td class="center">{f_num(row.get('SM225_R3',0))}</td><td class="center bold-col"></td><td class="left bold-col">R3</td><td class="center">Krt</td>{fmt_v('R3')}</tr><tr><td class="center">{f_num(row.get('RT225_R06EXC',0))}</td><td class="center">{f_num(row.get('SM225_R06EXC',0))}</td><td class="center bold-col"></td><td class="left bold-col">R06</td><td class="center">Krt</td>{fmt_v('R06EXC')}</tr><tr><td class="center">{f_num(row.get('RT225_ALK',0))}</td><td class="center">{f_num(row.get('SM225_ALK',0))}</td><td class="center bold-col">8</td><td class="left bold-col">ALK</td><td class="center">Krt</td>{fmt_v('ALK')}</tr><tr><td class="center">{f_num(row.get('RT225_ALKREG',0))}</td><td class="center">{f_num(row.get('SM225_ALKREG',0))}</td><td class="center bold-col"></td><td class="left bold-col">ALK REG</td><td class="center">Krt</td>{fmt_v('ALKREG')}</tr><tr><td class="center">{f_num(row.get('RT225_ALKNONREG',0))}</td><td class="center">{f_num(row.get('SM225_ALKNONREG',0))}</td><td class="center bold-col"></td><td class="left bold-col">ALK NON REG</td><td class="center">Krt</td>{fmt_v('ALKNONREG')}</tr><tr><td class="center">{f_num(row.get('RT225_MAA',0))}</td><td class="center">{f_num(row.get('SM225_MAA',0))}</td><td class="center bold-col">9</td><td class="left bold-col">MAA</td><td class="center">Krt</td>{fmt_v('MAA')}</tr><tr class="row-category"><td class="center">{f_dec(row.get('RT225_HC',0))}</td><td class="center">{f_dec(row.get('SM225_HC',0))}</td><td colspan="2" class="left bold-col" style="padding-left:10px;">HOME CARE</td><td class="center">Jt Rp</td>{fmt_raw('HC')}</tr><tr class="row-total"><td class="center">{f_dec(row.get('RT225_AB4',0))}</td><td class="center">{f_dec(row.get('SM225_AB4',0))}</td><td colspan="2" class="left bold-col" style="padding-left:10px;">DIVISI AB4</td><td class="center">Jt Rp</td>{fmt_raw('AB4')}</tr></tbody></table></div>"""
                try: st.html(table_html)
                except AttributeError: st.markdown(table_html, unsafe_allow_html=True)

            pdf_bytes = generate_pdf_multi_toko(selected_rows, bln_list)
            st.markdown("<br>", unsafe_allow_html=True)
            col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 1])
            with col_pdf2:
                st.download_button(label=f"📄 Export / Download PDF ({len(selected_tokos)} Toko)", data=pdf_bytes, file_name=f"Laporan_Omset_MultiToko_{len(selected_tokos)}_Toko.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("💡 Silakan ketik atau pilih toko pada pencarian di atas.")

    except Exception as e:
        st.error("🚨 TERJADI KESALAHAN PADA APLIKASI:")
        st.code(traceback.format_exc(), language="bash")

elif page == "lintas_divisi":
    # ----------------------------------------------------
    # HALAMAN 2: TOKO LINTAS DIVISI
    # ----------------------------------------------------
    st.title("🔄 Dashboard Toko Lintas Divisi Belum Transaksi AB4")
    st.markdown("<hr style='margin-top: -10px; margin-bottom: 25px;'>", unsafe_allow_html=True)
    
    with st.spinner("⚡ Memuat database..."):
        df = load_data_from_github()

    # Menyiapkan List Wilayah
    list_wilayah = ["SEMUA WILAYAH"]
    if "wilayah" in df.columns:
        w_opts = sorted([w for w in df["wilayah"].unique() if w != "LAINNYA"])
        list_wilayah.extend(w_opts)
        if "LAINNYA" in df["wilayah"].unique(): list_wilayah.append("LAINNYA")

    # Fungsi Reset Page
    def reset_page_lintas(): st.session_state.page_lintas = 1

    st.markdown("<div style='font-size:16px; font-weight:600; color:#1f2937; margin-bottom: 8px;'>⚙️ Filter Pencarian</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sel_wilayah = st.selectbox("🌍 Filter Wilayah", list_wilayah, on_change=reset_page_lintas)
    with c2: sel_divisi = st.selectbox("🏢 Filter Divisi", ["AB2", "AB3"], on_change=reset_page_lintas)
    with c3: sel_omset = st.selectbox("💰 Filter Omset (Berdasarkan Max Jul-Sep)", ["Semua", "1JT UP", "5JT UP", "10JT UP", "40JT UP"], on_change=reset_page_lintas)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- LOGIKA FILTERING SUPER CEPAT ---
    df_filter = df.copy()

    # 1. Filter Wilayah
    if sel_wilayah != "SEMUA WILAYAH": df_filter = df_filter[df_filter['wilayah'] == sel_wilayah]

    # 2. Belum Transaksi AB4 (JUL-SEP) - Angka sudah numeric dari awal
    df_filter = df_filter[
        (df_filter['JUL26_AB4'] == 0) & 
        (df_filter['AGT26_AB4'] == 0) & 
        (df_filter['SEP26_AB4'] == 0)
    ]

    # 3. Hitung Max Omset Divisi
    df_filter['max_omset'] = df_filter[[f'JUL26_{sel_divisi}', f'AGT26_{sel_divisi}', f'SEP26_{sel_divisi}']].max(axis=1)

    # 4. Limit Omset
    if sel_omset == "1JT UP": df_filter = df_filter[df_filter['max_omset'] >= 1.0]
    elif sel_omset == "5JT UP": df_filter = df_filter[df_filter['max_omset'] >= 5.0]
    elif sel_omset == "10JT UP": df_filter = df_filter[df_filter['max_omset'] >= 10.0]
    elif sel_omset == "40JT UP": df_filter = df_filter[df_filter['max_omset'] >= 40.0]

    # 5. Sorting
    df_filter = df_filter.sort_values(by='max_omset', ascending=False).reset_index(drop=True)

    # --- PAGINATION ---
    if "page_lintas" not in st.session_state: st.session_state.page_lintas = 1
    items_per_page = 25
    total_pages = math.ceil(len(df_filter) / items_per_page) if len(df_filter) > 0 else 1
    if st.session_state.page_lintas > total_pages: st.session_state.page_lintas = 1
    if st.session_state.page_lintas < 1: st.session_state.page_lintas = 1

    start_idx = (st.session_state.page_lintas - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_page = df_filter.iloc[start_idx:end_idx]

    def prev_page(): st.session_state.page_lintas -= 1
    def next_page(): st.session_state.page_lintas += 1

    pg_c1, pg_c2, pg_c3 = st.columns([1, 2, 1])
    with pg_c1: st.button("⬅️ Previous", disabled=(st.session_state.page_lintas <= 1), on_click=prev_page, use_container_width=True)
    with pg_c2: st.markdown(f"<div style='text-align: center; margin-top: 8px; font-weight: bold;'>Halaman {st.session_state.page_lintas} dari {total_pages} (Total: {len(df_filter)} Toko Ditemukan)</div>", unsafe_allow_html=True)
    with pg_c3: st.button("Next ➡️", disabled=(st.session_state.page_lintas >= total_pages), on_click=next_page, use_container_width=True)

    # --- RENDER TABEL HTML ---
    def fmt_val(v): return "-" if v == 0 else f"{v:,.1f}"

    # HILANGKAN SPASI DI AWAL BARIS HTML AGAR TIDAK DIANGGAP CODE BLOCK OLEH MARKDOWN
    thead_html = """<style>
.tbl-ld { width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; margin-top: 15px; margin-bottom: 25px; }
.tbl-ld th, .tbl-ld td { border: 1px solid #111827; padding: 6px 4px; text-align: center; white-space: nowrap; }
.bg-orange { background-color: #FFC000; color: #000; font-weight: 800; }
.bg-yellow { background-color: #FFFF00; color: #000; font-weight: 800; }
.bg-blue { background-color: #00B0F0; color: #000; font-weight: 800; }
.bg-green { background-color: #92D050; color: #000; font-weight: 800; }
.td-left { text-align: left !important; padding-left: 8px !important; }
.tbl-ld tbody tr:nth-child(even) { background-color: #f9fafb; }
.tbl-ld tbody tr:hover { background-color: #e5e7eb; }
</style>
<div style="overflow-x: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
<table class="tbl-ld">
    <thead>
        <tr>
            <th rowspan="2" class="bg-orange">DEPO</th>
            <th rowspan="2" class="bg-orange">KD CUST</th>
            <th rowspan="2" class="bg-orange" style="min-width: 200px;">NAMA CUST</th>
            <th colspan="6" class="bg-yellow">DIVISI AB2</th>
            <th colspan="6" class="bg-orange">DIVISI AB3</th>
            <th colspan="6" class="bg-blue">DIVISI AB4</th>
        </tr>
        <tr>
            <th class="bg-green">RT2 25</th><th class="bg-green">SM2 25</th><th class="bg-yellow">JUL 26</th><th class="bg-yellow">AGT 26</th><th class="bg-yellow">SEP 26</th><th class="bg-yellow">OKT 26</th>
            <th class="bg-green">RT2 25</th><th class="bg-green">SM2 25</th><th class="bg-orange">JUL 26</th><th class="bg-orange">AGT 26</th><th class="bg-orange">SEP 26</th><th class="bg-orange">OKT 26</th>
            <th class="bg-green">RT2 25</th><th class="bg-green">SM2 25</th><th class="bg-blue">JUL 26</th><th class="bg-blue">AGT 26</th><th class="bg-blue">SEP 26</th><th class="bg-blue">OKT 26</th>
        </tr>
    </thead>
    <tbody>"""
    
    tbody_html = ""
    for _, row in df_page.iterrows():
        tbody_html += "<tr>"
        tbody_html += f"<td class='td-left'>{row.get('depo', '-')}</td>"
        tbody_html += f"<td class='td-left'>{row.get('kdCust_orig', '-')}</td>"
        tbody_html += f"<td class='td-left'><b>{row.get('cust', '-')}</b></td>"
        
        tbody_html += f"<td>{fmt_val(row['RT225_AB2'])}</td><td>{fmt_val(row['SM225_AB2'])}</td>"
        tbody_html += f"<td>{fmt_val(row['JUL26_AB2'])}</td><td>{fmt_val(row['AGT26_AB2'])}</td><td>{fmt_val(row['SEP26_AB2'])}</td><td>{fmt_val(row['OKT26_AB2'])}</td>"
        
        tbody_html += f"<td>{fmt_val(row['RT225_AB3'])}</td><td>{fmt_val(row['SM225_AB3'])}</td>"
        tbody_html += f"<td>{fmt_val(row['JUL26_AB3'])}</td><td>{fmt_val(row['AGT26_AB3'])}</td><td>{fmt_val(row['SEP26_AB3'])}</td><td>{fmt_val(row['OKT26_AB3'])}</td>"
        
        tbody_html += f"<td>{fmt_val(row['RT225_AB4'])}</td><td>{fmt_val(row['SM225_AB4'])}</td>"
        tbody_html += f"<td>{fmt_val(row['JUL26_AB4'])}</td><td>{fmt_val(row['AGT26_AB4'])}</td><td>{fmt_val(row['SEP26_AB4'])}</td><td>{fmt_val(row['OKT26_AB4'])}</td>"
        
        tbody_html += "</tr>"
        
    if len(df_page) == 0: tbody_html += "<tr><td colspan='21' style='text-align:center; padding: 30px; font-weight: bold; color: #ef4444;'>TIDAK ADA DATA TOKO YANG MEMENUHI KRITERIA PENCARIAN INI</td></tr>"
    
    tfoot_html = "</tbody></table></div>"
    
    final_table = thead_html + tbody_html + tfoot_html
    try: st.html(final_table)
    except AttributeError: st.markdown(final_table, unsafe_allow_html=True)

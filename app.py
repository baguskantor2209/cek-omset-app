import io
import os
import traceback
import requests
from datetime import datetime, timezone
import pytz
import pandas as pd
import streamlit as st

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
</style>""",
    unsafe_allow_html=True,
)

# --- FUNGSI LAST UPDATED 100% AKURAT DARI GITHUB API ---
@st.cache_data(ttl=300) # Refresh tiap 5 menit
def get_github_last_updated():
    """Tarik waktu aktual BDB_AB4.parquet di-commit ke GitHub"""
    url = "https://api.github.com/repos/baguskantor2209/cek-omset-app/commits?path=BDB_AB4.parquet&page=1&per_page=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Ambil waktu UTC dari GitHub
                date_str = data[0]['commit']['committer']['date']
                dt_utc = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                # Ubah ke WIB
                tz_wib = pytz.timezone('Asia/Jakarta')
                dt_wib = dt_utc.astimezone(tz_wib)
                return dt_wib.strftime("%d-%m-%Y %H:%M WIB")
    except Exception:
        pass
    
    # Fallback jika GitHub sedang error
    return "Sedang memuat..."

# --- TATA LETAK JUDUL & LAST UPDATED YANG RAPI ---
st.title("📊 Dashboard Cek Omset Toko")

st.markdown(
    f"<div style='text-align: right; margin-top: -35px; margin-bottom: 20px; color: #4b5563; font-size: 15px;'>"
    f"🕘 Last Updated: &nbsp;<span style='color: #2563eb; font-weight: bold;'>{get_github_last_updated()}</span>"
    f"</div>", 
    unsafe_allow_html=True
)

st.markdown("<hr style='margin-top: -10px; margin-bottom: 25px;'>", unsafe_allow_html=True)


def read_file_fast(file_path):
    if file_path.endswith(".parquet"):
        return pd.read_parquet(file_path)
    elif file_path.endswith(".csv.gz") or file_path.endswith(".csv"):
        return pd.read_csv(file_path, engine="python", on_bad_lines="skip", encoding='utf-8', sep=None)
    return pd.read_excel(file_path, engine="openpyxl")


def read_grouping_smart(file_path):
    if file_path.endswith(".parquet"):
        return pd.read_parquet(file_path)
    elif file_path.endswith(".csv"):
        return pd.read_csv(file_path, engine="python", on_bad_lines="skip")
    
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
    if pd.isna(depo_str) or val == "NAN" or val == "":
        return "LAINNYA"
        
    banten_codes = ["0819", "0820", "0823", "0910", "0921", "0924"]
    dki_codes = ["0107", "0116", "0117", "0118", "0203", "0204", "0208", "0209"]
    bodebek_codes = ["0301", "0303", "0304", "0310", "0602", "0605", "0622"]
    
    if any(code in val for code in banten_codes): return "BANTEN"
    if any(code in val for code in dki_codes): return "DKI"
    if any(code in val for code in bodebek_codes): return "BODEBEK"
    
    return "LAINNYA"


@st.cache_data
def load_data_from_github():
    bdb_candidates = ["BDB_AB4.parquet", "BDB AB4.parquet", "BDB_AB4.csv.gz", "BDB_AB4.csv", "BDB_AB4.xlsx"]
    target_bdb = next((f for f in bdb_candidates if os.path.exists(f)), None)

    if not target_bdb:
        raise FileNotFoundError("Data 'BDB_AB4' tidak ditemukan!")

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

def f_num(val):
    try:
        val = float(val)
        return f"{val:,.0f}" if val != 0 else "-"
    except: return "-"

def f_dec(val):
    try:
        val = float(val)
        return f"{val:,.1f}" if val != 0 else "-"
    except: return "-"

def format_month_label(bln_code):
    months_map = { "JAN": "Januari", "FEB": "Februari", "MAR": "Maret", "APR": "April", "MEI": "Mei", "JUN": "Juni", "JUL": "Juli", "AGT": "Agustus", "SEP": "September", "OKT": "Oktober"}
    prefix = str(bln_code)[:3].upper()
    return f"{months_map.get(prefix, prefix)} 2026" if "26" in str(bln_code) else months_map.get(prefix, prefix)

def aggregate_store_rows(sub_df, bln_list):
    first_row = sub_df.iloc[0].copy()
    if len(sub_df) == 1: return first_row

    numeric_suffixes = ["TOR", "UCV", "KTD", "RBL", "UCW", "ISO", "EDV", "CZLSN", "CZKRT", "R3", "R06EXC", "ALK", "ALKREG", "ALKNONREG", "MAA", "HC", "AB4"]
    
    for suf in numeric_suffixes:
        if f"RT225_{suf}" in sub_df: first_row[f"RT225_{suf}"] = sub_df[f"RT225_{suf}"].apply(pd.to_numeric, errors="coerce").sum()
        if f"SM225_{suf}" in sub_df: first_row[f"SM225_{suf}"] = sub_df[f"SM225_{suf}"].apply(pd.to_numeric, errors="coerce").sum()

    for b in bln_list:
        for suf in numeric_suffixes:
            if f"{b}_{suf}" in sub_df:
                first_row[f"{b}_{suf}"] = sub_df[f"{b}_{suf}"].apply(pd.to_numeric, errors="coerce").sum()

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
            if r_type == "cat":
                t_style.extend([("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#002060")), ("TEXTCOLOR", (0, r_idx), (-1, r_idx), colors.white), ("FONTNAME", (0, r_idx), (-1, r_idx), "Helvetica-Bold"), ("SPAN", (2, r_idx), (3, r_idx))])
            elif r_type == "total":
                t_style.extend([("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#d92525")), ("TEXTCOLOR", (0, r_idx), (-1, r_idx), colors.white), ("FONTNAME", (0, r_idx), (-1, r_idx), "Helvetica-Bold"), ("SPAN", (2, r_idx), (3, r_idx))])
            r_idx += 1

        pdf_table = Table(table_data, colWidths=[45, 45, 20, 100, 40] + [42]*10, hAlign="CENTER")
        pdf_table.setStyle(TableStyle(t_style))
        elements.append(pdf_table)

        if idx < len(rows_list) - 1: elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- MAIN APP EXECUTION ---
try:
    with st.spinner("⚡ Memuat database & Sinkronisasi Grouping Toko..."):
        df = load_data_from_github()

    # === 1. FILTER BERJENJANG: WILAYAH (BANTEN, DKI, BODEBEK) ===
    if "wilayah" in df.columns:
        list_wilayah = sorted([w for w in df["wilayah"].unique() if w != "LAINNYA"])
        if "LAINNYA" in df["wilayah"].unique():
            list_wilayah.append("LAINNYA")
    else:
        list_wilayah = []
        
    list_wilayah.insert(0, "SEMUA WILAYAH")
    
    selected_wilayah = st.selectbox(
        "🌍 Filter By Wilayah", 
        options=list_wilayah,
        help="Pilih wilayah (DKI/BANTEN/BODEBEK) untuk mengurangi daftar toko di bawah, sehingga ketikan tidak nge-lag."
    )

    if selected_wilayah != "SEMUA WILAYAH":
        df_filtered = df[df["wilayah"] == selected_wilayah]
    else:
        df_filtered = df

    # === 2. FILTER BERJENJANG: TOKO ===
    toko_df = df_filtered[["search_code", "search_name"]].drop_duplicates()
    toko_options = (toko_df["search_code"].astype(str) + " - " + toko_df["search_name"].astype(str)).unique()

    selected_tokos = st.multiselect(
        "🔍 Cari Toko", 
        options=list(toko_options), 
        max_selections=5,
        placeholder="Ketik Kode / Nama Toko (Atau Toko Grouping)...",
    )

    bln_list = ["JAN26", "FEB26", "MAR26", "APR26", "MEI26", "JUN26", "JUL26", "AGT26", "SEP26", "OKT26"]

    if selected_tokos:
        selected_rows = []
        for selected_toko in selected_tokos:
            selected_code = selected_toko.split(" - ")[0].strip().upper()
            sub_df = df[df["search_code"].astype(str).str.strip().str.upper() == selected_code]
            row = aggregate_store_rows(sub_df, bln_list)
            selected_rows.append(row)

            # METRIK 1: vs RT2 25
            omset_okt26, rt225_ab4 = row.get("OKT26_AB4", 0), row.get("RT225_AB4", 0)
            diff_omset = omset_okt26 - rt225_ab4
            pct_omset = (diff_omset / rt225_ab4 * 100) if rt225_ab4 and rt225_ab4 > 0 else 0
            status_arrow, status_color = ("▲", "#10b981") if diff_omset >= 0 else ("▼", "#ef4444")

            # METRIK 2: vs SM1 26 (Rata Rata JAN - JUN)
            jan_jun_cols = ["JAN26_AB4", "FEB26_AB4", "MAR26_AB4", "APR26_AB4", "MEI26_AB4", "JUN26_AB4"]
            sm1_26_total = sum(float(row.get(m, 0) or 0) for m in jan_jun_cols)
            sm1_26_avg = sm1_26_total / 6.0
            
            diff_sm1 = omset_okt26 - sm1_26_avg
            pct_sm1 = (diff_sm1 / sm1_26_avg * 100) if sm1_26_avg > 0 else 0
            status_arrow_sm1, status_color_sm1 = ("▲", "#10b981") if diff_sm1 >= 0 else ("▼", "#ef4444")

            # Hitung Omset Terbesar
            max_val, max_month_code = -1.0, "OKT26"
            for b in bln_list:
                val = float(row.get(f"{b}_AB4", 0) or 0)
                if val > max_val: max_val, max_month_code = val, b

            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"""
<div class="metric-card" style="border-left-color: #2563eb;">
    <div class="metric-title">REAL OMSET OKT 26 DIVISI AB4</div>
    <div class="metric-value">Rp {omset_okt26:,.1f} Jt</div>
    <div class="metric-subtitle" style="color: {status_color};">
        {status_arrow} {abs(pct_omset):,.1f}% vs RT2 25 ({diff_omset:+,.1f} Jt)
    </div>
    <div class="metric-subtitle" style="color: {status_color_sm1}; margin-top: 5px;">
        {status_arrow_sm1} {abs(pct_sm1):,.1f}% vs SM1 26 ({diff_sm1:+,.1f} Jt)
    </div>
</div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="metric-card" style="border-left-color: #06b6d4;"><div class="metric-title">OMSET TERBESAR DIVISI AB4</div><div class="metric-value" style="font-size: 1.25rem;">Puncak Omset Pada Bulan <b>{format_month_label(max_month_code)}</b></div><div class="metric-subtitle" style="color: #06b6d4;">Dengan Jumlah Omset Rp {max_val:,.1f} Jt</div></div>""", unsafe_allow_html=True)

            def fmt_v(suf): return "".join([f"<td>{f_num(row.get(f'{b}_{suf}', 0))}</td>" for b in bln_list])
            def fmt_raw(suf): return "".join([f"<td>{f_dec(row.get(f'{b}_{suf}', 0))}</td>" for b in bln_list])

            table_html = f"""<div class="omset-table-container"><div style="font-size: 14px; font-weight: bold; margin-bottom: 10px;">Depo : <span style="background: #e5e7eb; padding: 3px 8px; border-radius: 4px;">{row.get('depo', '-')}</span><br>Kode Cust : <span style="background: #e5e7eb; padding: 3px 8px; border-radius: 4px;">{row['search_code']}</span><br>Nama Toko : <b>{row['cust']}</b></div>
<table class="report-table"><thead><tr><th class="blue-header" style="width: 55px;">RT2 25</th><th class="blue-header" style="width: 55px;">SM2 25</th><th style="width: 25px;">No</th><th style="text-align: left;">KP</th><th style="width: 45px;">Satuan</th><th>JAN 26</th><th>FEB 26</th><th>MAR 26</th><th>APR 26</th><th>MEI 26</th><th>JUN 26</th><th>JUL 26</th><th>AGT 26</th><th>SEP 26</th><th>OKT 26</th></tr></thead><tbody>
<tr><td class="center">{f_num(row.get('RT225_TOR',0))}</td><td class="center">{f_num(row.get('SM225_TOR',0))}</td><td class="center bold-col">1</td><td class="left bold-col">TOR</td><td class="center">Krt</td>{fmt_v('TOR')}</tr>
<tr><td class="center">{f_num(row.get('RT225_UCV',0))}</td><td class="center">{f_num(row.get('SM225_UCV',0))}</td><td class="center bold-col">2</td><td class="left bold-col">UCV</td><td class="center">Krt</td>{fmt_v('UCV')}</tr>
<tr><td class="center">{f_num(row.get('RT225_KTD',0))}</td><td class="center">{f_num(row.get('SM225_KTD',0))}</td><td class="center bold-col">3</td><td class="left bold-col">KTD</td><td class="center">Krt</td>{fmt_v('KTD')}</tr>
<tr><td class="center">{f_num(row.get('RT225_RBL',0))}</td><td class="center">{f_num(row.get('SM225_RBL',0))}</td><td class="center bold-col">4</td><td class="left bold-col">RBLGOLD</td><td class="center">Krt</td>{fmt_v('RBL')}</tr>
<tr><td class="center">{f_num(row.get('RT225_UCW',0))}</td><td class="center">{f_num(row.get('SM225_UCW',0))}</td><td class="center bold-col">5</td><td class="left bold-col">UCW</td><td class="center">Krt</td>{fmt_v('UCW')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ISO',0))}</td><td class="center">{f_num(row.get('SM225_ISO',0))}</td><td class="center bold-col">6</td><td class="left bold-col">ISO</td><td class="center">Krt</td>{fmt_v('ISO')}</tr>
<tr class="row-category"><td class="center">{f_dec(row.get('RT225_EDV',0))}</td><td class="center">{f_dec(row.get('SM225_EDV',0))}</td><td colspan="2" class="left bold-col" style="padding-left:10px;">ENERGY DRINK VITAMIN</td><td class="center">Jt Rp</td>{fmt_raw('EDV')}</tr>
<tr><td class="center">{f_num(row.get('RT225_CZLSN',0))}</td><td class="center">{f_num(row.get('SM225_CZLSN',0))}</td><td class="center bold-col">7</td><td class="left bold-col">CZ</td><td class="center">Lsn</td>{fmt_v('CZLSN')}</tr>
<tr><td class="center">{f_num(row.get('RT225_CZKRT',0))}</td><td class="center">{f_num(row.get('SM225_CZKRT',0))}</td><td class="center bold-col"></td><td class="left bold-col">CZ</td><td class="center">Krt</td>{fmt_v('CZKRT')}</tr>
<tr><td class="center">{f_num(row.get('RT225_R3',0))}</td><td class="center">{f_num(row.get('SM225_R3',0))}</td><td class="center bold-col"></td><td class="left bold-col">R3</td><td class="center">Krt</td>{fmt_v('R3')}</tr>
<tr><td class="center">{f_num(row.get('RT225_R06EXC',0))}</td><td class="center">{f_num(row.get('SM225_R06EXC',0))}</td><td class="center bold-col"></td><td class="left bold-col">R06</td><td class="center">Krt</td>{fmt_v('R06EXC')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ALK',0))}</td><td class="center">{f_num(row.get('SM225_ALK',0))}</td><td class="center bold-col">8</td><td class="left bold-col">ALK</td><td class="center">Krt</td>{fmt_v('ALK')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ALKREG',0))}</td><td class="center">{f_num(row.get('SM225_ALKREG',0))}</td><td class="center bold-col"></td><td class="left bold-col">ALK REG</td><td class="center">Krt</td>{fmt_v('ALKREG')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ALKNONREG',0))}</td><td class="center">{f_num(row.get('SM225_ALKNONREG',0))}</td><td class="center bold-col"></td><td class="left bold-col">ALK NON REG</td><td class="center">Krt</td>{fmt_v('ALKNONREG')}</tr>
<tr><td class="center">{f_num(row.get('RT225_MAA',0))}</td><td class="center">{f_num(row.get('SM225_MAA',0))}</td><td class="center bold-col">9</td><td class="left bold-col">MAA</td><td class="center">Krt</td>{fmt_v('MAA')}</tr>
<tr class="row-category"><td class="center">{f_dec(row.get('RT225_HC',0))}</td><td class="center">{f_dec(row.get('SM225_HC',0))}</td><td colspan="2" class="left bold-col" style="padding-left:10px;">HOME CARE</td><td class="center">Jt Rp</td>{fmt_raw('HC')}</tr>
<tr class="row-total"><td class="center">{f_dec(row.get('RT225_AB4',0))}</td><td class="center">{f_dec(row.get('SM225_AB4',0))}</td><td colspan="2" class="left bold-col" style="padding-left:10px;">DIVISI AB4</td><td class="center">Jt Rp</td>{fmt_raw('AB4')}</tr>
</tbody></table></div>"""
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
    st.warning("☝ Silakan screenshot kotak merah di atas dan kirimkan agar bisa diperbaiki persis di titik kerusakannya.")

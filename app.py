import io
import os
import pandas as pd

# Library untuk Export PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)
import streamlit as st

st.set_page_config(
    page_title="Dashboard Cek Omset Toko", layout="wide", page_icon="📊"
)

# Custom CSS: Sembunyikan Watermark / Footer / Header / Badge Streamlit Cloud di HP & Desktop
st.markdown(
    """<style>
/* 1. Sembunyikan Header Atas & Menus */
header { visibility: hidden !important; height: 0px !important; display: none !important; }
#MainMenu { visibility: hidden !important; display: none !important; }
.stAppToolbar { display: none !important; visibility: hidden !important; }

/* 2. Sembunyikan Footer, Watermark "Hosted with Streamlit" & "Created by" di HP & PC */
footer { visibility: hidden !important; height: 0px !important; display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { visibility: hidden !important; display: none !important; }
[data-testid="stViewerBadge"] { display: none !important; visibility: hidden !important; }
.viewerBadge_container__13vls { display: none !important; }
div[class*="viewerBadge"] { display: none !important; visibility: hidden !important; }
div[class*="styles_viewerBadge"] { display: none !important; visibility: hidden !important; }
div[class*="Profile"] { display: none !important; }
iframe[title="streamlit_app"] { bottom: 0 !important; }

/* 3. Style Tampilan Dashboard */
.stApp { background-color: #f8f9fa; color: #111827; }

/* Custom Styling Tombol Download PDF (Biru Terang & Teks Putih Tebal) */
div.stDownloadButton > button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 12px 24px !important;
    font-size: 14px !important;
    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
    transition: all 0.3s ease !important;
}
div.stDownloadButton > button:hover {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    box-shadow: 0 6px 12px rgba(29, 78, 216, 0.3) !important;
}
div.stDownloadButton > button p {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Metric Cards */
.metric-card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    border-left: 5px solid #2563eb;
    margin-bottom: 12px;
}
.metric-title { color: #4b5563; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }
.metric-value { color: #1e3a8a; font-size: 1.6rem; font-weight: 800; margin: 4px 0; }
.metric-subtitle { font-size: 0.85rem; font-weight: 600; }

/* Table Container & Responsiveness */
.omset-table-container {
    background: #ffffff;
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    margin-top: 15px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
.report-table {
    width: 100%;
    min-width: 750px;
    border-collapse: collapse;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    color: #111827;
}
.report-table th {
    background-color: #00c0f0;
    color: #000000;
    font-weight: 700;
    text-align: center;
    padding: 8px 4px;
    border: 1px solid #bce8f1;
    white-space: nowrap;
}
.report-table th.blue-header { background-color: #002060; color: #ffffff; }
.report-table td {
    padding: 6px 8px;
    border: 1px solid #d1d5db;
    text-align: right;
    color: #111827;
    background-color: #ffffff;
    white-space: nowrap;
}
.report-table td.center { text-align: center; }
.report-table td.left { text-align: left; font-weight: 600; }
.report-table td.bold-col { font-weight: 700 !important; }

/* Dynamic Row Colors */
.row-category { background-color: #002060 !important; color: #ffffff !important; font-weight: bold; }
.row-category td { background-color: #002060 !important; color: #ffffff !important; border-color: #001040 !important; }
.row-total { background-color: #d92525 !important; color: #ffffff !important; font-weight: bold; }
.row-total td { background-color: #d92525 !important; color: #ffffff !important; border-color: #b01010 !important; }
.row-ab23 { background-color: #800000 !important; color: #ffffff !important; font-weight: bold; }
.row-ab23 td { background-color: #800000 !important; color: #ffffff !important; border-color: #500000 !important; }

/* Media Query Khusus Layar HP */
@media (max-width: 768px) {
    .metric-value { font-size: 1.3rem; }
    .omset-table-container { padding: 10px; }
    .report-table { font-size: 11px; }
    .report-table th, .report-table td { padding: 5px 4px; }
}
</style>""",
    unsafe_allow_html=True,
)

st.title("📊 Dashboard Cek Omset & KP Toko")


# Helper pembaca CSV pintar (tahan berbagai delimiter & encoding)
def read_file_fast(file_path):
    if file_path.endswith(".csv.gz") or file_path.endswith(".csv"):
        for enc in ["utf-8", "latin-1", "cp1252"]:
            for sep in [None, ",", ";", "\t"]:
                try:
                    if sep is None:
                        return pd.read_csv(
                            file_path,
                            encoding=enc,
                            engine="python",
                            on_bad_lines="skip",
                        )
                    else:
                        return pd.read_csv(
                            file_path,
                            encoding=enc,
                            sep=sep,
                            engine="python",
                            on_bad_lines="skip",
                        )
                except Exception:
                    continue
    return pd.read_excel(file_path, engine="openpyxl")


@st.cache_data
def load_data_from_github():
    file_div_path, file_kp_path = None, None

    div_candidates = [
        "DIV_BDB_TEST.csv.gz",
        "DIV BDB TEST.csv.gz",
        "DIV_BDB_TEST.csv",
        "DIV BDB TEST.csv",
        "DIV_BDB_TEST.xlsx",
        "DIV BDB TEST.xlsx",
    ]
    kp_candidates = [
        "KP_BDB_TEST.csv.gz",
        "KP BDB TEST.csv.gz",
        "KP_BDB_TEST.csv",
        "KP BDB TEST.csv",
        "KP_BDB_TEST.xlsx",
        "KP BDB TEST.xlsx",
    ]

    for f in div_candidates:
        if os.path.exists(f):
            file_div_path = f
            break
    for f in kp_candidates:
        if os.path.exists(f):
            file_kp_path = f
            break

    if not file_div_path or not file_kp_path:
        raise FileNotFoundError("File database tidak ditemukan di GitHub.")

    df_div = read_file_fast(file_div_path)
    df_kp = read_file_fast(file_kp_path)

    cols_to_use = df_kp.columns.difference(df_div.columns).tolist()
    cols_to_use.append("kdCust")
    return pd.merge(df_div, df_kp[cols_to_use], on="kdCust", how="inner")


# Helper Format Angka: Jika 0 / 0.0 diubah jadi '-'
def f_num(val):
    try:
        val = float(val)
        return f"{val:,.0f}" if val != 0 else "-"
    except (ValueError, TypeError):
        return "-"


def f_dec(val):
    try:
        val = float(val)
        return f"{val:,.1f}" if val != 0 else "-"
    except (ValueError, TypeError):
        return "-"


# Fungsi Generate PDF Landscape & Center
def generate_pdf_landscape(row, bln_list):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=16,
        alignment=1,  # Center
        textColor=colors.HexColor("#002060"),
        spaceAfter=10,
    )

    info_style = ParagraphStyle(
        "InfoStyle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=1,  # Center
        spaceAfter=12,
    )

    elements.append(
        Paragraph("<b>DASHBOARD LAPORAN OMSET & KP TOKO</b>", title_style)
    )

    depo_str = str(row.get("depo", "-"))
    cust_code = str(row.get("kdCust", "-"))
    cust_name = str(row.get("cust", "-"))

    info_text = f"<b>Depo:</b> {depo_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Kode Cust:</b> {cust_code} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Nama Toko:</b> {cust_name}"
    elements.append(Paragraph(info_text, info_style))
    elements.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#002060"),
            spaceAfter=15,
        )
    )

    headers = [
        "RT2 25",
        "SM2 25",
        "No",
        "KP",
        "Satuan",
        "JAN 26",
        "FEB 26",
        "MAR 26",
        "APR 26",
        "MEI 26",
        "JUN 26",
        "JUL 26",
        "AGT 26",
        "SEP 26",
    ]

    table_data = [headers]

    def get_v_list(suffix, is_num=True):
        return [
            f_num(row.get(f"{b}_{suffix}", 0))
            if is_num
            else f_dec(row.get(f"{b}_{suffix}", 0))
            for b in bln_list
        ]

    rows_config = [
        (
            f_num(row.get("RT225_TOR", 0)),
            f_num(row.get("SM225_TOR", 0)),
            "1",
            "TOR",
            "Krt",
            get_v_list("TOR", True),
            "item",
        ),
        (
            f_num(row.get("RT225_UCV", 0)),
            f_num(row.get("SM225_UCV", 0)),
            "2",
            "UCV",
            "Krt",
            get_v_list("UCV", True),
            "item",
        ),
        (
            f_num(row.get("RT225_KTD", 0)),
            f_num(row.get("SM225_KTD", 0)),
            "3",
            "KTD",
            "Krt",
            get_v_list("KTD", True),
            "item",
        ),
        (
            f_num(row.get("RT225_RBL", 0)),
            f_num(row.get("SM225_RBL", 0)),
            "4",
            "RBLGOLD",
            "Krt",
            get_v_list("RBL", True),
            "item",
        ),
        (
            f_num(row.get("RT225_UCW", 0)),
            f_num(row.get("SM225_UCW", 0)),
            "5",
            "UCW",
            "Krt",
            get_v_list("UCW", True),
            "item",
        ),
        (
            f_num(row.get("RT225_ISO", 0)),
            f_num(row.get("SM225_ISO", 0)),
            "6",
            "ISO",
            "Krt",
            get_v_list("ISO", True),
            "item",
        ),
        (
            f_dec(row.get("RT225_EDV", 0)),
            f_dec(row.get("SM225_EDV", 0)),
            "",
            "ENERGY DRINK VITAMIN",
            "Jt Rp",
            get_v_list("EDV", False),
            "cat",
        ),
        (
            f_num(row.get("RT225_CZLSN", 0)),
            f_num(row.get("SM225_CZLSN", 0)),
            "7",
            "CZ",
            "Lsn",
            get_v_list("CZLSN", True),
            "item",
        ),
        (
            f_num(row.get("RT225_CZKRT", 0)),
            f_num(row.get("SM225_CZKRT", 0)),
            "",
            "CZ",
            "Krt",
            get_v_list("CZKRT", True),
            "item",
        ),
        (
            f_num(row.get("RT225_R3", 0)),
            f_num(row.get("SM225_R3", 0)),
            "",
            "R3",
            "Krt",
            get_v_list("R3", True),
            "item",
        ),
        (
            f_num(row.get("RT225_R06EXC", 0)),
            f_num(row.get("SM225_R06EXC", 0)),
            "",
            "R06",
            "Krt",
            get_v_list("R06EXC", True),
            "item",
        ),
        (
            f_num(row.get("RT225_ALK", 0)),
            f_num(row.get("SM225_ALK", 0)),
            "8",
            "ALK",
            "Krt",
            get_v_list("ALK", True),
            "item",
        ),
        (
            f_num(row.get("RT225_ALKREG", 0)),
            f_num(row.get("SM225_ALKREG", 0)),
            "",
            "ALK REG",
            "Krt",
            get_v_list("ALKREG", True),
            "item",
        ),
        (
            f_num(row.get("RT225_ALKNONREG", 0)),
            f_num(row.get("SM225_ALKNONREG", 0)),
            "",
            "ALK NON REG",
            "Krt",
            get_v_list("ALKNONREG", True),
            "item",
        ),
        (
            f_num(row.get("RT225_MAA", 0)),
            f_num(row.get("SM225_MAA", 0)),
            "9",
            "MAA",
            "Krt",
            get_v_list("MAA", True),
            "item",
        ),
        (
            f_dec(row.get("RT225_HC", 0)),
            f_dec(row.get("SM225_HC", 0)),
            "",
            "HOME CARE",
            "Jt Rp",
            get_v_list("HC", False),
            "cat",
        ),
        (
            f_dec(row.get("RT225_AB4", 0)),
            f_dec(row.get("SM225_AB4", 0)),
            "",
            "DIVISI AB4",
            "Jt Rp",
            get_v_list("AB4", False),
            "total",
        ),
        (
            f_dec(row.get("RT225_AB2", 0)),
            f_dec(row.get("SM225_AB2", 0)),
            "",
            "DIVISI AB2",
            "Jt Rp",
            get_v_list("AB2", False),
            "ab23",
        ),
        (
            f_dec(row.get("RT225_AB3", 0)),
            f_dec(row.get("SM225_AB3", 0)),
            "",
            "DIVISI AB3",
            "Jt Rp",
            get_v_list("AB3", False),
            "ab23",
        ),
    ]

    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00c0f0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
    ]

    r_idx = 1
    for rt2, sm2, no, kp, sat, vals, r_type in rows_config:
        table_data.append([rt2, sm2, no, kp, sat] + vals)
        if r_type == "cat":
            t_style.append(
                (
                    "BACKGROUND",
                    (0, r_idx),
                    (-1, r_idx),
                    colors.HexColor("#002060"),
                )
            )
            t_style.append(
                ("TEXTCOLOR", (0, r_idx), (-1, r_idx), colors.white)
            )
            t_style.append(
                ("FONTNAME", (0, r_idx), (-1, r_idx), "Helvetica-Bold")
            )
            t_style.append(("SPAN", (2, r_idx), (3, r_idx)))
        elif r_type == "total":
            t_style.append(
                (
                    "BACKGROUND",
                    (0, r_idx),
                    (-1, r_idx),
                    colors.HexColor("#d92525"),
                )
            )
            t_style.append(
                ("TEXTCOLOR", (0, r_idx), (-1, r_idx), colors.white)
            )
            t_style.append(
                ("FONTNAME", (0, r_idx), (-1, r_idx), "Helvetica-Bold")
            )
            t_style.append(("SPAN", (2, r_idx), (3, r_idx)))
        elif r_type == "ab23":
            t_style.append(
                (
                    "BACKGROUND",
                    (0, r_idx),
                    (-1, r_idx),
                    colors.HexColor("#800000"),
                )
            )
            t_style.append(
                ("TEXTCOLOR", (0, r_idx), (-1, r_idx), colors.white)
            )
            t_style.append(
                ("FONTNAME", (0, r_idx), (-1, r_idx), "Helvetica-Bold")
            )
            t_style.append(("SPAN", (2, r_idx), (3, r_idx)))

        r_idx += 1

    col_widths = [50, 50, 25, 110, 45] + [48] * 9
    pdf_table = Table(table_data, colWidths=col_widths, hAlign="CENTER")
    pdf_table.setStyle(TableStyle(t_style))

    elements.append(pdf_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


try:
    with st.spinner("⚡ Memuat data..."):
        df = load_data_from_github()

    toko_options = (
        df["kdCust"].astype(str) + " - " + df["cust"].astype(str)
    ).unique()

    selected_toko = st.selectbox(
        "🔍 CARI NAMA TOKO / KODE CUSTOMER:",
        options=list(toko_options),
        index=None,
        placeholder="Ketik Kode / Nama Toko Disini...",
        help="Ketik kode customer atau nama toko untuk memfilter secara langsung.",
    )

    if selected_toko:
        selected_code = selected_toko.split(" - ")[0]
        row = df[df["kdCust"].astype(str) == str(selected_code)].iloc[0]

        omset_sep26 = row.get("SEP26_AB4", 0)
        rt225_ab4 = row.get("RT225_AB4", 0)
        diff_omset = omset_sep26 - rt225_ab4
        pct_omset = (
            (diff_omset / rt225_ab4 * 100)
            if rt225_ab4 and rt225_ab4 > 0
            else 0
        )
        status_arrow = "▲" if diff_omset >= 0 else "▼"
        status_color = "#10b981" if diff_omset >= 0 else "#ef4444"

        # Hitung kontributor terbesar dinamis antar divisi
        div_sums = {
            "DIVISI AB4": sum(
                [
                    float(row.get(f"{b}_AB4", 0) or 0)
                    for b in [
                        "JAN26",
                        "FEB26",
                        "MAR26",
                        "APR26",
                        "MEI26",
                        "JUN26",
                        "JUL26",
                        "AGT26",
                        "SEP26",
                    ]
                ]
            ),
            "DIVISI AB2": sum(
                [
                    float(row.get(f"{b}_AB2", 0) or 0)
                    for b in [
                        "JAN26",
                        "FEB26",
                        "MAR26",
                        "APR26",
                        "MEI26",
                        "JUN26",
                        "JUL26",
                        "AGT26",
                        "SEP26",
                    ]
                ]
            ),
            "DIVISI AB3": sum(
                [
                    float(row.get(f"{b}_AB3", 0) or 0)
                    for b in [
                        "JAN26",
                        "FEB26",
                        "MAR26",
                        "APR26",
                        "MEI26",
                        "JUN26",
                        "JUL26",
                        "AGT26",
                        "SEP26",
                    ]
                ]
            ),
        }
        top_div = max(div_sums, key=div_sums.get)

        # Metric Cards
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.markdown(
                f"""<div class="metric-card" style="border-left-color: #2563eb;">
<div class="metric-title">REAL OMSET SEP 26 DIVISI AB4</div>
<div class="metric-value">Rp {omset_sep26:,.1f} Jt</div>
<div class="metric-subtitle" style="color: {status_color};">
{status_arrow} {abs(pct_omset):,.1f}% vs RT2 25 ({diff_omset:+,.1f} Jt)
</div>
</div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""<div class="metric-card" style="border-left-color: #9333ea;">
<div class="metric-title">KONTRIBUTOR OMSET TERBESAR DIVISI</div>
<div class="metric-value">{top_div}</div>
<div class="metric-subtitle" style="color: #9333ea;">Penyumbang Omset Utama</div>
</div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """<div class="metric-card" style="border-left-color: #06b6d4;">
<div class="metric-title">KATEGORI KONTRIBUTOR TERTINGGI</div>
<div class="metric-value" style="font-size: 1.3rem;">ENERGY DRINK VITAMIN</div>
<div class="metric-subtitle" style="color: #06b6d4;">Volume Penjualan Terbesar</div>
</div>""",
                unsafe_allow_html=True,
            )

        bln_list = [
            "JAN26",
            "FEB26",
            "MAR26",
            "APR26",
            "MEI26",
            "JUN26",
            "JUL26",
            "AGT26",
            "SEP26",
        ]

        def fmt_v(suffix):
            tds = ""
            for b in bln_list:
                tds += f"<td>{f_num(row.get(f'{b}_{suffix}', 0))}</td>"
            return tds

        def fmt_raw(suffix):
            tds = ""
            for b in bln_list:
                tds += f"<td>{f_dec(row.get(f'{b}_{suffix}', 0))}</td>"
            return tds

        table_html = f"""<div class="omset-table-container">
<div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; line-height: 1.6;">
Depo : <span style="background: #e5e7eb; padding: 3px 8px; border-radius: 4px;">{row.get('depo', '-')}</span><br>
Kode Cust : <span style="background: #e5e7eb; padding: 3px 8px; border-radius: 4px;">{row['kdCust']}</span><br>
Nama Toko : <b>{row['cust']}</b>
</div>
<table class="report-table">
<thead>
<tr>
<th class="blue-header" style="width: 55px;">RT2 25</th>
<th class="blue-header" style="width: 55px;">SM2 25</th>
<th style="width: 25px;">No</th>
<th style="text-align: left;">KP</th>
<th style="width: 45px;">Satuan</th>
<th>JAN 26</th><th>FEB 26</th><th>MAR 26</th><th>APR 26</th>
<th>MEI 26</th><th>JUN 26</th><th>JUL 26</th><th>AGT 26</th><th>SEP 26</th>
</tr>
</thead>
<tbody>
<tr><td class="center">{f_num(row.get('RT225_TOR',0))}</td><td class="center">{f_num(row.get('SM225_TOR',0))}</td><td class="center bold-col">1</td><td class="left bold-col">TOR</td><td class="center">Krt</td>{fmt_v('TOR')}</tr>
<tr><td class="center">{f_num(row.get('RT225_UCV',0))}</td><td class="center">{f_num(row.get('SM225_UCV',0))}</td><td class="center bold-col">2</td><td class="left bold-col">UCV</td><td class="center">Krt</td>{fmt_v('UCV')}</tr>
<tr><td class="center">{f_num(row.get('RT225_KTD',0))}</td><td class="center">{f_num(row.get('SM225_KTD',0))}</td><td class="center bold-col">3</td><td class="left bold-col">KTD</td><td class="center">Krt</td>{fmt_v('KTD')}</tr>
<tr><td class="center">{f_num(row.get('RT225_RBL',0))}</td><td class="center">{f_num(row.get('SM225_RBL',0))}</td><td class="center bold-col">4</td><td class="left bold-col">RBLGOLD</td><td class="center">Krt</td>{fmt_v('RBL')}</tr>
<tr><td class="center">{f_num(row.get('RT225_UCW',0))}</td><td class="center">{f_num(row.get('SM225_UCW',0))}</td><td class="center bold-col">5</td><td class="left bold-col">UCW</td><td class="center">Krt</td>{fmt_v('UCW')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ISO',0))}</td><td class="center">{f_num(row.get('SM225_ISO',0))}</td><td class="center bold-col">6</td><td class="left bold-col">ISO</td><td class="center">Krt</td>{fmt_v('ISO')}</tr>

<!-- SUB-TOTAL ENERGY DRINK -->
<tr class="row-category">
<td class="center">{f_dec(row.get('RT225_EDV',0))}</td><td class="center">{f_dec(row.get('SM225_EDV',0))}</td>
<td colspan="2" class="left bold-col" style="padding-left:10px;">ENERGY DRINK VITAMIN</td><td class="center">Jt Rp</td>
{fmt_raw('EDV')}
</tr>

<!-- HOME CARE -->
<tr><td class="center">{f_num(row.get('RT225_CZLSN',0))}</td><td class="center">{f_num(row.get('SM225_CZLSN',0))}</td><td class="center bold-col">7</td><td class="left bold-col">CZ</td><td class="center">Lsn</td>{fmt_v('CZLSN')}</tr>
<tr><td class="center">{f_num(row.get('RT225_CZKRT',0))}</td><td class="center">{f_num(row.get('SM225_CZKRT',0))}</td><td class="center bold-col"></td><td class="left bold-col">CZ</td><td class="center">Krt</td>{fmt_v('CZKRT')}</tr>
<tr><td class="center">{f_num(row.get('RT225_R3',0))}</td><td class="center">{f_num(row.get('SM225_R3',0))}</td><td class="center bold-col"></td><td class="left bold-col">R3</td><td class="center">Krt</td>{fmt_v('R3')}</tr>
<tr><td class="center">{f_num(row.get('RT225_R06EXC',0))}</td><td class="center">{f_num(row.get('SM225_R06EXC',0))}</td><td class="center bold-col"></td><td class="left bold-col">R06</td><td class="center">Krt</td>{fmt_v('R06EXC')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ALK',0))}</td><td class="center">{f_num(row.get('SM225_ALK',0))}</td><td class="center bold-col">8</td><td class="left bold-col">ALK</td><td class="center">Krt</td>{fmt_v('ALK')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ALKREG',0))}</td><td class="center">{f_num(row.get('SM225_ALKREG',0))}</td><td class="center bold-col"></td><td class="left bold-col">ALK REG</td><td class="center">Krt</td>{fmt_v('ALKREG')}</tr>
<tr><td class="center">{f_num(row.get('RT225_ALKNONREG',0))}</td><td class="center">{f_num(row.get('SM225_ALKNONREG',0))}</td><td class="center bold-col"></td><td class="left bold-col">ALK NON REG</td><td class="center">Krt</td>{fmt_v('ALKNONREG')}</tr>
<tr><td class="center">{f_num(row.get('RT225_MAA',0))}</td><td class="center">{f_num(row.get('SM225_MAA',0))}</td><td class="center bold-col">9</td><td class="left bold-col">MAA</td><td class="center">Krt</td>{fmt_v('MAA')}</tr>

<!-- SUB-TOTAL HOME CARE -->
<tr class="row-category">
<td class="center">{f_dec(row.get('RT225_HC',0))}</td><td class="center">{f_dec(row.get('SM225_HC',0))}</td>
<td colspan="2" class="left bold-col" style="padding-left:10px;">HOME CARE</td><td class="center">Jt Rp</td>
{fmt_raw('HC')}
</tr>

<!-- TOTAL DIVISI AB4 -->
<tr class="row-total">
<td class="center">{f_dec(row.get('RT225_AB4',0))}</td><td class="center">{f_dec(row.get('SM225_AB4',0))}</td>
<td colspan="2" class="left bold-col" style="padding-left:10px;">DIVISI AB4</td><td class="center">Jt Rp</td>
{fmt_raw('AB4')}
</tr>

<!-- DIVISI AB2 & AB3 -->
<tr class="row-ab23">
<td class="center">{f_dec(row.get('RT225_AB2',0))}</td><td class="center">{f_dec(row.get('SM225_AB2',0))}</td>
<td colspan="2" class="left bold-col" style="padding-left:10px;">DIVISI AB2</td><td class="center">Jt Rp</td>
{fmt_raw('AB2')}
</tr>
<tr class="row-ab23">
<td class="center">{f_dec(row.get('RT225_AB3',0))}</td><td class="center">{f_dec(row.get('SM225_AB3',0))}</td>
<td colspan="2" class="left bold-col" style="padding-left:10px;">DIVISI AB3</td><td class="center">Jt Rp</td>
{fmt_raw('AB3')}
</tr>
</tbody>
</table>
</div>"""

        try:
            st.html(table_html)
        except AttributeError:
            st.markdown(table_html, unsafe_allow_html=True)

        # Tombol Download PDF Landscape Center dengan Warna Biru Terang
        pdf_bytes = generate_pdf_landscape(row, bln_list)
        st.markdown("<br>", unsafe_allow_html=True)
        col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 1])
        with col_pdf2:
            st.download_button(
                label="📄 Export / Download Laporan PDF (Landscape)",
                data=pdf_bytes,
                file_name=f"Laporan_Omset_{selected_code}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    else:
        st.info("💡 Silakan ketik atau pilih toko pada pencarian di atas.")

except Exception as e:
    st.error(f"❌ Error: {e}")

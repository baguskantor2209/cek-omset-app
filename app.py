import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Bagus SDA AB4", layout="wide", page_icon="📊"
)

# Custom CSS Responsif HP + Desktop
st.markdown(
    """<style>
.stApp { background-color: #f8f9fa; color: #111827; }

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


# Helper pembaca CSV pintar
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


try:
    with st.spinner("⚡ Memuat data..."):
        df = load_data_from_github()

    # Opsi daftar toko
    toko_options = (
        df["kdCust"].astype(str) + " - " + df["cust"].astype(str)
    ).unique()

    # Searchbox Default Kosong
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
                """<div class="metric-card" style="border-left-color: #9333ea;">
<div class="metric-title">KONTRIBUTOR OMSET TERBESAR DIVISI</div>
<div class="metric-value">DIVISI AB4</div>
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

<!-- DIVISI AB2 & AB3 SEKARANG TERISI DARI DATABASE -->
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
    else:
        st.info("💡 Silakan ketik atau pilih toko pada pencarian di atas.")

except Exception as e:
    st.error(f"❌ Error: {e}")

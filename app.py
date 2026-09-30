import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Dashboard Cek Omset Toko", layout="wide", page_icon="📊"
)

# Style CSS dimasukkan secara bersih tanpa indentasi ganda
st.markdown(
    """<style>
.stApp { background-color: #f8f9fa; color: #111827; }
.metric-card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 18px 22px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    border-left: 5px solid #2563eb;
    margin-bottom: 20px;
}
.metric-title { color: #4b5563; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; }
.metric-value { color: #1e3a8a; font-size: 1.8rem; font-weight: 800; margin: 4px 0; }
.metric-subtitle { font-size: 0.85rem; font-weight: 600; }

.omset-table-container {
    background: #ffffff;
    padding: 24px;
    border-radius: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    margin-top: 15px;
    color: #111827;
}
.report-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #111827;
}
.report-table th {
    background-color: #00c0f0;
    color: #000000;
    font-weight: 700;
    text-align: center;
    padding: 8px 4px;
    border: 1px solid #bce8f1;
}
.report-table th.blue-header { background-color: #002060; color: #ffffff; }
.report-table td {
    padding: 6px 8px;
    border: 1px solid #d1d5db;
    text-align: right;
    color: #111827;
    background-color: #ffffff;
}
.report-table td.center { text-align: center; }
.report-table td.left { text-align: left; font-weight: 600; }

.row-category { background-color: #002060 !important; color: #ffffff !important; font-weight: bold; }
.row-category td { background-color: #002060 !important; color: #ffffff !important; border-color: #001040 !important; }
.row-total { background-color: #d92525 !important; color: #ffffff !important; font-weight: bold; }
.row-total td { background-color: #d92525 !important; color: #ffffff !important; border-color: #b01010 !important; }
.row-ab23 { background-color: #800000 !important; color: #ffffff !important; font-weight: bold; }
.row-ab23 td { background-color: #800000 !important; color: #ffffff !important; border-color: #500000 !important; }
</style>""",
    unsafe_allow_html=True,
)

st.title("📊 Dashboard Cek Omset & KP Toko")


@st.cache_data
def load_data_from_github():
    file_div_path, file_kp_path = None, None
    div_candidates = [
        "DIV_BDB_TEST.xlsx",
        "DIV BDB TEST.xlsx",
        "DIV_BDB_TEST.csv",
        "DIV BDB TEST.csv",
    ]
    kp_candidates = [
        "KP_BDB_TEST.xlsx",
        "KP BDB TEST.xlsx",
        "KP_BDB_TEST.csv",
        "KP BDB TEST.csv",
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

    df_div = (
        pd.read_csv(file_div_path)
        if file_div_path.endswith(".csv")
        else pd.read_excel(file_div_path, engine="openpyxl")
    )
    df_kp = (
        pd.read_csv(file_kp_path)
        if file_kp_path.endswith(".csv")
        else pd.read_excel(file_kp_path, engine="openpyxl")
    )

    cols_to_use = df_kp.columns.difference(df_div.columns).tolist()
    cols_to_use.append("kdCust")
    return pd.merge(df_div, df_kp[cols_to_use], on="kdCust", how="inner")


try:
    with st.spinner("⏳ Memuat data..."):
        df = load_data_from_github()

    col_search1, col_search2 = st.columns([2, 1])
    toko_list = (
        df["kdCust"].astype(str) + " - " + df["cust"].astype(str)
    ).unique()

    with col_search1:
        selected_toko = st.selectbox(
            "PILIH / CARI CUSTOMER",
            options=["-- Pilih Toko --"] + list(toko_list),
        )
    with col_search2:
        quick_search = st.text_input(
            "CARI NAMA TOKO QUICK FILTER",
            placeholder="Ketik Kode/Nama Toko...",
        )

    selected_code = None
    if selected_toko != "-- Pilih Toko --":
        selected_code = selected_toko.split(" - ")[0]
    elif quick_search:
        matched = df[
            df["kdCust"].astype(str).str.contains(quick_search, case=False)
            | df["cust"].astype(str).str.contains(quick_search, case=False)
        ]
        if not matched.empty:
            selected_code = matched.iloc[0]["kdCust"]

    if selected_code:
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

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""<div class="metric-card" style="border-left-color: #2563eb;">
<div class="metric-title">REAL OMSET BULAN BERJALAN DIVISI AB4</div>
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
<div class="metric-value" style="font-size: 1.4rem;">ENERGY DRINK VITAMIN</div>
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
                v = row.get(f"{b}_{suffix}", 0)
                txt = f"{v:,.1f}".replace(".0", "") if v != 0 else "-"
                tds += f"<td>{txt}</td>"
            return tds

        def fmt_raw(suffix):
            tds = ""
            for b in bln_list:
                v = row.get(f"{b}_{suffix}", 0)
                tds += f"<td>{v:,.1f}</td>"
            return tds

        table_html = f"""<div class="omset-table-container">
<div style="font-size: 15px; font-weight: bold; margin-bottom: 12px;">
Kode Cust : <span style="background: #e5e7eb; padding: 3px 8px; border-radius: 4px;">{row['kdCust']}</span><br>
Nama Toko : <b>{row['cust']}</b>
</div>
<table class="report-table">
<thead>
<tr>
<th class="blue-header" style="width: 60px;">RT2 25</th>
<th class="blue-header" style="width: 60px;">SM2 25</th>
<th style="width: 30px;">No</th>
<th style="text-align: left;">KP</th>
<th style="width: 50px;">Satuan</th>
<th>JAN 26</th><th>FEB 26</th><th>MAR 26</th><th>APR 26</th>
<th>MEI 26</th><th>JUN 26</th><th>JUL 26</th><th>AGT 26</th><th>SEP 26</th>
</tr>
</thead>
<tbody>
<tr><td class="center">{row.get('RT225_TOR',0):,.0f}</td><td class="center">{row.get('SM225_TOR',0):,.0f}</td><td class="center">1</td><td class="left">TOR</td><td class="center">Krt</td>{fmt_v('TOR')}</tr>
<tr><td class="center">{row.get('RT225_UCV',0):,.0f}</td><td class="center">{row.get('SM225_UCV',0):,.0f}</td><td class="center">2</td><td class="left">UCV</td><td class="center">Krt</td>{fmt_v('UCV')}</tr>
<tr><td class="center">{row.get('RT225_KTD',0):,.0f}</td><td class="center">{row.get('SM225_KTD',0):,.0f}</td><td class="center">3</td><td class="left">KTD</td><td class="center">Krt</td>{fmt_v('KTD')}</tr>
<tr><td class="center">{row.get('RT225_RBL',0):,.0f}</td><td class="center">{row.get('SM225_RBL',0):,.0f}</td><td class="center">4</td><td class="left">RBLGOLD</td><td class="center">Krt</td>{fmt_v('RBL')}</tr>
<tr><td class="center">{row.get('RT225_UCW',0):,.0f}</td><td class="center">{row.get('SM225_UCW',0):,.0f}</td><td class="center">5</td><td class="left">UCW</td><td class="center">Krt</td>{fmt_v('UCW')}</tr>
<tr><td class="center">{row.get('RT225_ISO',0):,.0f}</td><td class="center">{row.get('SM225_ISO',0):,.0f}</td><td class="center">6</td><td class="left">ISO</td><td class="center">Krt</td>{fmt_v('ISO')}</tr>
<tr class="row-category">
<td class="center">{row.get('RT225_EDV',0):,.1f}</td><td class="center">{row.get('SM225_EDV',0):,.1f}</td>
<td colspan="2" class="left" style="padding-left:10px;">ENERGY DRINK VITAMIN</td><td class="center">Jt Rp</td>
{fmt_raw('EDV')}
</tr>
<tr><td class="center">{row.get('RT225_CZLSN',0):,.0f}</td><td class="center">{row.get('SM225_CZLSN',0):,.0f}</td><td class="center">7</td><td class="left">CZ</td><td class="center">Lsn</td>{fmt_v('CZLSN')}</tr>
<tr><td class="center">{row.get('RT225_CZKRT',0):,.0f}</td><td class="center">{row.get('SM225_CZKRT',0):,.0f}</td><td class="center"></td><td class="left">CZ</td><td class="center">Krt</td>{fmt_v('CZKRT')}</tr>
<tr><td class="center">{row.get('RT225_R06EXC',0):,.0f}</td><td class="center">{row.get('SM225_R06EXC',0):,.0f}</td><td class="center"></td><td class="left">R06</td><td class="center">Krt</td>{fmt_v('R06EXC')}</tr>
<tr><td class="center">{row.get('RT225_R3',0):,.0f}</td><td class="center">{row.get('SM225_R3',0):,.0f}</td><td class="center">8</td><td class="left">ALK</td><td class="center">Krt</td>{fmt_v('R3')}</tr>
<tr><td class="center">{row.get('RT225_ALKREG',0):,.0f}</td><td class="center">{row.get('SM225_ALKREG',0):,.0f}</td><td class="center"></td><td class="left">ALK REG</td><td class="center">Krt</td>{fmt_v('ALKREG')}</tr>
<tr><td class="center">{row.get('RT225_ALKNONREG',0):,.0f}</td><td class="center">{row.get('SM225_ALKNONREG',0):,.0f}</td><td class="center"></td><td class="left">ALK NON REG</td><td class="center">Krt</td>{fmt_v('ALKNONREG')}</tr>
<tr><td class="center">{row.get('RT225_MAA',0):,.0f}</td><td class="center">{row.get('SM225_MAA',0):,.0f}</td><td class="center">9</td><td class="left">MAA</td><td class="center">Krt</td>{fmt_v('MAA')}</tr>
<tr class="row-category">
<td class="center">{row.get('RT225_HC',0):,.1f}</td><td class="center">{row.get('SM225_HC',0):,.1f}</td>
<td colspan="2" class="left" style="padding-left:10px;">HOME CARE</td><td class="center">Jt Rp</td>
{fmt_raw('HC')}
</tr>
<tr class="row-total">
<td class="center">{row.get('RT225_AB4',0):,.1f}</td><td class="center">{row.get('SM225_AB4',0):,.1f}</td>
<td colspan="2" class="left" style="padding-left:10px;">DIVISI AB4</td><td class="center">Jt Rp</td>
{fmt_raw('AB4')}
</tr>
<tr class="row-ab23">
<td class="center">-</td><td class="center">-</td>
<td colspan="2" class="left" style="padding-left:10px;">DIVISI AB2</td><td class="center">Jt Rp</td>
{''.join(['<td>-</td>' for _ in bln_list])}
</tr>
<tr class="row-ab23">
<td class="center">-</td><td class="center">-</td>
<td colspan="2" class="left" style="padding-left:10px;">DIVISI AB3</td><td class="center">Jt Rp</td>
{''.join(['<td>-</td>' for _ in bln_list])}
</tr>
</tbody>
</table>
</div>"""

        # Menggunakan st.components.v1.html / st.html agar 100% aman dirender sebagai visual tabel
        try:
            st.html(table_html)
        except AttributeError:
            st.markdown(table_html, unsafe_allow_html=True)

    else:
        st.info("💡 Silakan pilih toko pada pencarian di atas.")

except Exception as e:
    st.error(f"❌ Error: {e}")

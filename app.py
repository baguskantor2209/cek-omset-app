import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Dashboard Cek Omset Toko", layout="wide", page_icon="📊"
)

# Custom CSS untuk tampilan modern persis seperti gambar
st.markdown(
    """
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 5px solid #2563eb;
        margin-bottom: 20px;
    }
    .metric-title { color: #6b7280; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { color: #1e3a8a; font-size: 1.8rem; font-weight: 800; margin: 4px 0; }
    .metric-subtitle { color: #10b981; font-size: 0.85rem; font-weight: 600; }
    
    /* Table Styling */
    .omset-table-container {
        background: white;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-top: 15px;
    }
    .report-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 13px;
    }
    .report-table th {
        background-color: #00c0f0;
        color: #000;
        font-weight: 700;
        text-align: center;
        padding: 8px 4px;
        border: 1px solid #bce8f1;
    }
    .report-table th.blue-header { background-color: #002060; color: #fff; }
    .report-table td {
        padding: 6px 8px;
        border: 1px solid #e5e7eb;
        text-align: right;
    }
    .report-table td.center { text-align: center; }
    .report-table td.left { text-align: left; font-weight: 600; }
    
    /* Highlight Rows */
    .row-category { background-color: #002060 !important; color: #ffffff !important; font-weight: bold; }
    .row-category td { border-color: #001040 !important; }
    .row-total { background-color: #d92525 !important; color: #ffffff !important; font-weight: bold; }
    .row-total td { border-color: #b01010 !important; }
    .row-ab23 { background-color: #800000 !important; color: #ffffff !important; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("📊 Dashboard Cek Omset & KP Toko")


# Fungsi pembaca data dari GitHub yang aman dari error engine Excel
@st.cache_data
def load_data_from_github():
    file_div_path = None
    file_kp_path = None

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
        raise FileNotFoundError(
            "File database DIV/KP tidak ditemukan di repository GitHub."
        )

    # Baca file DIV
    if file_div_path.endswith(".csv"):
        df_div = pd.read_csv(file_div_path)
    else:
        df_div = pd.read_excel(file_div_path, engine="openpyxl")

    # Baca file KP
    if file_kp_path.endswith(".csv"):
        df_kp = pd.read_csv(file_kp_path)
    else:
        df_kp = pd.read_excel(file_kp_path, engine="openpyxl")

    # Clean & Merge
    cols_to_use = df_kp.columns.difference(df_div.columns).tolist()
    cols_to_use.append("kdCust")

    df_merged = pd.merge(df_div, df_kp[cols_to_use], on="kdCust", how="inner")
    return df_merged


try:
    df = load_data_from_github()

    # 1. PENCARIAN / QUICK FILTER
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

        # Nilai Omset Bulan Berjalan (SEP 26)
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

        # 2. METRICS CARDS
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(
                f"""
            <div class="metric-card" style="border-left-color: #2563eb;">
                <div class="metric-title">REAL OMSET BULAN BERJALAN DIVISI AB4</div>
                <div class="metric-value">Rp {omset_sep26:,.1f} Jt</div>
                <div class="metric-subtitle" style="color: {status_color};">
                    {status_arrow} {abs(pct_omset):,.1f}% vs RT2 25 ({diff_omset:+,.1f} Jt)
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                """
            <div class="metric-card" style="border-left-color: #9333ea;">
                <div class="metric-title">KONTRIBUTOR OMSET TERBESAR DIVISI</div>
                <div class="metric-value">DIVISI AB4</div>
                <div class="metric-subtitle" style="color: #9333ea;">Penyumbang Omset Utama</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                """
            <div class="metric-card" style="border-left-color: #06b6d4;">
                <div class="metric-title">KATEGORI KONTRIBUTOR TERTINGGI</div>
                <div class="metric-value" style="font-size: 1.4rem;">ENERGY DRINK VITAMIN</div>
                <div class="metric-subtitle" style="color: #06b6d4;">Volume Penjualan Terbesar</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # 3. TABEL HANYA TAHUN 2026
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

        def gv(suffix):
            return [
                f"{row.get(f'{b}_{suffix}', 0):,.1f}".replace(".0", "")
                if row.get(f"{b}_{suffix}", 0) != 0
                else "-"
                for b in bln_list
            ]

        def gv_raw(suffix):
            return [row.get(f"{b}_{suffix}", 0) for b in bln_list]

        table_html = f"""
        <div class="omset-table-container">
            <div style="font-size: 15px; font-weight: bold; margin-bottom: 12px; color: #333;">
                Kode Cust : <span style="background: #f3f4f6; padding: 3px 8px; border-radius: 4px; border: 1px solid #ccc;">{row['kdCust']}</span><br>
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
                    <tr><td class="center">{row.get('RT225_TOR',0):,.0f}</td><td class="center">{row.get('SM225_TOR',0):,.0f}</td><td class="center">1</td><td class="left">TOR</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('TOR')])}</tr>
                    <tr><td class="center">{row.get('RT225_UCV',0):,.0f}</td><td class="center">{row.get('SM225_UCV',0):,.0f}</td><td class="center">2</td><td class="left">UCV</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('UCV')])}</tr>
                    <tr><td class="center">{row.get('RT225_KTD',0):,.0f}</td><td class="center">{row.get('SM225_KTD',0):,.0f}</td><td class="center">3</td><td class="left">KTD</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('KTD')])}</tr>
                    <tr><td class="center">{row.get('RT225_RBL',0):,.0f}</td><td class="center">{row.get('SM225_RBL',0):,.0f}</td><td class="center">4</td><td class="left">RBLGOLD</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('RBL')])}</tr>
                    <tr><td class="center">{row.get('RT225_UCW',0):,.0f}</td><td class="center">{row.get('SM225_UCW',0):,.0f}</td><td class="center">5</td><td class="left">UCW</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('UCW')])}</tr>
                    <tr><td class="center">{row.get('RT225_ISO',0):,.0f}</td><td class="center">{row.get('SM225_ISO',0):,.0f}</td><td class="center">6</td><td class="left">ISO</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('ISO')])}</tr>
                    
                    <!-- SUB-TOTAL ENERGY DRINK -->
                    <tr class="row-category">
                        <td class="center">{row.get('RT225_EDV',0):,.1f}</td><td class="center">{row.get('SM225_EDV',0):,.1f}</td>
                        <td colspan="2" class="left" style="padding-left:10px;">ENERGY DRINK VITAMIN</td><td class="center">Jt Rp</td>
                        {''.join([f'<td>{v:,.1f}</td>' for v in gv_raw('EDV')])}
                    </tr>

                    <tr><td class="center">{row.get('RT225_CZLSN',0):,.0f}</td><td class="center">{row.get('SM225_CZLSN',0):,.0f}</td><td class="center">7</td><td class="left">CZ</td><td class="center">Lsn</td>{''.join([f'<td>{v}</td>' for v in gv('CZLSN')])}</tr>
                    <tr><td class="center">{row.get('RT225_CZKRT',0):,.0f}</td><td class="center">{row.get('SM225_CZKRT',0):,.0f}</td><td class="center"></td><td class="left">CZ</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('CZKRT')])}</tr>
                    <tr><td class="center">{row.get('RT225_R06EXC',0):,.0f}</td><td class="center">{row.get('SM225_R06EXC',0):,.0f}</td><td class="center"></td><td class="left">R06</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('R06EXC')])}</tr>
                    <tr><td class="center">{row.get('RT225_R3',0):,.0f}</td><td class="center">{row.get('SM225_R3',0):,.0f}</td><td class="center">8</td><td class="left">ALK</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('R3')])}</tr>
                    <tr><td class="center">{row.get('RT225_ALKREG',0):,.0f}</td><td class="center">{row.get('SM225_ALKREG',0):,.0f}</td><td class="center"></td><td class="left">ALK REG</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('ALKREG')])}</tr>
                    <tr><td class="center">{row.get('RT225_ALKNONREG',0):,.0f}</td><td class="center">{row.get('SM225_ALKNONREG',0):,.0f}</td><td class="center"></td><td class="left">ALK NON REG</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('ALKNONREG')])}</tr>
                    <tr><td class="center">{row.get('RT225_MAA',0):,.0f}</td><td class="center">{row.get('SM225_MAA',0):,.0f}</td><td class="center">9</td><td class="left">MAA</td><td class="center">Krt</td>{''.join([f'<td>{v}</td>' for v in gv('MAA')])}</tr>

                    <!-- SUB-TOTAL HOME CARE -->
                    <tr class="row-category">
                        <td class="center">{row.get('RT225_HC',0):,.1f}</td><td class="center">{row.get('SM225_HC',0):,.1f}</td>
                        <td colspan="2" class="left" style="padding-left:10px;">HOME CARE</td><td class="center">Jt Rp</td>
                        {''.join([f'<td>{v:,.1f}</td>' for v in gv_raw('HC')])}
                    </tr>

                    <!-- TOTAL DIVISI AB4 -->
                    <tr class="row-total">
                        <td class="center">{row.get('RT225_AB4',0):,.1f}</td><td class="center">{row.get('SM225_AB4',0):,.1f}</td>
                        <td colspan="2" class="left" style="padding-left:10px;">DIVISI AB4</td><td class="center">Jt Rp</td>
                        {''.join([f'<td>{v:,.1f}</td>' for v in gv_raw('AB4')])}
                    </tr>

                    <!-- DIVISI AB2 & AB3 -->
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
            <div style="font-size: 11px; color: #6b7280; margin-top: 10px; display: flex; justify-content: space-between;">
                <span>* Satuan Karton (Krt) / Lusin (Lsn) | Nilai Omset Kategori & Divisi dalam Juta Rupiah (Jt Rp)</span>
                <span>Diperbarui: September 2026</span>
            </div>
        </div>
        """

        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info(
            "💡 Silakan pilih customer dari dropdown di atas untuk melihat detail omset."
        )

except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat membaca file database di GitHub: {e}")

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cek Omset Toko", layout="wide")

st.title("📊Cek Omset Toko")


# 1. Load dan Gabungkan 2 Database
@st.cache_data
def load_data():
    # Baca file Rupiah (DIV) dan Qty (KP)
    df_div = pd.read_excel("DIV_BDB_TEST.xlsx")
    df_kp = pd.read_excel("KP_BDB_TEST.xlsx")

    # Ambil kolom khusus dari KP agar tidak bentrok dengan DIV
    cols_to_use = df_kp.columns.difference(df_div.columns).tolist()
    cols_to_use.append("kdCust")

    # Merge berdasarkan Kode Customer (kdCust)
    df_merged = pd.merge(df_div, df_kp[cols_to_use], on="kdCust", how="inner")
    return df_merged


# Memuat data
try:
    df = load_data()
    st.sidebar.success("✅ Database Berhasil Dimuat!")
except Exception as e:
    st.error(f"Gagal membaca file database: {e}")
    st.stop()

# 2. Fitur Pencarian
st.subheader("🔍 Cari Customer / Toko")
search_query = st.text_input(
    "Ketik Kode Cust atau Nama Toko:",
    placeholder="Contoh: 03176333 atau PT. JAGO SUKSES MAKMUR",
)

if search_query:
    filtered_df = df[
        df["kdCust"].astype(str).str.contains(search_query, case=False)
        | df["cust"].astype(str).str.contains(search_query, case=False)
    ]

    if not filtered_df.empty:
        st.write(
            f"Menampilkan hasil untuk: **{search_query}** ({len(filtered_df)} toko ditemukan)"
        )
        st.dataframe(filtered_df)
    else:
        st.warning("Customer tidak ditemukan.")
else:
    st.write("📌 Tampilan 50 Data Pertama:")
    st.dataframe(df.head(50))
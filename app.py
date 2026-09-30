import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cek Omset Toko", layout="wide")

st.title("📊 Aplikasi Cek Omset & Qty Toko")

# Sidebar Upload
st.sidebar.header("📁 Upload File Database")
file_div = st.sidebar.file_uploader(
    "1. Upload Database DIV (Rupiah)", type=["xlsx", "csv"]
)
file_kp = st.sidebar.file_uploader(
    "2. Upload Database KP (Qty)", type=["xlsx", "csv"]
)


@st.cache_data
def process_data(f_div, f_kp):
    # Baca file DIV
    df_div = (
        pd.read_csv(f_div) if f_div.name.endswith(".csv") else pd.read_excel(f_div)
    )
    # Baca file KP
    df_kp = (
        pd.read_csv(f_kp) if f_kp.name.endswith(".csv") else pd.read_excel(f_kp)
    )

    # Ambil kolom unik KP
    cols_to_use = df_kp.columns.difference(df_div.columns).tolist()
    cols_to_use.append("kdCust")

    # Merge data
    df_merged = pd.merge(df_div, df_kp[cols_to_use], on="kdCust", how="inner")
    return df_merged


if file_div is not None and file_kp is not None:
    try:
        df = process_data(file_div, file_kp)
        st.sidebar.success("✅ Kedua Database Berhasil Dimuat!")

        # Fitur Pencarian
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

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info(
        "👈 Silakan unggah file **DIV** (Rupiah) dan file **KP** (Qty) pada menu di sebelah kiri untuk mulai mencari data."
    )

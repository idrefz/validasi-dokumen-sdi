import streamlit as st
import fitz  # PyMuPDF
import os
import random
import datetime
import pandas as pd

# Set up halaman
st.set_page_config(page_title="PDF Serial Validator", layout="centered")
menu = st.sidebar.selectbox("Navigasi", ["📄 Upload & Generate", "🔍 Cek Validasi", "📜 Riwayat Upload"])

# Fungsi untuk generate nomor seri otomatis
def generate_nomor_seri():
    tanggal = datetime.datetime.now().strftime("%Y%m%d")  # 20250414
    unik = str(random.randint(1000, 9999))
    return f"SN-{tanggal}-{unik}"

# Fungsi untuk menambahkan watermark pada PDF
def tambah_watermark(pdf_file, nomor_seri):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    output_bytes = doc.write()
    for page in doc:
        rect = page.rect
        page.insert_text(
            point=(rect.width - 200, rect.height - 50),
            text=f"Nomor Seri: {nomor_seri}",
            fontsize=10,
            color=(0.6, 0.6, 0.6),
            overlay=True
        )
    return doc.write()

# Fungsi untuk ekstrak nomor seri dari PDF
def extract_nomor_seri_from_pdf(file):
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
        match = re.search(r"SN-\d{8}-\d{4}", text)
        return match.group(0) if match else None

# Menu Upload & Generate
if menu == "📄 Upload & Generate":
    st.title("📄 Upload PDF & Untuk Tambahkan Nomor Seri Otomatis")

    # Input nama pengunggah
    nama = st.text_input("Nama Pengunggah")
    uploaded_pdf = st.file_uploader("Unggah PDF", type=["pdf"])

    if nama and uploaded_pdf:
        nomor_seri = generate_nomor_seri()
        output = tambah_watermark(uploaded_pdf, nomor_seri)

        # Menyimpan log upload
        log_data = pd.DataFrame([[nama, nomor_seri, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]],
                                columns=["Nama", "Nomor Seri", "Waktu"])
        log_path = "log_upload.csv"
        if os.path.exists(log_path):
            log_data.to_csv(log_path, mode="a", index=False, header=False)
        else:
            log_data.to_csv(log_path, index=False)

        st.success(f"✅ Nomor Seri: `{nomor_seri}` telah ditambahkan.")
        st.info(f"📌 Nama Pengunggah: **{nama}**")
        st.download_button(
            "⬇️ Download PDF dengan Nomor Seri",
            output,
            file_name=f"{nomor_seri}.pdf"
        )

    elif uploaded_pdf and not nama:
        st.warning("⚠️ Mohon isi nama pengunggah sebelum mengunggah file.")

# Menu Cek Validasi
elif menu == "🔍 Cek Validasi":
    st.title("🔍 Validasi PDF yang sudah ada Nomor Seri")

    cek_pdf = st.file_uploader("Upload PDF untuk Dicek", type=["pdf"], key="cek")
    if cek_pdf:
        nomor_seri = extract_nomor_seri_from_pdf(cek_pdf)
        if nomor_seri:
            st.success(f"✅ Nomor Seri ditemukan: `{nomor_seri}`")

            tanggal_raw = nomor_seri.split("-")[1]
            tahun = tanggal_raw[:4]
            bulan = tanggal_raw[4:6]
            hari = tanggal_raw[6:8]
            tanggal_format = f"{hari}-{bulan}-{tahun}"
            st.info(f"📅 Tanggal dari Nomor Seri: `{tanggal_format}`")
        else:
            st.error("❌ Nomor Seri tidak ditemukan dalam PDF.")

# Menu Riwayat Upload
elif menu == "📜 Riwayat Upload":
    st.title("📜 Riwayat Upload PDF")

    if os.path.exists("log_upload.csv"):
        df_log = pd.read_csv("log_upload.csv")

        # Konversi kolom waktu jadi datetime
        df_log["Waktu"] = pd.to_datetime(df_log["Waktu"])

        # 🔍 Pencarian nama / nomor seri
        keyword = st.text_input("🔎 Cari Nama atau Nomor Seri:")
        if keyword:
            df_log = df_log[df_log.apply(lambda row: keyword.lower() in row.astype(str).str.lower().to_string(), axis=1)]

        # 📅 Filter tanggal
        tanggal_mulai = st.date_input("Tanggal Mulai", value=df_log["Waktu"].min().date())
        tanggal_akhir = st.date_input("Tanggal Akhir", value=df_log["Waktu"].max().date())

        df_log = df_log[
            (df_log["Waktu"].dt.date >= tanggal_mulai) &
            (df_log["Waktu"].dt.date <= tanggal_akhir)
        ]

        st.write(f"📄 Menampilkan {len(df_log)} data")
        st.dataframe(df_log)

        st.download_button(
            "⬇️ Download Hasil (CSV)",
            data=df_log.to_csv(index=False),
            file_name="riwayat_filtered.csv",
            mime="text/csv"
        )
    else:
        st.info("Belum ada data upload.")

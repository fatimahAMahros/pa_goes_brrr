import streamlit as st
import pandas as pd
from utils.queries import get_available_months, get_preprocessing_examples, get_comment_stats


def render():
    st.title("Preprocessing")
    st.markdown(
        "Sebelum clustering, komentar yang didapat dari Instagram diproses melalui beberapa tahap "
        "pembersihan. Bagian ini menunjukkan seperti apa bentuk komentar sebelum dan sesudahnya."
    )

    months = get_available_months()
    if not months:
        st.warning("Tidak ada data yang telah dipreprocess ditemukan di databse.")
        return

    # selected_month = st.selectbox("Pilih bulan", months, key="preproc_month")
    selected_month = st.selectbox(
        "Bulan", 
        months, 
        format_func=format_month_display, 
        key="mr_month"
    )
    stats = get_comment_stats(selected_month)

    st.divider()

    c1, c2 = st.columns(2)
    c1.metric("Total komentar", f"{stats['total_comments']:,}")
    c2.metric("Postingan Instagram", f"{stats['total_posts']:,}")

    st.divider()

    st.subheader("Langkah-langkah Preprocessing")

    with st.container():
        steps = [
            ("Case folding", "Semua teks diubah menjadi huruf kecil."),
            ("Penghapusan noise", "Menghapus tanda baca, emoji, URL, @mention, #hashtag."),
            ("Normalisasi bahasa gaul", "Bahasa gaul Indonesia/Jawa dipetakan ke kata baku (misal: 'gk' → 'tidak')."),
            ("Penghapusan stopword", "Kata hubung/pengisi yang umum dihapus (misal: 'yang', 'dan', 'di')."),
            ("Stemming", "Kata-kata diubah ke bentuk dasarnya menggunakan Sastrawi."),
            ("Penanganan sinonim dan antonim", "Sinonim dipetakan menjadi satu istilah perwakilan untuk mengurangi dimensi fitur"),
        ]
        for step, desc in steps:
            st.markdown(f"**{step} :** {desc}")

    st.divider()

    st.subheader("Contoh: komentar mentah → bentuk bersih")
    examples = get_preprocessing_examples(selected_month, n=10)

    if examples.empty:
        st.info(
            "Tidak ada contoh preprocessing yang ditemukan untuk bulan ini. "
            "Pastikan kolom `clean_text` pada tabel `comments` telah terisi."
        )
        placeholder = pd.DataFrame({
            "Komentar mentah": [
                "air ny mati lg, udh brp hari ini 😡",
                "tagihan bulan ini kok naik banyak banget??",
                "Terimakasih PDAM sdh cepet respon keluhannya 🙏",
            ],
            "Setelah pembersihan": [
                "air mati sudah berapa hari",
                "tagihan bulan naik banyak",
                "terima kasih pdam cepat respon keluhan",
            ],
        })
        st.dataframe(placeholder, width="stretch")
    else:
        display = pd.DataFrame({
            "Komentar mentah": examples["raw_text"],
            "Setelah pembersihan": examples["clean_text"],
        })
        st.dataframe(display, width="stretch")

    st.divider()

    st.subheader("Ekstraksi fitur — 4 Skenario")
    st.markdown(
        "Akan ada empat skenario berbeda dari dataset vektor yang akan dijalankan pada proses clustering:"
    )

    scenario_info = {
        "Skenario": ["1", "2", "3", "4"],
        "Deskripsi": [
            "Keluaran TF langsung",
            "Threshold",
            "Binary turned values",
            "Trheshold + Biner",
        ],
    }
    st.table(pd.DataFrame(scenario_info))
    
    st.markdown("""
**Penjelasan Logika Skenario:**

**_Threshold_**
1. Temukan nilai fitur tertinggi dari setiap komentar.
2. Bagi dua nilai tersebut dan gunakan sebagai batas (*threshold*) untuk komentar itu.
3. Untuk setiap fitur yang memiliki nilai di dalam komentar tersebut, jika nilainya kurang dari setengah nilai tertinggi tadi, maka ubah nilainya menjadi nol.

**Nilai diubah menjadi biner _(Binary turned values)_**
1. Untuk semua fitur dengan nilai bukan nol(0), ubah semuanya menjadi satu (1).
2. Proses ini dilakukan pada semua komentar.
    """)

MONTH_NAMES_ID = {
    "01": "Januari", "02": "Februari", "03": "Maret", "04": "April",
    "05": "Mei", "06": "Juni", "07": "Juli", "08": "Agustus",
    "09": "September", "10": "Oktober", "11": "November", "12": "Desember"
}

def format_month_display(month_str: str) -> str:
    try:
        year, month = month_str.split("-")
        return f"{MONTH_NAMES_ID.get(month, month)} {year}"
    except (ValueError, AttributeError):
        return month_str
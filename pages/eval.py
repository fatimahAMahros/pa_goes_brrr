import streamlit as st
import pandas as pd


def render():
    st.title("Evaluasi")
    st.markdown(
        "Bagian ini merangkum seberapa baik hasil clustering mencerminkan "
        "topik-topik yang sebenarnya ada di dalam data, dan apa langkah selanjutnya"
        "yang bisa diambil untuk upaya memperbaik hasil"
    )

    st.divider()

    # Observasi kualitatif
    st.subheader("Observasi Kualitatif")

    observations = [
        (
            "Proses dengan k rendah menghasilkan satu klaster yang dominan",
            "Untuk sebagian besar kombinasi linkage + skenario pada data yang digunakan untuk ujicoba "
            "Valley-Tracing mengembalikan nilai k yang kecil di mana salah satu klasternya berisi "
            "lebih dari 80% komentar. Hal ini membuat hasil clustering tidak dapat diringkas atupun"
            "dipahami dengan mudah, menjadikannya kurang informatif."
        ),
        (
            "Nilai φ(Akurasi) yang tinggi menyatakan keyakinan yang",
            "Nilai φ didapat dari pembagian ∂(rasio variansi) antara nilai rasio tertinggi dengan"
            "nilai rasio tertinggi kedua. Walaupun nilai φ yang didapat bernilai tinggi pada nilai k"
            "yang kecil, "
        )
    ]

    for title, detail in observations:
        with st.expander(f"**{title}**"):
            st.markdown(detail)

    st.divider()

    # Batasan
    st.subheader("Batasan")

    limitations = [
        "Weipe",
    ]

    for lim in limitations:
        st.markdown(f"- {lim}")

    st.divider()

    # Saran?/langkah slantunya
    st.subheader("Langkah Selanjutnya")

    next_steps = [
        ("Perluas kamus bahasa gaul (slang)", "Tambahkan bahasa gaul spesifik domain PDAM/utilitas yang mungkin belum tertangani dengan baik."),
    ]

    for step, detail in next_steps:
        st.markdown(f"**{step}** — {detail}")
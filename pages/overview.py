import streamlit as st
from utils.queries import get_available_months, get_all_months, get_comment_stats


def render():
    st.title("Opinion Mining pada Komentar Instagram PDAM Surya Sembada")
    st.markdown(
        "Dashboard ini menyajikan hasil _clustering_ dan "
        "peringkasan otomatis yang diterapkan pada komentar publik di "
        "akun Instagram resmi PDAM Surya Sembada. Tujuannya adalah untuk memunculkan "
        "opini pelanggan yang berulang tanpa harus membaca setiap komentar secara manual."
    )

    st.divider()

    # Dataset
    st.subheader("Cuplikan Dataset")

    months = get_available_months()
    # if not months:
    #     st.info("No data, run `python data/init_db.py` first")
    #     return

    # cols = st.columns(len(months) if len(months) <= 4 else 4)
    # for i, month in enumerate(months[:4]):
    #     stats = get_comment_stats(month)
    #     with cols[i]:
    #         st.metric(label=month, value=f"{stats['total_comments']:,} komentar")

    all_months = get_all_months()
    
    if not all_months:
        st.info("No data, run `python data/init_db.py` first")
        return

    total_comments = 0
    for month in all_months:
        stats = get_comment_stats(month)
        total_comments += stats['total_comments']

    st.metric(label="Total Keseluruhan Komentar", value=f"{total_comments:,} komentar")

    st.divider()

    #Diagram alru
    st.subheader("Pipeline Pengerjaan")

    pipeline_steps = [
        ("1 · Pengumpulan", "Komentar Instagram diambil dari postingan resmi PDAM dengan cara _web scraping_."),
        ("2 · Preprocessing", "Menormalkan bahasa gaul (slang), menghapus stopword, melakukan stemming token, dan menyamakan istilah sinonim."),
        ("3 · Ekstraksi fitur", "Membangun vektor TF(4 skenario dengan pembobotan istilah yang berbeda)."),
        ("4 · Clustering", "Hierarchical Agglomerative Clustering dengan Valley-Tracing untuk menemukan nilai k yang optimal."),
        ("5 · Summarisation", "Menghasilkan kalimat ringkasan dan kata kunci teratas untuk setiap klaster."),
    ]

    step_cols = st.columns(len(pipeline_steps))
    for col, (title, desc) in zip(step_cols, pipeline_steps):
        with col:
            st.markdown(f"**{title}**")
            st.caption(desc)
    
    st.divider()
    
    st.subheader("Data Mentah")
    st.markdown("Data komentar mentah yang tidak terstruktur yang diambil langsung dari Instagram sebelum proses pembersihan apa pun diterapkan.")

    from utils.queries import get_raw_comments
    # TO DO: Add selectore for month picking of the commments displayed
    raw_df = get_raw_comments(months[0])
    
    if not raw_df.empty:
        display_raw = raw_df.rename(columns={
            "comment_date": "Waktu Pembuatan",
            "post_id": "ID Post",
            "raw_text": "Komentar"
        })
        
        st.dataframe(
            display_raw, 
            width="stretch", 
            height=400, 
            hide_index=True
        )
    
    st.divider()

    with st.expander("Glosarium"):
        st.markdown("""
**Clustering** : mengelompokkan komentar sehingga komentar yang mirip berada di kelompok yang sama,
tanpa perlu melabelinya secara manual terlebih dahulu.

**Hierarchical Agglomerative Clustering (HAC)** : sebuah metode yang dimulai dengan
menjadikan setiap komentar sebagai kelompoknya sendiri, lalu terus menggabungkan kelompok-kelompok 
yang paling mirip sampai titik henti (stopping point) tercapai.

**Valley-Tracing** : teknik untuk secara otomatis menemukan jumlah
kelompok (k) terbaik dengan mendeteksi di mana metrik penggabungan "mencapai titik terendah", mirip dengan
menemukan titik terendah di sebuah lembah pada grafik.

**Term Frequency (TF)** : cara untuk mengubah teks menjadi angka dengan menghitung 
seberapa sering sebuah kata muncul di dalam satu komentar. Semakin sering suatu kata 
digunakan dalam sebuah komentar, semakin tinggi skornya, tanpa memperhitungkan kemunculan 
kata tersebut di komentar lainnya.

**Summarization** : setelah clustering, kalimat ringkasan pendek
dibuat untuk setiap kelompok guna mendeskripsikan tentang apa isi komentar-komentar di dalamnya.
        """)
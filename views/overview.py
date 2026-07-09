import streamlit as st
from utils.queries import get_available_months, get_all_months, get_comment_stats, get_dataset_overview


def render():
    st.title("Opinion Mining pada Komentar Instagram PDAM Surya Sembada")
    st.markdown(
        "Dashboard ini menyajikan hasil _clustering_ dan "
        "peringkasan otomatis yang diterapkan pada komentar publik di "
        "akun Instagram resmi PDAM Surya Sembada. Tujuannya adalah untuk memunculkan "
        "opini pelanggan yang berulang tanpa harus membaca setiap komentar secara manual."
    )

    st.divider()

    dataset_overview = get_dataset_overview()
    months = get_available_months()
    all_months = get_all_months()

    if not all_months:
        st.info("No data, run `python data/init_db.py` first")
        return

    total_comments = 0
    for month in all_months:
        month_stats = get_comment_stats(month) 
        total_comments += month_stats['total_comments']

    rentang_komentar = f"{dataset_overview['min_date']} - <br>{dataset_overview['max_date']}"

    if months:
        sorted_months = sorted(months)
        awal_uji_coba = sorted_months[0]
        akhir_uji_coba = sorted_months[-1]
        rentang_uji_coba = awal_uji_coba if awal_uji_coba == akhir_uji_coba \
                           else f"{awal_uji_coba} — {akhir_uji_coba}"
    else:
        rentang_uji_coba = "Belum ada data"

    #SVG icons
    svg_calendar = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
        <path d="M12 11.993a.75.75 0 0 0-.75.75v.006c0 .414.336.75.75.75h.006a.75.75 0 0 0 .75-.75v-.006a.75.75 0 0 0-.75-.75H12ZM12 16.494a.75.75 0 0 0-.75.75v.005c0 .414.335.75.75.75h.005a.75.75 0 0 0 .75-.75v-.005a.75.75 0 0 0-.75-.75H12ZM8.999 17.244a.75.75 0 0 1 .75-.75h.006a.75.75 0 0 1 .75.75v.006a.75.75 0 0 1-.75.75h-.006a.75.75 0 0 1-.75-.75v-.006ZM7.499 16.494a.75.75 0 0 0-.75.75v.005c0 .414.336.75.75.75h.005a.75.75 0 0 0 .75-.75v-.005a.75.75 0 0 0-.75-.75H7.5ZM13.499 14.997a.75.75 0 0 1 .75-.75h.006a.75.75 0 0 1 .75.75v.005a.75.75 0 0 1-.75.75h-.006a.75.75 0 0 1-.75-.75v-.005ZM14.25 16.494a.75.75 0 0 0-.75.75v.006c0 .414.335.75.75.75h.005a.75.75 0 0 0 .75-.75v-.006a.75.75 0 0 0-.75-.75h-.005ZM15.75 14.995a.75.75 0 0 1 .75-.75h.005a.75.75 0 0 1 .75.75v.006a.75.75 0 0 1-.75.75H16.5a.75.75 0 0 1-.75-.75v-.006ZM13.498 12.743a.75.75 0 0 1 .75-.75h2.25a.75.75 0 1 1 0 1.5h-2.25a.75.75 0 0 1-.75-.75ZM6.748 14.993a.75.75 0 0 1 .75-.75h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1-.75-.75Z" />
        <path fill-rule="evenodd" d="M18 2.993a.75.75 0 0 0-1.5 0v1.5h-9V2.994a.75.75 0 1 0-1.5 0v1.497h-.752a3 3 0 0 0-3 3v11.252a3 3 0 0 0 3 3h13.5a3 3 0 0 0 3-3V7.492a3 3 0 0 0-3-3H18V2.993ZM3.748 18.743v-7.5a1.5 1.5 0 0 1 1.5-1.5h13.5a1.5 1.5 0 0 1 1.5 1.5v7.5a1.5 1.5 0 0 1-1.5 1.5h-13.5a1.5 1.5 0 0 1-1.5-1.5Z" clip-rule="evenodd" />
    </svg>'''

    svg_database = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
        <path d="M21 6.375c0 2.692-4.03 4.875-9 4.875S3 9.067 3 6.375 7.03 1.5 12 1.5s9 2.183 9 4.875Z" />
        <path d="M12 12.75c2.685 0 5.19-.586 7.078-1.609a8.283 8.283 0 0 0 1.897-1.384c.016.121.025.244.025.368C21 12.817 16.97 15 12 15s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.285 8.285 0 0 0 1.897 1.384C6.809 12.164 9.315 12.75 12 12.75Z" />
        <path d="M12 16.5c2.685 0 5.19-.586 7.078-1.609a8.282 8.282 0 0 0 1.897-1.384c.016.121.025.244.025.368 0 2.692-4.03 4.875-9 4.875s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.284 8.284 0 0 0 1.897 1.384C6.809 15.914 9.315 16.5 12 16.5Z" />
        <path d="M12 20.25c2.685 0 5.19-.586 7.078-1.609a8.282 8.282 0 0 0 1.897-1.384c.016.121.025.244.025.368 0 2.692-4.03 4.875-9 4.875s-9-2.183-9-4.875c0-.124.009-.247.025-.368a8.284 8.284 0 0 0 1.897 1.384C6.809 19.664 9.315 20.25 12 20.25Z" />
    </svg>'''

    svg_chart = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
        <path fill-rule="evenodd" d="M1.5 7.125c0-1.036.84-1.875 1.875-1.875h6c1.036 0 1.875.84 1.875 1.875v3.75c0 1.036-.84 1.875-1.875 1.875h-6A1.875 1.875 0 0 1 1.5 10.875v-3.75Zm12 1.5c0-1.036.84-1.875 1.875-1.875h5.25c1.035 0 1.875.84 1.875 1.875v8.25c0 1.035-.84 1.875-1.875 1.875h-5.25a1.875 1.875 0 0 1-1.875-1.875v-8.25ZM3 16.125c0-1.036.84-1.875 1.875-1.875h5.25c1.036 0 1.875.84 1.875 1.875v2.25c0 1.035-.84 1.875-1.875 1.875h-5.25A1.875 1.875 0 0 1 3 18.375v-2.25Z" clip-rule="evenodd" />
    </svg>'''

    # Helper
    def create_card(icon_svg, title, subtitle, bg_color, icon_color):
            return f"""
    <div style="display: flex; align-items: center; background-color: #ffffff; padding: 1rem; border-radius: 0.5rem; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 95px;">
        <div style="margin-right: 15px; display: flex; align-items: center; justify-content: center; background-color: {bg_color}; color: {icon_color}; padding: 10px; border-radius: 8px;">
            {icon_svg}
        </div>
        <div style="display: flex; flex-direction: column;">
            <span style="font-size: 13px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>
            <span style="font-size: 16px; font-weight: 700; color: #0F172A; margin-top: 2px;">{subtitle}</span>
        </div>
    </div>
    """

    st.subheader("Dataset Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(create_card(svg_database, "Total Dataset", f"{total_comments} Komentar", "#dcfce7", "#166534"), unsafe_allow_html=True)
    with col2:
        st.markdown(create_card(svg_calendar, "Rentang Waktu Data", rentang_komentar, "#fee2e2", "#991b1b"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_card(svg_chart, "Bulan Terklaster", rentang_uji_coba, "#cbe6f3", "#2e92c4"), unsafe_allow_html=True)

    st.write("")
    st.divider()

    # Pipeline
    st.subheader("Pipeline Pengerjaan")

    pipeline_steps = [
        ("1 · Pengumpulan", "Komentar Instagram diambil dari postingan resmi PDAM dengan cara _web scraping_."),
        ("2 · Preprocessing", "Menormalkan bahasa gaul (slang), menghapus stopword, melakukan stemming token, dan menyamakan istilah sinonim."),
        ("3 · Ekstraksi fitur", "Membangun vektor TF (4 skenario dengan pembobotan istilah yang berbeda)."),
        ("4 · Clustering", "Hierarchical Agglomerative Clustering dengan Valley-Tracing untuk menemukan nilai k yang optimal."),
        ("5 · Summarisation", "Menghasilkan kalimat ringkasan dan kata kunci teratas untuk setiap klaster."),
    ]

    step_cols = st.columns(len(pipeline_steps))
    for col, (title, desc) in zip(step_cols, pipeline_steps):
        with col:
            st.markdown(f"**{title}**")
            st.caption(desc)

    st.divider()

    # Data Mentah
    st.subheader("Data Mentah")
    st.markdown("Data komentar mentah yang tidak terstruktur yang diambil langsung dari Instagram sebelum proses pembersihan apa pun diterapkan.")

    from utils.queries import get_raw_comments
    raw_df = get_raw_comments(months[0])

    if not raw_df.empty:
        display_raw = raw_df.rename(columns={
            "comment_date": "Waktu Pembuatan",
            "post_id": "ID Post",
            "raw_text": "Komentar"
        }).reset_index(drop=True) 

        def striped_rows(row):
            bg_color = '#f1f5f9' if row.name % 2 == 0 else '#ffffff'
            return [f'background-color: {bg_color}'] * len(row)

        styled_raw_df = display_raw.style.apply(striped_rows, axis=1)

        st.dataframe(
            styled_raw_df,
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
kelompok (k) terbaik dengan mendeteksi di mana metrik penggabungan mencapai titik terendah, mirip dengan
menemukan titik terendah di sebuah lembah pada grafik.

**Term Frequency (TF)** : cara untuk mengubah teks menjadi angka dengan menghitung 
seberapa sering sebuah kata muncul di dalam satu komentar. Semakin sering suatu kata 
digunakan dalam sebuah komentar, semakin tinggi skornya, tanpa memperhitungkan kemunculan 
kata tersebut di komentar lainnya.

**Summarization** : setelah clustering, kalimat ringkasan pendek
dibuat untuk setiap kelompok guna mendeskripsikan tentang apa isi komentar-komentar di dalamnya.
        """)

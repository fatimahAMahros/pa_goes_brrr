import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.queries import (
    get_available_months, get_runs_for_month, get_run, get_valley_data,
    get_clusters_for_run, get_sample_comments
)

LINKAGE_OPTIONS = ["complete", "average", "single", "centroid"]
SCENARIO_OPTIONS = [1, 2, 3, 4]

def render():
    st.title("Metode & Hasil Klastering")
    st.markdown(
        "Halaman ini menggabungkan pencarian nilai k optimal menggunakan **Valley-Tracing** "
        "dengan eksplorasi hasil topik pembicaraan pelanggan (Opinion Mining). "
        "Pilih bulan dan konfigurasi klastering di bawah ini."
    )

    st.divider()

    #Slectors
    months = get_available_months()
    if not months:
        st.warning("Belum ada data hasil klastering yang ditemukan di dalam database.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_month = st.selectbox(
            "Bulan", 
            months, 
            format_func=format_month_display, 
            key="mr_month"
        )
    with col2:
        selected_scenario = st.selectbox("Skenario", SCENARIO_OPTIONS, key="mr_scenario", 
                                         index=SCENARIO_OPTIONS.index(1))
    with col3:
        selected_linkage = st.selectbox("Metode Linkage", LINKAGE_OPTIONS, key="mr_linkage", 
                                        index=LINKAGE_OPTIONS.index("complete"))

    run = get_run(selected_month, selected_scenario, selected_linkage)

    # Rekomendasi Kombinasi
    st.markdown(
        """
        <div style="
            background-color: #dcfce7;
            border: 1px solid #16a34a;
            border-left: 4px solid #16a34a;
            border-radius: 0.5rem;
            padding: 0.85rem 1.1rem;
            margin: 0.75rem 0 1rem 0;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        ">
            <div style="flex-shrink: 0; margin-top: 1px;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                    stroke-width="1.5" stroke="#16a34a" width="18" height="18">
                    <path stroke-linecap="round" stroke-linejoin="round"
                        d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
                </svg>
            </div>
            <div style="font-size: 13.5px; color: #0F172A; line-height: 1.55;">
                <span style="font-weight: 600;">Kombinasi yang Direkomendasikan: Complete Linkage – Skenario 4.</span>
                Hasil kombinasi ini cenderung paling mudah dibaca, meskipun tidak selalu optimal untuk setiap bulan.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    if run is None:
        st.info(
            f"Belum ada hasil untuk **{selected_month} · Skenario {selected_scenario} · "
            f"Linkage {selected_linkage.capitalize()}**. "
            "Jalankan clustering untuk kombinasi ini terlebih dahulu."
        )
        # _show_method_explainer()
        return

    _show_run_status_banner(run)

    if (run.get("is_recommended") or run["status"] == "done") and run.get("notes"):
        st.markdown(
            f"""
            <div style="
                background-color: #F0E6E0; 
                padding: 1rem 1.2rem; 
                border-radius: 0.5rem; 
                border: 1px solid #E2E8F0; 
                border-left: 4px solid #D85A30; 
                margin-top: 15px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            ">
                <div style="font-size: 14px; font-weight: 600; color: #0F172A; margin-bottom: 6px;">
                    Ringkasan Komentar
                </div>
                <div style="font-size: 14px; color: #334155; line-height: 1.5;">
                    {run['notes']}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.divider()

    # VALLEY-TRACING
    st.subheader("Kurva Valley-Tracing: Penentuan k Optimal")
    valley_df = get_valley_data(run["id"])

    if valley_df.empty:
        st.info("Data kurva valley-tracing belum tersedia untuk kombinasi ini.")
    else:
        optimal_k = run["optimal_k"]
        _plot_valley_curve(valley_df, optimal_k)
        st.caption(
            f"Lembah pada **k = {optimal_k}** terpilih sebagai jumlah klaster "
            "optimal — ini adalah titik di mana metrik berhenti membaik secara "
            "signifikan saat jumlah klaster ditambah."
        )

    st.divider()

    # HASIL KLASTERING
    st.subheader("Distribusi & Ringkasan Klaster")
    
    if run["status"] == "dominant":
        _show_dominant_summary(run)
    else:
        clusters = get_clusters_for_run(run["id"])
        if clusters.empty:
            st.info("Data detail klaster belum dimuat untuk run ini.")
        else:
            # --- Overview metrics ---
            total_comments = clusters["comment_count"].sum()
            largest_pct = clusters["comment_count"].max() / total_comments if total_comments > 0 else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Jumlah Klaster (k)", run["optimal_k"])
            m2.metric("Total Komentar", f"{total_comments:,}")
            m3.metric("Klaster Terbesar", f"{largest_pct:.0%}")

            st.write("")
            
            #Distrib chart
            st.markdown("**Distribusi Komentar per Klaster**")
            _plot_cluster_bar(clusters)

            #Cluster cardds
            st.markdown("**Detail Ringkasan Klaster**")
            _show_cluster_cards(clusters, run["id"])

    st.divider()

    # TABEL REKAPITULASI
    st.subheader("Semua Hasil Klastering Bulan Ini")
    runs_df = get_runs_for_month(selected_month)
    if not runs_df.empty:
        _show_runs_table(runs_df)

    st.divider()
    # _show_method_explainer()


# HELPERs

def _show_run_status_banner(run: dict):
    status = run["status"]
    is_rec = run["is_recommended"]

    if is_rec:
        st.success(
            f"**Kombinasi Rekomendasi** — "
            f"Skenario {run['scenario']} · Linkage {run['linkage'].capitalize()} · "
            f"k = {run['optimal_k']}"
        )
    elif status == "dominant":
        pct = run.get("dominant_threshold")
        pct_str = f" ({pct:.0%} komentar berada di satu klaster)" if pct else ""
        
        text = (
            f"<div style='margin-bottom: 5px;'><b>Terdeteksi Klaster Dominan{pct_str}.</b></div>"
            "<div style='font-size: 14px; opacity: 0.95;'>"
            "Nilai k optimal sangat rendah atau ekstrem, sehingga sebagian besar komentar menumpuk "
            "ke dalam satu klaster saja. Proses peringkasan <i>(summarization)</i> dilewati."
            "</div>"
        )
        
        st.markdown(
            f"""
            <div style="
                background-color: #fee2e2; 
                color: #7f1d1d; 
                padding: 1rem 1.2rem; 
                border-radius: 0.5rem; 
                border: 1px solid #fca5a5;
                border-left: 5px solid #ef4444;
                box-shadow: 0 1px 3px rgba(0,0,0,0.07);
                display: flex;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 1rem;
            ">
                <div style="flex-shrink: 0; margin-top: 2px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="#ca8a04" width="22" height="22">
                        <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div style="line-height: 1.4;">{text}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    elif status == "done":
        st.info(
            f"Skenario {run['scenario']} · Linkage {run['linkage'].capitalize()} · "
            f"k = {run['optimal_k']}"
        )
    elif status == "pending":
        st.info("Kombinasi ini belum diproses.")

def _plot_valley_curve(valley_df: pd.DataFrame, optimal_k: int | None):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=valley_df["k_value"],
        y=valley_df["metric"],
        mode="lines+markers",
        name="Metrik Linkage",
        line=dict(color="#185FA5", width=2),
        marker=dict(size=6),
    ))

    if optimal_k is not None and optimal_k in valley_df["k_value"].values:
        opt_metric = valley_df.loc[valley_df["k_value"] == optimal_k, "metric"].values[0]
        fig.add_trace(go.Scatter(
            x=[optimal_k],
            y=[opt_metric],
            mode="markers",
            name=f"k Optimal = {optimal_k}",
            marker=dict(color="#D85A30", size=12, symbol="diamond"),
        ))
        fig.add_vline(
            x=optimal_k,
            line_dash="dash",
            line_color="#D85A30",
            annotation_text=f"k = {optimal_k}",
            annotation_position="top right",
        )

    fig.update_layout(
        xaxis_title="Jumlah Klaster (k)",
        yaxis_title="Metrik Linkage",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0),
        height=340,
    )
    st.plotly_chart(fig, width="stretch")

def _show_dominant_summary(run: dict):
    cols = st.columns(2)
    cols[0].metric("k Optimal", run["optimal_k"] or "—")
    cols[1].metric("Proporsi Klaster Dominan", f"{run['dominant_threshold']:.0%}" if run.get("dominant_threshold") else "—")
    if run.get("notes"):
        st.caption(f"Catatan: {run['notes']}")

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

def _plot_cluster_bar(clusters: pd.DataFrame):
    # Pisahkan klaster utama dan minoritas
    main_clusters = clusters[clusters["display_name"] != "Misc / Minoritas"].copy()
    misc_clusters = clusters[clusters["display_name"] == "Misc / Minoritas"].copy()
    
    # Gunakan klaster utama sebagai dasar data grafik
    plot_df = main_clusters.copy()
    
    # Jika ada klaster minoritas, gabungkan (aggregate) menjadi satu baris
    if not misc_clusters.empty:
        total_misc_comments = misc_clusters["comment_count"].sum()
        misc_count = len(misc_clusters)
        
        # Buat baris baru khusus untuk gabungan minoritas
        misc_row = pd.DataFrame([{
            "cluster_label": "Misc", 
            "display_name": f"Gabungan Minoritas ({misc_count} Klaster)",
            "comment_count": total_misc_comments
        }])
        
        # Tambahkan baris gabungan ini ke dataframe yang akan di-plot
        plot_df = pd.concat([plot_df, misc_row], ignore_index=True)

    labels = plot_df.apply(
        lambda row: row['display_name'] if row['cluster_label'] == 'Misc'
        else f"C{row['cluster_label']} - {row['display_name']}" if pd.notna(row['display_name']) 
        else f"Cluster {row['cluster_label']}",
        axis=1
    )
    
    fig = go.Figure(go.Bar(
        x=plot_df["comment_count"],
        y=labels,
        orientation="h",
        marker_color="#185FA5",
        text=plot_df["comment_count"],
        textposition="auto",
    ))
    
    fig.update_layout(
        xaxis_title="Jumlah Komentar",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=0, r=40, t=10, b=0),
        height=max(300, len(plot_df) * 35), 
    )
    st.plotly_chart(fig, width="stretch")
    
    # Tambahkan keterangan khusus jika ada klaster minoritas yang digabung
    if not misc_clusters.empty:
        st.caption(
            f"*Terdapat **{misc_count} klaster minoritas** yang digabungkan ke dalam "
            "satu grafik bar agar visualisasi distribusi komentar tetap rapi dan fokus pada topik utama."
        )
        
def _show_cluster_cards(clusters: pd.DataFrame, run_id: int):
    #session_state untuk run_id biar gak tumpang tindih
    state_key = f"show_misc_{run_id}"
    if state_key not in st.session_state:
        st.session_state[state_key] = False

    def toggle_misc():
        st.session_state[state_key] = not st.session_state[state_key]

    #pisahklaster utama dan klaster minoritas
    main_clusters = clusters[clusters["display_name"] != "Misc / Minoritas"]
    misc_clusters = clusters[clusters["display_name"] == "Misc / Minoritas"]

    #helper bwat render satu isi expander
    def render_card(row):
        label = row["display_name"] or f"Cluster {row['cluster_label']}"
        dominant_tag = "Dominan" if row["is_dominant"] else ""

        with st.expander(f"**{label}**{dominant_tag} — {row['comment_count']} komentar"):
            # Summary
            if row["summary"]:
                st.markdown(f"**Ringkasan:** {row['summary']}")
            else:
                st.caption("Ringkasan tidak tersedia.")

            # Keywords
            if row["keywords"]:
                st.markdown("**Kata kunci utama:**")
                kw_cols = st.columns(min(len(row["keywords"]), 5))
                for i, kw in enumerate(row["keywords"][:5]):
                    kw_cols[i].markdown(
                        f"<span style='background:#E6F1FB;color:#185FA5;"
                        f"padding:3px 10px;border-radius:8px;font-size:13px'>{kw}</span>",
                        unsafe_allow_html=True
                    )

            st.markdown(" ")

            # Sample comments
            if row["comment_count"] > 0:
                samples = get_sample_comments(run_id, int(row["id"]), n=5)
                if samples:
                    st.markdown("**Contoh komentar:**")
                    for comment in samples:
                        st.markdown(f"> {comment}")
                else:
                    st.caption("Contoh komentar belum dipetakan di dalam database.")

    #render semua klaster utama secara default
    for _, row in main_clusters.iterrows():
        render_card(row)

    #render klaster minor klo ada, dibungkus dengan session_state
    if not misc_clusters.empty:
        # if 'show_misc' True, tampilkan sisa klaster dan tombol buat nutup
        if st.session_state[state_key]:
            for _, row in misc_clusters.iterrows():
                render_card(row)
            
            st.button(
                "Tutup klaster Minoritas", 
                on_click=toggle_misc, 
                key=f"btn_hide_{run_id}"
            )
        # if False, tampilkan tombol readmore
        else:
            st.button(
                f"Lihat {len(misc_clusters)} klaster Minoritas lainnya", 
                on_click=toggle_misc, 
                key=f"btn_show_{run_id}"
            )

def _show_runs_table(runs_df: pd.DataFrame):
    def status_label(row):
        # if row["is_recommended"]:
        #     return "Hasil Terbaik"
        if row["status"] == "dominant":
            return "Klaster Dominan"
        if row["status"] == "done":
            return "Selesai"
        return "Belum Diproses"

    display = runs_df.copy()
    display["Status"] = display.apply(status_label, axis=1)
    display["Skenario"] = display["scenario"].apply(lambda s: f"{s}")
    display["Metode Linkage"] = display["linkage"].str.capitalize()
    display["k Optimal"] = display["optimal_k"].fillna("—").astype(str)
    display["% Klaster Dominan"] = display["dominant_threshold"].apply(
        lambda x: f"{x:.0%}" if pd.notna(x) else "—"
    )
    display["Akurasi (φ)"] = display.get("accuracy", pd.Series([None]*len(display))).apply(
        lambda x: f"{x:.4f}" if pd.notna(x) else "—"
    )

    display = display.sort_values(by=["Metode Linkage", "Skenario"], ascending=[True, True])
    
    st.dataframe(
        display[["Skenario", "Metode Linkage", "k Optimal", "% Klaster Dominan", "Akurasi (φ)"]],
        width="stretch",
        hide_index=True,
    )

# TO DO: FIX THE WORDING. Kata Eus bahasanya masih sulit dimengerti, coba diperbaiki lagi :v. 
# lit:"jujur antara aku yg bodoh atau kamu nggak pinter jelasin"

# def _show_method_explainer():
#     with st.expander("Bagaimana cara kerja Valley-Tracing?"):
#         st.markdown("""
# Valley-Tracing bekerja dengan memetakan metrik jarak linkage pada setiap kemungkinan 
# nilai k. Saat nilai k meningkat, metrik umumnya menurun — yang mengindikasikan bahwa anggota klaster 
# menjadi lebih padat (kompak). Namun pada titik tertentu, penurunannya mulai mendatar, 
# yang berarti penambahan klaster baru tidak lagi memberikan pemisahan topik yang bermakna.

# "Lembah" (valley) adalah titik algoritma di mana metrik berada pada posisi terendah sebelum 
# mulai naik atau mendatar kembali. Inovasi utama dan kebaruan (originality) dalam analisis ini 
# terletak pada penerapan **Valley Tracing yang dipadukan dengan metode Centroid Linkage** pada data komentar sosial media. 
# Pendekatan ini memberikan landasan otomatis untuk menentukan k yang optimal, bukan sekadar menebak.

# Terkadang algoritma akan menghasilkan k yang sangat rendah. Ini biasanya terjadi saat model menemukan 
# satu pemisahan yang sangat jelas berdasarkan perbedaan rasio variansinya, namun kesulitan memisahkan 
# komentar lainnya, sehingga menghasilkan satu klaster dominan yang menampung hampir seluruh komentar.
#         """)
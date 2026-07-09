"""pages/method.py — Bagian 3: Valley-Tracing dan penentuan k optimal."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.queries import get_available_months, get_runs_for_month, get_run, get_valley_data


LINKAGE_OPTIONS = ["complete", "average", "single", "centroid"]
SCENARIO_OPTIONS = [1, 2, 3, 4]


def render():
    st.title("Metode Klastering — Mencari Nilai k Optimal")
    st.markdown(
        "Hierarchical Agglomerative Clustering (HAC) memerlukan penentuan berapa banyak "
        "klaster (k) yang akan digunakan. Proyek ini menggunakan **Valley-Tracing** untuk "
        "mendeteksi nilai k yang optimal secara otomatis dengan mencari titik di mana metrik "
        "linkage mencapai titik terendahnya — atau 'lembah' (valley) pada kurva di bawah ini."
    )

    st.divider()

    # --- Pilihan (Selectors) ---
    months = get_available_months()
    if not months:
        st.warning("Belum ada data hasil klastering yang ditemukan di dalam database.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_month = st.selectbox("Bulan", months, key="method_month")
    with col2:
        selected_scenario = st.selectbox("Skenario", SCENARIO_OPTIONS, key="method_scenario")
    with col3:
        selected_linkage = st.selectbox("Metode Linkage", LINKAGE_OPTIONS, key="method_linkage")

    run = get_run(selected_month, selected_scenario, selected_linkage)

    st.divider()

    if run is None:
        st.info(
            f"Belum ada hasil untuk **{selected_month} · Skenario {selected_scenario} · "
            f"Linkage {selected_linkage.capitalize()}**. "
            "Jalankan pipeline untuk kombinasi ini terlebih dahulu."
        )
        _show_method_explainer()
        return

    # --- Status banner ---
    _show_run_status_banner(run)

    st.divider()

    # --- Grafik Valley-Tracing ---
    st.subheader("Kurva Valley-Tracing: Metrik vs. k")

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

    # --- Tabel Ringkasan Kombinasi ---
    st.subheader("Semua Hasil Klastering Bulan Ini")
    runs_df = get_runs_for_month(selected_month)
    if not runs_df.empty:
        _show_runs_table(runs_df)

    st.divider()
    _show_method_explainer()


def _show_run_status_banner(run: dict):
    status = run["status"]
    is_rec = run["is_recommended"]

    if is_rec:
        st.success(
            f"✅ **Kombinasi Rekomendasi** — "
            f"Skenario {run['scenario']} · Linkage {run['linkage'].capitalize()} · "
            f"k = {run['optimal_k']}"
        )
    elif status == "dominant":
        pct = run.get("dominant_threshold")
        pct_str = f" ({pct:.0%} komentar berada di satu klaster)" if pct else ""
        st.warning(
            f"⚠️ **Terdeteksi Klaster Dominan{pct_str}.** "
            "Nilai k optimal sangat rendah, sehingga hampir seluruh komentar menumpuk "
            "ke dalam satu klaster saja. Proses peringkasan (summarization) dilewati."
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


def _show_runs_table(runs_df: pd.DataFrame):
    def status_label(row):
        if row["is_recommended"]:
            return "⭐ Rekomendasi"
        if row["status"] == "dominant":
            return "⚠️ Klaster Dominan"
        if row["status"] == "done":
            return "✅ Selesai"
        return "⏳ Belum Diproses"

    display = runs_df.copy()
    display["Status"] = display.apply(status_label, axis=1)
    display["Skenario"] = display["scenario"].apply(lambda s: f"Skenario {s}")
    display["Metode Linkage"] = display["linkage"].str.capitalize()
    display["k Optimal"] = display["optimal_k"].fillna("—").astype(str)
    display["% Dominan"] = display["dominant_threshold"].apply(
        lambda x: f"{x:.0%}" if pd.notna(x) else "—"
    )
    display["Akurasi (φ)"] = display["accuracy"].apply(
        lambda x: f"{x:.4f}" if pd.notna(x) else "—"
    )
    st.dataframe(
        display[["Skenario", "Metode Linkage", "k Optimal", "% Dominan", "Status", "notes"]].rename(
            columns={"notes": "Catatan"}
        ),
        width="stretch",
        hide_index=True,
    )


def _show_method_explainer():
    with st.expander("Bagaimana cara kerja Valley-Tracing?"):
        st.markdown("""
Valley-Tracing bekerja dengan memetakan metrik jarak linkage pada setiap kemungkinan 
nilai k. Saat nilai k meningkat, metrik umumnya menurun — yang mengindikasikan bahwa anggota klaster 
menjadi lebih padat (kompak). Namun pada titik tertentu, penurunannya mulai mendatar, 
yang berarti penambahan klaster baru tidak lagi memberikan pemisahan topik yang bermakna.

"Lembah" (valley) adalah titik algoritma di mana metrik berada pada posisi terendah sebelum 
mulai naik atau mendatar kembali. Inovasi utama dan kebaruan (originality) dalam analisis ini 
terletak pada penerapan **Valley Tracing yang dipadukan dengan metode Centroid Linkage**. 
Pendekatan ini memberikan landasan otomatis untuk menentukan k yang optimal, bukan sekadar menebak.

Terkadang algoritma akan menghasilkan k yang sangat rendah (misalnya k=2). Ini biasanya terjadi 
saat model menemukan satu pemisahan yang sangat jelas, namun kesulitan memisahkan komentar lainnya, 
sehingga menghasilkan satu klaster dominan yang menampung hampir seluruh komentar.
        """)
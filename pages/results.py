import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.queries import (
    get_available_months, get_runs_for_month, get_run,
    get_clusters_for_run, get_sample_comments,
)


LINKAGE_OPTIONS = ["complete", "average", "single", "centroid"]
SCENARIO_OPTIONS = [1, 2, 3, 4]


def render():
    st.title("Clustering results")
    st.markdown(
        "Explore what customers are talking about by selecting a month and "
        "clustering configuration below."
    )

    # --- Selectors ---
    months = get_available_months()
    if not months:
        st.warning("No clustering results found in the database.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_month = st.selectbox("Month", months, key="res_month")
    with col2:
        selected_scenario = st.selectbox("Scenario", SCENARIO_OPTIONS, key="res_scenario",
                                          index=SCENARIO_OPTIONS.index(4))
    with col3:
        selected_linkage = st.selectbox("Linkage", LINKAGE_OPTIONS, key="res_linkage",
                                         index=LINKAGE_OPTIONS.index("complete"))

    run = get_run(selected_month, selected_scenario, selected_linkage)

    st.divider()

    if run is None:
        st.info("No results for this combination. Select a different month or method.")
        return

    # --- Status banner ---
    if run["is_recommended"]:
        st.success("⭐ This is the recommended combination (Scenario 4 · Complete linkage).")
    elif run["status"] == "dominant":
        pct = run.get("dominant_threshold")
        pct_str = f" ({pct:.0%} of comments in one cluster)" if pct else ""
        st.warning(
            f"⚠️ Dominant cluster detected{pct_str}. "
            "This configuration produced a very low optimal k, meaning most "
            "comments ended up in a single cluster. "
            "Summaries are not available for this run. "
            "Try **Scenario 4 · Complete linkage** for the best result."
        )
        _show_dominant_summary(run)
        return

    # --- Load cluster data ---
    clusters = get_clusters_for_run(run["id"])
    if clusters.empty:
        st.info("Cluster data not yet loaded for this run.")
        return

    # --- Overview metrics ---
    total_comments = clusters["comment_count"].sum()
    largest_pct = clusters["comment_count"].max() / total_comments if total_comments > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Clusters found (k)", run["optimal_k"])
    m2.metric("Total comments", f"{total_comments:,}")
    m3.metric("Largest cluster", f"{largest_pct:.0%} of comments")

    st.divider()

    # --- Distribution chart ---
    st.subheader("Comment distribution across clusters")
    _plot_cluster_bar(clusters)

    st.divider()

    # --- Cluster cards ---
    st.subheader("Cluster summaries")
    _show_cluster_cards(clusters, run["id"])


def _show_dominant_summary(run: dict):
    """Minimal view for dominant-cluster runs."""
    st.subheader("Run summary")
    cols = st.columns(2)
    cols[0].metric("Optimal k", run["optimal_k"] or "—")
    cols[1].metric("Dominant cluster", f"{run['dominant_threshold']:.0%}" if run.get("dominant_threshold") else "—")
    if run.get("notes"):
        st.caption(run["notes"])


def _plot_cluster_bar(clusters: pd.DataFrame):
    labels = clusters["display_name"].fillna(
        clusters["cluster_label"].astype(str).apply(lambda x: f"Cluster {x}")
    )
    fig = go.Figure(go.Bar(
        x=clusters["comment_count"],
        y=labels,
        orientation="h",
        marker_color="#185FA5",
        text=clusters["comment_count"],
        textposition="outside",
    ))
    fig.update_layout(
        xaxis_title="Number of comments",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=0, r=40, t=10, b=0),
        height=max(250, len(clusters) * 42),
    )
    st.plotly_chart(fig, width="stretch")


def _show_cluster_cards(clusters: pd.DataFrame, run_id: int):
    for _, row in clusters.iterrows():
        label = row["display_name"] or f"Cluster {row['cluster_label']}"
        dominant_tag = " 🔴 Dominant" if row["is_dominant"] else ""

        with st.expander(f"**{label}**{dominant_tag} — {row['comment_count']} comments"):
            # Summary
            if row["summary"]:
                st.markdown(f"**Summary:** {row['summary']}")
            else:
                st.caption("No summary available.")

            # Keywords
            if row["keywords"]:
                st.markdown("**Top keywords:**")
                kw_cols = st.columns(min(len(row["keywords"]), 5))
                for i, kw in enumerate(row["keywords"][:5]):
                    kw_cols[i].markdown(
                        f"<span style='background:#E6F1FB;color:#185FA5;"
                        f"padding:3px 10px;border-radius:8px;font-size:13px'>{kw}</span>",
                        unsafe_allow_html=True
                    )

            st.markdown(" ")

            # Sample comments (lazy load on expand)
            if row["comment_count"] > 0:
                samples = get_sample_comments(run_id, int(row["id"]), n=5)
                if samples:
                    st.markdown("**Sample comments:**")
                    for comment in samples:
                        st.markdown(
                            f"> {comment}",
                        )
                else:
                    st.caption(
                        "Sample comments not available — populate "
                        "`comment_cluster_map` to enable this."
                    )

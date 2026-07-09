import streamlit as st
from views import overview, preprocessing,clustering

st.set_page_config(
    page_title="PDAM Surya Sembada - Opinion Mining",
    page_icon="static/water-svgrepo-com.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

p_overview = st.Page(overview.render, title="Overview", url_path="overview")
p_preprocessing = st.Page(preprocessing.render, title="Preprocessing", url_path="preprocessing")
p_clustering = st.Page(clustering.render, title="Clustering", url_path="clustering")

pg = st.navigation(
    [p_overview, p_preprocessing, p_clustering], 
    position="hidden"
)

with st.sidebar:
    st.image("static/vecteezy_water-wave-icon-vector_10454300-Photoroom.png", use_container_width=True)
    st.markdown("### Komentar Instagram Perumda Surya Sembada")
    st.divider()

    st.page_link(p_overview, label="Overview")
    st.page_link(p_preprocessing, label="Preprocessing")
    st.page_link(p_clustering, label="Clustering")

    st.divider()
    st.caption("Final Project · Automatic Clustering & Summarization")

pg.run()
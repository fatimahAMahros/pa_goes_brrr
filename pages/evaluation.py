import streamlit as st
import pandas as pd


def render():
    st.title("Evaluation")
    st.markdown(
        "This section summarises how well the clustering results reflect "
        "the actual topics in the data, and what comes next."
    )

    st.divider()

    # --- Accuracy status ---
    st.subheader("Pairwise accuracy")
    st.info(
        "⏳ **Work in progress.** Ground-truth labels are currently being "
        "assigned manually to a sample of comments. Once labelling is complete, "
        "pairwise accuracy will be calculated by comparing whether pairs of "
        "comments that belong to the same human-assigned topic are also placed "
        "in the same cluster."
    )

    with st.expander("How is pairwise accuracy calculated?"):
        st.markdown("""
For a set of labelled comments, every possible pair is examined. A pair is
considered:

- **True Positive (TP)** — same human label, same cluster
- **True Negative (TN)** — different human label, different cluster
- **False Positive (FP)** — different human label, same cluster
- **False Negative (FN)** — same human label, different cluster

Pairwise accuracy = (TP + TN) / (TP + TN + FP + FN)

This metric captures both how well the clustering groups similar comments
together *and* how well it separates dissimilar ones.
        """)

    st.divider()

    # --- Qualitative observations ---
    st.subheader("Qualitative observations (so far)")

    observations = [
        (
            "Complete linkage · Scenario 4 gives the most interpretable result",
            "High k with balanced cluster sizes. Summary sentences are coherent "
            "and keywords match the expected topics (billing, outages, water quality, etc.).",
        ),
        (
            "Low-k runs produce a dominant cluster",
            "For most linkage + scenario combinations on October 2025 data, "
            "Valley-Tracing returns k=2 or k=3 with one cluster containing "
            "over 80% of comments. This makes summarization uninformative.",
        ),
        (
            "September 2025 shows a similar pattern",
            "Preliminary results for September 2025 with Scenario 4 · Complete "
            "linkage mirror the October results — encouraging, but other months "
            "remain to be processed.",
        ),
    ]

    for title, detail in observations:
        with st.expander(f"**{title}**"):
            st.markdown(detail)

    st.divider()

    # --- Limitations ---
    st.subheader("Limitations")

    limitations = [
        "Only October 2025 is fully processed; results for other months are pending.",
        "Ground-truth labels are still being assigned — quantitative accuracy is not yet available.",
        "Indonesian slang and code-switching (Indonesian/Javanese) may not be fully normalised by the slang dictionary.",
        "Very short comments (single words, emojis only) may not cluster meaningfully.",
        "Valley-Tracing tends to prefer low k for some configurations, which limits the granularity of topics found.",
    ]

    for lim in limitations:
        st.markdown(f"- {lim}")

    st.divider()

    # --- Next steps ---
    st.subheader("Next steps")

    next_steps = [
        ("Complete manual labelling", "Finish assigning ground-truth labels to the sample set."),
        ("Calculate pairwise accuracy", "Run the pairwise evaluation once labels are ready."),
        ("Process remaining months", "Run the full pipeline on Nov 2025 – present data."),
        ("Expand slang dictionary", "Add domain-specific PDAM/utility slang that may be mishandled."),
        ("Compare across months", "Examine whether the same topics recur month to month."),
    ]

    for step, detail in next_steps:
        st.markdown(f"**{step}** — {detail}")

"""
pipeline.py
-----------
One script that handles the entire flow from raw CSV → SQLite:
  1. Load & upsert comments from CSV (with upsert logic for updates)
  2. Run all linkage × scenario combinations and store outputs
  3. Auto-detect dominant clusters
  4. Auto-run summarization on non-dominant runs and store results

Usage:
    # First time — load comments for a month
    python pipeline.py load-comments --csv instagram_comments.csv --month 2025-10

    # Run all clustering for a month (all linkages × all scenarios)
    python pipeline.py cluster --month 2025-10

    # Summarize all valid runs for a month (skips dominant clusters automatically)
    python pipeline.py summarize --month 2025-10

    # Do everything in one shot
    python pipeline.py run-all --csv instagram_comments.csv --month 2025-10
"""

import sqlite3
import json
import argparse
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import pdist

# ── adjust this import to wherever your project's preprocessing lives ──
# from your_preprocessing_module import preprocess_text, extract_features
# For now we include a stub so the file is runnable without your modules.

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "pdam.db")

# ── Tuning knobs ────────────────────────────────────────────────────────
DOMINANT_THRESHOLD = 0.60   # if any cluster holds ≥60% of comments → dominant
SCENARIOS = {
    1: "Scenario 1 (Unigram)",
    2: "Scenario 2 (Unigram + Bigram)",
    3: "Scenario 3 (Threshold)",
    4: "Scenario 4 (Threshold + Binary)",
}
LINKAGES = ["single", "complete", "average", "centroid"]


# ════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ════════════════════════════════════════════════════════════════════════

def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables. Safe to call multiple times (IF NOT EXISTS)."""
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS comments (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        comment_id          TEXT    UNIQUE NOT NULL,   -- original Instagram comment_id
        month               TEXT    NOT NULL,          -- e.g. '2025-10'
        post_id             TEXT,
        post_url            TEXT,
        raw_text            TEXT    NOT NULL,
        created_at          TEXT,
        user_id             TEXT,
        username            TEXT,
        processed_text      TEXT,                      -- updated separately after preprocessing
        tokens              TEXT,                      -- JSON list; updated separately
        last_updated        TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS clustering_runs (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        month               TEXT    NOT NULL,
        scenario            INTEGER NOT NULL,
        linkage             TEXT    NOT NULL,
        feature_shape       TEXT,                      -- e.g. '(1102, 1059)' — stored as text
        optimal_k           INTEGER,
        best_k_valley       INTEGER,                   -- best k from valley-tracing
        k_closest_max_d     INTEGER,                   -- closest value to max ∂
        max_d               REAL,                      -- max ∂ value
        second_max_d        REAL,
        accuracy_score      REAL,                      -- the 'Acuuracy' metric from your output
        candidate_ks        TEXT,                      -- JSON list of valley-tracing candidates
        status              TEXT    DEFAULT 'pending', -- pending / done / dominant
        dominant_cluster_id INTEGER,                   -- which cluster_label is dominant (if any)
        dominant_pct        REAL,                      -- e.g. 0.91 = 91%
        is_recommended      INTEGER DEFAULT 0,
        notes               TEXT,
        created_at          TEXT    DEFAULT (datetime('now')),
        UNIQUE(month, scenario, linkage)
    );

    CREATE TABLE IF NOT EXISTS clusters (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id          INTEGER NOT NULL REFERENCES clustering_runs(id) ON DELETE CASCADE,
        cluster_label   INTEGER NOT NULL,
        comment_count   INTEGER DEFAULT 0,
        is_dominant     INTEGER DEFAULT 0,
        display_name    TEXT,                          -- you fill this in manually later
        summary         TEXT,                          -- filled by summarization step
        keywords        TEXT,                          -- JSON list; filled by summarization step
        UNIQUE(run_id, cluster_label)
    );

    CREATE TABLE IF NOT EXISTS comment_cluster_map (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id      INTEGER NOT NULL REFERENCES clustering_runs(id) ON DELETE CASCADE,
        comment_id  INTEGER NOT NULL REFERENCES comments(id),
        cluster_id  INTEGER NOT NULL REFERENCES clusters(id),
        UNIQUE(run_id, comment_id)
    );

    CREATE TABLE IF NOT EXISTS valley_tracing_data (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id      INTEGER NOT NULL REFERENCES clustering_runs(id) ON DELETE CASCADE,
        k_value     INTEGER NOT NULL,
        metric      REAL    NOT NULL,
        UNIQUE(run_id, k_value)
    );

    CREATE TABLE IF NOT EXISTS global_summaries (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id              INTEGER NOT NULL REFERENCES clustering_runs(id) ON DELETE CASCADE,
        total_komentar      INTEGER,
        total_klaster       INTEGER,
        klaster_dirangkum   INTEGER,
        ringkasan_global    TEXT,
        raw_json            TEXT,                      -- store original JSON blob
        created_at          TEXT    DEFAULT (datetime('now')),
        UNIQUE(run_id)
    );
    """)

    conn.commit()
    conn.close()
    print("✓ Database schema ready.")


# ════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD COMMENTS FROM CSV
# ════════════════════════════════════════════════════════════════════════

def load_comments_from_csv(csv_path: str, month: str):
    """
    Load Instagram comments from CSV into the comments table.

    Expected CSV columns (at minimum):
        comment_id, text, post_id, post_url, created_at, user_id, username

    Logic:
    - If comment_id doesn't exist yet → INSERT
    - If comment_id exists and raw_text changed → UPDATE raw_text + clear processed_text
      (forces re-preprocessing on next run)
    - processed_text / tokens are left alone here — they are updated separately
      by your preprocessing step.
    """
    df = pd.read_csv(csv_path)

    # Normalise column names — drop columns we don't need
    keep = {"comment_id", "text", "post_id", "post_url", "created_at", "user_id", "username"}
    df = df[[c for c in df.columns if c in keep]]

    if "text" not in df.columns or "comment_id" not in df.columns:
        raise ValueError("CSV must have at least 'comment_id' and 'text' columns.")

    df["comment_id"] = df["comment_id"].astype(str)
    df["month"] = month

    conn = get_conn()
    cur = conn.cursor()

    inserted = updated = skipped = 0

    for _, row in df.iterrows():
        cid = row["comment_id"]
        raw = str(row.get("text", "")).strip()

        cur.execute("SELECT id, raw_text FROM comments WHERE comment_id = ?", (cid,))
        existing = cur.fetchone()

        if existing is None:
            # Brand-new comment
            cur.execute("""
                INSERT INTO comments
                    (comment_id, month, post_id, post_url, raw_text,
                     created_at, user_id, username)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, month,
                row.get("post_id"), row.get("post_url"), raw,
                row.get("created_at"), row.get("user_id"), row.get("username"),
            ))
            inserted += 1

        elif existing["raw_text"] != raw:
            # Text changed (shouldn't happen for Instagram data, but handles re-scrapes)
            cur.execute("""
                UPDATE comments
                SET raw_text = ?,
                    processed_text = NULL,
                    tokens = NULL,
                    last_updated = datetime('now')
                WHERE comment_id = ?
            """, (raw, cid))
            updated += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()

    total = inserted + updated + skipped
    print(f"✓ Comments loaded  | month={month}  total={total}  "
          f"new={inserted}  updated={updated}  unchanged={skipped}")


def update_processed_text(month: str, processed_df: pd.DataFrame):
    """
    After your preprocessing runs, call this to save processed_text + tokens
    back into the DB.

    processed_df must have columns: comment_id (str), processed_text (str),
    tokens (list of str — will be JSON-encoded).
    """
    conn = get_conn()
    cur = conn.cursor()
    updated = 0

    for _, row in processed_df.iterrows():
        tokens_json = json.dumps(row["tokens"]) if isinstance(row["tokens"], list) else row["tokens"]
        cur.execute("""
            UPDATE comments
            SET processed_text = ?,
                tokens = ?,
                last_updated = datetime('now')
            WHERE comment_id = ?
        """, (row["processed_text"], tokens_json, str(row["comment_id"])))
        updated += cur.rowcount

    conn.commit()
    conn.close()
    print(f"✓ processed_text updated for {updated} comments (month={month})")


# ════════════════════════════════════════════════════════════════════════
# STEP 2 & 3 — CLUSTER + AUTO-DETECT DOMINANT
# ════════════════════════════════════════════════════════════════════════

def detect_dominant(labels: np.ndarray, threshold: float = DOMINANT_THRESHOLD):
    """
    Returns (is_dominant, dominant_label, dominant_pct).
    is_dominant is True if the largest cluster holds ≥ threshold of all comments.
    """
    unique, counts = np.unique(labels, return_counts=True)
    total = len(labels)
    max_idx = np.argmax(counts)
    dominant_pct = counts[max_idx] / total
    is_dominant = dominant_pct >= threshold
    return is_dominant, int(unique[max_idx]), float(dominant_pct)


def save_clustering_run(
    month: str,
    scenario: int,
    linkage_method: str,
    feature_matrix,           # scipy-compatible 2D array (tfidf output)
    comment_ids: list,        # list of DB comment IDs (integers), same order as feature_matrix
    valley_result: dict,      # output dict from your valley_tracing function
    is_recommended: bool = False,
):
    """
    Runs HAC + valley-tracing, detects dominant cluster, saves everything to DB.

    valley_result keys expected (matching your existing output):
        best_k      : int — best k from valley-tracing
        k_curv      : int — fallback k (closest to max ∂)
        Z           : linkage matrix
        max_d       : float
        second_max_d: float
        accuracy    : float (your 'Acuuracy' metric)
        candidates  : list of int — candidate k values
        shape       : tuple — feature matrix shape
        valley_ks   : list of (k, metric) tuples for the curve chart
    """
    conn = get_conn()
    cur = conn.cursor()

    # ── Determine k ──────────────────────────────────────────────────
    k_used = int(valley_result.get("best_k") or valley_result.get("k_curv"))
    Z = valley_result["Z"]
    labels = fcluster(Z, t=k_used, criterion="maxclust")

    # ── Dominant cluster detection ────────────────────────────────────
    is_dominant, dominant_label, dominant_pct = detect_dominant(labels)
    status = "dominant" if is_dominant else "done"

    shape_str = str(valley_result.get("shape", ""))
    candidates_json = json.dumps(valley_result.get("candidates", []))

    # ── Upsert clustering_runs ────────────────────────────────────────
    cur.execute("""
        INSERT INTO clustering_runs
            (month, scenario, linkage, feature_shape, optimal_k,
             best_k_valley, k_closest_max_d, max_d, second_max_d,
             accuracy_score, candidate_ks, status,
             dominant_cluster_id, dominant_pct,
             is_recommended, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(month, scenario, linkage) DO UPDATE SET
            feature_shape       = excluded.feature_shape,
            optimal_k           = excluded.optimal_k,
            best_k_valley       = excluded.best_k_valley,
            k_closest_max_d     = excluded.k_closest_max_d,
            max_d               = excluded.max_d,
            second_max_d        = excluded.second_max_d,
            accuracy_score      = excluded.accuracy_score,
            candidate_ks        = excluded.candidate_ks,
            status              = excluded.status,
            dominant_cluster_id = excluded.dominant_cluster_id,
            dominant_pct        = excluded.dominant_pct,
            is_recommended      = excluded.is_recommended,
            created_at          = datetime('now')
    """, (
        month, scenario, linkage_method, shape_str, k_used,
        int(valley_result.get("best_k", k_used)),
        int(valley_result.get("k_curv", k_used)),
        valley_result.get("max_d"),
        valley_result.get("second_max_d"),
        valley_result.get("accuracy"),
        candidates_json, status,
        dominant_label if is_dominant else None,
        dominant_pct if is_dominant else None,
        1 if is_recommended else 0,
    ))

    cur.execute("""
        SELECT id FROM clustering_runs
        WHERE month=? AND scenario=? AND linkage=?
    """, (month, scenario, linkage_method))
    run_id = cur.fetchone()["id"]

    # ── Clear old cluster data for this run (in case of re-run) ──────
    cur.execute("DELETE FROM comment_cluster_map WHERE run_id=?", (run_id,))
    cur.execute("DELETE FROM valley_tracing_data  WHERE run_id=?", (run_id,))
    cur.execute("DELETE FROM clusters              WHERE run_id=?", (run_id,))

    # ── Insert clusters ───────────────────────────────────────────────
    unique_labels, counts = np.unique(labels, return_counts=True)
    cluster_db_ids = {}

    for lbl, cnt in zip(unique_labels, counts):
        is_dom = 1 if (is_dominant and lbl == dominant_label) else 0
        cur.execute("""
            INSERT INTO clusters (run_id, cluster_label, comment_count, is_dominant)
            VALUES (?, ?, ?, ?)
        """, (run_id, int(lbl), int(cnt), is_dom))
        cluster_db_ids[int(lbl)] = cur.lastrowid

    # ── Map comments → clusters ───────────────────────────────────────
    for comment_db_id, cluster_label in zip(comment_ids, labels):
        cid = cluster_db_ids[int(cluster_label)]
        cur.execute("""
            INSERT OR IGNORE INTO comment_cluster_map (run_id, comment_id, cluster_id)
            VALUES (?, ?, ?)
        """, (run_id, comment_db_id, cid))

    # ── Valley-tracing curve ──────────────────────────────────────────
    for k_val, metric_val in valley_result.get("valley_ks", []):
        cur.execute("""
            INSERT OR REPLACE INTO valley_tracing_data (run_id, k_value, metric)
            VALUES (?, ?, ?)
        """, (run_id, int(k_val), float(metric_val)))

    conn.commit()
    conn.close()

    dom_msg = (f"  ⚠ DOMINANT cluster {dominant_label} "
               f"({dominant_pct:.1%} of comments)" if is_dominant else "")
    print(f"  ✓ Saved | linkage={linkage_method:10s} scenario={scenario} "
          f"k={k_used:4d}  status={status}{dom_msg}")
    return run_id, status


def run_all_clustering_for_month(month: str, build_features_fn, valley_tracing_fn):
    """
    Run all 4 linkages × 4 scenarios for a given month and save all to DB.

    You need to pass in two callables from your own code:
      build_features_fn(month, scenario_id) → (feature_matrix, comment_ids_list)
        where comment_ids_list is the list of SQLite comment.id integers
        in the same order as rows in feature_matrix.

      valley_tracing_fn(Z) → dict with keys:
        best_k, k_curv, Z, max_d, second_max_d, accuracy,
        candidates, shape, valley_ks (list of (k, metric) tuples)
    """
    print(f"\n{'='*60}")
    print(f"  Clustering: month={month}")
    print(f"{'='*60}")

    for scenario_id in SCENARIOS:
        print(f"\n── Scenario {scenario_id}: {SCENARIOS[scenario_id]} ──")
        feature_matrix, comment_ids = build_features_fn(month, scenario_id)

        for linkage_method in LINKAGES:
            print(f"   Linkage: {linkage_method}", end=" ... ")
            try:
                Z = linkage(feature_matrix, method=linkage_method, metric="cosine")
                valley_result = valley_tracing_fn(Z)
                valley_result["shape"] = feature_matrix.shape

                is_rec = (scenario_id == 4 and linkage_method == "complete")

                save_clustering_run(
                    month=month,
                    scenario=scenario_id,
                    linkage_method=linkage_method,
                    feature_matrix=feature_matrix,
                    comment_ids=comment_ids,
                    valley_result=valley_result,
                    is_recommended=is_rec,
                )
            except Exception as e:
                print(f"\n   ✗ Error: {e}")

    print(f"\n✓ All clustering runs saved for month={month}")


# ════════════════════════════════════════════════════════════════════════
# STEP 4 — AUTO-SUMMARIZE ALL VALID RUNS
# ════════════════════════════════════════════════════════════════════════

def save_cluster_summaries_from_json(run_id: int, global_summary_json: dict):
    """
    Parse a global_summary.json (like your uploaded file) and save
    cluster-level and global summaries to the DB for the given run_id.

    This is for importing existing JSON outputs you've already generated.
    """
    conn = get_conn()
    cur = conn.cursor()

    # ── Global summary ────────────────────────────────────────────────
    cur.execute("""
        INSERT OR REPLACE INTO global_summaries
            (run_id, total_komentar, total_klaster, klaster_dirangkum,
             ringkasan_global, raw_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        global_summary_json.get("total_komentar"),
        global_summary_json.get("total_klaster"),
        global_summary_json.get("klaster_dirangkum"),
        global_summary_json.get("ringkasan_global"),
        json.dumps(global_summary_json, ensure_ascii=False),
    ))

    # ── Per-cluster summaries ─────────────────────────────────────────
    # cluster_summaries.csv has: cluster_id (original), jumlah_komentar, tema, ringkasan
    # We match on cluster_label (cast to str) OR on 'misc' which maps to label 0.
    saved = 0
    for entry in global_summary_json.get("klaster_utama", []):
        original_id = str(entry.get("cluster_id", "")).strip()
        tema = entry.get("tema")
        ringkasan = entry.get("ringkasan")

        # The cluster_id in the JSON is the original label from your pipeline.
        # If your pipeline uses integer cluster labels, convert here.
        # 'misc' is a special case — map it to label 0 or handle as needed.
        if original_id == "misc":
            # Try matching by 'misc' display_name or just find the largest cluster
            cur.execute("""
                UPDATE clusters
                SET display_name = ?,
                    summary = ?
                WHERE run_id = ?
                  AND is_dominant = 1
            """, (tema, ringkasan, run_id))
        else:
            try:
                label_int = int(original_id)
                cur.execute("""
                    UPDATE clusters
                    SET display_name = ?,
                        summary = ?
                    WHERE run_id = ? AND cluster_label = ?
                """, (tema, ringkasan, run_id, label_int))
            except ValueError:
                pass  # non-integer cluster id we can't map

        saved += cur.rowcount

    conn.commit()
    conn.close()
    print(f"✓ Saved global summary + {saved} cluster summaries for run_id={run_id}")


def run_summarization_for_month(month: str, summarize_fn):
    """
    For every non-dominant run in a given month, fetch comments per cluster
    and call your summarize_fn, then store results.

    summarize_fn signature:
        summarize_fn(clusters: list[dict]) → dict
        where each cluster dict has:
            cluster_label, comment_count, comments (list of str)
        and the return value is a global_summary dict matching your JSON format.

    Dominant runs are automatically skipped with a log message.
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, scenario, linkage, optimal_k, status
        FROM clustering_runs
        WHERE month = ? AND status != 'pending'
        ORDER BY scenario, linkage
    """, (month,))
    runs = [dict(r) for r in cur.fetchall()]
    conn.close()

    if not runs:
        print(f"No completed runs found for month={month}")
        return

    print(f"\n{'='*60}")
    print(f"  Summarization: month={month}")
    print(f"{'='*60}")

    for run in runs:
        run_id = run["id"]
        tag = f"scenario={run['scenario']} linkage={run['linkage']}"

        if run["status"] == "dominant":
            print(f"  ⚠ Skipping {tag} — dominant cluster detected.")
            continue

        # Check if already summarized
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM global_summaries WHERE run_id=?", (run_id,))
        already_done = cur.fetchone()
        conn.close()

        if already_done:
            print(f"  ↷ Already summarized: {tag}")
            continue

        print(f"  ◌ Summarizing {tag} (k={run['optimal_k']})...")

        # ── Fetch comments grouped by cluster ────────────────────────
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT cl.cluster_label, cl.comment_count,
                   GROUP_CONCAT(c.processed_text, '|||') as texts
            FROM clusters cl
            JOIN comment_cluster_map m ON m.cluster_id = cl.id
            JOIN comments c ON c.id = m.comment_id
            WHERE cl.run_id = ?
              AND c.processed_text IS NOT NULL
            GROUP BY cl.id
            ORDER BY cl.comment_count DESC
        """, (run_id,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            print(f"    ✗ No processed_text found — run preprocessing first.")
            continue

        clusters_input = [
            {
                "cluster_label": row["cluster_label"],
                "comment_count": row["comment_count"],
                "comments": row["texts"].split("|||") if row["texts"] else [],
            }
            for row in rows
        ]

        try:
            summary_json = summarize_fn(clusters_input)
            save_cluster_summaries_from_json(run_id, summary_json)
            print(f"    ✓ Done.")
        except Exception as e:
            print(f"    ✗ Summarization failed: {e}")

    print(f"\n✓ Summarization complete for month={month}")


# ════════════════════════════════════════════════════════════════════════
# IMPORT EXISTING OUTPUTS (for data you've already generated)
# ════════════════════════════════════════════════════════════════════════

def import_existing_csv_clustering(
    csv_path: str,
    month: str,
    scenario: int,
    linkage_method: str,
    valley_metadata: dict,
):
    """
    Import an existing clustering output CSV (like sept25_clustering_output_copy.csv)
    that has columns: comment_id, komentar (raw text), cluster.

    valley_metadata should be the dict you printed earlier, e.g.:
    {
        "best_k": 884,
        "k_curv": 960,
        "max_d": 71.4078,
        "second_max_d": 64.0435,
        "accuracy": 1.1150,
        "candidates": [960, 884, 740, ...],
        "valley_ks": [(960, 0.82), (884, 0.74), ...]  # if you have the curve
    }
    """
    df = pd.read_csv(csv_path)
    required = {"comment_id", "cluster"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV must have columns: {required}")

    df["comment_id"] = df["comment_id"].astype(str)

    conn = get_conn()
    cur = conn.cursor()

    # Look up DB comment IDs from comment_id strings
    placeholders = ",".join("?" * len(df))
    cur.execute(
        f"SELECT id, comment_id FROM comments WHERE comment_id IN ({placeholders}) AND month=?",
        df["comment_id"].tolist() + [month]
    )
    id_map = {row["comment_id"]: row["id"] for row in cur.fetchall()}
    conn.close()

    if not id_map:
        print("⚠ No matching comment_ids found in DB. Run load-comments first.")
        return

    labels = np.array([df.loc[df["comment_id"] == cid, "cluster"].values[0]
                       for cid in id_map.keys()])
    comment_db_ids = list(id_map.values())

    # Build a fake valley_result compatible with save_clustering_run
    valley_result = {
        "Z": None,           # we don't have Z for imported runs
        "best_k": valley_metadata.get("best_k"),
        "k_curv": valley_metadata.get("k_curv"),
        "max_d": valley_metadata.get("max_d"),
        "second_max_d": valley_metadata.get("second_max_d"),
        "accuracy": valley_metadata.get("accuracy"),
        "candidates": valley_metadata.get("candidates", []),
        "shape": (len(df), valley_metadata.get("n_features", 0)),
        "valley_ks": valley_metadata.get("valley_ks", []),
    }

    # For imports, we skip the fcluster step and use existing labels directly
    _save_clustering_run_from_labels(
        month=month,
        scenario=scenario,
        linkage_method=linkage_method,
        comment_db_ids=comment_db_ids,
        labels=labels,
        valley_result=valley_result,
    )


def _save_clustering_run_from_labels(
    month, scenario, linkage_method, comment_db_ids, labels, valley_result
):
    """Internal: same as save_clustering_run but accepts pre-computed labels."""
    conn = get_conn()
    cur = conn.cursor()

    k_used = int(valley_result.get("best_k") or valley_result.get("k_curv"))
    is_dominant, dominant_label, dominant_pct = detect_dominant(labels)
    status = "dominant" if is_dominant else "done"
    shape_str = str(valley_result.get("shape", ""))
    candidates_json = json.dumps(valley_result.get("candidates", []))
    is_rec = (scenario == 4 and linkage_method == "complete")

    cur.execute("""
        INSERT INTO clustering_runs
            (month, scenario, linkage, feature_shape, optimal_k,
             best_k_valley, k_closest_max_d, max_d, second_max_d,
             accuracy_score, candidate_ks, status,
             dominant_cluster_id, dominant_pct, is_recommended, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(month, scenario, linkage) DO UPDATE SET
            feature_shape       = excluded.feature_shape,
            optimal_k           = excluded.optimal_k,
            best_k_valley       = excluded.best_k_valley,
            k_closest_max_d     = excluded.k_closest_max_d,
            max_d               = excluded.max_d,
            second_max_d        = excluded.second_max_d,
            accuracy_score      = excluded.accuracy_score,
            candidate_ks        = excluded.candidate_ks,
            status              = excluded.status,
            dominant_cluster_id = excluded.dominant_cluster_id,
            dominant_pct        = excluded.dominant_pct,
            is_recommended      = excluded.is_recommended,
            created_at          = datetime('now')
    """, (
        month, scenario, linkage_method, shape_str, k_used,
        int(valley_result.get("best_k", k_used)),
        int(valley_result.get("k_curv", k_used)),
        valley_result.get("max_d"),
        valley_result.get("second_max_d"),
        valley_result.get("accuracy"),
        candidates_json, status,
        dominant_label if is_dominant else None,
        dominant_pct if is_dominant else None,
        1 if is_rec else 0,
    ))

    cur.execute("SELECT id FROM clustering_runs WHERE month=? AND scenario=? AND linkage=?",
                (month, scenario, linkage_method))
    run_id = cur.fetchone()["id"]

    cur.execute("DELETE FROM comment_cluster_map WHERE run_id=?", (run_id,))
    cur.execute("DELETE FROM valley_tracing_data  WHERE run_id=?", (run_id,))
    cur.execute("DELETE FROM clusters              WHERE run_id=?", (run_id,))

    unique_labels, counts = np.unique(labels, return_counts=True)
    cluster_db_ids = {}
    for lbl, cnt in zip(unique_labels, counts):
        is_dom = 1 if (is_dominant and lbl == dominant_label) else 0
        cur.execute("""
            INSERT INTO clusters (run_id, cluster_label, comment_count, is_dominant)
            VALUES (?, ?, ?, ?)
        """, (run_id, int(lbl), int(cnt), is_dom))
        cluster_db_ids[int(lbl)] = cur.lastrowid

    for comment_db_id, cluster_label in zip(comment_db_ids, labels):
        cid = cluster_db_ids[int(cluster_label)]
        cur.execute("""
            INSERT OR IGNORE INTO comment_cluster_map (run_id, comment_id, cluster_id)
            VALUES (?, ?, ?)
        """, (run_id, comment_db_id, cid))

    for k_val, metric_val in valley_result.get("valley_ks", []):
        cur.execute("""
            INSERT OR REPLACE INTO valley_tracing_data (run_id, k_value, metric)
            VALUES (?, ?, ?)
        """, (run_id, int(k_val), float(metric_val)))

    conn.commit()
    conn.close()

    dom_msg = (f"  ⚠ DOMINANT ({dominant_pct:.1%})" if is_dominant else "")
    print(f"✓ Imported | linkage={linkage_method} scenario={scenario} "
          f"k={k_used} status={status}{dom_msg}")


def import_existing_json_summary(json_path: str, run_id: int):
    """
    Import an existing global_summary.json file for a known run_id.
    Use this for summaries you've already generated outside the pipeline.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    save_cluster_summaries_from_json(run_id, data)


# ════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDAM clustering pipeline")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialise the database schema")

    p_load = sub.add_parser("load-comments", help="Load comments CSV into DB")
    p_load.add_argument("--csv",   required=True)
    p_load.add_argument("--month", required=True, help="e.g. 2025-10")

    p_cluster = sub.add_parser("cluster", help="Run all clustering for a month")
    p_cluster.add_argument("--month", required=True)

    p_sum = sub.add_parser("summarize", help="Summarize all valid runs for a month")
    p_sum.add_argument("--month", required=True)

    p_all = sub.add_parser("run-all", help="Load + cluster + summarize in one shot")
    p_all.add_argument("--csv",   required=True)
    p_all.add_argument("--month", required=True)

    args = parser.parse_args()

    if args.command == "init":
        init_db()

    elif args.command == "load-comments":
        init_db()
        load_comments_from_csv(args.csv, args.month)

    elif args.command in ("cluster", "summarize", "run-all"):
        print("To use the cluster / summarize commands, import pipeline.py "
              "from your Jupyter notebook and call the functions directly "
              "with your own build_features_fn and valley_tracing_fn. "
              "See the README for the integration example.")

    else:
        parser.print_help()

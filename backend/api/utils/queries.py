import sqlite3
import json
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pdam.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Month / selector helpers

def get_available_months() -> list[str]:
    """Return all months that have at least one clustering run."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT month FROM clustering_runs ORDER BY month DESC")
    months = [r["month"] for r in cur.fetchall()]
    conn.close()
    return months


def get_all_months() -> list[str]:
    """
    Return all months that have comments, even if not yet clustered.
    Useful for showing 'pending' months greyed out in the selector.
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT month FROM comments ORDER BY month DESC")
    months = [r["month"] for r in cur.fetchall()]
    conn.close()
    return months

def get_runs_for_month(month: str) -> pd.DataFrame:
    """Return all clustering runs for a given month as a DataFrame."""
    conn = _conn()
    
    df = pd.read_sql_query("""
        SELECT 
            id, 
            scenario, 
            linkage, 
            optimal_k, 
            status, 
            is_recommended, 
            dominant_threshold, 
            accuracy,   -- <-- TAMBAHKAN INI
            notes
        FROM clustering_runs
        WHERE month = ?
        ORDER BY scenario ASC, linkage ASC
    """, conn, params=(month,))
    
    conn.close()
    return df


def get_run(month: str, scenario: int, linkage: str) -> dict | None:
    """Return a single run's metadata as a dict, or None if not found."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM clustering_runs
        WHERE month=? AND scenario=? AND linkage=?
    """, (month, scenario, linkage))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# Cluster result queries

def get_clusters_for_run(run_id: int) -> pd.DataFrame:
    """
    Return all clusters for a given run_id.
    Columns: id, cluster_label, display_name, summary,
             keywords (parsed list), comment_count, is_dominant
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT id, cluster_label, display_name, summary,
               keywords, comment_count, is_dominant
        FROM clusters
        WHERE run_id = ?
        ORDER BY comment_count DESC
    """, conn, params=(run_id,))
    conn.close()
    # Parse keywords JSON to Python list
    df["keywords"] = df["keywords"].apply(
        lambda x: json.loads(x) if x else []
    )
    return df


def get_sample_comments(run_id: int, cluster_id: int, n: int = 5) -> list[str]:
    """Return up to n raw comments for a given cluster in a given run."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.raw_text
        FROM comments c
        JOIN comment_cluster_map m ON m.comment_id = c.id
        WHERE m.run_id = ? AND m.cluster_id = ?
        LIMIT ?
    """, (run_id, cluster_id, n))
    rows = cur.fetchall()
    conn.close()
    return [r["raw_text"] for r in rows]


# Valley-tracing curve data

def get_valley_data(run_id: int) -> pd.DataFrame:
    """Return the metric-vs-k curve for a run. Columns: k_value, metric."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT k_value, metric
        FROM valley_tracing_data
        WHERE run_id = ?
        ORDER BY k_value
    """, conn, params=(run_id,))
    conn.close()
    return df


# Overview / stats

def get_comment_stats(month: str) -> dict:
    """Return basic comment stats for a month."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT post_id) as posts
        FROM comments
        WHERE month = ?
    """, (month,))
    row = cur.fetchone()
    conn.close()
    return {"total_comments": row["total"], "total_posts": row["posts"]}


def get_preprocessing_examples(month: str, n: int = 3) -> pd.DataFrame:
    """
    Return n example comments showing before/after preprocessing.
    Picks one short, one medium, one long comment where clean_text exists.
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT raw_text, clean_text, tokens
        FROM comments
        WHERE month = ? AND clean_text IS NOT NULL
        LIMIT ?
    """, conn, params=(month, n))
    conn.close()
    df["tokens"] = df["tokens"].apply(lambda x: json.loads(x) if x else [])
    return df

def get_raw_comments(month: str) -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql_query("SELECT comment_date, post_id, raw_text FROM comments WHERE month = ? ORDER BY comment_date DESC", conn, params=(month,))
    conn.close()
    return df

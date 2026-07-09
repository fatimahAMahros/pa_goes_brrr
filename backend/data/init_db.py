import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "pdam.db")


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_connection()
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # Table 1: comments
    # Stores every raw + preprocessed comment, tagged by month.
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            instagram_comment_id TEXT UNIQUE,       -- The 17-digit ID (Stored as text for safety)
            month               TEXT    NOT NULL,   -- e.g. '2025-10' (for grouping/filtering)
            comment_date        TEXT    NOT NULL,   -- e.g. '2025-11-11 13:17:55' (full timestamp)
            post_id             TEXT,               -- Instagram post identifier
            raw_text            TEXT    NOT NULL,   -- original comment
            clean_text          TEXT,               -- after stopword removal, normalization
            tokens              TEXT,               -- JSON list of tokens after stemming
            created_at          TEXT    DEFAULT (datetime('now')) -- when it was inserted into DB
        )
    """)

    # ------------------------------------------------------------------
    # Table 2: clustering_runs
    # One row per (month × scenario × linkage) combination.
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clustering_runs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            month               TEXT    NOT NULL,
            scenario            INTEGER NOT NULL,
            linkage             TEXT    NOT NULL,
            optimal_k           INTEGER,
            status              TEXT    DEFAULT 'pending',
            is_recommended      INTEGER DEFAULT 0,
            dominant_threshold  REAL,
            accuracy            REAL,
            notes               TEXT,
            created_at          TEXT    DEFAULT (datetime('now')),
            UNIQUE(month, scenario, linkage)
        )
    """)

    # ------------------------------------------------------------------
    # Table 3: clusters
    # One row per cluster within a clustering run.
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id          INTEGER NOT NULL REFERENCES clustering_runs(id),
            cluster_label   INTEGER NOT NULL,   -- cluster index (0, 1, 2, ...)
            display_name    TEXT,               -- human-readable label you assign
            summary         TEXT,               -- generated summary sentence
            keywords        TEXT,               -- JSON list of top keywords
            comment_count   INTEGER DEFAULT 0,
            is_dominant     INTEGER DEFAULT 0   -- 1 if this is the dominant cluster
        )
    """)

    # ------------------------------------------------------------------
    # Table 4: comment_cluster_map
    # Maps each comment to its cluster within a specific run.
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comment_cluster_map (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      INTEGER NOT NULL REFERENCES clustering_runs(id),
            comment_id  INTEGER NOT NULL REFERENCES comments(id),
            cluster_id  INTEGER NOT NULL REFERENCES clusters(id)
        )
    """)

    # ------------------------------------------------------------------
    # Table 5: valley_tracing_data
    # Stores the metric-vs-k curve for each run (for the chart).
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS valley_tracing_data (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      INTEGER NOT NULL REFERENCES clustering_runs(id),
            k_value     INTEGER NOT NULL,
            metric      REAL    NOT NULL    -- the linkage/distance metric at this k
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database initialised at: {DB_PATH}")


# ----------------------------------------------------------------------
# Helper insert functions — call these from your pipeline scripts
# ----------------------------------------------------------------------

def insert_comment(month, comment_date, raw_text, instagram_comment_id=None, clean_text=None, tokens=None, post_id=None):
    """Insert a single preprocessed comment. Returns the new row id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO comments (instagram_comment_id, month, comment_date, post_id, raw_text, clean_text, tokens)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(instagram_comment_id) if instagram_comment_id else None, month, comment_date, post_id, raw_text, clean_text, json.dumps(tokens) if tokens else None))
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id

def insert_comments_bulk(rows: list[dict]):
    """
    Insert many comments at once.
    Each dict: {instagram_comment_id, month, comment_date, raw_text, clean_text, tokens (list), post_id (optional)}
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("""
        INSERT OR IGNORE INTO comments (instagram_comment_id, month, comment_date, post_id, raw_text, clean_text, tokens)
        VALUES (:instagram_comment_id, :month, :comment_date, :post_id, :raw_text, :clean_text, :tokens)
    """, [
        {
            **r,
            "instagram_comment_id": str(r.get("instagram_comment_id")) if r.get("instagram_comment_id") else None,
            "tokens": json.dumps(r.get("tokens")), 
            "post_id": str(r.get("post_id")) if r.get("post_id") else None,
            "comment_date": r.get("comment_date")
        }
        for r in rows
    ])
    conn.commit()
    conn.close()

def upsert_clustering_run(month, scenario, linkage, optimal_k, status, dominant_threshold=None, accuracy=None, notes=None, is_recommended=0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clustering_runs (month, scenario, linkage, optimal_k, status, dominant_threshold, accuracy, notes, is_recommended)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(month, scenario, linkage) DO UPDATE SET
            optimal_k = excluded.optimal_k,
            status = excluded.status,
            dominant_threshold = excluded.dominant_threshold,
            accuracy = excluded.accuracy,
            notes = excluded.notes,
            is_recommended = excluded.is_recommended,
            created_at = datetime('now')
    """, (month, scenario, linkage, optimal_k, status, dominant_threshold, accuracy, notes, is_recommended))
    conn.commit()
    row_id = cur.execute("SELECT id FROM clustering_runs WHERE month=? AND scenario=? AND linkage=?", (month, scenario, linkage)).fetchone()[0]
    conn.close()
    return row_id


def insert_cluster(run_id, cluster_label, display_name=None,
                   summary=None, keywords=None,
                   comment_count=0, is_dominant=False):
    """Insert one cluster result. Returns cluster id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clusters
            (run_id, cluster_label, display_name, summary,
             keywords, comment_count, is_dominant)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (run_id, cluster_label, display_name, summary,
          json.dumps(keywords) if keywords else None,
          comment_count, 1 if is_dominant else 0))
    conn.commit()
    cluster_id = cur.lastrowid
    conn.close()
    return cluster_id


def insert_valley_data(run_id, k_values: list, metrics: list):
    """Store the valley-tracing curve (parallel lists of k and metric)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO valley_tracing_data (run_id, k_value, metric)
        VALUES (?, ?, ?)
    """, [(run_id, k, m) for k, m in zip(k_values, metrics)])
    conn.commit()
    conn.close()


def map_comments_to_cluster(run_id, comment_ids: list, cluster_id: int):
    """Record which comments belong to a given cluster in a given run."""
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO comment_cluster_map (run_id, comment_id, cluster_id)
        VALUES (?, ?, ?)
    """, [(run_id, cid, cluster_id) for cid in comment_ids])
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
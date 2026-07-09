import argparse
from db import get_connection  # adjust to your actual db module name


def list_runs(month):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, scenario, linkage, optimal_k, status, evaluation_score, is_recommended,
               CASE WHEN notes IS NOT NULL THEN 'yes' ELSE 'no' END as has_summary
        FROM clustering_runs
        WHERE month = ?
        ORDER BY scenario, linkage
    """, (month,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print(f"No runs found for month={month}")
        return

    print(f"\n{'ID':<5} {'Scenario':<10} {'Linkage':<10} {'k':<6} {'Status':<10} {'ARI':<8} {'Has Summary':<13} {'Recommended'}")
    print("-" * 75)
    for row in rows:
        rid, scen, link, k, status, ari, is_rec, has_sum = row
        ari_str = f"{ari:.4f}" if ari is not None else "N/A"
        rec_str = "★" if is_rec else ""
        print(f"{rid:<5} {scen:<10} {link:<10} {k:<6} {status:<10} {ari_str:<8} {has_sum:<13} {rec_str}")


def set_recommended_auto(month):
    conn = get_connection()
    cur = conn.cursor()

    # if exists complete linkage, scenario 4, non-dominant, auto pick that
    cur.execute("""
        SELECT id FROM clustering_runs
        WHERE month = ? AND linkage = 'complete' AND scenario = 4 AND status != 'dominant'
    """, (month,))
    preferred = cur.fetchone()

    if preferred:
        cur.execute("UPDATE clustering_runs SET is_recommended = 0 WHERE month = ?", (month,))
        cur.execute("UPDATE clustering_runs SET is_recommended = 1 WHERE id = ?", (preferred[0],))
        conn.commit()
        conn.close()
        print(f"Recommended set to complete-scenario4 (id={preferred[0]})")
    else:
        # Fallback: highest evaluation_score among non-dominants
        cur.execute("""
            SELECT id FROM clustering_runs
            WHERE month = ? AND status != 'dominant' AND notes IS NOT NULL
            ORDER BY evaluation_score DESC
            LIMIT 1
        """, (month,))
        fallback = cur.fetchone()
        if fallback:
            cur.execute("UPDATE clustering_runs SET is_recommended = 0 WHERE month = ?", (month,))
            cur.execute("UPDATE clustering_runs SET is_recommended = 1 WHERE id = ?", (fallback[0],))
            conn.commit()
            conn.close()
            print(f"Recommended set to fallback id={fallback[0]} (highest ARI with summary)")
        else:
            conn.close()
            print("No eligible runs found — either all dominant or none have a summary yet.")


def set_recommended_manual(month, run_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, scenario, linkage, status 
        FROM clustering_runs 
        WHERE id = ? AND month = ?
    """, (run_id, month))
    row = cur.fetchone()

    if not row:
        conn.close()
        print(f"No run found with id={run_id} for month={month}")
        return

    cur.execute("UPDATE clustering_runs SET is_recommended = 0 WHERE month = ?", (month,))
    cur.execute("UPDATE clustering_runs SET is_recommended = 1 WHERE id = ?", (run_id,))
    conn.commit()
    conn.close()
    print(f"Recommended set to id={run_id} (scenario={row[1]}, linkage={row[2]}, status={row[3]})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set is_recommended for clustering runs.")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format e.g. 2025-10")
    parser.add_argument("--auto",  action="store_true", help="Auto-select: prefers complete-scenario4, fallback to highest ARI with summary")
    parser.add_argument("--id",    type=int,            help="Manually set recommended by run ID")
    parser.add_argument("--list",  action="store_true", help="List all runs for the month")
    args = parser.parse_args()

    if args.list:
        list_runs(args.month)
    elif args.auto:
        set_recommended_auto(args.month)
    elif args.id:
        set_recommended_manual(args.month, args.id)
    else:
        parser.print_help()

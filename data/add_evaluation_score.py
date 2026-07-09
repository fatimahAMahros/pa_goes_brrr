from init_db import get_connection

def add_evaluation_score_column():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE clustering_runs ADD COLUMN evaluation_score REAL")
        conn.commit()
        print("Column 'evaluation_score' added successfully.")
    except Exception as e:
        print(f"Skipped (column likely already exists): {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    add_evaluation_score_column()
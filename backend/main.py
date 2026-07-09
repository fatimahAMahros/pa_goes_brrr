from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from api.utils.queries import (
    get_available_months,
    get_runs_for_month,
    get_clusters_for_run,
    get_valley_data,
    get_comment_stats,
    get_preprocessing_examples,
    get_raw_comments
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_df(df):
    return df.replace({np.nan: None}).to_dict(orient="records")

@app.get("/api/months")
def get_months():
    return {"months": get_available_months()}

@app.get("/api/overview/{month}")
def get_overview(month: str):
    stats = get_comment_stats(month)
    return stats

@app.get("/api/preprocessing/{month}")
def get_preprocessing(month: str):
    df = get_preprocessing_examples(month)
    return clean_df(df)

@app.get("/api/clustering/{month}")
def get_clustering_runs(month: str):
    df = get_runs_for_month(month)
    return clean_df(df)

@app.get("/api/clusters/{run_id}")
def get_cluster_details(run_id: int):
    df_curve = get_valley_data(run_id)
    df_clusters = get_clusters_for_run(run_id)
    
    return {
        "curve": clean_df(df_curve),
        "distribution": clean_df(df_clusters)
    }

@app.get("/api/raw_comments/{month}")
def get_raw_comments_data(month: str):
    df = get_raw_comments(month)
    return clean_df(df)
import pandas as pd
import pytz
import re
import ast
from data.init_db import insert_comments_bulk

comments = pd.read_csv('instagram_comments.csv')
data = comments.loc[:, ['post_id','comment_id','created_at','username','text','parent_comment_id']]

data = data[data['username'].str.contains('pdamsuryasembada') == False]
data = data.drop_duplicates(subset=['text'])

local_timezone = pytz.timezone('Asia/Jakarta')
data['created_at'] = pd.to_datetime(data['created_at'], unit='s')
data['created_at'] = data['created_at'].dt.tz_localize('UTC').dt.tz_convert(local_timezone)

def remove_tags(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r'@\w[\w\.]*', '', text).strip()

data['text'] = data['text'].apply(remove_tags)
data = data.dropna(subset=["text"])
data = data[data["text"].astype(str).str.strip() != ""]

cleaned_comments = pd.read_csv('oct25_stemmed_all.csv')

def parse_tokens(token_str):
    if pd.isna(token_str):
        return []
    try:
        return ast.literal_eval(token_str)
    except (ValueError, SyntaxError):
        return []

cleaned_comments['tokens_list'] = cleaned_comments['text'].apply(parse_tokens)
cleaned_comments['processed_text'] = cleaned_comments['tokens_list'].apply(lambda x: " ".join(x))

merge_cols = cleaned_comments[['comment_id', 'processed_text', 'tokens_list']]
data = data.merge(merge_cols, on='comment_id', how='left')

data = data.dropna(subset=['processed_text'])
data = data[data['processed_text'].astype(str).str.strip() != ""]

data['comment_date'] = data['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
data['month'] = data['created_at'].dt.strftime('%Y-%m')

from data.init_db import insert_comments_bulk

print(f"Preparing to insert {len(data)} comments into the database with full timestamps...")

records_to_insert = []
for _, row in data.iterrows():
    records_to_insert.append({
        "instagram_comment_id": str(row['comment_id']),
        "month": row['month'],
        "comment_date": row['comment_date'],
        "post_id": str(row['post_id']),
        "raw_text": row['text'],
        "clean_text": row['processed_text'], 
        "tokens": row['tokens_list']
    })

insert_comments_bulk(records_to_insert)
print("Insertion complete! Your database columns are updated and synced with your Streamlit layout.")
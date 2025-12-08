import pandas as pd
import pytz
import re
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize


comments = pd.read_csv('instagram_comments_test.csv')
data = comments.loc[:,['post_id','created_at','username','text','parent_comment_id',]]
data = data.dropna(subset=['text'])
data["text"] = data["text"].str.lower()

def remove_tags(text):
    return re.sub(r'@\w[\w\.]*', '', text).strip()

data['text'] = data['text'].apply(remove_tags)

PUNCT_TO_REMOVE = "!\"#$%&\'()*+,-./:;<=>?@[\\]^_{|}~`"
def remove_punctuation(text):
    """custom function to remove the punctuation"""
    return text.translate(str.maketrans('', '', PUNCT_TO_REMOVE))

data["text"] = data["text"].apply(lambda text: remove_punctuation(text))

def remove_emojis(text):
    """Removes standard unicode emojis from the text."""
    if not isinstance(text, str):
        return text
    
    emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F" 
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\u2600-\u26FF"
            u"\u2700-\u27BF"
            u"\ufe0f"
            "]+", flags=re.UNICODE)
    
    return emoji_pattern.sub(r'', text)

data['text'] = data['text'].apply(remove_emojis)
data['text'] = data['text'].str.strip()
data = data[data['username'].str.contains('pdamsuryasembada') == False]

local_timezone = pytz.timezone('Asia/Jakarta')
data['created_at'] = pd.to_datetime(data['created_at'], unit='s')
data['created_at'] = data['created_at'].dt.tz_localize('UTC').dt.tz_convert(local_timezone)
data['created_at'] = data['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')

data['text'] = data['text'].astype(str).apply(word_tokenize)

data.to_csv('test_no_pdam_notags.csv', index=False)
import os
from dotenv import load_dotenv

load_dotenv()

TWELVE_LABS_API_KEY = os.getenv("TWELVE_LABS_API_KEY")

VIDEO_DATA_DIR = "data/videos"
EMBEDDINGS_FILE = "embeddings.json"
VECTOR_DB_PATH = "vector_db.index"

MAX_SEARCH_RESULTS = 5
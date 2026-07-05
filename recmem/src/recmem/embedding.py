from sentence_transformers import SentenceTransformer
from .config import EMBEDDING_MODEL

model = SentenceTransformer(EMBEDDING_MODEL)

def get_embedding(user_msg: str, assistant_msg: str) -> list[float]:
    combined_text = f"{user_msg} {assistant_msg}".strip()
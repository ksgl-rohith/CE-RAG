from typing import List
from app.config import settings

class EmbeddingService:
    _model = None

    @classmethod
    def get_model(cls):
        """Lazy loads the embedding model client (singleton pattern)."""
        if cls._model is None:
            if settings.EMBEDDING_PROVIDER == "local":
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            elif settings.EMBEDDING_PROVIDER == "openai":
                from openai import OpenAI
                cls._model = OpenAI(api_key=settings.LLM_API_KEY)
            else:
                raise NotImplementedError(
                    f"Embedding provider '{settings.EMBEDDING_PROVIDER}' is not implemented yet. "
                    f"Please configure EMBEDDING_PROVIDER=local or openai."
                )
        return cls._model

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """Generates an embedding vector for the query text."""
        if settings.EMBEDDING_PROVIDER == "local":
            model = cls.get_model()
            embedding = model.encode(text, show_progress_bar=False)
            return embedding.tolist()
        elif settings.EMBEDDING_PROVIDER == "openai":
            client = cls.get_model()
            try:
                response = client.embeddings.create(
                    model=settings.EMBEDDING_MODEL or "text-embedding-3-small",
                    input=[text]
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"Error calling OpenAI Embeddings API: {e}")
                raise e
        else:
            raise NotImplementedError(f"Embedding provider '{settings.EMBEDDING_PROVIDER}' is not implemented.")

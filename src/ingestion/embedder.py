"""Sentence embeddings. Lazily imported so the pipeline runs without the extra deps."""
import os

DEFAULT_MODEL = os.environ.get("EMBED_MODEL", "intfloat/multilingual-e5-small")


class Embedder:
    """Multilingual embedder (E5 family by default).

    E5 models expect 'query: ' / 'passage: ' prefixes; BGE-M3 does not. The prefix is
    applied based on the model name so switching models stays a config change.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or DEFAULT_MODEL
        self._model = None
        self.uses_prefix = "e5" in self.model_name.lower()

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _wrap(self, texts, kind: str):
        if not self.uses_prefix:
            return texts
        return [f"{kind}: {t}" for t in texts]

    def encode(self, texts: list[str], kind: str = "passage"):
        model = self._load()
        return model.encode(self._wrap(texts, kind), normalize_embeddings=True,
                            show_progress_bar=len(texts) > 64)

    def encode_one(self, text: str, kind: str = "query"):
        return self.encode([text], kind=kind)[0]

    @property
    def dim(self) -> int:
        return int(self._load().get_sentence_embedding_dimension())

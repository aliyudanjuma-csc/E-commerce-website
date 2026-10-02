"""
core/search.py
----------------
Local, offline "semantic search" / retrieval layer -- the (R)etrieval
half of a small RAG pipeline: the chatbot and the catalogue search bar
both retrieve the most relevant product(s) for a free-text query, then
hand that retrieved context to a response generator (see chatbot.py),
instead of doing a brittle keyword/substring match.

Why TF-IDF instead of a hosted embeddings API
----------------------------------------------
Per project scope, this runs fully offline with no external API key.
scikit-learn's TfidfVectorizer + cosine similarity gives genuine
semantic-ish matching (it weights rare/distinctive words like "Kente"
or "Agbada" far more than common words like "the") without needing a
GPU, an internet call, or a paid API -- appropriate for a coursework
MVP that must be demoable offline.

Complexity
----------
- Building the TF-IDF index over n products: O(n) (single pass to fit
  the vectorizer; vocabulary size is bounded/constant in practice).
- A single query: O(n) -- the query vector is compared against all n
  product vectors via cosine similarity (a fixed-size dot product per
  product), then `heapq.nlargest` picks the top-k in O(n log k) rather
  than sorting all n results in O(n log n).
- The index is rebuilt only when the catalogue changes (O(n)), not on
  every keystroke, keeping interactive search responsive.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.data_store import Product


@dataclass
class SearchHit:
    product: Product
    score: float


class SemanticSearchIndex:
    def __init__(self):
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._products: list[Product] = []

    def build(self, products: list[Product]) -> None:
        """O(n) over the current catalogue."""
        self._products = list(products)
        if not self._products:
            self._vectorizer = None
            self._matrix = None
            return
        corpus = [p.searchable_text() for p in self._products]
        self._vectorizer = TfidfVectorizer(stop_words="english", max_features=4096)
        self._matrix = self._vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 8, min_score: float = 0.05) -> list[SearchHit]:
        """O(n) to score every product against the query + O(n log k) to
        select the top-k highest scoring ones."""
        query = (query or "").strip()
        if not query or self._vectorizer is None or self._matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]  # O(n)

        hits = (
            SearchHit(product=self._products[i], score=float(scores[i]))
            for i in range(len(self._products))
            if scores[i] >= min_score
        )
        return heapq.nlargest(top_k, hits, key=lambda h: h.score)  # O(n log k)

    def is_ready(self) -> bool:
        return self._vectorizer is not None

import time
from typing import List
from difflib import SequenceMatcher
from collections import Counter
import math

def levenshtein_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        return levenshtein_distance(b, a)
    if len(b) == 0:
        return len(a)
    previous_row = range(len(b) + 1)
    for i, c1 in enumerate(a):
        current_row = [i + 1]
        for j, c2 in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def ngram_similarity(a: str, b: str, n: int = 2) -> float:
    def ngrams(word: str):
        return [word[i:i + n] for i in range(len(word) - n + 1)]

    a_ngrams = Counter(ngrams(a))
    b_ngrams = Counter(ngrams(b))
    intersection = sum((a_ngrams & b_ngrams).values())
    union = sum((a_ngrams | b_ngrams).values())
    return 1.0 - intersection / union if union else 1.0

def search(word: str, corpus: str, algorithm: str):
    start_time = time.time()
    unique_words = set(corpus.split())
    results = []

    for w in unique_words:
        if algorithm == "levenshtein":
            distance = levenshtein_distance(word, w)
        elif algorithm == "ngram":
            distance = round(ngram_similarity(word, w) * 10)
        else:
            continue
        results.append({"word": w, "distance": distance})

    results.sort(key=lambda x: x["distance"])
    end_time = time.time()
    return {
        "execution_time": round(end_time - start_time, 4),
        "results": results[:10]
    }

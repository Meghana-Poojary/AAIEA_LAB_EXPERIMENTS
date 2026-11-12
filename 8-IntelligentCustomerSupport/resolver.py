"""Approved knowledge-base retrieval and heuristic match scoring."""
import json
from pathlib import Path

def load_knowledge_base(path="knowledge_base.json"):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("Knowledge base must be a JSON list")
    for article in data:
        if not all(k in article for k in ("article_id", "keywords", "approved", "response")):
            raise ValueError("Malformed knowledge-base article")
    return data

def retrieve_article(query_text, knowledge_base):
    text = (query_text or "").lower()
    matches = []
    for article in knowledge_base:
        if not article.get("approved", False):
            continue
        keywords = article.get("keywords", [])
        matched = [word for word in keywords if word.lower() in text]
        if matched and keywords:
            score = len(set(matched)) / len(set(keywords)) * 100
            matches.append((score, article))
    if not matches:
        return None, 0.0
    score, article = max(matches, key=lambda item: item[0])
    return article, round(score, 2)

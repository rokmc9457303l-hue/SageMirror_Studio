import os
import re
from typing import List, Dict


def load_obsidian_notes(vault_path: str) -> List[Dict]:
    notes = []

    if not os.path.exists(vault_path):
        return notes

    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue

                notes.append({
                    "title": os.path.splitext(file)[0],
                    "path": path,
                    "content": content
                })

    return notes


def simple_keyword_search(vault_path: str, query: str, top_k: int = 10) -> List[Dict]:
    notes = load_obsidian_notes(vault_path)

    query_terms = re.findall(r"\w+", query.lower())
    results = []

    for note in notes:
        text = (note["title"] + "\n" + note["content"]).lower()

        score = 0
        for term in query_terms:
            score += text.count(term)

        if score > 0:
            results.append({
                "title": note["title"],
                "path": note["path"],
                "score": score,
                "preview": note["content"][:500]
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
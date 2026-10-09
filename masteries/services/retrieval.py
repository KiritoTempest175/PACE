"""Deterministic, low-memory keyword retrieval for uploaded document excerpts.

Not embedding-based search. Excerpts are explicitly bounded to fit free-tier models.
"""
from __future__ import annotations
import re

def document_excerpt(text: str, question: str, limit: int=6400) -> str:
    if not text.strip(): return ''
    terms=set(re.findall(r'[a-z0-9]{3,}',question.lower()))
    blocks=[x.strip() for x in re.split(r'(?<=\.)\s+|\n+',text) if x.strip()]
    weighted=[]
    for index,block in enumerate(blocks):
        words=set(re.findall(r'[a-z0-9]{3,}',block.lower()))
        score=len(words&terms)
        weighted.append((score,index,block))
    chosen=[];used=0
    for score,index,block in sorted(weighted,key=lambda x:(-x[0],x[1])):
        part=block[:1800]
        if used+len(part)>limit: continue
        chosen.append((index,part));used+=len(part)
        if used>=limit-1800: break
    return '\n'.join(f'[Excerpt {index+1}] {block}' for index,block in sorted(chosen))

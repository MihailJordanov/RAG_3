import re
import unicodedata
from dataclasses import dataclass

@dataclass(frozen=True)
class NormalizeConfig:
    # Ако искаш: включвай/изключвай етапи
    lowercase: bool = True
    strip_quotes: bool = True
    strip_punct: bool = True
    collapse_spaces: bool = True


_QUOTES = ['„', '“', '"', "'"]

def normalize_query(q: str, cfg: NormalizeConfig = NormalizeConfig()) -> str:
    q = unicodedata.normalize("NFKC", q or "")
    q = q.strip()

    if cfg.lowercase:
        q = q.lower()

    if cfg.strip_quotes:
        for ch in _QUOTES:
            q = q.replace(ch, "")

    if cfg.strip_punct:
        # оставяме букви/цифри/underscore/интервали/тире
        q = re.sub(r"[^\w\s\-]", " ", q, flags=re.UNICODE)

    if cfg.collapse_spaces:
        q = re.sub(r"\s+", " ", q).strip()

    # word-level fixes
    words = q.split()
    return " ".join(words)
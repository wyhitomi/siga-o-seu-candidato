import unicodedata


def normalize(text: str) -> str:
    """Lowercase, strip accents and collapse whitespace ("JOSÉ  da Silva" -> "jose da silva")."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(without_accents.lower().split())

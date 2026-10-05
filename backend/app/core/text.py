import unicodedata


def normalize(text: str) -> str:
    """Lowercase, strip accents and collapse whitespace ("JOSÉ  da Silva" -> "jose da silva")."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(without_accents.lower().split())


_LOWERCASE_PARTICLES = {"da", "das", "de", "di", "do", "dos", "du", "e"}


def title_name(text: str) -> str:
    """Format an upper-case name for display ("JOÃO DA SILVA" -> "João da Silva")."""
    words = text.lower().split()
    return " ".join(
        w if i > 0 and w in _LOWERCASE_PARTICLES else w.capitalize() for i, w in enumerate(words)
    )

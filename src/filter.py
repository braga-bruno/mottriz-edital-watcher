"""Filtragem de relevância dos editais para a Mottriz."""

from __future__ import annotations

from typing import List

from src.scraper import Edital

# Grupo A — Tipo de projeto (pelo menos um deve aparecer)
KEYWORDS_TIPO = [
    "música", "musica", "show", "banda", "circulação", "circulacao",
    "apresentação", "apresentacao", "rock", "popular", "autoral",
    "produção musical", "producao musical", "gravação", "gravacao",
    "criativa", "artística", "artistica", "cultural", "proposta",
]

# Grupo B — Abrangência geográfica (pelo menos um deve aparecer)
KEYWORDS_GEO = [
    "paraíba", "paraiba", "nordeste", "joão pessoa", "joao pessoa",
    "nacional", "todo o brasil", "todo brasil", "abrangência nacional",
]

# Fontes que são inerentemente locais (PB) — passam Grupo B automaticamente
FONTES_LOCAIS_PB = {
    "Secult-PB", "Funesc-PB", "Viva Usina", "Paraíba Criativa", "Instituto Energisa",
}

# Grupo C — Exclusão (se presente SEM "música", é descartado)
EXCLUSOES = [
    "teatro", "artes visuais", "dança", "danca", "circo", "literatura",
]


def _normalizar(texto: str) -> str:
    return texto.lower().strip()


def _contem_keyword(texto: str, keywords: List[str]) -> bool:
    texto_norm = _normalizar(texto)
    return any(kw in texto_norm for kw in keywords)


def _excluido(texto: str) -> bool:
    texto_norm = _normalizar(texto)
    tem_musica = "música" in texto_norm or "musica" in texto_norm
    if tem_musica:
        return False
    return any(exc in texto_norm for exc in EXCLUSOES)


def edital_relevante(edital: Edital) -> bool:
    """Retorna True se o edital é relevante para a Mottriz."""
    texto_completo = f"{edital.titulo} {edital.descricao}"

    # Critério de exclusão
    if _excluido(texto_completo):
        return False

    # Grupo A — Tipo de projeto
    tem_tipo = _contem_keyword(texto_completo, KEYWORDS_TIPO)

    # Grupo B — fontes locais PB passam automaticamente; demais checam keywords
    tem_geo = edital.fonte in FONTES_LOCAIS_PB or _contem_keyword(texto_completo, KEYWORDS_GEO)

    return tem_tipo and tem_geo


def filtrar_editais(editais: List[Edital]) -> List[Edital]:
    """Filtra lista de editais, retornando apenas os relevantes."""
    return [e for e in editais if edital_relevante(e)]

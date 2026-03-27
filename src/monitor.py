"""Monitoramento de páginas específicas aguardando publicação de resultado."""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from src.notify import notificar_edital

logger = logging.getLogger(__name__)

TIMEOUT = 30
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Palavras-chave que indicam publicação de resultado
KEYWORDS_RESULTADO = [
    "resultado", "classificado", "selecionado", "aprovado",
    "habilitado", "homologação", "gabarito", "lista de",
]


def _extrair_texto_relevante(html: str) -> str:
    """Extrai texto visível da página, ignorando nav/header/footer."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.select("nav, header, footer, script, style"):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _hash_conteudo(texto: str) -> str:
    return hashlib.md5(texto.encode()).hexdigest()


def _tem_resultado(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in KEYWORDS_RESULTADO)


def verificar_monitoramentos(state: dict) -> dict:
    """Verifica todas as páginas em monitoramento e notifica se houver mudanças."""
    monitoramentos = state.setdefault("monitoramentos", {})

    for url, info in monitoramentos.items():
        if info.get("status") == "resultado_publicado":
            continue

        logger.info(f"Monitorando: {info['titulo']}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            texto = _extrair_texto_relevante(resp.text)
            hash_atual = _hash_conteudo(texto)
        except Exception as e:
            logger.error(f"Erro ao acessar {url}: {e}")
            continue

        hash_anterior = info.get("hash_conteudo")
        tem_resultado = _tem_resultado(texto)

        if hash_anterior and hash_atual != hash_anterior:
            logger.info(f"Mudança detectada em: {info['titulo']}")
            if tem_resultado:
                logger.info("Resultado encontrado na página!")
                info["status"] = "resultado_publicado"
                _notificar_resultado(info, url)
            else:
                logger.info("Página mudou mas resultado ainda não identificado")
                info["status"] = "pagina_alterada"
                _notificar_alteracao(info, url)

        info["hash_conteudo"] = hash_atual

    return state


def _notificar_resultado(info: dict, url: str) -> None:
    edital_fake = {
        "titulo": f"RESULTADO PUBLICADO — {info['titulo']}",
        "fonte": info.get("fonte", "Monitoramento"),
        "url": url,
        "prazo": None,
    }
    notificar_edital(edital_fake, "resultado")


def _notificar_alteracao(info: dict, url: str) -> None:
    edital_fake = {
        "titulo": f"PÁGINA ALTERADA (verifique resultado) — {info['titulo']}",
        "fonte": info.get("fonte", "Monitoramento"),
        "url": url,
        "prazo": None,
    }
    notificar_edital(edital_fake, "alteracao")


def adicionar_monitoramento(state: dict, titulo: str, url: str,
                             fonte: str = "Secult-PB") -> dict:
    """Adiciona uma página ao monitoramento de resultados."""
    monitoramentos = state.setdefault("monitoramentos", {})
    if url not in monitoramentos:
        monitoramentos[url] = {
            "titulo": titulo,
            "fonte": fonte,
            "adicionado_em": __import__("datetime").datetime.now().strftime("%Y-%m-%d"),
            "status": "aguardando_resultado",
            "hash_conteudo": None,
        }
        logger.info(f"Monitoramento adicionado: {titulo}")
    return state

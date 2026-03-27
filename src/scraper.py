"""Scrapers para cada fonte de editais culturais."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 30
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


@dataclass
class Edital:
    titulo: str
    fonte: str
    url: str
    descricao: str = ""
    prazo: Optional[str] = None


def _get(url: str) -> Optional[BeautifulSoup]:
    """Faz GET e retorna BeautifulSoup, ou None em caso de erro."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.error(f"Erro ao acessar {url}: {e}")
        return None


def _get_json(url: str) -> Optional[list]:
    """Faz GET e retorna JSON, ou None em caso de erro."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro ao acessar API {url}: {e}")
        return None


def _extrair_prazo(texto: str) -> Optional[str]:
    """Tenta extrair data de prazo de um texto."""
    padrao = re.compile(r"\d{2}/\d{2}/\d{4}")
    match = padrao.search(texto)
    if match:
        partes = match.group().split("/")
        return f"{partes[2]}-{partes[1]}-{partes[0]}"
    return None


# ---- Paraíba ----

def scrape_secult_pb() -> list[Edital]:
    """Secretaria da Cultura da Paraíba."""
    url = "https://paraiba.pb.gov.br/diretas/secretaria-da-cultura/editais"
    fonte = "Secult-PB"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    for item in soup.select("a.state-published, article a, .tileItem a, .entry-title a, a[href*='edital']"):
        titulo = item.get_text(strip=True)
        href = item.get("href", "")
        if not titulo or len(titulo) < 5:
            continue
        link = urljoin(url, href)
        editais.append(Edital(titulo=titulo, fonte=fonte, url=link))

    # Fallback: buscar links genéricos com texto relevante
    if not editais:
        for link_tag in soup.find_all("a", href=True):
            texto = link_tag.get_text(strip=True)
            href = link_tag["href"]
            if any(kw in texto.lower() for kw in ["edital", "chamada", "seleção", "inscrição"]):
                editais.append(Edital(
                    titulo=texto, fonte=fonte, url=urljoin(url, href)
                ))

    return editais


def scrape_prosas() -> list[Edital]:
    """Prosas — plataforma de editais sociais."""
    url = "https://prosas.com.br/editais"
    fonte = "Prosas"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    for card in soup.select(".edital-card, .card, article, .opportunity-card, [class*='edital']"):
        titulo_el = card.select_one("h2, h3, .card-title, .title, a")
        link_el = card.select_one("a[href]") or card.find_parent("a")
        if not titulo_el:
            continue
        titulo = titulo_el.get_text(strip=True)
        href = link_el["href"] if link_el else ""
        link = urljoin(url, href)
        desc = card.get_text(strip=True)
        prazo = _extrair_prazo(desc)
        editais.append(Edital(titulo=titulo, fonte=fonte, url=link,
                              descricao=desc, prazo=prazo))

    return editais


def scrape_funesc() -> list[Edital]:
    """Funesc — Fundação Espaço Cultural da Paraíba."""
    url = "https://funesc.pb.gov.br/editais"
    fonte = "Funesc-PB"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    for item in soup.select("a.state-published, article a, .tileItem a, a[href*='edital']"):
        titulo = item.get_text(strip=True)
        href = item.get("href", "")
        if not titulo or len(titulo) < 5:
            continue
        link = urljoin(url, href)
        editais.append(Edital(titulo=titulo, fonte=fonte, url=link))

    if not editais:
        for link_tag in soup.find_all("a", href=True):
            texto = link_tag.get_text(strip=True)
            href = link_tag["href"]
            if any(kw in texto.lower() for kw in ["edital", "chamada", "seleção"]):
                editais.append(Edital(
                    titulo=texto, fonte=fonte, url=urljoin(url, href)
                ))

    return editais


def scrape_viva_usina() -> list[Edital]:
    """Viva Usina — site Wix (JS-rendered), monitorado via hash no monitor.py.

    Retorna lista vazia; a detecção de novos editais é feita por mudança de
    hash da homepage em monitor.py (entrada 'monitoramentos' do state.json).
    """
    logger.info("Viva Usina: site Wix (JS-rendered) — monitorado via hash.")
    return []


def scrape_energisa() -> list[Edital]:
    """Usina Cultural Energisa / Instituto Energisa."""
    url = "https://www.energisa.com.br/instituto-energisa"
    fonte = "Instituto Energisa"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    for link_tag in soup.find_all("a", href=True):
        texto = link_tag.get_text(strip=True)
        href = link_tag["href"]
        if any(kw in texto.lower() for kw in ["edital", "chamada", "seleção", "inscrição", "cultural"]):
            editais.append(Edital(
                titulo=texto, fonte=fonte, url=urljoin(url, href)
            ))

    return editais


def scrape_paraiba_criativa() -> list[Edital]:
    """Paraíba Criativa."""
    url = "https://paraibacriativa.com.br"
    fonte = "Paraíba Criativa"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    for link_tag in soup.find_all("a", href=True):
        texto = link_tag.get_text(strip=True)
        href = link_tag["href"]
        if any(kw in texto.lower() for kw in ["edital", "chamada", "seleção", "inscrição"]):
            editais.append(Edital(
                titulo=texto, fonte=fonte, url=urljoin(url, href)
            ))

    return editais


# ---- Nordeste ----

def scrape_secult_pe() -> list[Edital]:
    """Secretaria de Cultura de Pernambuco / Fundarpe."""
    url = "https://cultura.pe.gov.br/editais"
    fonte = "Secult-PE"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    for item in soup.select("article a, .entry-title a, h2 a, h3 a, a[href*='edital']"):
        titulo = item.get_text(strip=True)
        href = item.get("href", "")
        if not titulo or len(titulo) < 5:
            continue
        link = urljoin(url, href)
        editais.append(Edital(titulo=titulo, fonte=fonte, url=link))

    if not editais:
        for link_tag in soup.find_all("a", href=True):
            texto = link_tag.get_text(strip=True)
            href = link_tag["href"]
            if any(kw in texto.lower() for kw in ["edital", "chamada", "seleção"]):
                editais.append(Edital(
                    titulo=texto, fonte=fonte, url=urljoin(url, href)
                ))

    return editais


def _scrape_mapas_culturais(base_url: str, fonte: str) -> list[Edital]:
    """Scraper genérico para instâncias do Mapas Culturais (API REST)."""
    api_url = f"{base_url}/api/opportunity/find"
    params = {
        "@select": "id,name,shortDescription,registrationFrom,registrationTo",
        "@order": "createTimestamp DESC",
        "@limit": 50,
        "status": "GTE(0)",
    }
    editais = []

    data = _get_json(f"{api_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
    if data is None:
        raise ConnectionError(f"Falha ao acessar API {fonte}")

    if not isinstance(data, list):
        logger.warning(f"Resposta inesperada da API {fonte}: {type(data)}")
        return editais

    for item in data:
        titulo = item.get("name", "").strip()
        if not titulo:
            continue
        opp_id = item.get("id", "")
        url = f"{base_url}/oportunidade/{opp_id}"
        desc = item.get("shortDescription", "") or ""
        prazo = item.get("registrationTo", "")
        if prazo and "T" in prazo:
            prazo = prazo.split("T")[0]
        elif not prazo:
            prazo = None
        editais.append(Edital(titulo=titulo, fonte=fonte, url=url,
                              descricao=desc, prazo=prazo))

    return editais


def scrape_mapa_cultural_pe() -> list[Edital]:
    """Mapa Cultural de Pernambuco."""
    return _scrape_mapas_culturais("https://www.mapacultural.pe.gov.br", "Mapa Cultural PE")


def scrape_mapa_cultural_ce() -> list[Edital]:
    """Mapa Cultural do Ceará."""
    return _scrape_mapas_culturais("https://mapacultural.secult.ce.gov.br", "Mapa Cultural CE")


def scrape_mapa_cultura_gov() -> list[Edital]:
    """Mapa da Cultura — Ministério da Cultura."""
    return _scrape_mapas_culturais("https://mapa.cultura.gov.br", "Mapa da Cultura (MinC)")


def scrape_jp_cultura() -> list[Edital]:
    """JP Cultura — Plataforma Municipal de João Pessoa (Mapas Culturais)."""
    return _scrape_mapas_culturais("https://jpcultura.joaopessoa.pb.gov.br", "JP Cultura")


def scrape_sesc_pb() -> list[Edital]:
    """SESC Paraíba — MusiSesc e outros editais musicais."""
    url = "https://sescpb.com.br/?s=edital"
    fonte = "SESC-PB"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    for post in soup.select(".wp-block-post, article"):
        titulo_el = post.select_one(".entry-title a, h2 a, h3 a")
        if not titulo_el:
            continue
        titulo = titulo_el.get_text(strip=True)
        href = titulo_el.get("href", "")
        if not titulo or len(titulo) < 5:
            continue
        desc = post.get_text(strip=True)
        prazo = _extrair_prazo(desc)
        editais.append(Edital(titulo=titulo, fonte=fonte, url=href,
                              descricao=desc, prazo=prazo))

    return editais


def scrape_funjope() -> list[Edital]:
    """FUNJOPE — Fundação Cultural de João Pessoa."""
    url = "https://www.joaopessoa.pb.gov.br/noticias/secretarias-e-orgaos/funjope-noticias/"
    fonte = "FUNJOPE"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    kws = ["edital", "chamada", "seleção", "selecao", "inscrição",
           "inscricao", "convocatória", "premio", "prêmio", "fomento"]

    for post in soup.select("article, .post, .entry"):
        titulo_el = post.select_one("h2 a, h3 a, .entry-title a")
        if not titulo_el:
            continue
        titulo = titulo_el.get_text(strip=True)
        href = titulo_el.get("href", "")
        if not any(kw in titulo.lower() for kw in kws):
            continue
        desc = post.get_text(strip=True)
        prazo = _extrair_prazo(desc)
        editais.append(Edital(titulo=titulo, fonte=fonte, url=href,
                              descricao=desc, prazo=prazo))

    # Fallback genérico se não encontrar posts estruturados
    if not editais:
        for link_tag in soup.find_all("a", href=True):
            texto = link_tag.get_text(strip=True)
            if any(kw in texto.lower() for kw in kws) and len(texto) > 10:
                editais.append(Edital(
                    titulo=texto, fonte=fonte,
                    url=urljoin(url, link_tag["href"])
                ))

    return editais


def scrape_bnb_cultural() -> list[Edital]:
    """Banco do Nordeste — Programa BNB de Cultura."""
    url = "https://www.bnb.gov.br/cultura"
    fonte = "BNB Cultural"
    editais = []

    soup = _get(url)
    if not soup:
        raise ConnectionError(f"Falha ao acessar {fonte}")

    kws = ["edital", "chamada", "seleção", "selecao", "inscrição",
           "inscricao", "ocupação", "ocupacao"]

    for link_tag in soup.find_all("a", href=True):
        texto = link_tag.get_text(strip=True)
        href = link_tag["href"]
        if not any(kw in texto.lower() for kw in kws):
            continue
        if len(texto) < 10:
            continue
        link = href if href.startswith("http") else urljoin(url, href)
        editais.append(Edital(titulo=texto, fonte=fonte, url=link))

    return editais


# ---- Registro de todas as fontes ----

FONTES: list[tuple[str, Callable]] = [
    ("Secult-PB", scrape_secult_pb),
    ("Prosas", scrape_prosas),
    ("Funesc-PB", scrape_funesc),
    ("Viva Usina", scrape_viva_usina),          # Wix: retorna [], monitorado via hash
    ("Instituto Energisa", scrape_energisa),
    ("Paraíba Criativa", scrape_paraiba_criativa),
    ("JP Cultura", scrape_jp_cultura),
    ("SESC-PB", scrape_sesc_pb),
    ("FUNJOPE", scrape_funjope),
    ("BNB Cultural", scrape_bnb_cultural),
    ("Secult-PE", scrape_secult_pe),
    ("Mapa Cultural PE", scrape_mapa_cultural_pe),
    ("Mapa Cultural CE", scrape_mapa_cultural_ce),
    ("Mapa da Cultura (MinC)", scrape_mapa_cultura_gov),
]

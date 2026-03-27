"""Gerenciamento do state.json e comandos.txt."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

STATE_FILE = Path("state.json")
COMANDOS_FILE = Path("comandos.txt")


def gerar_id(titulo: str, fonte: str) -> str:
    """Gera hash MD5 do título + fonte como ID único do edital."""
    raw = f"{titulo.strip().lower()}|{fonte.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def carregar_state() -> dict:
    """Carrega o state.json. Retorna estrutura padrão se não existir."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_run": None, "editais": {}, "erros_ultima_execucao": []}


def salvar_state(state: dict) -> None:
    """Salva o state.json formatado."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def processar_comandos(state: dict) -> dict:
    """Lê comandos.txt, aplica mudanças no state e limpa o arquivo."""
    if not COMANDOS_FILE.exists():
        return state

    conteudo = COMANDOS_FILE.read_text(encoding="utf-8").strip()
    if not conteudo:
        return state

    for linha in conteudo.splitlines():
        linha = linha.strip()
        if not linha:
            continue

        partes = linha.split(maxsplit=1)
        if len(partes) != 2:
            logger.warning(f"Comando inválido: {linha}")
            continue

        comando, edital_id = partes[0].lower(), partes[1].strip()

        if edital_id not in state["editais"]:
            logger.warning(f"Edital não encontrado: {edital_id}")
            continue

        if comando == "ignorar":
            state["editais"][edital_id]["status"] = "ignorado"
            logger.info(f"Edital {edital_id} marcado como ignorado")
        elif comando == "resultado":
            state["editais"][edital_id]["status"] = "aguardando_resultado"
            logger.info(f"Edital {edital_id} marcado como aguardando_resultado")
        elif comando == "ativar":
            state["editais"][edital_id]["status"] = "notificado"
            logger.info(f"Edital {edital_id} reativado")
        else:
            logger.warning(f"Comando desconhecido: {comando}")

    # Limpa o arquivo de comandos
    COMANDOS_FILE.write_text("", encoding="utf-8")
    return state


def adicionar_edital(state: dict, titulo: str, fonte: str, url: str,
                     prazo: Optional[str] = None) -> Tuple[dict, Optional[str]]:
    """Adiciona edital ao state se for novo. Retorna (state, edital_id ou None se já existia)."""
    edital_id = gerar_id(titulo, fonte)

    if edital_id in state["editais"]:
        return state, None

    state["editais"][edital_id] = {
        "titulo": titulo,
        "fonte": fonte,
        "url": url,
        "encontrado_em": datetime.now().strftime("%Y-%m-%d"),
        "status": "novo",
        "prazo": prazo,
        "notas": "",
    }

    logger.info(f"Novo edital encontrado: {titulo} ({fonte})")
    return state, edital_id


def registrar_erro(state: dict, fonte: str, erro: str) -> dict:
    """Registra erro de uma fonte na execução atual."""
    state.setdefault("erros_ultima_execucao", [])
    state["erros_ultima_execucao"].append({
        "fonte": fonte,
        "erro": erro,
        "timestamp": datetime.now().isoformat(),
    })
    return state

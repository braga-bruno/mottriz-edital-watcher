"""Orquestrador principal do Mottriz Edital Watcher."""

import logging
import sys
from datetime import datetime

from src.filter import filtrar_editais
from src.notify import notificar_edital
from src.scraper import FONTES
from src.state import (
    adicionar_edital,
    carregar_state,
    processar_comandos,
    registrar_erro,
    salvar_state,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Mottriz Edital Watcher — início da execução ===")

    # Carregar estado e processar comandos pendentes
    state = carregar_state()
    state = processar_comandos(state)
    state["erros_ultima_execucao"] = []

    # Scraping de todas as fontes
    todos_editais = []
    for nome_fonte, scraper_fn in FONTES:
        logger.info(f"Acessando fonte: {nome_fonte}")
        try:
            editais = scraper_fn()
            logger.info(f"  {len(editais)} editais encontrados em {nome_fonte}")
            todos_editais.extend(editais)
        except Exception as e:
            logger.error(f"  Erro em {nome_fonte}: {e}")
            state = registrar_erro(state, nome_fonte, str(e))

    logger.info(f"Total bruto de editais coletados: {len(todos_editais)}")

    # Filtragem de relevância
    editais_relevantes = filtrar_editais(todos_editais)
    logger.info(f"Editais relevantes após filtro: {len(editais_relevantes)}")

    # Adicionar novos ao state e notificar
    novos = 0
    for edital in editais_relevantes:
        state, edital_id = adicionar_edital(
            state, edital.titulo, edital.fonte, edital.url, edital.prazo
        )
        if edital_id is None:
            continue  # Já existia

        novos += 1
        # Notificar via WhatsApp
        edital_data = state["editais"][edital_id]
        sucesso = notificar_edital(edital_data, edital_id)
        if sucesso:
            state["editais"][edital_id]["status"] = "notificado"
        else:
            logger.warning(f"Falha ao notificar edital: {edital_data['titulo']}")

    # Atualizar timestamp
    state["last_run"] = datetime.now().isoformat()

    # Salvar estado
    salvar_state(state)

    logger.info(f"=== Execução finalizada: {novos} novos editais ===")
    if state["erros_ultima_execucao"]:
        logger.warning(f"Erros em {len(state['erros_ultima_execucao'])} fonte(s)")


if __name__ == "__main__":
    main()

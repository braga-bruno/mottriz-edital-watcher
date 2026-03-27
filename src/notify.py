"""Envio de notificações via WhatsApp usando Callmebot."""

import logging
import os
import time
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"


def _enviar_mensagem(texto: str, phone: str, apikey: str) -> bool:
    """Envia uma mensagem via Callmebot. Retorna True se sucesso."""
    params = {
        "phone": phone,
        "text": texto,
        "apikey": apikey,
    }
    try:
        resp = requests.get(CALLMEBOT_URL, params=params, timeout=30)
        if resp.status_code == 200:
            logger.info("Mensagem enviada com sucesso via Callmebot")
            return True
        logger.warning(f"Callmebot retornou status {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem Callmebot: {e}")
        return False


def notificar_edital(edital: dict, edital_id: str) -> bool:
    """Envia notificação WhatsApp para um edital novo."""
    phone = os.environ.get("CALLMEBOT_PHONE", "")
    apikey = os.environ.get("CALLMEBOT_APIKEY", "")

    if not phone or not apikey:
        logger.warning("CALLMEBOT_PHONE ou CALLMEBOT_APIKEY não configurados. "
                        "Pulando notificação.")
        return False

    prazo = edital.get("prazo") or "não informado"
    mensagem = (
        f"🎸 NOVO EDITAL — Mottriz Watcher\n\n"
        f"📌 {edital['titulo']}\n"
        f"🏛 Fonte: {edital['fonte']}\n"
        f"📅 Prazo: {prazo}\n"
        f"🔗 {edital['url']}\n\n"
        f"Para ignorar: edite comandos.txt com:\n"
        f"ignorar {edital_id}"
    )

    # Primeira tentativa
    if _enviar_mensagem(mensagem, phone, apikey):
        return True

    # Retry após 30 segundos
    logger.info("Retry de envio em 30 segundos...")
    time.sleep(30)
    return _enviar_mensagem(mensagem, phone, apikey)

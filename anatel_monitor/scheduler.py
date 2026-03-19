"""
Agendador de execução diária do robô de monitoramento.

Usa a biblioteca `schedule` para disparar a coleta uma vez por dia
no horário configurado em HORARIO_EXECUCAO (padrão: 08:00).
"""

import logging
import time

import schedule

from .config import HORARIO_EXECUCAO
from .core import executar_ciclo

logger = logging.getLogger(__name__)


def iniciar_agendador() -> None:
    """
    Inicia o loop de agendamento.

    O ciclo completo é executado imediatamente na inicialização
    e depois conforme o horário configurado.
    """
    logger.info("Agendador iniciado. Próxima execução programada: %s", HORARIO_EXECUCAO)

    # Executa imediatamente ao iniciar
    logger.info("Executando ciclo inicial...")
    executar_ciclo()

    # Agenda execução diária
    schedule.every().day.at(HORARIO_EXECUCAO).do(executar_ciclo)
    logger.info("Ciclo diário agendado para: %s", HORARIO_EXECUCAO)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # verifica a cada minuto
    except KeyboardInterrupt:
        logger.info("Agendador encerrado pelo usuário.")

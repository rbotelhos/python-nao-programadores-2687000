"""
Orquestra o ciclo completo de coleta → persistência → notificação.
"""

import logging
from datetime import datetime

from .database import inicializar_banco, salvar_consulta, estatisticas
from .notifier import processar_notificacoes
from .scraper import AnatelScraper

logger = logging.getLogger(__name__)


def executar_ciclo(enriquecer: bool = True) -> dict:
    """
    Executa um ciclo completo:
      1. Scraping dos portais Anatel
      2. Persistência no banco de dados
      3. Disparo de notificações

    Args:
        enriquecer: Se True, acessa as páginas individuais de cada
                    consulta para extrair detalhes adicionais.

    Retorna:
        Dicionário com o resumo do ciclo.
    """
    inicio = datetime.now()
    logger.info("=== Ciclo iniciado: %s ===", inicio.strftime("%d/%m/%Y %H:%M"))

    inicializar_banco()

    resultados = {"novas": 0, "atualizadas": 0, "sem_changes": 0, "erros": 0}

    try:
        with AnatelScraper() as scraper:
            consultas = scraper.coletar_todas(enriquecer=enriquecer)

        for consulta in consultas:
            try:
                resultado = salvar_consulta(consulta)
                resultados[resultado if resultado in resultados else "sem_changes"] += 1
            except Exception as exc:
                logger.error("Erro ao salvar consulta %s: %s", consulta.codigo, exc)
                resultados["erros"] += 1

    except Exception as exc:
        logger.error("Erro crítico no ciclo de coleta: %s", exc)
        resultados["erros"] += 1

    notificacoes_enviadas = processar_notificacoes()
    stats = estatisticas()

    duracao = (datetime.now() - inicio).total_seconds()
    logger.info(
        "=== Ciclo concluído em %.1fs | Novas: %d | Atualizadas: %d | "
        "Notificações: %d ===",
        duracao,
        resultados["novas"],
        resultados["atualizadas"],
        notificacoes_enviadas,
    )

    return {
        **resultados,
        "notificacoes_enviadas": notificacoes_enviadas,
        "duracao_segundos": duracao,
        "estatisticas_banco": stats,
    }

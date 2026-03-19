#!/usr/bin/env python3
"""
Robô de Monitoramento — Anatel Participação Social
===================================================

Monitora diariamente o portal Participa Anatel e o SACP em busca de
novas Consultas Públicas e Tomadas de Subsídio, persistindo os dados
em banco SQLite e notificando por console e/ou e-mail.

Uso:
    python main.py                  # inicia agendamento diário
    python main.py --agora          # executa uma vez imediatamente
    python main.py --web            # inicia interface web (http://localhost:5000)
    python main.py --demo           # popula banco com dados de demonstração
    python main.py --listar         # lista consultas salvas no banco
    python main.py --stats          # exibe estatísticas do banco
    python main.py --sem-detalhes   # roda sem buscar páginas individuais
"""

import argparse
import logging
import sys

from anatel_monitor.core import executar_ciclo
from anatel_monitor.database import inicializar_banco, listar_consultas, estatisticas
from anatel_monitor.scheduler import iniciar_agendador

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("anatel_monitor.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Robô de monitoramento de Participação Social da Anatel"
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument(
        "--agora",
        action="store_true",
        help="Executa o ciclo completo uma única vez e encerra.",
    )
    grupo.add_argument(
        "--web",
        action="store_true",
        help="Inicia a interface web (padrão: http://localhost:5000).",
    )
    grupo.add_argument(
        "--demo",
        action="store_true",
        help="Popula o banco com dados de demonstração e inicia a interface web.",
    )
    grupo.add_argument(
        "--listar",
        action="store_true",
        help="Lista as consultas salvas no banco e encerra.",
    )
    grupo.add_argument(
        "--stats",
        action="store_true",
        help="Exibe estatísticas do banco e encerra.",
    )
    parser.add_argument(
        "--sem-detalhes",
        action="store_true",
        help="Não acessa páginas individuais (mais rápido, menos dados).",
    )
    parser.add_argument(
        "--tipo",
        choices=["cp", "ts"],
        help="Filtra listagem: 'cp' = Consulta Pública, 'ts' = Tomada de Subsídio.",
    )
    parser.add_argument(
        "--porta",
        type=int,
        default=5000,
        help="Porta da interface web (padrão: 5000).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host da interface web (padrão: 127.0.0.1).",
    )
    return parser.parse_args()


def _exibir_listagem(tipo_filtro: str | None) -> None:
    inicializar_banco()
    tipo_map = {
        "cp": "Consulta Pública",
        "ts": "Tomada de Subsídio",
    }
    tipo = tipo_map.get(tipo_filtro) if tipo_filtro else None
    consultas = listar_consultas(tipo=tipo)

    if not consultas:
        print("Nenhuma consulta encontrada no banco.")
        return

    print(f"\n{'='*70}")
    print(f"  {len(consultas)} consulta(s) encontrada(s)")
    print(f"{'='*70}")
    for c in consultas:
        adiada = "Sim" if c["adiada"] else "Não"
        prazo = c.get("prazo_resposta") or c.get("data_encerramento") or "N/D"
        print(
            f"\n[{c['tipo']}] Nº {c['numero']}  |  {c['status']}  |  Adiada: {adiada}\n"
            f"  Título : {c['titulo']}\n"
            f"  Objeto : {c['objeto'] or 'N/D'}\n"
            f"  Prazo  : {prazo}\n"
            f"  Link   : {c['link'] or 'N/D'}"
        )


def _exibir_stats() -> None:
    inicializar_banco()
    stats = estatisticas()
    print(f"\n{'='*40}")
    print("  Estatísticas do Banco de Dados")
    print(f"{'='*40}")
    print(f"  Total de consultas         : {stats['total']}")
    print(f"  Abertas                    : {stats['abertas']}")
    print(f"  Encerradas                 : {stats['encerradas']}")
    print(f"  Consultas Públicas         : {stats['consultas_publicas']}")
    print(f"  Tomadas de Subsídio        : {stats['tomadas_subsidio']}")
    print(f"  Com prazo adiado           : {stats['adiadas']}")
    print(f"  Notificações pendentes     : {stats['notificacoes_pendentes']}")


def _iniciar_web(host: str, porta: int, debug: bool = False) -> None:
    from anatel_monitor.web.app import criar_app
    flask_app = criar_app(debug=debug)
    logger.info("Interface web em http://%s:%d", host, porta)
    flask_app.run(host=host, port=porta, debug=debug)


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    enriquecer = not args.sem_detalhes

    if args.demo:
        from anatel_monitor.demo_data import popular_demo
        popular_demo()
        _iniciar_web(args.host, args.porta)

    elif args.web:
        _iniciar_web(args.host, args.porta)

    elif args.listar:
        _exibir_listagem(args.tipo)

    elif args.stats:
        _exibir_stats()

    elif args.agora:
        logger.info("Iniciando ciclo único...")
        resultado = executar_ciclo(enriquecer=enriquecer)
        print(f"\nCiclo concluído: {resultado}")

    else:
        logger.info("Iniciando agendamento diário...")
        iniciar_agendador()


if __name__ == "__main__":
    main()

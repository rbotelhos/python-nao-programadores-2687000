"""Gerenciamento do banco de dados SQLite para as consultas da Anatel."""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional

from .config import DB_PATH
from .models import Consulta

logger = logging.getLogger(__name__)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS consultas (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo               TEXT    NOT NULL UNIQUE,
    tipo                 TEXT    NOT NULL,
    numero               TEXT    NOT NULL,
    titulo               TEXT    NOT NULL,
    objeto               TEXT    DEFAULT '',
    descricao            TEXT    DEFAULT '',
    questionamentos      TEXT    DEFAULT '',
    data_abertura        TEXT,
    data_encerramento    TEXT,
    prazo_resposta       TEXT,
    data_publicacao_dou  TEXT,
    status               TEXT    DEFAULT 'Aberta',
    adiada               INTEGER DEFAULT 0,
    orgao_responsavel    TEXT    DEFAULT 'Anatel',
    numero_contribuicoes INTEGER DEFAULT 0,
    link                 TEXT    DEFAULT '',
    fonte                TEXT    DEFAULT '',
    data_descoberta      TEXT    NOT NULL,
    data_atualizacao     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS historico_alteracoes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    consulta_codigo  TEXT    NOT NULL,
    campo_alterado   TEXT    NOT NULL,
    valor_anterior   TEXT,
    valor_novo       TEXT,
    data_alteracao   TEXT    NOT NULL,
    FOREIGN KEY (consulta_codigo) REFERENCES consultas(codigo)
);

CREATE TABLE IF NOT EXISTS notificacoes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    consulta_codigo   TEXT    NOT NULL,
    tipo_notificacao  TEXT    NOT NULL,  -- 'nova' | 'atualizada' | 'encerrada' | 'adiada'
    mensagem          TEXT    DEFAULT '',
    data_notificacao  TEXT    NOT NULL,
    enviada           INTEGER DEFAULT 0,
    FOREIGN KEY (consulta_codigo) REFERENCES consultas(codigo)
);

CREATE INDEX IF NOT EXISTS idx_consultas_tipo   ON consultas(tipo);
CREATE INDEX IF NOT EXISTS idx_consultas_status ON consultas(status);
CREATE INDEX IF NOT EXISTS idx_notificacoes_enviada ON notificacoes(enviada);
"""


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager para conexão com o banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicializar_banco() -> None:
    """Cria as tabelas se não existirem."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info("Banco de dados inicializado em: %s", DB_PATH)


def salvar_consulta(consulta: Consulta) -> str:
    """
    Insere ou atualiza uma consulta no banco.

    Retorna:
        'nova'       — consulta inserida pela primeira vez
        'atualizada' — consulta existente com campos modificados
        'sem_changes'— consulta existente sem alterações
    """
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM consultas WHERE codigo = ?", (consulta.codigo,)
        ).fetchone()

        agora = datetime.now().isoformat()

        if existing is None:
            conn.execute(
                """
                INSERT INTO consultas (
                    codigo, tipo, numero, titulo, objeto, descricao,
                    questionamentos, data_abertura, data_encerramento,
                    prazo_resposta, data_publicacao_dou, status, adiada,
                    orgao_responsavel, numero_contribuicoes, link, fonte,
                    data_descoberta, data_atualizacao
                ) VALUES (
                    :codigo, :tipo, :numero, :titulo, :objeto, :descricao,
                    :questionamentos, :data_abertura, :data_encerramento,
                    :prazo_resposta, :data_publicacao_dou, :status, :adiada,
                    :orgao_responsavel, :numero_contribuicoes, :link, :fonte,
                    :data_descoberta, :data_atualizacao
                )
                """,
                {**consulta.to_dict(), "adiada": int(consulta.adiada)},
            )
            _registrar_notificacao(conn, consulta.codigo, "nova", agora)
            logger.info("Nova consulta salva: %s", consulta.codigo)
            return "nova"

        # Verifica campos que mudaram
        campos_monitorados = [
            "status", "adiada", "prazo_resposta", "data_encerramento",
            "numero_contribuicoes", "titulo", "objeto", "descricao",
        ]
        alteracoes = []
        for campo in campos_monitorados:
            valor_bd = existing[campo]
            valor_novo = getattr(consulta, campo)
            if campo == "adiada":
                valor_novo = int(valor_novo)
            if str(valor_bd) != str(valor_novo):
                alteracoes.append((campo, valor_bd, valor_novo))

        if not alteracoes:
            return "sem_changes"

        # Registra histórico
        for campo, anterior, novo in alteracoes:
            conn.execute(
                """
                INSERT INTO historico_alteracoes
                    (consulta_codigo, campo_alterado, valor_anterior, valor_novo, data_alteracao)
                VALUES (?, ?, ?, ?, ?)
                """,
                (consulta.codigo, campo, str(anterior), str(novo), agora),
            )

        # Atualiza registro
        conn.execute(
            """
            UPDATE consultas SET
                titulo = :titulo, objeto = :objeto, descricao = :descricao,
                questionamentos = :questionamentos,
                data_encerramento = :data_encerramento,
                prazo_resposta = :prazo_resposta,
                data_publicacao_dou = :data_publicacao_dou,
                status = :status, adiada = :adiada,
                numero_contribuicoes = :numero_contribuicoes,
                link = :link, data_atualizacao = :data_atualizacao
            WHERE codigo = :codigo
            """,
            {**consulta.to_dict(), "adiada": int(consulta.adiada), "data_atualizacao": agora},
        )

        # Notificação adequada
        tipo_notif = "adiada" if any(c[0] == "adiada" for c in alteracoes) else "atualizada"
        _registrar_notificacao(conn, consulta.codigo, tipo_notif, agora)
        logger.info("Consulta atualizada: %s (%s)", consulta.codigo, tipo_notif)
        return tipo_notif


def _registrar_notificacao(
    conn: sqlite3.Connection,
    codigo: str,
    tipo: str,
    agora: str,
) -> None:
    conn.execute(
        """
        INSERT INTO notificacoes (consulta_codigo, tipo_notificacao, data_notificacao, enviada)
        VALUES (?, ?, ?, 0)
        """,
        (codigo, tipo, agora),
    )


def buscar_notificacoes_pendentes() -> list[dict]:
    """Retorna notificações ainda não enviadas."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT n.id, n.consulta_codigo, n.tipo_notificacao, n.data_notificacao,
                   c.tipo, c.numero, c.titulo, c.status, c.prazo_resposta,
                   c.data_encerramento, c.link, c.adiada
            FROM notificacoes n
            JOIN consultas c ON c.codigo = n.consulta_codigo
            WHERE n.enviada = 0
            ORDER BY n.data_notificacao
            """
        ).fetchall()
        return [dict(r) for r in rows]


def marcar_notificacoes_enviadas(ids: list[int]) -> None:
    """Marca notificações como enviadas."""
    if not ids:
        return
    with get_connection() as conn:
        placeholders = ",".join("?" * len(ids))
        conn.execute(
            f"UPDATE notificacoes SET enviada = 1 WHERE id IN ({placeholders})", ids
        )


def listar_consultas(
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    apenas_abertas: bool = False,
) -> list[dict]:
    """Lista consultas com filtros opcionais."""
    query = "SELECT * FROM consultas WHERE 1=1"
    params: list = []

    if tipo:
        query += " AND tipo = ?"
        params.append(tipo)
    if status:
        query += " AND status = ?"
        params.append(status)
    if apenas_abertas:
        query += " AND status = 'Aberta'"

    query += " ORDER BY data_descoberta DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def buscar_consulta(codigo: str) -> Optional[dict]:
    """Busca uma consulta pelo código."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM consultas WHERE codigo = ?", (codigo,)
        ).fetchone()
        return dict(row) if row else None


def estatisticas() -> dict:
    """Retorna estatísticas gerais do banco."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM consultas").fetchone()[0]
        abertas = conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE status = 'Aberta'"
        ).fetchone()[0]
        cp = conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE tipo = 'Consulta Pública'"
        ).fetchone()[0]
        ts = conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE tipo = 'Tomada de Subsídio'"
        ).fetchone()[0]
        adiadas = conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE adiada = 1"
        ).fetchone()[0]
        pendentes = conn.execute(
            "SELECT COUNT(*) FROM notificacoes WHERE enviada = 0"
        ).fetchone()[0]

    return {
        "total": total,
        "abertas": abertas,
        "encerradas": total - abertas,
        "consultas_publicas": cp,
        "tomadas_subsidio": ts,
        "adiadas": adiadas,
        "notificacoes_pendentes": pendentes,
    }

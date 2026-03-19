"""Modelos de dados para as consultas da Anatel."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Consulta:
    """Representa um instrumento de Participação Social da Anatel."""

    # Identificação
    codigo: str                              # Código único (ex: "CP-10", "TS-26")
    tipo: str                                # "Consulta Pública" | "Tomada de Subsídio"
    numero: str                              # Número do instrumento

    # Conteúdo
    titulo: str                              # Título/nome do instrumento
    objeto: str = ""                         # Objeto / tema principal
    descricao: str = ""                      # Descrição detalhada
    questionamentos: str = ""               # Perguntas/questionamentos levantados

    # Datas e prazos
    data_abertura: Optional[str] = None     # Data de abertura
    data_encerramento: Optional[str] = None # Data de encerramento/prazo
    prazo_resposta: Optional[str] = None    # Prazo para envio de contribuições
    data_publicacao_dou: Optional[str] = None  # Publicação no Diário Oficial

    # Status
    status: str = "Aberta"                  # "Aberta" | "Encerrada" | "Suspensa"
    adiada: bool = False                    # Se o prazo foi prorrogado/adiado

    # Metadados
    orgao_responsavel: str = "Anatel"
    numero_contribuicoes: int = 0
    link: str = ""                          # URL para a consulta completa
    fonte: str = ""                         # "ParticipaAnatel" | "SACP"

    # Controle interno
    data_descoberta: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    data_atualizacao: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "tipo": self.tipo,
            "numero": self.numero,
            "titulo": self.titulo,
            "objeto": self.objeto,
            "descricao": self.descricao,
            "questionamentos": self.questionamentos,
            "data_abertura": self.data_abertura,
            "data_encerramento": self.data_encerramento,
            "prazo_resposta": self.prazo_resposta,
            "data_publicacao_dou": self.data_publicacao_dou,
            "status": self.status,
            "adiada": self.adiada,
            "orgao_responsavel": self.orgao_responsavel,
            "numero_contribuicoes": self.numero_contribuicoes,
            "link": self.link,
            "fonte": self.fonte,
            "data_descoberta": self.data_descoberta,
            "data_atualizacao": self.data_atualizacao,
        }

    @property
    def adiada_label(self) -> str:
        return "Sim" if self.adiada else "Não"

    def __str__(self) -> str:
        return (
            f"[{self.tipo}] {self.numero} — {self.titulo}\n"
            f"  Status: {self.status} | Adiada: {self.adiada_label}\n"
            f"  Prazo: {self.prazo_resposta or self.data_encerramento or 'N/D'}\n"
            f"  Link: {self.link}"
        )

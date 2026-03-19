"""Configurações do robô de monitoramento da Anatel."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Diretório raiz do projeto
BASE_DIR = Path(__file__).parent.parent

# Banco de dados
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "anatel_consultas.db"))

# URLs do portal Anatel
URLS = {
    "participa_anatel_em_andamento": (
        "https://apps.anatel.gov.br/participaanatel/ConsultasEmAndamento.aspx"
    ),
    "participa_anatel_encerradas": (
        "https://apps.anatel.gov.br/participaanatel/ConsultasEncerradas.aspx"
    ),
    "sacp_em_andamento": (
        "https://sistemas.anatel.gov.br/SACP/Contribuicoes/"
        "ListaConsultasContribuicoes.asp?Tipo=1&Opcao=andamento&SISQSmodulo=1442"
    ),
    "sacp_tomada_subsidio": (
        "https://sistemas.anatel.gov.br/SACP/Contribuicoes/"
        "ListaConsultasContribuicoes.asp?Tipo=2&Opcao=andamento&SISQSmodulo=1442"
    ),
}

# Notificações por e-mail (opcional)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_DESTINATARIOS = [
    e.strip()
    for e in os.getenv("EMAIL_DESTINATARIOS", "").split(",")
    if e.strip()
]

# Agendamento
HORARIO_EXECUCAO = os.getenv("HORARIO_EXECUCAO", "08:00")

# Playwright
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
PLAYWRIGHT_TIMEOUT_MS = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "30000"))

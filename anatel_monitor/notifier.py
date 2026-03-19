"""
Módulo de notificações.

Suporta dois canais:
  - Console (sempre ativo)
  - E-mail via SMTP (opcional, configurado via .env)
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from .config import (
    EMAIL_DESTINATARIOS,
    EMAIL_ENABLED,
    EMAIL_PASSWORD,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PORT,
    EMAIL_USER,
)
from .database import buscar_notificacoes_pendentes, marcar_notificacoes_enviadas

logger = logging.getLogger(__name__)

# Rótulos legíveis para cada tipo de notificação
TIPO_LABELS = {
    "nova": "NOVA Consulta/Tomada de Subsídio",
    "atualizada": "Consulta Atualizada",
    "encerrada": "Consulta Encerrada",
    "adiada": "Prazo Prorrogado/Adiado",
}


def _formatar_notificacao(notif: dict) -> str:
    """Formata uma notificação como texto legível."""
    tipo_label = TIPO_LABELS.get(notif["tipo_notificacao"], notif["tipo_notificacao"])
    adiada = "Sim" if notif.get("adiada") else "Não"
    prazo = notif.get("prazo_resposta") or notif.get("data_encerramento") or "N/D"

    return (
        f"{'='*60}\n"
        f"[{tipo_label}]\n"
        f"  Tipo       : {notif['tipo']}\n"
        f"  Número     : {notif['numero']}\n"
        f"  Título     : {notif['titulo']}\n"
        f"  Status     : {notif['status']}\n"
        f"  Adiada     : {adiada}\n"
        f"  Prazo      : {prazo}\n"
        f"  Link       : {notif.get('link', 'N/D')}\n"
        f"  Detectado  : {notif['data_notificacao'][:19]}\n"
    )


def _corpo_email_html(notificacoes: list[dict]) -> str:
    """Gera o corpo HTML do e-mail de notificação."""
    linhas_tabela = ""
    for n in notificacoes:
        tipo_label = TIPO_LABELS.get(n["tipo_notificacao"], n["tipo_notificacao"])
        adiada = "Sim" if n.get("adiada") else "Não"
        prazo = n.get("prazo_resposta") or n.get("data_encerramento") or "N/D"
        link = n.get("link", "")
        link_html = f'<a href="{link}" target="_blank">Abrir</a>' if link else "N/D"

        cor = {
            "nova": "#d4edda",
            "atualizada": "#fff3cd",
            "adiada": "#f8d7da",
            "encerrada": "#d1ecf1",
        }.get(n["tipo_notificacao"], "#ffffff")

        linhas_tabela += f"""
        <tr style="background:{cor}">
            <td>{tipo_label}</td>
            <td>{n['tipo']}</td>
            <td>{n['numero']}</td>
            <td>{n['titulo']}</td>
            <td>{n['status']}</td>
            <td>{adiada}</td>
            <td>{prazo}</td>
            <td>{link_html}</td>
        </tr>
        """

    return f"""
    <html><body>
    <h2>Monitoramento Anatel — Participação Social</h2>
    <p>Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <table border="1" cellpadding="6" cellspacing="0"
           style="border-collapse:collapse; font-family:Arial; font-size:13px;">
        <thead style="background:#003366; color:white">
            <tr>
                <th>Evento</th><th>Tipo</th><th>Número</th><th>Título</th>
                <th>Status</th><th>Adiada</th><th>Prazo</th><th>Link</th>
            </tr>
        </thead>
        <tbody>
            {linhas_tabela}
        </tbody>
    </table>
    <hr>
    <small>Robô de Monitoramento Anatel | python-anatel-monitor</small>
    </body></html>
    """


def _enviar_email(notificacoes: list[dict]) -> bool:
    """Envia e-mail com as notificações pendentes. Retorna True se bem-sucedido."""
    if not EMAIL_ENABLED or not EMAIL_USER or not EMAIL_DESTINATARIOS:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"[Anatel] {len(notificacoes)} atualização(ões) — "
        f"{datetime.now().strftime('%d/%m/%Y')}"
    )
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(EMAIL_DESTINATARIOS)

    corpo_texto = "\n".join(_formatar_notificacao(n) for n in notificacoes)
    corpo_html = _corpo_email_html(notificacoes)

    msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_USER, EMAIL_DESTINATARIOS, msg.as_string())
        logger.info("E-mail enviado para: %s", EMAIL_DESTINATARIOS)
        return True
    except Exception as exc:
        logger.error("Falha ao enviar e-mail: %s", exc)
        return False


def processar_notificacoes() -> int:
    """
    Processa e envia todas as notificações pendentes.

    Retorna o número de notificações processadas.
    """
    pendentes = buscar_notificacoes_pendentes()
    if not pendentes:
        logger.info("Nenhuma notificação pendente.")
        return 0

    logger.info("%d notificação(ões) pendente(s).", len(pendentes))

    # Exibe no console (sempre)
    print(f"\n{'#'*60}")
    print(f"  ANATEL — {len(pendentes)} notificação(ões)  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'#'*60}")
    for notif in pendentes:
        print(_formatar_notificacao(notif))

    # E-mail (opcional)
    email_ok = _enviar_email(pendentes)
    if EMAIL_ENABLED and not email_ok:
        logger.warning("E-mail não enviado. Verifique as configurações no .env")

    # Marca como enviadas
    ids = [n["id"] for n in pendentes]
    marcar_notificacoes_enviadas(ids)

    return len(pendentes)

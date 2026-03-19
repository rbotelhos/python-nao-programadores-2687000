"""
Scraper do portal Participa Anatel e SACP.

Usa Playwright para renderizar as páginas ASP.NET e extrair
as consultas públicas e tomadas de subsídio.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    sync_playwright,
    TimeoutError as PlaywrightTimeout,
)

from .config import PLAYWRIGHT_HEADLESS, PLAYWRIGHT_TIMEOUT_MS, URLS
from .models import Consulta

logger = logging.getLogger(__name__)

# Mapa de abreviaturas de mês em português
MESES_PT = {
    "jan": "01", "fev": "02", "mar": "03", "abr": "04",
    "mai": "05", "jun": "06", "jul": "07", "ago": "08",
    "set": "09", "out": "10", "nov": "11", "dez": "12",
}


def _normalizar_data(texto: str) -> Optional[str]:
    """Converte datas em vários formatos para ISO (YYYY-MM-DD)."""
    if not texto:
        return None
    texto = texto.strip().lower()

    # DD/MM/YYYY ou DD/MM/YY
    m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", texto)
    if m:
        d, mo, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"

    # DD de MÊS de YYYY
    m = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", texto)
    if m:
        d, mes, y = m.groups()
        mo = MESES_PT.get(mes[:3], "01")
        return f"{y}-{mo}-{d.zfill(2)}"

    return None


def _extrair_numero_tipo(titulo: str) -> tuple[str, str, str]:
    """
    Extrai tipo, número e código a partir do título.

    Exemplos:
        "Consulta Pública nº 10" → ("Consulta Pública", "10", "CP-10")
        "Tomada de Subsídio nº 26" → ("Tomada de Subsídio", "26", "TS-26")
    """
    titulo_lower = titulo.lower()

    if "tomada de subsídio" in titulo_lower or "tomada de subsidio" in titulo_lower:
        tipo = "Tomada de Subsídio"
        prefixo = "TS"
    else:
        tipo = "Consulta Pública"
        prefixo = "CP"

    m = re.search(r"n[°º\.]\s*(\d+)", titulo, re.IGNORECASE)
    numero = m.group(1) if m else "0"
    codigo = f"{prefixo}-{numero}"
    return tipo, numero, codigo


# ---------------------------------------------------------------------------
# Scraper principal — Participa Anatel
# ---------------------------------------------------------------------------

class AnatelScraper:
    """
    Scraper para o portal Participa Anatel (consultas a partir de abr/2022)
    e para o SACP (consultas anteriores).
    """

    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    def __enter__(self) -> "AnatelScraper":
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=PLAYWRIGHT_HEADLESS,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        return self

    def __exit__(self, *_) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _nova_pagina(self) -> Page:
        page = self._browser.new_page()
        page.set_default_timeout(PLAYWRIGHT_TIMEOUT_MS)
        page.set_extra_http_headers({
            "Accept-Language": "pt-BR,pt;q=0.9",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })
        return page

    # ------------------------------------------------------------------
    # Participa Anatel — consultas em andamento
    # ------------------------------------------------------------------

    def coletar_participa_anatel(self) -> list[Consulta]:
        """Coleta consultas em andamento do portal Participa Anatel."""
        consultas: list[Consulta] = []
        page = self._nova_pagina()

        try:
            logger.info("Acessando Participa Anatel...")
            page.goto(URLS["participa_anatel_em_andamento"], wait_until="networkidle")

            # Aguarda tabela ou cards de consultas
            try:
                page.wait_for_selector(
                    "table, .consulta-item, .card, [class*='consulta'], [class*='Consulta']",
                    timeout=15000,
                )
            except PlaywrightTimeout:
                logger.warning("Timeout aguardando elementos da página.")

            consultas = self._extrair_da_pagina_participa(page)
            logger.info("Participa Anatel: %d consultas encontradas.", len(consultas))

        except Exception as exc:
            logger.error("Erro ao coletar Participa Anatel: %s", exc)
        finally:
            page.close()

        return consultas

    def _extrair_da_pagina_participa(self, page: Page) -> list[Consulta]:
        """Extrai consultas da página do Participa Anatel via DOM."""
        consultas: list[Consulta] = []

        # Tenta extrair de tabelas
        linhas = page.query_selector_all("table tr")
        if len(linhas) > 1:
            headers = [
                th.inner_text().strip().lower()
                for th in (linhas[0].query_selector_all("th, td") or [])
            ]
            logger.debug("Colunas encontradas: %s", headers)

            for linha in linhas[1:]:
                cells = linha.query_selector_all("td")
                if not cells:
                    continue
                c = self._celulas_para_consulta(cells, headers, page.url)
                if c:
                    consultas.append(c)
            return consultas

        # Tenta extrair de cards/divs
        items = page.query_selector_all(
            "[class*='consulta'], [class*='Consulta'], [class*='card']"
        )
        for item in items:
            texto = item.inner_text()
            link_el = item.query_selector("a")
            href = ""
            if link_el:
                href = link_el.get_attribute("href") or ""
                if href and not href.startswith("http"):
                    href = "https://apps.anatel.gov.br" + href

            c = self._texto_para_consulta(texto, href)
            if c:
                consultas.append(c)

        return consultas

    def _celulas_para_consulta(
        self, cells: list, headers: list[str], base_url: str
    ) -> Optional[Consulta]:
        """Mapeia células de uma linha de tabela para um objeto Consulta."""
        dados: dict[str, str] = {}
        link = ""

        for i, cell in enumerate(cells):
            texto = cell.inner_text().strip()
            chave = headers[i] if i < len(headers) else f"col{i}"
            dados[chave] = texto

            # Captura link da célula
            a_el = cell.query_selector("a")
            if a_el and not link:
                href = a_el.get_attribute("href") or ""
                if href and not href.startswith("http"):
                    href = "https://apps.anatel.gov.br" + href
                link = href

        # Monta título a partir de campos disponíveis
        titulo = (
            dados.get("título", "")
            or dados.get("objeto", "")
            or dados.get("assunto", "")
            or dados.get("descrição", "")
            or next((v for v in dados.values() if len(v) > 10), "")
        )
        if not titulo:
            return None

        tipo, numero, codigo = _extrair_numero_tipo(titulo)

        # Datas
        data_enc = _normalizar_data(
            dados.get("encerramento", "")
            or dados.get("prazo", "")
            or dados.get("data final", "")
        )
        data_ab = _normalizar_data(
            dados.get("abertura", "")
            or dados.get("data inicial", "")
            or dados.get("início", "")
        )
        dou = _normalizar_data(dados.get("dou", "") or dados.get("publicação", ""))

        status_raw = dados.get("status", "Aberta").strip()
        status = "Encerrada" if "encerr" in status_raw.lower() else "Aberta"

        return Consulta(
            codigo=codigo,
            tipo=tipo,
            numero=numero,
            titulo=titulo,
            objeto=titulo,
            data_abertura=data_ab,
            data_encerramento=data_enc,
            prazo_resposta=data_enc,
            data_publicacao_dou=dou,
            status=status,
            link=link,
            fonte="ParticipaAnatel",
        )

    def _texto_para_consulta(self, texto: str, link: str) -> Optional[Consulta]:
        """Extrai uma Consulta a partir de texto bruto de um card/div."""
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        if not linhas:
            return None

        titulo = linhas[0]
        tipo, numero, codigo = _extrair_numero_tipo(titulo)

        descricao = " ".join(linhas[1:]) if len(linhas) > 1 else ""

        # Busca datas no texto completo
        data_enc = None
        for linha in linhas:
            if any(p in linha.lower() for p in ["prazo", "encerramento", "até"]):
                data_enc = _normalizar_data(linha)
                if data_enc:
                    break

        return Consulta(
            codigo=codigo,
            tipo=tipo,
            numero=numero,
            titulo=titulo,
            objeto=titulo,
            descricao=descricao,
            data_encerramento=data_enc,
            prazo_resposta=data_enc,
            link=link,
            fonte="ParticipaAnatel",
        )

    # ------------------------------------------------------------------
    # Detalhe de cada consulta
    # ------------------------------------------------------------------

    def enriquecer_consulta(self, consulta: Consulta) -> Consulta:
        """
        Acessa a página individual da consulta para extrair
        campos detalhados (objeto, questionamentos, adiamento, etc.).
        """
        if not consulta.link:
            return consulta

        page = self._nova_pagina()
        try:
            logger.debug("Enriquecendo consulta %s...", consulta.codigo)
            page.goto(consulta.link, wait_until="networkidle")

            texto_completo = page.inner_text("body")
            consulta = self._extrair_detalhes(consulta, page, texto_completo)

        except Exception as exc:
            logger.warning("Não foi possível enriquecer %s: %s", consulta.codigo, exc)
        finally:
            page.close()

        return consulta

    def _extrair_detalhes(
        self, consulta: Consulta, page: Page, texto: str
    ) -> Consulta:
        """Extrai campos detalhados da página individual de uma consulta."""
        texto_lower = texto.lower()

        # Objeto
        m = re.search(
            r"objeto[:\s]+(.*?)(?:\n|prazo|questionamento|contribui)",
            texto_lower,
            re.DOTALL,
        )
        if m:
            consulta.objeto = m.group(1).strip()[:500]

        # Questionamentos
        m = re.search(
            r"questionamento[s]?[:\s]+(.*?)(?:\n\n|prazo|contribui|encerr)",
            texto_lower,
            re.DOTALL,
        )
        if m:
            consulta.questionamentos = m.group(1).strip()[:2000]

        # Adiada / prorrogada
        if any(p in texto_lower for p in ["prorrogado", "adiado", "nova data", "prazo ampliado"]):
            consulta.adiada = True

        # Datas de encerramento
        for padrao in [
            r"encerramento[:\s]+(\d{2}/\d{2}/\d{4})",
            r"prazo[:\s]+(\d{2}/\d{2}/\d{4})",
            r"até[:\s]+(\d{2}/\d{2}/\d{4})",
        ]:
            m = re.search(padrao, texto_lower)
            if m:
                data = _normalizar_data(m.group(1))
                if data:
                    consulta.prazo_resposta = data
                    if not consulta.data_encerramento:
                        consulta.data_encerramento = data
                    break

        # Número de contribuições
        m = re.search(r"(\d+)\s+contribui[çc][õo]", texto_lower)
        if m:
            consulta.numero_contribuicoes = int(m.group(1))

        # Publicação no DOU
        m = re.search(
            r"(?:dou|di[aá]rio oficial)[:\s]+(\d{2}/\d{2}/\d{4})", texto_lower
        )
        if m:
            consulta.data_publicacao_dou = _normalizar_data(m.group(1))

        return consulta

    # ------------------------------------------------------------------
    # SACP — consultas anteriores a abril/2022
    # ------------------------------------------------------------------

    def coletar_sacp(self, tipo: str = "1") -> list[Consulta]:
        """
        Coleta consultas do SACP (sistema legado).

        tipo="1" → Consultas Públicas
        tipo="2" → Tomadas de Subsídio
        """
        consultas: list[Consulta] = []
        chave_url = "sacp_em_andamento" if tipo == "1" else "sacp_tomada_subsidio"
        page = self._nova_pagina()

        try:
            logger.info("Acessando SACP (tipo=%s)...", tipo)
            page.goto(URLS[chave_url], wait_until="networkidle")
            page.wait_for_selector("table", timeout=15000)

            linhas = page.query_selector_all("table tr")
            if len(linhas) <= 1:
                return consultas

            headers = [
                th.inner_text().strip().lower()
                for th in linhas[0].query_selector_all("th, td")
            ]

            for linha in linhas[1:]:
                cells = linha.query_selector_all("td")
                if not cells:
                    continue

                texts = [c.inner_text().strip() for c in cells]
                link_el = linha.query_selector("a")
                href = ""
                if link_el:
                    href = link_el.get_attribute("href") or ""
                    if href and not href.startswith("http"):
                        href = "https://sistemas.anatel.gov.br" + href

                # SACP: número, objeto, data_abertura, data_encerramento
                numero = texts[0] if texts else "0"
                titulo = texts[1] if len(texts) > 1 else f"Consulta {numero}"
                data_ab = _normalizar_data(texts[2]) if len(texts) > 2 else None
                data_enc = _normalizar_data(texts[3]) if len(texts) > 3 else None

                tipo_nome = "Tomada de Subsídio" if tipo == "2" else "Consulta Pública"
                prefixo = "TS" if tipo == "2" else "CP"
                codigo = f"{prefixo}-{numero}"

                consultas.append(
                    Consulta(
                        codigo=codigo,
                        tipo=tipo_nome,
                        numero=numero,
                        titulo=titulo,
                        objeto=titulo,
                        data_abertura=data_ab,
                        data_encerramento=data_enc,
                        prazo_resposta=data_enc,
                        link=href,
                        fonte="SACP",
                    )
                )

            logger.info("SACP (tipo=%s): %d consultas.", tipo, len(consultas))

        except Exception as exc:
            logger.error("Erro ao coletar SACP tipo=%s: %s", tipo, exc)
        finally:
            page.close()

        return consultas

    # ------------------------------------------------------------------
    # Coleta completa
    # ------------------------------------------------------------------

    def coletar_todas(self, enriquecer: bool = True) -> list[Consulta]:
        """
        Executa a coleta completa de ambos os portais.

        Args:
            enriquecer: Se True, acessa cada página individual para
                        extrair detalhes adicionais (mais lento).
        """
        todas: list[Consulta] = []

        # Portal novo (pós abr/2022)
        todas.extend(self.coletar_participa_anatel())

        # SACP legado
        todas.extend(self.coletar_sacp(tipo="1"))
        todas.extend(self.coletar_sacp(tipo="2"))

        # Deduplica por código
        vistos: set[str] = set()
        unicas: list[Consulta] = []
        for c in todas:
            if c.codigo not in vistos:
                vistos.add(c.codigo)
                unicas.append(c)

        logger.info("Total único de consultas coletadas: %d", len(unicas))

        if enriquecer:
            logger.info("Enriquecendo detalhes das consultas...")
            unicas = [self.enriquecer_consulta(c) for c in unicas]

        return unicas

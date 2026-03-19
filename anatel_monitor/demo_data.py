"""
Popula o banco com dados de demonstração realistas baseados em
consultas públicas e tomadas de subsídio reais da Anatel.

Uso:
    python main.py --demo
"""

from datetime import datetime

from .database import inicializar_banco, salvar_consulta
from .models import Consulta

_HOJE = datetime.now()
_ANO  = _hoje_ano = _HOJE.year


def _iso(y: int, m: int, d: int) -> str:
    return f"{y:04d}-{m:02d}-{d:02d}"


DEMO_CONSULTAS: list[dict] = [
    # ── Abertas — Ano Atual ─────────────────────────────────────
    {
        "codigo": f"CP-{_ANO}-01",
        "tipo": "Consulta Pública",
        "numero": f"{_ANO}-01",
        "titulo": f"Consulta Pública nº 1/{_ANO} — Revisão do PGMC",
        "objeto": (
            "Revisão do Plano Geral de Metas de Competição (PGMC), "
            "com foco na regulação assimétrica de operadoras com Poder "
            "de Mercado Significativo (PMS) no setor de telecomunicações."
        ),
        "descricao": (
            "A Anatel coloca em consulta pública a proposta de revisão "
            "do PGMC para adequação às condições competitivas atuais do mercado."
        ),
        "questionamentos": (
            "1. A metodologia de definição de PMS proposta é adequada?\n"
            "2. As obrigações simétricas devem ser mantidas ou reduzidas?\n"
            "3. Há necessidade de incluir novos mercados relevantes?"
        ),
        "data_abertura": _iso(_ANO, 1, 15),
        "data_encerramento": _iso(_ANO, 4, 30),
        "prazo_resposta": _iso(_ANO, 4, 30),
        "status": "Aberta",
        "adiada": False,
        "numero_contribuicoes": 87,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"TS-{_ANO}-01",
        "tipo": "Tomada de Subsídio",
        "numero": f"{_ANO}-01",
        "titulo": f"Tomada de Subsídio nº 1/{_ANO} — Regulamentação de Comunicação por Satélite",
        "objeto": (
            "Levantamento de subsídios para a regulamentação do uso de órbitas "
            "e espectro por sistemas de satélite de órbita baixa (LEO), "
            "incluindo constelações de banda larga."
        ),
        "descricao": (
            "Diante da expansão de constelações de satélites LEO no Brasil, "
            "a Anatel busca subsídios da sociedade e da indústria para "
            "elaborar um marco regulatório específico."
        ),
        "questionamentos": (
            "1. Quais são as principais barreiras regulatórias para implantação de LEO no Brasil?\n"
            "2. Como deve ser tratada a coordenação de frequências com sistemas GEO?\n"
            "3. Há necessidade de licença específica para terminais de usuário?"
        ),
        "data_abertura": _iso(_ANO, 2, 1),
        "data_encerramento": _iso(_ANO, 3, 31),
        "prazo_resposta": _iso(_ANO, 3, 31),
        "status": "Aberta",
        "adiada": False,
        "numero_contribuicoes": 124,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"CP-{_ANO}-02",
        "tipo": "Consulta Pública",
        "numero": f"{_ANO}-02",
        "titulo": f"Consulta Pública nº 2/{_ANO} — Atualização do RGC",
        "objeto": (
            "Proposta de atualização do Regulamento Geral de Acessibilidade "
            "de Serviços de Telecomunicações de Interesse Coletivo (RGA), "
            "incorporando novas tecnologias assistivas."
        ),
        "descricao": (
            "A Anatel propõe a atualização do RGA para incluir obrigações "
            "de acessibilidade para aplicativos de comunicação e serviços OTT."
        ),
        "questionamentos": (
            "1. Os prazos de adequação propostos são factíveis?\n"
            "2. Quais tecnologias assistivas devem ser obrigatórias?\n"
            "3. Como garantir a fiscalização efetiva das novas obrigações?"
        ),
        "data_abertura": _iso(_ANO, 3, 1),
        "data_encerramento": _iso(_ANO, 3, 25),
        "prazo_resposta": _iso(_ANO, 3, 25),
        "status": "Aberta",
        "adiada": True,   # Prazo adiado — urgente!
        "numero_contribuicoes": 43,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"TS-{_ANO}-02",
        "tipo": "Tomada de Subsídio",
        "numero": f"{_ANO}-02",
        "titulo": f"Tomada de Subsídio nº 2/{_ANO} — Espectro para 6G",
        "objeto": (
            "Consulta prévia sobre faixas de radiofrequências candidatas "
            "ao 6G no Brasil, em preparação à Conferência Mundial de "
            "Radiocomunicações (CMR-27)."
        ),
        "descricao": (
            "A Anatel inicia o processo de preparação nacional para a CMR-27, "
            "identificando faixas candidatas para sistemas IMT-2030 (6G) "
            "e coletando posições da indústria brasileira."
        ),
        "questionamentos": (
            "1. Quais faixas de espectro o Brasil deve defender na CMR-27 para o 6G?\n"
            "2. Há conflitos com sistemas atuais nas faixas candidatas?\n"
            "3. Qual o impacto econômico estimado do 6G para o Brasil?"
        ),
        "data_abertura": _iso(_ANO, 2, 20),
        "data_encerramento": _iso(_ANO, 5, 20),
        "prazo_resposta": _iso(_ANO, 5, 20),
        "status": "Aberta",
        "adiada": False,
        "numero_contribuicoes": 56,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },

    # ── Abertas — Ano Anterior ───────────────────────────────────
    {
        "codigo": f"CP-{_ANO-1}-04",
        "tipo": "Consulta Pública",
        "numero": f"{_ANO-1}-04",
        "titulo": f"Consulta Pública nº 4/{_ANO-1} — Revisão do PGMU V",
        "objeto": (
            "Revisão do Plano Geral de Metas de Universalização (PGMU V) "
            "para o Serviço Telefônico Fixo Comutado (STFC), com propostas "
            "de adequação às demandas de conectividade em áreas rurais."
        ),
        "descricao": (
            "Proposta de revisão das metas de universalização do STFC, "
            "priorizando acesso à internet em banda larga em municípios "
            "remotos e comunidades indígenas."
        ),
        "questionamentos": (
            "1. As metas de velocidade mínima são adequadas para áreas remotas?\n"
            "2. Quais mecanismos de financiamento devem ser adotados?\n"
            "3. Como incluir populações indígenas nas metas de universalização?"
        ),
        "data_abertura": _iso(_ANO-1, 9, 10),
        "data_encerramento": _iso(_ANO, 2, 28),
        "prazo_resposta": _iso(_ANO, 2, 28),
        "status": "Aberta",
        "adiada": True,
        "numero_contribuicoes": 312,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"TS-{_ANO-1}-03",
        "tipo": "Tomada de Subsídio",
        "numero": f"{_ANO-1}-03",
        "titulo": f"Tomada de Subsídio nº 3/{_ANO-1} — Qualidade na Banda Larga Fixa",
        "objeto": (
            "Coleta de subsídios para revisão da regulamentação de qualidade "
            "do Serviço de Comunicação Multimídia (SCM), com ênfase em "
            "indicadores de latência e disponibilidade."
        ),
        "descricao": (
            "A Anatel avalia a necessidade de atualizar os indicadores de "
            "qualidade do SCM frente ao crescimento do trabalho remoto e "
            "serviços de streaming."
        ),
        "questionamentos": (
            "1. Os indicadores atuais refletem a experiência do usuário?\n"
            "2. Quais métricas de latência devem ser reguladas?\n"
            "3. Como mensurar a qualidade em redes wireless (FWA)?"
        ),
        "data_abertura": _iso(_ANO-1, 11, 5),
        "data_encerramento": _iso(_ANO, 3, 15),
        "prazo_resposta": _iso(_ANO, 3, 15),
        "status": "Aberta",
        "adiada": False,
        "numero_contribuicoes": 198,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },

    # ── Encerradas ──────────────────────────────────────────────
    {
        "codigo": f"CP-{_ANO-1}-01",
        "tipo": "Consulta Pública",
        "numero": f"{_ANO-1}-01",
        "titulo": f"Consulta Pública nº 1/{_ANO-1} — Regulamento de Gestão de Redes",
        "objeto": "Proposta de regulamento sobre gestão de tráfego e neutralidade de rede.",
        "descricao": (
            "Revisão das regras de neutralidade de rede para serviços de "
            "telecomunicações e aplicações de internet."
        ),
        "questionamentos": (
            "1. As exceções à neutralidade de rede são suficientes?\n"
            "2. Como deve ser tratado o tráfego zero-rating?\n"
            "3. Quais são as práticas discriminatórias que devem ser vedadas?"
        ),
        "data_abertura": _iso(_ANO-1, 1, 20),
        "data_encerramento": _iso(_ANO-1, 3, 31),
        "prazo_resposta": _iso(_ANO-1, 3, 31),
        "data_publicacao_dou": _iso(_ANO-1, 1, 22),
        "status": "Encerrada",
        "adiada": False,
        "numero_contribuicoes": 567,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"TS-{_ANO-1}-01",
        "tipo": "Tomada de Subsídio",
        "numero": f"{_ANO-1}-01",
        "titulo": f"Tomada de Subsídio nº 1/{_ANO-1} — Revisão do PGMC",
        "objeto": "Subsídios para a revisão do Plano Geral de Metas de Competição.",
        "data_abertura": _iso(_ANO-1, 3, 1),
        "data_encerramento": _iso(_ANO-1, 5, 15),
        "prazo_resposta": _iso(_ANO-1, 5, 15),
        "data_publicacao_dou": _iso(_ANO-1, 3, 3),
        "status": "Encerrada",
        "adiada": False,
        "numero_contribuicoes": 289,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"CP-{_ANO-1}-02",
        "tipo": "Consulta Pública",
        "numero": f"{_ANO-1}-02",
        "titulo": f"Consulta Pública nº 2/{_ANO-1} — Regulamentação do 5G Standalone",
        "objeto": (
            "Atualização do marco regulatório para implantação de redes "
            "5G Standalone (SA) no Brasil, incluindo network slicing e MEC."
        ),
        "data_abertura": _iso(_ANO-1, 4, 1),
        "data_encerramento": _iso(_ANO-1, 6, 30),
        "prazo_resposta": _iso(_ANO-1, 6, 30),
        "data_publicacao_dou": _iso(_ANO-1, 4, 3),
        "status": "Encerrada",
        "adiada": True,
        "numero_contribuicoes": 431,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"CP-{_ANO-1}-03",
        "tipo": "Consulta Pública",
        "numero": f"{_ANO-1}-03",
        "titulo": f"Consulta Pública nº 3/{_ANO-1} — Proteção contra Radiações Eletromagnéticas",
        "objeto": (
            "Revisão dos limites de exposição humana a campos eletromagnéticos "
            "emitidos por equipamentos e antenas de telecomunicações."
        ),
        "data_abertura": _iso(_ANO-1, 7, 10),
        "data_encerramento": _iso(_ANO-1, 9, 20),
        "prazo_resposta": _iso(_ANO-1, 9, 20),
        "status": "Encerrada",
        "adiada": False,
        "numero_contribuicoes": 1204,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"TS-{_ANO-1}-02",
        "tipo": "Tomada de Subsídio",
        "numero": f"{_ANO-1}-02",
        "titulo": f"Tomada de Subsídio nº 2/{_ANO-1} — IoT e Redes LP-WAN",
        "objeto": (
            "Subsídios para revisão do regulamento de uso de radiofrequências "
            "para aplicações de Internet das Coisas (IoT) e redes LP-WAN."
        ),
        "data_abertura": _iso(_ANO-1, 8, 1),
        "data_encerramento": _iso(_ANO-1, 10, 31),
        "prazo_resposta": _iso(_ANO-1, 10, 31),
        "status": "Encerrada",
        "adiada": False,
        "numero_contribuicoes": 178,
        "link": "https://apps.anatel.gov.br/ParticipaAnatel/Home.aspx",
        "fonte": "ParticipaAnatel",
    },
    {
        "codigo": f"CP-{_ANO-2}-05",
        "tipo": "Consulta Pública",
        "numero": f"{_ANO-2}-05",
        "titulo": f"Consulta Pública nº 5/{_ANO-2} — Revisão do RGQ do SMP",
        "objeto": (
            "Revisão do Regulamento de Gestão de Qualidade do Serviço Móvel Pessoal (RGQ-SMP), "
            "com foco em cobertura 4G em áreas urbanas e indicadores de voz."
        ),
        "data_abertura": _iso(_ANO-2, 10, 5),
        "data_encerramento": _iso(_ANO-2, 12, 20),
        "prazo_resposta": _iso(_ANO-2, 12, 20),
        "status": "Encerrada",
        "adiada": False,
        "numero_contribuicoes": 892,
        "link": "https://sistemas.anatel.gov.br/SACP/Contribuicoes/ListaConsultasContribuicoes.asp",
        "fonte": "SACP",
    },
]


def popular_demo() -> int:
    """Insere dados de demonstração no banco. Retorna número de registros inseridos."""
    inicializar_banco()
    inseridos = 0
    for dados in DEMO_CONSULTAS:
        c = Consulta(
            codigo=dados["codigo"],
            tipo=dados["tipo"],
            numero=dados["numero"],
            titulo=dados["titulo"],
            objeto=dados.get("objeto", dados["titulo"]),
            descricao=dados.get("descricao", ""),
            questionamentos=dados.get("questionamentos", ""),
            data_abertura=dados.get("data_abertura"),
            data_encerramento=dados.get("data_encerramento"),
            prazo_resposta=dados.get("prazo_resposta"),
            data_publicacao_dou=dados.get("data_publicacao_dou"),
            status=dados.get("status", "Aberta"),
            adiada=dados.get("adiada", False),
            numero_contribuicoes=dados.get("numero_contribuicoes", 0),
            link=dados.get("link", ""),
            fonte=dados.get("fonte", "Demo"),
        )
        resultado = salvar_consulta(c)
        if resultado == "nova":
            inseridos += 1

    print(f"✓ {inseridos} consultas de demonstração inseridas no banco.")
    return inseridos

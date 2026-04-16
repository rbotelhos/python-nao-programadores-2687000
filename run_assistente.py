#!/usr/bin/env python3
"""
Assistente Regulatório Anatel
Ponto de entrada principal.

Uso:
    python run_assistente.py
    python run_assistente.py --reindexar

Pré-requisitos:
    1. pip install -r requirements_assistente.txt
    2. export ANTHROPIC_API_KEY='sua-chave'
    3. Adicione documentos PDF/DOCX/TXT em documentos/
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from assistente_anatel.cli import main

if __name__ == "__main__":
    main()

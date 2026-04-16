import argparse
import os
import sys

import anthropic


def print_banner():
    print("\n" + "=" * 65)
    print("  Assistente Regulatório Anatel")
    print("  Análise e Estratégia Normativa em Telecomunicações")
    print("=" * 65)


def print_help():
    print("\nComandos disponíveis:")
    print("  /reindexar   Reindexar todos os documentos da pasta 'documentos/'")
    print("  /limpar      Limpar histórico da conversa atual")
    print("  /fontes      Exibir detalhes das últimas fontes consultadas")
    print("  /ajuda       Exibir esta mensagem")
    print("  /sair        Encerrar o assistente")


def main():
    from .config import DOCUMENTOS_DIR, CHROMA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
    from .loader import load_all_documents
    from .store import VectorStore
    from .assistant import AnatelAssistant

    parser = argparse.ArgumentParser(description="Assistente Regulatório Anatel")
    parser.add_argument(
        "--reindexar", action="store_true",
        help="Forçar reindexação completa dos documentos"
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Erro: variável de ambiente ANTHROPIC_API_KEY não definida.")
        print("Configure com: export ANTHROPIC_API_KEY='sua-chave-aqui'")
        sys.exit(1)

    print_banner()

    store = VectorStore(CHROMA_DIR)

    needs_index = args.reindexar or store.count() == 0
    if needs_index:
        if args.reindexar:
            print("\nReindexando documentos...")
            store.reset()
        else:
            print(f"\nBase de conhecimento vazia. Indexando documentos em '{DOCUMENTOS_DIR}/'...")

        docs = load_all_documents(DOCUMENTOS_DIR, CHUNK_SIZE, CHUNK_OVERLAP)
        if not docs:
            print(f"\nNenhum documento encontrado em '{DOCUMENTOS_DIR}/'.")
            print("Adicione arquivos PDF, DOCX ou TXT nessa pasta e execute novamente.")
            print("O assistente continuará no modo genérico (sem base documental).")
        else:
            store.add_documents(docs)
            n_files = len(set(d['file'] for d in docs))
            print(f"\n✓ {len(docs)} trechos indexados de {n_files} documento(s).")
    else:
        print(f"\n✓ Base de conhecimento pronta: {store.count()} trechos indexados.")

    print_help()
    print("-" * 65)

    assistant = AnatelAssistant(store)
    last_sources: list = []

    while True:
        try:
            user_input = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nEncerrando. Até logo!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "/sair":
            print("Encerrando. Até logo!")
            break
        elif cmd == "/limpar":
            assistant.reset()
            print("Histórico da conversa limpo.")
            continue
        elif cmd == "/ajuda":
            print_help()
            continue
        elif cmd == "/fontes":
            if last_sources:
                print("\nFontes consultadas na última resposta:")
                seen = set()
                for s in last_sources:
                    key = (s['file'], s['chunk_idx'])
                    if key not in seen:
                        seen.add(key)
                        print(f"  • {s['file']} — trecho {s['chunk_idx'] + 1}")
            else:
                print("Nenhuma fonte consultada ainda.")
            continue
        elif cmd == "/reindexar":
            print(f"\nReindexando documentos em '{DOCUMENTOS_DIR}/'...")
            store.reset()
            docs = load_all_documents(DOCUMENTOS_DIR, CHUNK_SIZE, CHUNK_OVERLAP)
            if docs:
                store.add_documents(docs)
                n_files = len(set(d['file'] for d in docs))
                print(f"✓ {len(docs)} trechos reindexados de {n_files} documento(s).")
            else:
                print("Nenhum documento encontrado.")
            continue

        print("\nAssistente: ", end="", flush=True)
        try:
            _, last_sources = assistant.chat(user_input)
            if last_sources:
                unique_files = list(dict.fromkeys(s['file'] for s in last_sources))
                print(f"\n\n[Fontes: {', '.join(unique_files)}]")
            else:
                print()
        except anthropic.AuthenticationError:
            print("\nErro de autenticação: chave de API inválida. Verifique ANTHROPIC_API_KEY.")
        except anthropic.RateLimitError:
            print("\nErro: limite de requisições atingido. Aguarde e tente novamente.")
        except anthropic.APIConnectionError:
            print("\nErro de conexão. Verifique sua internet e tente novamente.")
        except Exception as e:
            print(f"\nErro inesperado: {e}")

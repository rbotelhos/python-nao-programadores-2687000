import re
from pathlib import Path
from typing import List, Dict, Any


def load_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def load_pdf(file_path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("Instale pypdf: pip install pypdf")
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append(f"[Página {i + 1}]\n{text}")
    return "\n\n".join(pages)


def load_docx(file_path: str) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ImportError("Instale python-docx: pip install python-docx")
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def load_document(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    loaders = {
        '.pdf': load_pdf,
        '.docx': load_docx,
        '.doc': load_docx,
        '.txt': load_txt,
        '.md': load_txt,
    }
    loader = loaders.get(ext, load_txt)
    return loader(file_path)


def chunk_legal_text(text: str, chunk_size: int = 1500, overlap: int = 300) -> List[str]:
    """Split regulatory/legal text preserving article and section boundaries."""
    text = re.sub(r'\n{3,}', '\n\n', text.strip())

    # Split at article/section boundary markers common in Brazilian normative docs
    article_pattern = r'(?=\n\s*(?:Art\.|Artigo\s|§\s*\d|\bCAPÍTULO\b|\bCapítulo\b|\bSEÇÃO\b|\bSeção\b|\bSUBSEÇÃO\b)[\s\d])'
    sections = re.split(article_pattern, text)

    chunks = []
    current = ""

    for section in sections:
        if not section.strip():
            continue
        if len(current) + len(section) <= chunk_size:
            current += section
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(section) <= chunk_size:
                current = section
            else:
                # Section too long: split by paragraph
                for para in re.split(r'\n\n+', section):
                    if len(current) + len(para) + 2 <= chunk_size:
                        current += ('\n\n' if current else '') + para
                    else:
                        if current.strip():
                            chunks.append(current.strip())
                        current = para

    if current.strip():
        chunks.append(current.strip())

    # Add trailing overlap from previous chunk for context continuity
    result = []
    for i, chunk in enumerate(chunks):
        if i > 0 and overlap > 0:
            prev_tail = chunks[i - 1][-overlap:]
            break_pos = prev_tail.find('\n')
            if break_pos > 0:
                prev_tail = prev_tail[break_pos:].strip()
            if prev_tail:
                chunk = prev_tail + '\n\n' + chunk
        result.append(chunk)

    return [c for c in result if len(c.strip()) > 50]


def load_all_documents(docs_dir: str, chunk_size: int = 1500, overlap: int = 300) -> List[Dict[str, Any]]:
    """Load and chunk all supported documents from a directory."""
    supported_exts = {'.pdf', '.docx', '.doc', '.txt', '.md'}
    docs_path = Path(docs_dir)

    if not docs_path.exists():
        docs_path.mkdir(parents=True)
        return []

    all_chunks = []
    files = sorted([f for f in docs_path.rglob('*') if f.suffix.lower() in supported_exts])

    if not files:
        return []

    for file_path in files:
        print(f"  Carregando: {file_path.name}...")
        try:
            text = load_document(str(file_path))
            if not text.strip():
                print(f"    Aviso: arquivo vazio ou sem texto extraível.")
                continue
            chunks = chunk_legal_text(text, chunk_size, overlap)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    'id': f"{file_path.stem}_{i}",
                    'file': file_path.name,
                    'chunk_idx': i,
                    'total_chunks': len(chunks),
                    'text': chunk,
                })
            print(f"    {len(chunks)} trecho(s) indexado(s).")
        except Exception as e:
            print(f"    Erro ao processar {file_path.name}: {e}")

    return all_chunks

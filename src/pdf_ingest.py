import io
import re
from typing import List

import pandas as pd
import pdfplumber

from .bank_ingest import parse_statement_csv


def _extract_tables_from_pdf_bytes(pdf_bytes: bytes) -> List[pd.DataFrame]:
    tables = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            try:
                page_tables = page.extract_tables()
            except Exception:
                page_tables = []
            for t in page_tables:
                # converter tabela (lista de linhas) em DataFrame
                try:
                    df = pd.DataFrame(t[1:], columns=t[0])
                    tables.append(df)
                except Exception:
                    continue
    return tables


def _extract_lines_from_pdf_bytes(pdf_bytes: bytes) -> List[str]:
    lines = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                s = line.strip()
                if s:
                    lines.append(s)
    return lines


def _lines_to_df(lines: List[str]) -> pd.DataFrame:
    """Tentativa heurística de extrair transações de linhas de texto.

    Procura por linhas contendo data e valor. Formatos comuns: dd/mm/yyyy, yyyy-mm-dd.
    """
    rows = []
    date_re = r"(\d{2}[\/\-]\d{2}[\/\-]\d{4}|\d{4}[\-]\d{2}[\-]\d{2})"
    amount_re = r"(-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)"

    for line in lines:
        # tentar encontrar data e valor
        d_match = re.search(date_re, line)
        a_match = re.search(amount_re + r"(?!.*\d)", line)
        if d_match and a_match:
            date = d_match.group(0)
            amount = a_match.group(0)
            # descrição: remover data e valor do texto
            desc = line.replace(date, "").replace(amount, "").strip()
            # normalizar amount
            amt = amount.replace('.', '').replace(',', '.') if ',' in amount else amount
            try:
                amt_f = float(amt)
            except Exception:
                try:
                    amt_f = float(amt.replace(' ', ''))
                except Exception:
                    amt_f = 0.0
            rows.append({"date": date, "description": desc, "amount": amt_f})

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # tentar converter date
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    return df


def parse_statement_pdf(file_stream) -> pd.DataFrame:
    """Parseia um PDF de extrato bancário, tentando extrair tabelas ou linhas e
    retornando um DataFrame normalizado com colunas date, description, amount.

    Usa pdfplumber para extrair tabelas. Se encontrar tabelas, tenta salvá-las em CSV
    em memória e reaproveitar o `parse_statement_csv` para normalização conservadora.
    """
    pdf_bytes = file_stream.read()

    # 1) Tentar extrair tabelas
    try:
        tables = _extract_tables_from_pdf_bytes(pdf_bytes)
    except Exception as e:
        tables = []

    if tables:
        # concatenar tabelas em CSV em memória e chamar parse_statement_csv para heurísticas
        for tbl in tables:
            try:
                csv_buf = io.StringIO()
                tbl.to_csv(csv_buf, index=False)
                csv_buf.seek(0)
                parsed = parse_statement_csv(csv_buf)
                if not parsed.empty:
                    return parsed
            except Exception:
                continue

    # 2) fallback: extrair linhas de texto e construir df heurístico
    try:
        lines = _extract_lines_from_pdf_bytes(pdf_bytes)
        parsed = _lines_to_df(lines)
        if not parsed.empty:
            # normalizar chamando parse_statement_csv com CSV gerado
            csv_buf = io.StringIO()
            parsed.to_csv(csv_buf, index=False)
            csv_buf.seek(0)
            return parse_statement_csv(csv_buf)
    except Exception:
        pass

    # 3) fallback vazio
    return pd.DataFrame()

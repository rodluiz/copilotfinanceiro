import io
import pandas as pd


def parse_statement_csv(file_stream) -> pd.DataFrame:
    """Tenta parsear um CSV de extrato bancário e normalizar colunas.

    Heurísticas:
    - Procura colunas que contenham: date, data, descricao, description, amount, valor, credit, debit
    - Converte data para datetime e amount para float (negativos despesas)
    - Retorna DataFrame com colunas: date, description, amount
    """
    # Ler CSV com pandas a partir do stream
    try:
        df = pd.read_csv(file_stream, sep=None, engine="python")
    except Exception:
        # Tentar leitura simples com vírgula
        df = pd.read_csv(file_stream)

    cols = {c.lower(): c for c in df.columns}

    # Encontrar coluna de data
    date_col = None
    for candidate in ("date", "data", "transaction_date", "dt"):
        if candidate in cols:
            date_col = cols[candidate]
            break

    # Encontrar descrição
    desc_col = None
    for candidate in ("description", "descricao", "details", "historico", "lancamento"):
        if candidate in cols:
            desc_col = cols[candidate]
            break

    # Encontrar valor
    amt_col = None
    for candidate in ("amount", "valor", "valor_r$", "value", "valor_bruto"):
        if candidate in cols:
            amt_col = cols[candidate]
            break

    # Tentar colunas de crédito/débito
    credit_col = None
    debit_col = None
    for candidate in ("credit", "credito"):
        if candidate in cols:
            credit_col = cols[candidate]
            break
    for candidate in ("debit", "debito"):
        if candidate in cols:
            debit_col = cols[candidate]
            break

    # Construir DataFrame normalizado
    norm = pd.DataFrame()

    if date_col:
        norm["date"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        # Se não houver data, usar índice sequencial
        norm["date"] = pd.NaT

    if desc_col:
        norm["description"] = df[desc_col].astype(str)
    else:
        norm["description"] = df.astype(str).apply(lambda row: " ".join(row.values), axis=1)

    if amt_col:
        norm["amount"] = (
            df[amt_col]
            .astype(str)
            .str.replace(r"[^0-9,\-\.]+", "", regex=True)
            .str.replace(",", ".")
            .replace("", "0")
            .astype(float)
        )
    else:
        # Se houver colunas credit/debit
        if credit_col and debit_col:
            cred = df[credit_col].astype(str).str.replace(r"[^0-9,\-\.]+", "", regex=True).str.replace(",", ".")
            deb = df[debit_col].astype(str).str.replace(r"[^0-9,\-\.]+", "", regex=True).str.replace(",", ".")
            # assumir débito negativo
            norm["amount"] = cred.replace("", "0").astype(float).fillna(0) - deb.replace("", "0").astype(float).fillna(0)
        elif credit_col:
            norm["amount"] = (
                df[credit_col].astype(str).str.replace(r"[^0-9,\-\.]+", "", regex=True).str.replace(",", ".").replace("", "0").astype(float)
            )
        elif debit_col:
            norm["amount"] = -(
                df[debit_col].astype(str).str.replace(r"[^0-9,\-\.]+", "", regex=True).str.replace(",", ".").replace("", "0").astype(float)
            )
        else:
            # fallback: tentar converter primeira coluna numérica
            num_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if num_cols:
                norm["amount"] = df[num_cols[0]].astype(float)
            else:
                # última alternativa: zeros
                norm["amount"] = 0.0

    # Ordenar por data quando presente
    if norm["date"].notna().any():
        norm = norm.sort_values(by="date")

    norm = norm.reset_index(drop=True)
    return norm

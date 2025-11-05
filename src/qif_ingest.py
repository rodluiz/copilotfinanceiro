import pandas as pd


def parse_statement_qif(file_stream) -> pd.DataFrame:
    """Parser simples para QIF que extrai registros com campos D (date), T (amount), P (payee/memo).

    Retorna DataFrame com colunas date, description, amount.
    """
    text = file_stream.read()
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')

    records = []
    current = {}
    for line in text.splitlines():
        if not line:
            continue
        tag = line[0]
        value = line[1:].strip()
        if tag == 'D':
            current['date'] = value
        elif tag == 'T':
            # amount
            try:
                amt = float(value.replace(',', ''))
            except Exception:
                try:
                    amt = float(value.replace('.', '').replace(',', '.'))
                except Exception:
                    amt = 0.0
            current['amount'] = amt
        elif tag == 'P':
            current['description'] = value
        elif tag == '^':
            # end of record
            records.append(current.copy())
            current = {}
        else:
            # ignorar outros
            continue

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True)
    if 'description' not in df.columns:
        df['description'] = ''
    if 'amount' not in df.columns:
        df['amount'] = 0.0

    return df[['date', 'description', 'amount']]

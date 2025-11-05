from io import BytesIO
import pandas as pd

try:
    from ofxparse import OfxParser
except Exception:
    OfxParser = None


def parse_statement_ofx(file_stream) -> pd.DataFrame:
    """Parseia arquivo OFX/QFX e retorna DataFrame com colunas: date, description, amount."""
    if OfxParser is None:
        raise ImportError("ofxparse não está instalado")

    # ofxparse espera um file-like de bytes
    data = file_stream.read()
    if isinstance(data, str):
        data = data.encode("utf-8")

    buf = BytesIO(data)
    try:
        ofx = OfxParser.parse(buf)
    except Exception as e:
        # ofxparse pode falhar em arquivos OFX/QFX incompletos; realizar fallback heurístico
        # Primeiro tentar decodificar e reprocessar
        buf.seek(0)
        try:
            text = buf.read().decode('utf-8', errors='ignore')
            buf2 = BytesIO(text.encode('utf-8'))
            ofx = OfxParser.parse(buf2)
        except Exception:
            # Fallback: tentar extrair transações por regex das tags <STMTTRN> ... </STMTTRN>
            try:
                from re import findall, DOTALL, search

                raw = data.decode('utf-8', errors='ignore')
                # buscar blocos STMTTRN
                blocks = findall(r"<STMTTRN>(.*?)</STMTTRN>", raw, flags=DOTALL | 0)
                transactions = []
                for b in blocks:
                    # extrair DTPOSTED, TRNAMT, NAME (ou MEMO)
                    dt = None
                    amt = None
                    name = ''
                    m = search(r"<DTPOSTED>([0-9T+-:\.]+)", b)
                    if m:
                        dt = m.group(1)
                    m = search(r"<TRNAMT>(-?[0-9.,]+)", b)
                    if m:
                        amt_raw = m.group(1)
                        amt = float(amt_raw.replace(',', ''))
                    m = search(r"<NAME>([^<\n]+)", b)
                    if m:
                        name = m.group(1).strip()
                    if dt or amt is not None:
                        transactions.append({'date': dt, 'description': name, 'amount': amt if amt is not None else 0.0})

                if not transactions:
                    raise e

                df = pd.DataFrame(transactions)
                # Normalizar data: OFX costuma usar YYYYMMDD or YYYYMMDDHHMMSS
                def _parse_ofx_date(s):
                    import pandas as _pd
                    if s is None:
                        return _pd.NaT
                    s2 = s.strip()
                    # pegar apenas a parte numérica inicial
                    import re as _re
                    m = _re.match(r"(\d{4})(\d{2})(\d{2})", s2)
                    if m:
                        return _pd.to_datetime(f"{m.group(1)}-{m.group(2)}-{m.group(3)}", errors='coerce')
                    try:
                        return _pd.to_datetime(s2, errors='coerce')
                    except Exception:
                        return _pd.NaT

                df['date'] = df['date'].apply(_parse_ofx_date)
                return df.sort_values('date').reset_index(drop=True)
            except Exception:
                # re-raise original exception se não for possível o fallback
                raise

    transactions = []
    # ofx.account.statement.transactions
    for account in getattr(ofx, 'accounts', []) or []:
        stmt = getattr(account, 'statement', None)
        if not stmt:
            continue
        for t in getattr(stmt, 'transactions', []) or []:
            date = getattr(t, 'date', None)
            amount = getattr(t, 'amount', None)
            payee = getattr(t, 'payee', '') or getattr(t, 'memo', '') or ''
            transactions.append({
                'date': date,
                'description': str(payee),
                'amount': float(amount) if amount is not None else 0.0,
            })

    if not transactions:
        return pd.DataFrame()

    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df.sort_values('date').reset_index(drop=True)

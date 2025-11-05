import os
import requests
import pandas as pd

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def get_stock_data(symbol: str = "IBM", interval: str = "60min", outputsize: str = "compact") -> pd.DataFrame:
    """Busca dados intraday de uma ação via Alpha Vantage e retorna DataFrame.

    Retorna colunas: open, high, low, close, volume com índice datetime.
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise EnvironmentError("ALPHA_VANTAGE_API_KEY não definida")

    url = (
        f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}"
        f"&interval={interval}&outputsize={outputsize}&apikey={ALPHA_VANTAGE_API_KEY}"
    )
    r = requests.get(url, timeout=30)
    data = r.json()
    key = f"Time Series ({interval})"
    if key not in data:
        # Em caso de erro, retornar DataFrame vazio e registrar a mensagem
        print(f"Erro ao obter dados: {data}")
        return pd.DataFrame()

    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df.columns = ["open", "high", "low", "close", "volume"]
    df = df.sort_index()
    return df

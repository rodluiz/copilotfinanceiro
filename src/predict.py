from statsmodels.tsa.arima.model import ARIMA
import pandas as pd


def arima_forecast(close_prices: pd.Series, steps: int = 5, order=(5, 1, 0)):
    """Ajusta ARIMA e retorna forecast e intervalos de confiança.

    Args:
        close_prices: série temporal de preços de fechamento (index datetime)
        steps: número de passos a prever
        order: tupla (p,d,q)

    Returns:
        forecast (pd.Series), conf_int (pd.DataFrame)
    """
    if close_prices.empty:
        return pd.Series(dtype=float), pd.DataFrame()

    # Ajusta modelo
    model = ARIMA(close_prices, order=order)
    model_fit = model.fit()

    forecast_result = model_fit.get_forecast(steps=steps)
    forecast = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int()
    return forecast, conf_int

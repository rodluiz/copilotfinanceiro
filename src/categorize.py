import re
import pandas as pd

# Regras simples de palavra-chave para categorias
CATEGORY_KEYWORDS = {
    "transporte": ["uber", "lyft", "taxi", "metrô", "onibus", "bus", "uber eats"],
    "alimentacao": ["restaurante", "supermercado", "grocery", "mercado", "padaria", "uber eats", "ifood"],
    "assinatura": ["netflix", "spotify", "prime", "hulu", "subscription", "assinatura"],
    "saude": ["hospital", "farmacia", "drogaria", "clínica"],
    "lazer": ["cinema", "teatro", "viagem", "hotel"],
    "moradia": ["aluguel", "condominio", "energia", "agua", "iptu"],
    "servicos": ["telefone", "internet", "movimento", "cartao"],
}


def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica regras de correspondência de keywords para atribuir categorias.

    Retorna uma cópia do DataFrame com coluna `category`.
    """
    def categorize_description(desc: str) -> str:
        d = desc.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                # padrão simples
                if kw in d:
                    return category
        return "outros"

    out = df.copy()
    out["category"] = out["description"].fillna("").apply(categorize_description)
    return out


def summary_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna soma absoluta de gastos por categoria (considera amount < 0 como gasto)."""
    # Gastos são valores negativos
    df_expenses = df[df["amount"] < 0].copy()
    df_expenses["abs_amount"] = df_expenses["amount"].abs()
    summary = df_expenses.groupby("category")["abs_amount"].sum().sort_values(ascending=False)
    return summary.reset_index().rename(columns={"abs_amount": "total_spent"})

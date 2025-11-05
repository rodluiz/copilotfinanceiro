from collections import Counter
import pandas as pd

from .categorize import summary_by_category
from .llm import generate_financial_summary


def detect_recurring_subscriptions(df: pd.DataFrame, min_occurrences: int = 3) -> list:
    """Detecta descrições que ocorrem repetidamente (possíveis assinaturas)."""
    descs = df["description"].fillna("")
    counts = Counter(descs)
    recurring = [d for d, c in counts.items() if c >= min_occurrences]
    return recurring


def rule_based_savings(df: pd.DataFrame) -> list:
    """Gera sugestões simples baseadas em regras:
    - listar top categorias de gasto
    - identificar assinaturas recorrentes
    - sugerir redução percentual genérica
    """
    suggestions = []
    cat_summary = summary_by_category(df)
    if not cat_summary.empty:
        top = cat_summary.head(3)
        for _, row in top.iterrows():
            cat = row["category"]
            total = row["total_spent"]
            suggestions.append(f"Gasto alto em '{cat}': R${total:.2f}. Considere revisar assinaturas e reduzir 10% nas despesas desse grupo.")

    recurring = detect_recurring_subscriptions(df)
    if recurring:
        suggestions.append(f"Possíveis assinaturas recorrentes detectadas: {', '.join(recurring[:5])}. Revise contratos e cancele o que não utiliza.")

    # Sugerir montar reserva: 10% da renda mensal (se detectarmos entradas positivas)
    income = df[df["amount"] > 0]["amount"].sum()
    if income > 0:
        suggestions.append(f"Renda total detectada no período: R${income:.2f}. Considere poupar 10% da sua renda mensal como meta inicial.")

    return suggestions


def generate_statement_insights(df: pd.DataFrame) -> dict:
    """Retorna um dicionário com resumo, categorias e sugestões. Usa LLM para complemento quando disponível."""
    summary = summary_by_category(df).to_dict(orient="records")
    rules = rule_based_savings(df)

    # Texto resumo para LLM
    text_input = "Resumo das maiores categorias e sugestões:\n"
    for item in summary:
        text_input += f"Categoria: {item['category']}, gasto: R${item['total_spent']:.2f}\n"
    text_input += "Sugestões iniciais:\n"
    for s in rules:
        text_input += f"- {s}\n"

    try:
        llm_text = generate_financial_summary(text_input)
    except Exception:
        llm_text = ""  # fallback

    return {
        "category_summary": summary,
        "rule_suggestions": rules,
        "llm_suggestion": llm_text,
    }

import os
import openai

# Compatibilidade: biblioteca openai pode requerer OPENAI_API_KEY ou variável mais nova
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_financial_summary(text_input: str, model: str = "gpt-3.5-turbo") -> str:
    """Gera um resumo simples a partir de um texto financeiro usando OpenAI ChatCompletion.

    Retorna string vazia se chave não estiver definida para facilitar fallback em regras.
    """
    if not openai.api_key:
        raise EnvironmentError("OPENAI_API_KEY não definida")

    prompt = (
        "Analise o seguinte texto financeiro e forneça um resumo conciso, identifique o sentimento "
        "(positivo/negativo/neutro) e proponha 2-3 ações práticas para reduzir gastos ou aumentar poupança.\n\n"
        + text_input
    )

    try:
        # Utilizando ChatCompletion compatível com openai>=0.27.x; adaptável conforme SDK
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é um analista financeiro experiente e imparcial."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.6,
        )
        # Algumas versões retornam resp.choices[0].message.content ou resp.choices[0].text
        choice = resp.choices[0]
        if hasattr(choice, "message"):
            return choice.message["content"].strip()
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"].strip()
        if "text" in choice:
            return choice["text"].strip()
        return ""
    except Exception as e:
        print(f"Erro na chamada OpenAI: {e}")
        return ""

from flask import Flask, request, jsonify, render_template
from src.ingest import get_stock_data
from src.predict import arima_forecast
from src.llm import generate_financial_summary
from src.bank_ingest import parse_statement_csv
from src.pdf_ingest import parse_statement_pdf
from src.categorize import categorize_transactions
from src.insights import generate_statement_insights

app = Flask(__name__)


@app.route("/fetch")
def fetch():
    symbol = request.args.get("symbol", "IBM")
    df = get_stock_data(symbol=symbol, interval="60min", outputsize="compact")
    if df.empty:
        return jsonify({"error": "Dados não disponíveis"}), 400
    # Retornar os últimos 20 registros resumidos
    last = df.tail(20)[["close"]]
    return jsonify({"symbol": symbol, "last_close": last["close"].round(2).to_dict()})


@app.route("/analysis")
def analysis():
    symbol = request.args.get("symbol", "IBM")
    steps = int(request.args.get("steps", 5))

    df = get_stock_data(symbol=symbol, interval="60min", outputsize="compact")
    if df.empty:
        return jsonify({"error": "Dados não disponíveis"}), 400

    close = df["close"].dropna()
    # Para estabilidade, usamos apenas os últimos 200 pontos se existirem
    series = close[-200:]

    forecast, conf_int = arima_forecast(series, steps=steps)

    # Construir um texto simples para o LLM
    text_input = (
        f"Símbolo: {symbol}. Último preço: {series.iloc[-1]:.2f}. "
        f"Média (últimos 20): {series[-20:].mean():.2f}. Última tendência (últimos 5): {series[-5:].pct_change().mean():.4f}"
    )

    llm_summary = generate_financial_summary(text_input)

    return jsonify({
        "symbol": symbol,
        "forecast": forecast.round(2).to_dict(),
        "conf_int": conf_int.round(2).to_dict(),
        "llm_summary": llm_summary,
    })


@app.route("/statement", methods=["POST"])
def statement():
    """Recebe um CSV ou PDF de extrato bancário via upload multipart/form-data (campo 'file').
    Retorna JSON ou renderiza HTML quando a requisição aceita HTML (interface web).
    """
    if "file" not in request.files:
        return jsonify({"error": "Envie o arquivo CSV/PDF no campo 'file'"}), 400

    f = request.files["file"]
    # Ler conteúdo em memória e parsear conforme extensão
    filename = (f.filename or "").lower()
    try:
        if filename.endswith(".pdf"):
            df = parse_statement_pdf(f)
        elif filename.endswith(".ofx") or filename.endswith(".qfx"):
            # OFX/QFX
            from src.ofx_ingest import parse_statement_ofx

            df = parse_statement_ofx(f)
        elif filename.endswith(".qif"):
            from src.qif_ingest import parse_statement_qif

            df = parse_statement_qif(f)
        else:
            # tratar como CSV por padrão
            df = parse_statement_csv(f)
    except Exception as e:
        return jsonify({"error": f"Falha ao parsear arquivo: {e}"}), 400

    if df.empty:
        return jsonify({"error": "Nenhuma transação detectada no arquivo."}), 400

    cat_df = categorize_transactions(df)
    insights = generate_statement_insights(cat_df)

    # Breve resumo: total gasto e top categorias
    total_spent = float(cat_df[cat_df["amount"] < 0]["amount"].abs().sum())
    income = float(cat_df[cat_df["amount"] > 0]["amount"].sum())

    result = {
        "total_spent": round(total_spent, 2),
        "income": round(income, 2),
        "category_summary": insights["category_summary"],
        "rule_suggestions": insights["rule_suggestions"],
        "llm_suggestion": insights.get("llm_suggestion", ""),
    }

    # Se o cliente aceita HTML (ex.: navegador), renderizar template
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    if best == "text/html" and request.accept_mimetypes["text/html"] >= request.accept_mimetypes["application/json"]:
        return render_template(
            "statement_result.html",
            total_spent=result["total_spent"],
            income=result["income"],
            category_summary=result["category_summary"],
            rule_suggestions=result["rule_suggestions"],
            llm_suggestion=result["llm_suggestion"],
        )

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

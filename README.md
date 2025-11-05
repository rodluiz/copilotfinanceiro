# CoPiloto Financeiro — PoC

Prova de Conceito (PoC) para o artigo "Deep Dive: Construindo um Co-Piloto Financeiro com IA Generativa".

Objetivo: demonstrar um pipeline simples que busca dados de mercado (Alpha Vantage), gera previsões (ARIMA) e produz um resumo em linguagem natural usando um LLM (OpenAI).

Pré-requisitos

- Python 3.10+
- Chaves de API definidas nas variáveis de ambiente:
  - ALPHA_VANTAGE_API_KEY
  - OPENAI_API_KEY

Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Como executar (exemplo)

```bash
export ALPHA_VANTAGE_API_KEY=seu_key
export OPENAI_API_KEY=seu_key
python app.py
```

Endpoints

- GET /fetch?symbol=IBM  — busca séries de preço via AlphaVantage
- GET /analysis?symbol=IBM&steps=5 — retorna forecast ARIMA e resumo gerado pelo LLM
 - POST /statement — faz upload de um CSV de extrato bancário (campo form 'file') e retorna categorização e sugestões de economia

# CoPiloto Financeiro — PoC

Prova de Conceito (PoC) para o artigo "Deep Dive: Construindo um Co-Piloto Financeiro com IA Generativa".

Resumo do estado atual (5 de novembro de 2025)

- Pipeline PoC com endpoints e UI para ingest de dados, análise preditiva e análise de extratos pessoais.
- Implementações principais:
  - Fetch de séries temporais via Alpha Vantage (`src/ingest.py`).
  - Wrapper LLM (OpenAI) em `src/llm.py` (ChatCompletion).
  - Previsão ARIMA (`src/predict.py`).
  - Parser de extratos:
    - CSV (`src/bank_ingest.py`)
    - PDF heurístico via `pdfplumber` (`src/pdf_ingest.py`)
    - OFX/QFX via `ofxparse` com fallback regex (`src/ofx_ingest.py`)
    - QIF via parser simples (`src/qif_ingest.py`)
  - Categorização por regras (`src/categorize.py`) e geração de insights (`src/insights.py`).
  - API Flask com endpoints JSON e UI (templates + CSS).

Requisitos

- Python 3.10+
- Variáveis de ambiente (opcionais para funcionalidades externas):
  - `ALPHA_VANTAGE_API_KEY` (opcional — para dados de mercado)
  - `OPENAI_API_KEY` (opcional — para enriquecimento LLM)

Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Como executar

```bash
# (opcional) export ALPHA_VANTAGE_API_KEY=seu_key
# (opcional) export OPENAI_API_KEY=seu_key
python3 app.py

# Abra http://127.0.0.1:5000/ para usar a UI
```

Endpoints principais

- `GET /fetch?symbol=SYMBOL` — busca séries via Alpha Vantage
- `GET /analysis?symbol=SYMBOL&steps=N` — previsão ARIMA + resumo LLM
- `POST /statement` — upload de extrato (CSV, PDF, OFX, QIF) e retorno de resumo/categorias/sugestões (suporta render HTML para navegador)

Testes e exemplos

- CSV exemplo: `examples/sample_statement.csv`
- Scripts de teste (usam Flask test client):
  - `tests/run_statement_test.py` — gera PDF de exemplo e envia CSV+PDF
  - `tests/run_ofx_qif_test.py` — envia OFX e QIF de exemplo

Uso rápido com curl

```bash
curl -F "file=@examples/sample_statement.csv" http://127.0.0.1:5000/statement
```

Decisões arquiteturais e segurança

- PoC não é pronto para produção: falta autenticação, armazenamento seguro e controle de acesso.
- LLM (OpenAI) é um complemento — o sistema tem fallback rule-based quando `OPENAI_API_KEY` não está presente.
- PDFs e OFX/QIF são processados com heurísticas; layouts variados podem exigir ajustes específicos.

Limitações e próximos passos

1. Melhorar a robustez do parsing de PDFs/OFX via templates por banco.
2. Adicionar mapeamento manual de colunas e histórico de uploads (persistência criptografada).
3. Escrever testes unitários mais completos e montar CI com coverage.
4. Tornar a categorização mais precisa (modelo ML ou LLM supervisionado com verificação humana).

Referência

Artigo: https://rodluiz.com.br/deep-dive-construindo-um-co-piloto-financeiro-com-ia-generativa-da-api-a-analise-preditiva-e-os-riscos-no-caminho/

--
Status: PoC implementado parcialmente — API + UI + parsers para CSV/PDF/QIF/OFX (com fallback).

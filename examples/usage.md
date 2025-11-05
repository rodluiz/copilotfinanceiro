# Exemplo de uso

1) Defina variáveis de ambiente:

```bash
export ALPHA_VANTAGE_API_KEY=seu_key
export OPENAI_API_KEY=seu_key
```

2) Inicie o servidor:

```bash
python app.py
```

3) Teste os endpoints:

```bash
curl "http://127.0.0.1:5000/fetch?symbol=IBM"
curl "http://127.0.0.1:5000/analysis?symbol=IBM&steps=5"
```

# Teste de upload de extrato

```bash
curl -F "file=@/caminho/para/extrato.csv" http://127.0.0.1:5000/statement
```

# Envio de PDF

```bash
curl -F "file=@/caminho/para/extrato.pdf" http://127.0.0.1:5000/statement
```

import io
import os
from reportlab.pdfgen import canvas
from flask import Flask

# Import app factory (app object)
from app import app as flask_app


def create_sample_pdf(path):
    c = canvas.Canvas(path)
    c.setFont("Helvetica", 10)
    c.drawString(40, 800, "01/10/2025 Salario 5000.00")
    c.drawString(40, 780, "03/10/2025 Supermercado XYZ -320.45")
    c.drawString(40, 760, "05/10/2025 NETFLIX -29.90")
    c.drawString(40, 740, "10/10/2025 Uber -15.60")
    c.drawString(40, 720, "15/10/2025 Farmacia Saude -45.20")
    c.save()


def post_file(client, filepath, field_name="file"):
    with open(filepath, "rb") as fh:
        data = {field_name: (fh, os.path.basename(filepath))}
        resp = client.post("/statement", data=data, content_type='multipart/form-data', headers={"Accept": "application/json"})
        return resp


if __name__ == "__main__":
    # criar PDF de exemplo
    pdf_path = os.path.join(os.path.dirname(__file__), "sample_statement.pdf")
    create_sample_pdf(pdf_path)

    # criar cliente de teste e enviar CSV e PDF
    client = flask_app.test_client()

    csv_path = os.path.join(os.path.dirname(__file__), "..", "examples", "sample_statement.csv")
    print("Enviando CSV de exemplo:")
    r1 = post_file(client, csv_path)
    print("Status:", r1.status_code)
    print(r1.get_data(as_text=True))

    print("\nEnviando PDF de exemplo:")
    r2 = post_file(client, pdf_path)
    print("Status:", r2.status_code)
    print(r2.get_data(as_text=True))

import os
from app import app as flask_app


def post_file(client, filepath, field_name="file"):
    with open(filepath, "rb") as fh:
        data = {field_name: (fh, os.path.basename(filepath))}
        resp = client.post("/statement", data=data, content_type='multipart/form-data', headers={"Accept": "application/json"})
        return resp


if __name__ == "__main__":
    client = flask_app.test_client()
    base = os.path.join(os.path.dirname(__file__), "..", "examples")

    ofx_path = os.path.join(base, "sample_statement.ofx")
    qif_path = os.path.join(base, "sample_statement.qif")

    print("Enviando OFX de exemplo:")
    r1 = post_file(client, ofx_path)
    print("Status:", r1.status_code)
    print(r1.get_data(as_text=True))

    print("\nEnviando QIF de exemplo:")
    r2 = post_file(client, qif_path)
    print("Status:", r2.status_code)
    print(r2.get_data(as_text=True))

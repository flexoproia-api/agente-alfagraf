from flask import Flask, request, jsonify
from gerar_orcamento import gerar_pdf
import os, tempfile, requests

app = Flask(__name__)

PHONE_NUMBER_ID = "959137950626170"

@app.route("/gerar-orcamento", methods=["POST"])
def gerar():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"erro": "Token não informado"}), 401

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        caminho = tmp.name

    try:
        # 1 — Gerar o PDF
        gerar_pdf(dados, caminho)

        # 2 — Upload para os servidores da Meta
        upload_url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/media"
        with open(caminho, 'rb') as f:
            upload_resp = requests.post(
                upload_url,
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("Orcamento_Alfagraf.pdf", f, "application/pdf")},
                data={"messaging_product": "whatsapp"}
            )

        if upload_resp.status_code != 200:
            return jsonify({"erro": "Falha no upload para Meta", "detalhe": upload_resp.text}), 500

        media_id = upload_resp.json().get("id")
        return jsonify({"sucesso": True, "media_id": media_id})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        if os.path.exists(caminho):
            os.unlink(caminho)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
```

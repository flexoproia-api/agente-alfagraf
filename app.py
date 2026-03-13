from flask import Flask, request, jsonify
from gerar_orcamento import gerar_pdf
import base64, os, tempfile

app = Flask(__name__)

@app.route("/gerar-orcamento", methods=["POST"])
def gerar():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        caminho = tmp.name

    try:
        gerar_pdf(dados, caminho)
        with open(caminho, 'rb') as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
        return jsonify({"pdf_base64": pdf_base64, "sucesso": True})
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

from flask import Flask, request, jsonify, send_file
from gerar_orcamento import gerar_pdf
import os, tempfile, uuid

app = Flask(__name__)

PDF_DIR = "/tmp/pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

@app.route("/gerar-orcamento", methods=["POST"])
def gerar():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados invalidos"}), 400

    nome = f"orcamento_{uuid.uuid4().hex[:8]}.pdf"
    caminho = os.path.join(PDF_DIR, nome)

    try:
        gerar_pdf(dados, caminho)
        link = f"https://agente-alfagraf.onrender.com/pdf/{nome}"
        return jsonify({"sucesso": True, "link": link})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/pdf/<nome>", methods=["GET"])
def servir_pdf(nome):
    caminho = os.path.join(PDF_DIR, nome)
    if not os.path.exists(caminho):
        return jsonify({"erro": "Arquivo nao encontrado"}), 404
    return send_file(caminho, mimetype="application/pdf",
                     as_attachment=False,
                     download_name="Orcamento_Alfagraf.pdf")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

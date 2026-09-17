from flask import Blueprint, jsonify, request
from backend.processadores.importador_excel import ImportadorExcelService
from backend.services.auth_service import require_auth

importacao_bp = Blueprint("importacao", __name__)

@importacao_bp.route("/api/importar-excel", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def importar_excel():
    if 'file' not in request.files and 'arquivo' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    arquivo = request.files.get('file') or request.files.get('arquivo')
    motivo_afastamento = request.form.get('motivo_afastamento') or "Retirado da escala via importação de planilha"

    filename = (arquivo.filename or "").strip()
    if not filename:
        return jsonify({"error": "Nome do arquivo inválido"}), 400

    try:
        bytes_data = arquivo.read()
        arquivo.seek(0)
        resultado, status_code = ImportadorExcelService.processar(
            bytes_data=bytes_data,
            filename=filename,
            motivo_afastamento=motivo_afastamento
        )
        return jsonify(resultado), status_code
    except Exception as e:
        return jsonify({"error": f"Erro inesperado no processamento: {str(e)}"}), 500

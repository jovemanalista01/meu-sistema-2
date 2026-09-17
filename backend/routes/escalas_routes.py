from flask import Blueprint, jsonify, request, send_file
import pandas as pd
import io
from backend.database.db_factory import get_repository
from backend.services.auth_service import require_auth
from backend.geradores.exportador_dados import ExportadorDadosService

escalas_bp = Blueprint("escalas", __name__)

@escalas_bp.route("/api/escalas", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_escalas():
    repo = get_repository()
    escalas = repo.listar_escalas()
    return jsonify(escalas), 200

@escalas_bp.route("/api/escalas", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def criar_escala():
    dados = request.get_json() or {}
    motorista_id = dados.get("motorista_id")
    frota_id = dados.get("frota_id")
    rota_id = dados.get("rota_id")
    data_saida = dados.get("data_saida")
    ajudante_id = dados.get("ajudante_id")

    if not motorista_id or not frota_id or not rota_id or not data_saida:
        return jsonify({"error": "Campos 'motorista_id', 'frota_id', 'rota_id' e 'data_saida' são obrigatórios"}), 400

    try:
        repo = get_repository()
        novo_id = repo.criar_escala(
            motorista_id=motorista_id,
            frota_id=frota_id,
            rota_id=rota_id,
            data_saida=data_saida,
            ajudante_id=ajudante_id
        )
        return jsonify({"id": novo_id, "message": "Escala criada com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao criar escala: {str(e)}"}), 400

@escalas_bp.route("/api/escalas/<int:escala_id>/chegada", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def registrar_chegada(escala_id):
    dados = request.get_json() or {}
    data_chegada = dados.get("data_chegada")

    if not data_chegada:
        return jsonify({"error": "Campo 'data_chegada' é obrigatório"}), 400

    try:
        repo = get_repository()
        repo.registrar_chegada(escala_id, data_chegada)
        return jsonify({"escala_id": escala_id, "data_chegada": data_chegada, "message": "Chegada registrada com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar chegada: {str(e)}"}), 400

@escalas_bp.route("/api/escalas/<int:escala_id>/trocar-motorista", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def trocar_motorista(escala_id):
    dados = request.get_json() or {}
    novo_motorista_id = dados.get("novo_motorista_id")
    data_troca = dados.get("data_troca")

    if not novo_motorista_id or not data_troca:
        return jsonify({"error": "Campos 'novo_motorista_id' e 'data_troca' são obrigatórios"}), 400

    try:
        repo = get_repository()
        nova_escala_id = repo.trocar_motorista(escala_id, novo_motorista_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Motorista substituído com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar motorista: {str(e)}"}), 400

@escalas_bp.route("/api/escalas/<int:escala_id>/trocar-ajudante", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def trocar_ajudante(escala_id):
    dados = request.get_json() or {}
    novo_ajudante_id = dados.get("novo_ajudante_id")
    data_troca = dados.get("data_troca")

    if not data_troca:
        return jsonify({"error": "Campo 'data_troca' é obrigatório"}), 400

    try:
        repo = get_repository()
        nova_escala_id = repo.trocar_ajudante(escala_id, novo_ajudante_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Ajudante substituído com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar ajudante: {str(e)}"}), 400

@escalas_bp.route("/api/escalas/<int:escala_id>/trocar-frota", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def trocar_frota(escala_id):
    dados = request.get_json() or {}
    nova_frota_id = dados.get("nova_frota_id")
    data_troca = dados.get("data_troca")

    if not nova_frota_id or not data_troca:
        return jsonify({"error": "Campos 'nova_frota_id' e 'data_troca' são obrigatórios"}), 400

    try:
        repo = get_repository()
        nova_escala_id = repo.trocar_frota(escala_id, nova_frota_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Frota substituída com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar frota: {str(e)}"}), 400

@escalas_bp.route("/api/escalas/<int:escala_id>/trocar-rota", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def trocar_rota(escala_id):
    dados = request.get_json() or {}
    nova_rota_id = dados.get("nova_rota_id")
    data_troca = dados.get("data_troca")

    if not nova_rota_id or not data_troca:
        return jsonify({"error": "Campos 'nova_rota_id' e 'data_troca' são obrigatórios"}), 400

    try:
        repo = get_repository()
        nova_escala_id = repo.trocar_rota(escala_id, nova_rota_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Rota substituída com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar rota: {str(e)}"}), 400

@escalas_bp.route("/api/escalas/exportar/excel", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def exportar_escalas_excel():
    repo = get_repository()
    escalas = repo.listar_escalas()
    output = ExportadorDadosService.exportar_escalas_excel(escalas)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="escalas_logiscale.xlsx"
    )

@escalas_bp.route("/api/escalas/exportar/csv", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def exportar_escalas_csv():
    repo = get_repository()
    escalas = repo.listar_escalas()
    output = ExportadorDadosService.exportar_escalas_csv(escalas)
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="escalas_logiscale.csv"
    )

@escalas_bp.route("/api/escalas/importar", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def importar_escalas_legada():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    motivo_afastamento = request.form.get("motivo_afastamento")

    if file.filename == '':
        return jsonify({"error": "Nome do arquivo inválido"}), 400

    try:
        in_memory_file = io.BytesIO(file.read())
        df = pd.read_excel(in_memory_file)
        repo = get_repository()

        linhas_processadas = 0
        for _, row in df.iterrows():
            motorista_id = row.get("motorista_id")
            frota_id = row.get("frota_id")
            rota_id = row.get("rota_id")
            data_saida = row.get("data_saida")
            ajudante_id = row.get("ajudante_id")

            if pd.isna(motorista_id) or pd.isna(frota_id) or pd.isna(rota_id) or pd.isna(data_saida):
                continue

            repo.criar_escala(
                motorista_id=int(motorista_id),
                frota_id=int(frota_id),
                rota_id=int(rota_id),
                data_saida=str(data_saida),
                ajudante_id=int(ajudante_id) if pd.notna(ajudante_id) else None
            )
            linhas_processadas += 1

        return jsonify({
            "message": f"Importação concluída com sucesso! {linhas_processadas} escalas foram processadas.",
            "motivo_afastamento_aplicado": motivo_afastamento
        }), 200

    except Exception as e:
        return jsonify({"error": f"Falha ao processar arquivo: {str(e)}"}), 500

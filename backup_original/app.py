from flask import Flask, jsonify, request, render_template
from database import db_manager
import pandas as pd
import io
import sqlite3
import traceback

app = Flask(__name__)
db_manager._ensure_db()


# --- ROTA DA INTERFACE WEB ---

@app.route("/")
def index():
    """Renderiza a página principal do aplicativo."""
    return render_template("index.html")


# --- APIS DE COLABORADORES ---

@app.route("/api/colaboradores", methods=["GET"])
def api_colaboradores():
    colaboradores = db_manager.listar_colaboradores()
    return jsonify([dict(c) for c in colaboradores]), 200


@app.route("/api/colaboradores", methods=["POST"])
def api_criar_colaborador():
    dados = request.get_json() or {}
    nome = dados.get("nome")
    funcao = dados.get("funcao")

    if not nome or not funcao:
        return jsonify({"error": "Campos 'nome' e 'funcao' são obrigatórios"}), 400

    try:
        novo_id = db_manager.adicionar_colaborador(nome, funcao)
        return jsonify({"id": novo_id, "nome": nome, "funcao": funcao}), 201
    except sqlite3.IntegrityError as e:
        return jsonify({"error": f"Não foi possível cadastrar colaborador: {e}"}), 409


@app.route("/api/colaboradores/<int:colaborador_id>", methods=["PUT", "DELETE"])
def api_editar_ou_excluir_colaborador(colaborador_id):
    if request.method == "DELETE":
        try:
            if not db_manager.excluir_colaborador(colaborador_id):
                return jsonify({"error": "Colaborador não encontrado"}), 404
            return jsonify({"message": "Colaborador excluído com sucesso"}), 200
        except sqlite3.IntegrityError:
            return jsonify({"error": "Colaborador possui escalas ou afastamentos relacionados"}), 409

    dados = request.get_json() or {}
    nome = dados.get("nome")
    funcao = dados.get("funcao")
    status = dados.get("status")
    if not nome or funcao not in ("motorista", "ajudante"):
        return jsonify({"error": "'nome' e uma função válida são obrigatórios"}), 400
    if status is not None and status not in ("disponivel", "em_rota", "afastado", "reserva"):
        return jsonify({"error": "Status inválido"}), 400
    try:
        if not db_manager.atualizar_colaborador(colaborador_id, nome, funcao, status):
            return jsonify({"error": "Colaborador não encontrado"}), 404
        return jsonify({"message": "Colaborador atualizado com sucesso"}), 200
    except sqlite3.IntegrityError as e:
        return jsonify({"error": f"Não foi possível atualizar colaborador: {e}"}), 409


@app.route("/api/colaboradores/disponiveis/<funcao>", methods=["GET"])
def api_colaboradores_disponiveis(funcao):
    if funcao not in ["motorista", "ajudante"]:
        return jsonify({"error": "Função deve ser 'motorista' ou 'ajudante'"}), 400

    disponiveis = db_manager.listar_disponiveis(funcao)
    return jsonify([dict(d) for d in disponiveis]), 200


@app.route("/api/colaboradores/<int:colaborador_id>/historico", methods=["GET"])
def api_historico_colaborador(colaborador_id):
    try:
        dados = db_manager.obter_historico_colaborador(colaborador_id)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


# --- APIS DE FROTA ---

@app.route("/api/frota", methods=["GET"])
def api_frota():
    frota = db_manager.listar_frota()
    return jsonify([dict(f) for f in frota]), 200


@app.route("/api/frota", methods=["POST"])
def api_criar_frota():
    dados = request.get_json() or {}
    numero_frota = dados.get("numero_frota")
    placa = dados.get("placa")

    if not numero_frota or not placa:
        return jsonify({"error": "Campos 'numero_frota' e 'placa' são obrigatórios"}), 400

    try:
        novo_id = db_manager.adicionar_frota(numero_frota, placa)
        return jsonify({"id": novo_id, "numero_frota": numero_frota, "placa": placa}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao adicionar frota: {str(e)}"}), 400


@app.route("/api/frota/<int:frota_id>", methods=["PUT", "DELETE"])
def api_editar_ou_excluir_frota(frota_id):
    if request.method == "DELETE":
        try:
            if not db_manager.excluir_frota(frota_id):
                return jsonify({"error": "Frota não encontrada"}), 404
            return jsonify({"message": "Frota excluída com sucesso"}), 200
        except sqlite3.IntegrityError:
            return jsonify({"error": "Frota possui escalas relacionadas"}), 409

    dados = request.get_json() or {}
    numero_frota = dados.get("numero_frota")
    placa = dados.get("placa")
    if not numero_frota or not placa:
        return jsonify({"error": "'numero_frota' e 'placa' são obrigatórios"}), 400
    try:
        if not db_manager.atualizar_frota(frota_id, numero_frota, placa):
            return jsonify({"error": "Frota não encontrada"}), 404
        return jsonify({"message": "Frota atualizada com sucesso"}), 200
    except sqlite3.IntegrityError as e:
        return jsonify({"error": f"Não foi possível atualizar frota: {e}"}), 409


# --- APIS DE ROTAS ---

@app.route("/api/rotas", methods=["GET"])
def api_rotas():
    rotas = db_manager.listar_rotas()
    return jsonify([dict(r) for r in rotas]), 200


@app.route("/api/rotas", methods=["POST"])
def api_adicionar_rota():
    dados = request.get_json() or {}
    nome_rota = dados.get("nome_rota")
    duracao_media_dias = dados.get("duracao_media_dias")

    if not nome_rota:
        return jsonify({"error": "Campo 'nome_rota' é obrigatório"}), 400

    try:
        duracao_media_dias = int(duracao_media_dias) if duracao_media_dias else None
        novo_id = db_manager.adicionar_rota(nome_rota, duracao_media_dias)
        return jsonify({"id": novo_id, "nome_rota": nome_rota, "duracao_media_dias": duracao_media_dias}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao adicionar rota: {str(e)}"}), 400


@app.route("/api/rotas/<int:rota_id>", methods=["PUT", "DELETE"])
def api_editar_ou_excluir_rota(rota_id):
    if request.method == "DELETE":
        try:
            if not db_manager.excluir_rota(rota_id):
                return jsonify({"error": "Rota não encontrada"}), 404
            return jsonify({"message": "Rota excluída com sucesso"}), 200
        except sqlite3.IntegrityError:
            return jsonify({"error": "Rota possui escalas relacionadas"}), 409

    dados = request.get_json() or {}
    nome_rota = dados.get("nome_rota")
    if not nome_rota:
        return jsonify({"error": "'nome_rota' é obrigatório"}), 400
    try:
        duracao = dados.get("duracao_media_dias")
        duracao = int(duracao) if duracao is not None and duracao != "" else None
        if not db_manager.atualizar_rota(rota_id, nome_rota, duracao):
            return jsonify({"error": "Rota não encontrada"}), 404
        return jsonify({"message": "Rota atualizada com sucesso"}), 200
    except (ValueError, sqlite3.IntegrityError) as e:
        return jsonify({"error": f"Não foi possível atualizar rota: {e}"}), 400


# --- APIS DE ESCALAS ---

@app.route("/api/escalas", methods=["GET"])
def api_escalas():
    escalas = db_manager.listar_escalas()
    return jsonify([dict(e) for e in escalas]), 200


@app.route("/api/escalas", methods=["POST"])
def api_criar_escala():
    dados = request.get_json() or {}

    motorista_id = dados.get("motorista_id")
    frota_id = dados.get("frota_id")
    rota_id = dados.get("rota_id")
    data_saida = dados.get("data_saida")
    ajudante_id = dados.get("ajudante_id")

    if not motorista_id or not frota_id or not rota_id or not data_saida:
        return jsonify({"error": "Campos 'motorista_id', 'frota_id', 'rota_id' e 'data_saida' são obrigatórios"}), 400

    try:
        novo_id = db_manager.criar_escala(
            motorista_id=motorista_id,
            frota_id=frota_id,
            rota_id=rota_id,
            data_saida=data_saida,
            ajudante_id=ajudante_id
        )
        return jsonify({"id": novo_id, "message": "Escala criada com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao criar escala: {str(e)}"}), 400


@app.route("/api/escalas/<int:escala_id>/chegada", methods=["POST"])
def api_registrar_chegada(escala_id):
    dados = request.get_json() or {}
    data_chegada = dados.get("data_chegada")

    if not data_chegada:
        return jsonify({"error": "Campo 'data_chegada' é obrigatório"}), 400

    try:
        db_manager.registrar_chegada(escala_id, data_chegada)
        return jsonify({"escala_id": escala_id, "data_chegada": data_chegada, "message": "Chegada registrada com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar chegada: {str(e)}"}), 400


# --- APIS DE TROCAS E SUBSTITUIÇÃO DE ESCALA ---

@app.route("/api/escalas/<int:escala_id>/trocar-motorista", methods=["POST"])
def api_trocar_motorista(escala_id):
    dados = request.get_json() or {}
    novo_motorista_id = dados.get("novo_motorista_id")
    data_troca = dados.get("data_troca")

    if not novo_motorista_id or not data_troca:
        return jsonify({"error": "Campos 'novo_motorista_id' e 'data_troca' são obrigatórios"}), 400

    try:
        nova_escala_id = db_manager.trocar_motorista(escala_id, novo_motorista_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Motorista substituído com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar motorista: {str(e)}"}), 400


@app.route("/api/escalas/<int:escala_id>/trocar-ajudante", methods=["POST"])
def api_trocar_ajudante(escala_id):
    dados = request.get_json() or {}
    novo_ajudante_id = dados.get("novo_ajudante_id")
    data_troca = dados.get("data_troca")

    if not data_troca:
        return jsonify({"error": "Campo 'data_troca' é obrigatório"}), 400

    try:
        nova_escala_id = db_manager.trocar_ajudante(escala_id, novo_ajudante_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Ajudante substituído com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar ajudante: {str(e)}"}), 400


@app.route("/api/escalas/<int:escala_id>/trocar-frota", methods=["POST"])
def api_trocar_frota(escala_id):
    dados = request.get_json() or {}
    nova_frota_id = dados.get("nova_frota_id")
    data_troca = dados.get("data_troca")

    if not nova_frota_id or not data_troca:
        return jsonify({"error": "Campos 'nova_frota_id' e 'data_troca' são obrigatórios"}), 400

    try:
        nova_escala_id = db_manager.trocar_frota(escala_id, nova_frota_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Frota substituída com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar frota: {str(e)}"}), 400


@app.route("/api/escalas/<int:escala_id>/trocar-rota", methods=["POST"])
def api_trocar_rota(escala_id):
    dados = request.get_json() or {}
    nova_rota_id = dados.get("nova_rota_id")
    data_troca = dados.get("data_troca")

    if not nova_rota_id or not data_troca:
        return jsonify({"error": "Campos 'nova_rota_id' e 'data_troca' são obrigatórios"}), 400

    try:
        nova_escala_id = db_manager.trocar_rota(escala_id, nova_rota_id, data_troca)
        return jsonify({"escala_anterior_id": escala_id, "nova_escala_id": nova_escala_id, "message": "Rota substituída com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao trocar rota: {str(e)}"}), 400


# --- APIS DE AFASTAMENTOS ---

@app.route("/api/afastamentos", methods=["GET"])
def api_afastamentos():
    afastamentos = db_manager.listar_afastamentos_ativos()
    return jsonify([dict(a) for a in afastamentos]), 200


@app.route("/api/afastamentos", methods=["POST"])
def api_registrar_afastamento():
    dados = request.get_json() or {}
    colaborador_id = dados.get("colaborador_id")
    motivo = dados.get("motivo")
    data_inicio = dados.get("data_inicio")
    data_fim_prevista = dados.get("data_fim_prevista")

    MOTIVOS_PERMITIDOS = ["Folga", "Falta", "Licença médica", "Demanda interna"]

    if not colaborador_id or not motivo or not data_inicio:
        return jsonify({"error": "Campos 'colaborador_id', 'motivo' e 'data_inicio' são obrigatórios"}), 400

    if motivo not in MOTIVOS_PERMITIDOS:
        return jsonify({"error": f"Motivo inválido. Opções aceitas: {', '.join(MOTIVOS_PERMITIDOS)}"}), 400

    try:
        novo_id = db_manager.registrar_afastamento(colaborador_id, motivo, data_inicio, data_fim_prevista)
        return jsonify({"id": novo_id, "message": "Afastamento registrado com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar afastamento: {str(e)}"}), 400


@app.route("/api/afastamentos/<int:afastamento_id>/retorno", methods=["POST"])
def api_registrar_retorno(afastamento_id):
    dados = request.get_json() or {}
    colaborador_id = dados.get("colaborador_id")
    data_retorno = dados.get("data_retorno")

    if not colaborador_id or not data_retorno:
        return jsonify({"error": "Campos 'colaborador_id' e 'data_retorno' são obrigatórios"}), 400

    try:
        db_manager.registrar_retorno(afastamento_id, colaborador_id, data_retorno)
        return jsonify({"afastamento_id": afastamento_id, "message": "Retorno registrado com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar retorno: {str(e)}"}), 400


# --- APIS DE AUDITORIA E HISTÓRICO ---

@app.route("/api/historico", methods=["GET"])
def api_historico():
    historico = db_manager.listar_historico()
    return jsonify([dict(h) for h in historico]), 200


# --- APIS DE INDICADORES E PAINEL ---

@app.route("/api/indicadores", methods=["GET"])
def api_indicadores():
    indicadores = db_manager.obter_indicadores()
    return jsonify(indicadores), 200


# --- API DE IMPORTAÇÃO DE PLANILHA EXCEL ---

@app.route("/api/importar-excel", methods=["POST"])
def api_importar_excel():
    if 'file' not in request.files and 'arquivo' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    arquivo = request.files.get('file') or request.files.get('arquivo')
    motivo_afastamento = request.form.get('motivo_afastamento') or "Retirado da escala via importação de planilha"

    filename = (arquivo.filename or "").lower()
    if not filename:
        return jsonify({"error": "Nome do arquivo inválido"}), 400

    try:
        bytes_data = arquivo.read()
        arquivo.seek(0)

        df = None
        erros_leitura = []

        if filename.endswith('.csv'):
            for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(io.BytesIO(bytes_data), encoding=enc, sep=None, engine='python')
                    break
                except Exception as e:
                    erros_leitura.append(str(e))
        else:
            engines_to_try = ['openpyxl', 'xlrd', None] if filename.endswith('.xlsx') else ['xlrd', 'openpyxl', None]
            for engine in engines_to_try:
                try:
                    if engine:
                        df = pd.read_excel(io.BytesIO(bytes_data), engine=engine)
                    else:
                        df = pd.read_excel(io.BytesIO(bytes_data))
                    break
                except Exception as e:
                    erros_leitura.append(f"{engine}: {str(e)}")

            if df is None:
                try:
                    tabelas_html = pd.read_html(io.BytesIO(bytes_data))
                    if tabelas_html:
                        df = tabelas_html[0]
                except Exception as e:
                    erros_leitura.append(f"html: {e}")

            if df is None:
                for enc in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(io.BytesIO(bytes_data), encoding=enc, sep=None, engine='python')
                        break
                    except Exception as e:
                        erros_leitura.append(f"csv fallback ({enc}): {e}")

        if df is None:
            return jsonify({"error": f"Não foi possível abrir o arquivo. Detalhes: {'; '.join(erros_leitura)}"}), 400

        # ===== DEBUG: mostrar colunas brutas do arquivo =====
        print("=" * 60)
        print(f"[IMPORT] ARQUIVO: {arquivo.filename}")
        print(f"[IMPORT] COLUNAS BRUTAS: {list(df.columns)}")
        print(f"[IMPORT] TOTAL DE LINHAS: {len(df)}")
        print(f"[IMPORT] PRIMEIRAS 3 LINHAS:")
        print(df.head(3).to_string())
        print("=" * 60)

        # Normaliza nomes de colunas do DataFrame
        colunas_normalizadas = {}
        for col in df.columns:
            col_clean = str(col).strip().lower()
            if 'motorista' in col_clean:
                colunas_normalizadas['motorista'] = col
            elif any(k in col_clean for k in ['frota', 'veiculo', 'veículo', 'placa']):
                colunas_normalizadas['frota'] = col
            elif any(k in col_clean for k in ['descrição', 'descricao', 'desc', 'nome_rota', 'nome da rota', 'nome rota']):
                colunas_normalizadas['rota'] = col
            elif 'rota' in col_clean and not any(nr in col_clean for nr in ['nr', 'numero', 'número', 'id']):
                if 'rota' not in colunas_normalizadas:
                    colunas_normalizadas['rota'] = col
            elif any(k in col_clean for k in ['nr', 'numero', 'número']) and 'rota' in col_clean:
                colunas_normalizadas['nr_rota'] = col
            elif 'ajudante' in col_clean:
                colunas_normalizadas['ajudante'] = col
            elif any(k in col_clean for k in ['saida', 'saída', 'data']):
                if 'data_saida' not in colunas_normalizadas or 'saida' in col_clean or 'saída' in col_clean:
                    colunas_normalizadas['data_saida'] = col

        if 'rota' not in colunas_normalizadas and 'nr_rota' in colunas_normalizadas:
            colunas_normalizadas['rota'] = colunas_normalizadas['nr_rota']

        # ===== DEBUG: mostrar mapeamento de colunas =====
        print(f"[IMPORT] COLUNAS NORMALIZADAS: {colunas_normalizadas}")

        if 'motorista' not in colunas_normalizadas or 'frota' not in colunas_normalizadas or 'rota' not in colunas_normalizadas:
            print(f"[IMPORT] ERRO: Colunas obrigatórias não encontradas!")
            print(f"[IMPORT] Procurando: motorista, frota, rota")
            print(f"[IMPORT] Encontrados: {list(colunas_normalizadas.keys())}")
            return jsonify({
                "error": "Colunas obrigatórias ('Motorista', 'Veículo' e 'Descrição'/'Rota') não foram encontradas na planilha.",
                "colunas_encontradas_no_arquivo": [str(c) for c in df.columns],
                "colunas_detectadas": colunas_normalizadas,
                "dica": "Renomeie as colunas da planilha para conter: 'Motorista', 'Veículo' ou 'Frota', e 'Descrição' ou 'Rota'"
            }), 400

        lote_id = db_manager.criar_lote_importacao(arquivo.filename)

        resultados = []
        rodape_processado = []
        afastamentos_gerados = 0
        escalas_criadas = 0
        linhas_rodape = 0
        linhas_vazias = 0
        erros = 0

        for index, row in df.iterrows():
            raw_motorista = row.get(colunas_normalizadas['motorista'])
            raw_frota = row.get(colunas_normalizadas['frota'])
            raw_rota = row.get(colunas_normalizadas['rota'])

            # Linha sem motorista/frota/rota: é separador em branco ou texto de rodapé
            if pd.isna(raw_motorista) and pd.isna(raw_frota) and pd.isna(raw_rota):
                primeira_coluna = row.iloc[0]
                if pd.notna(primeira_coluna) and str(primeira_coluna).strip():
                    linhas_rodape += 1
                    res_rodape = db_manager.processar_linha_rodape(str(primeira_coluna), lote_id=lote_id)
                    rodape_processado.append(res_rodape)
                else:
                    linhas_vazias += 1
                continue

            raw_ajudante = row.get(colunas_normalizadas['ajudante']) if 'ajudante' in colunas_normalizadas else None
            raw_data = row.get(colunas_normalizadas.get('data_saida')) if 'data_saida' in colunas_normalizadas else None

            # Normalização de datas
            data_formatada = None
            if pd.notna(raw_data) and raw_data is not None:
                val_str = str(raw_data).strip()
                if ' ' in val_str:
                    val_str = val_str.split(' ')[0]
                if '/' in val_str:
                    partes = val_str.split('/')
                    if len(partes) == 3:
                        if len(partes[2]) == 4:
                            data_formatada = f"{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
                        elif len(partes[0]) == 4:
                            data_formatada = f"{partes[0]}-{partes[1].zfill(2)}-{partes[2].zfill(2)}"
                else:
                    data_formatada = val_str

            dados_linha = {
                "motorista": str(raw_motorista).strip() if pd.notna(raw_motorista) else None,
                "frota": str(raw_frota).strip() if pd.notna(raw_frota) else None,
                "rota": str(raw_rota).strip() if pd.notna(raw_rota) else None,
                "ajudante": str(raw_ajudante).strip() if pd.notna(raw_ajudante) else None,
                "data_saida": data_formatada
            }

            # ===== DEBUG POR LINHA =====
            print(f"[IMPORT] LINHA {index + 2}: {dados_linha}")

            # ===== TRY/EXCEPT POR LINHA =====
            try:
                res = db_manager.processar_linha_importacao(
                    dados_linha,
                    motivo_afastamento_padrao=motivo_afastamento
                )

                # ===== DEBUG RESULTADO =====
                print(f"[IMPORT] RESULTADO LINHA {index + 2}: {res}")

                if res.get("status") == "sucesso":
                    escalas_criadas += 1
                    if res.get("afastamento_gerado"):
                        afastamentos_gerados += 1
                else:
                    erros += 1

                resultados.append(res)

            except Exception as e_line:
                erros += 1
                resultados.append({
                    "status": "erro",
                    "motivo": f"Exceção na linha {index + 2}: {str(e_line)}",
                    "dados": dados_linha
                })
                print(f"[IMPORT] ERRO LINHA {index + 2}: {e_line}")
                traceback.print_exc()
            # ================================

        # ===== DEBUG RESUMO FINAL =====
        print("=" * 60)
        print(f"[IMPORT] RESUMO DA IMPORTAÇÃO:")
        print(f"  Total de linhas: {len(df)}")
        print(f"  Escalas criadas: {escalas_criadas}")
        print(f"  Afastamentos gerados: {afastamentos_gerados}")
        print(f"  Linhas rodapé: {linhas_rodape}")
        print(f"  Linhas vazias: {linhas_vazias}")
        print(f"  Erros: {erros}")
        print("=" * 60)

        return jsonify({
            "message": "Importação concluída",
            "lote_id": lote_id,
            "total_linhas": len(df),
            "escalas_criadas": escalas_criadas,
            "afastamentos_gerados": afastamentos_gerados,
            "linhas_rodape_processadas": linhas_rodape,
            "linhas_vazias": linhas_vazias,
            "erros": erros,
            "detalhes": resultados,
            "rodape": rodape_processado
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": f"Falha ao processar arquivo: {str(e)}",
            "tipo": type(e).__name__
        }), 500


@app.route("/api/lotes-importacao", methods=["GET"])
def api_lotes_importacao():
    lotes = db_manager.listar_lotes_importacao()
    return jsonify([dict(l) for l in lotes]), 200


@app.route("/api/escalas/importar", methods=["POST"])
def api_importar_escalas_excel():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    motivo_afastamento = request.form.get("motivo_afastamento")

    if file.filename == '':
        return jsonify({"error": "Nome do arquivo inválido"}), 400

    try:
        in_memory_file = io.BytesIO(file.read())
        df = pd.read_excel(in_memory_file)

        linhas_processadas = 0
        for _, row in df.iterrows():
            motorista_id = row.get("motorista_id")
            frota_id = row.get("frota_id")
            rota_id = row.get("rota_id")
            data_saida = row.get("data_saida")
            ajudante_id = row.get("ajudante_id")

            if pd.isna(motorista_id) or pd.isna(frota_id) or pd.isna(rota_id) or pd.isna(data_saida):
                continue

            db_manager.criar_escala(
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


@app.route("/api/colaboradores/reserva", methods=["GET"])
def api_colaboradores_reserva():
    """Lista todos os colaboradores com status 'reserva'."""
    reservas = db_manager.listar_colaboradores_reserva()
    return jsonify([dict(c) for c in reservas]), 200


@app.route("/api/colaboradores/<int:colaborador_id>/remover-reserva", methods=["POST"])
def api_remover_reserva(colaborador_id):
    """Remove um colaborador da reserva."""
    try:
        db_manager.remover_reserva(colaborador_id)
        return jsonify({"message": "Colaborador disponibilizado com sucesso"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Erro ao remover reserva: {str(e)}"}), 400


@app.route("/api/frotas/status", methods=["GET"])
def api_frotas_status():
    """Retorna todas as frotas com status de uso."""
    frotas = db_manager.listar_frotas_com_status()
    return jsonify(frotas), 200


@app.route("/api/frotas/disponiveis", methods=["GET"])
def api_frotas_disponiveis():
    """Retorna apenas as frotas livres."""
    todas = db_manager.listar_frotas_com_status()
    disponiveis = [f for f in todas if f["status_frota"] == "livre"]
    return jsonify(disponiveis), 200


@app.route("/api/frotas/<int:frota_id>/historico", methods=["GET"])
def api_historico_frota(frota_id):
    """Retorna o histórico de uma frota com filtro opcional de data."""
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    resultado = db_manager.obter_historico_frota(
        frota_id=frota_id,
        data_inicio=data_inicio,
        data_fim=data_fim
    )

    if resultado is None:
        return jsonify({"erro": "Frota não encontrada"}), 404

    return jsonify(resultado), 200


# INICIALIZAÇÃO DO SERVIDOR
if __name__ == "__main__":
    # debug=True aqui é só para quando você roda "python app.py" direto
    # durante o desenvolvimento. Para o executável final, use run.py.
    app.run(debug=True, port=5000)
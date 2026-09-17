from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from backend.database.repository_interface import DataRepository
from backend.firebase.firebase_admin_client import get_firestore_client

logger = logging.getLogger(__name__)

class FirestoreRepository(DataRepository):
    """Implementação do repositório utilizando Google Cloud Firestore."""

    def __init__(self):
        self.db = get_firestore_client()
        if self.db is None:
            raise RuntimeError(
                "Não foi possível conectar ao Firestore. Verifique se o arquivo "
                "de credenciais do Firebase está configurado em config/firebase_credentials.json."
            )

    def _obter_proximo_id(self, colecao: str) -> int:
        """Gera um ID numérico sequencial para a coleção no Firestore."""
        contador_ref = self.db.collection("_contadores").document(colecao)
        contador_doc = contador_ref.get()
        if not contador_doc.exists:
            # Conta documentos existentes na coleção para inicializar
            docs = list(self.db.collection(colecao).stream())
            novo_id = len(docs) + 1
            contador_ref.set({"ultimo_id": novo_id})
            return novo_id
        else:
            novo_id = contador_doc.to_dict().get("ultimo_id", 0) + 1
            contador_ref.update({"ultimo_id": novo_id})
            return novo_id

    # --- COLABORADORES ---
    def listar_colaboradores(self) -> List[Dict[str, Any]]:
        docs = self.db.collection("colaboradores").order_by("nome").stream()
        return [dict(d.to_dict(), id=int(d.id) if d.id.isdigit() else d.id) for d in docs]

    def adicionar_colaborador(self, nome: str, funcao: str, status: str = "disponivel") -> int:
        novo_id = self._obter_proximo_id("colaboradores")
        doc_data = {
            "id": novo_id,
            "nome": nome.strip(),
            "funcao": funcao,
            "status": status,
            "data_cadastro": datetime.now().isoformat()
        }
        self.db.collection("colaboradores").document(str(novo_id)).set(doc_data)
        return novo_id

    def atualizar_colaborador(self, colaborador_id: int, nome: str, funcao: str, status: Optional[str] = None) -> bool:
        doc_ref = self.db.collection("colaboradores").document(str(colaborador_id))
        if not doc_ref.get().exists:
            return False
        update_data = {"nome": nome.strip(), "funcao": funcao}
        if status is not None:
            update_data["status"] = status
        doc_ref.update(update_data)
        return True

    def excluir_colaborador(self, colaborador_id: int) -> bool:
        # Checa se há escalas usando o colaborador
        escalas_mot = list(self.db.collection("escalas").where("motorista_id", "==", colaborador_id).limit(1).stream())
        escalas_ajud = list(self.db.collection("escalas").where("ajudante_id", "==", colaborador_id).limit(1).stream())
        if escalas_mot or escalas_ajud:
            raise ValueError("Colaborador possui escalas relacionadas.")

        doc_ref = self.db.collection("colaboradores").document(str(colaborador_id))
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    def listar_disponiveis(self, funcao: str) -> List[Dict[str, Any]]:
        docs = self.db.collection("colaboradores") \
            .where("status", "==", "disponivel") \
            .where("funcao", "==", funcao) \
            .order_by("nome").stream()
        return [dict(d.to_dict(), id=int(d.id) if d.id.isdigit() else d.id) for d in docs]

    def listar_colaboradores_reserva(self) -> List[Dict[str, Any]]:
        docs = self.db.collection("colaboradores") \
            .where("status", "==", "reserva") \
            .order_by("nome").stream()
        return [dict(d.to_dict(), id=int(d.id) if d.id.isdigit() else d.id) for d in docs]

    def remover_reserva(self, colaborador_id: int) -> int:
        doc_ref = self.db.collection("colaboradores").document(str(colaborador_id))
        doc = doc_ref.get()
        if not doc.exists or doc.to_dict().get("status") != "reserva":
            raise ValueError("Colaborador não encontrado ou não está em reserva")
        doc_ref.update({"status": "disponivel"})
        return 1

    def obter_historico_colaborador(self, colaborador_id: int) -> Dict[str, Any]:
        colab_doc = self.db.collection("colaboradores").document(str(colaborador_id)).get()
        if not colab_doc.exists:
            raise ValueError("Colaborador não encontrado")

        colab = dict(colab_doc.to_dict(), id=colaborador_id)

        # Buscar escalas
        escalas = []
        all_escalas = self.db.collection("escalas").order_by("id", direction="DESCENDING").stream()
        for d in all_escalas:
            e = d.to_dict()
            if e.get("motorista_id") == colaborador_id or e.get("ajudante_id") == colaborador_id:
                # Obter nomes de rota e frota
                rota_doc = self.db.collection("rotas").document(str(e.get("rota_id"))).get()
                frota_doc = self.db.collection("frota").document(str(e.get("frota_id"))).get()
                e["nome_rota"] = rota_doc.to_dict().get("nome_rota") if rota_doc.exists else "-"
                e["numero_frota"] = frota_doc.to_dict().get("numero_frota") if frota_doc.exists else "-"
                e["placa"] = frota_doc.to_dict().get("placa") if frota_doc.exists else "-"
                e["papel_exercido"] = "Motorista" if e.get("motorista_id") == colaborador_id else "Ajudante"
                escalas.append(e)

        # Buscar afastamentos
        afastamentos_docs = self.db.collection("afastamentos") \
            .where("colaborador_id", "==", colaborador_id) \
            .order_by("id", direction="DESCENDING").stream()
        afastamentos = [d.to_dict() for d in afastamentos_docs]

        return {
            "colaborador": colab,
            "total_viagens": len(escalas),
            "total_afastamentos": len(afastamentos),
            "escalas": escalas,
            "afastamentos": afastamentos
        }

    # --- FROTA ---
    def listar_frota(self) -> List[Dict[str, Any]]:
        docs = self.db.collection("frota").order_by("numero_frota").stream()
        return [dict(d.to_dict(), id=int(d.id) if d.id.isdigit() else d.id) for d in docs]

    def adicionar_frota(self, numero_frota: str, placa: str) -> int:
        novo_id = self._obter_proximo_id("frota")
        doc_data = {
            "id": novo_id,
            "numero_frota": str(numero_frota).strip(),
            "placa": str(placa).strip().upper()
        }
        self.db.collection("frota").document(str(novo_id)).set(doc_data)
        return novo_id

    def atualizar_frota(self, frota_id: int, numero_frota: str, placa: str) -> bool:
        doc_ref = self.db.collection("frota").document(str(frota_id))
        if not doc_ref.get().exists:
            return False
        doc_ref.update({
            "numero_frota": str(numero_frota).strip(),
            "placa": str(placa).strip().upper()
        })
        return True

    def excluir_frota(self, frota_id: int) -> bool:
        escalas = list(self.db.collection("escalas").where("frota_id", "==", frota_id).limit(1).stream())
        if escalas:
            raise ValueError("Frota possui escalas relacionadas.")
        doc_ref = self.db.collection("frota").document(str(frota_id))
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    def listar_frotas_com_status(self) -> List[Dict[str, Any]]:
        frotas = self.listar_frota()
        escalas_ativas = list(self.db.collection("escalas").where("status", "==", "em_rota").stream())
        ativas_por_frota = {e.to_dict().get("frota_id"): e.to_dict() for e in escalas_ativas}

        resultado = []
        for f in frotas:
            fid = f["id"]
            if fid in ativas_por_frota:
                escala = ativas_por_frota[fid]
                mot_doc = self.db.collection("colaboradores").document(str(escala.get("motorista_id"))).get()
                rota_doc = self.db.collection("rotas").document(str(escala.get("rota_id"))).get()
                resultado.append({
                    "id": fid,
                    "numero_frota": f["numero_frota"],
                    "placa": f["placa"],
                    "status_frota": "em_uso",
                    "escala_ativa_id": escala.get("id"),
                    "motorista_atual": mot_doc.to_dict().get("nome") if mot_doc.exists else "-",
                    "rota_atual": rota_doc.to_dict().get("nome_rota") if rota_doc.exists else "-",
                    "data_saida": escala.get("data_saida")
                })
            else:
                resultado.append({
                    "id": fid,
                    "numero_frota": f["numero_frota"],
                    "placa": f["placa"],
                    "status_frota": "livre",
                    "escala_ativa_id": None,
                    "motorista_atual": None,
                    "rota_atual": None,
                    "data_saida": None
                })
        return resultado

    def obter_historico_frota(self, frota_id: int, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, limite: int = 3) -> Optional[Dict[str, Any]]:
        frota_doc = self.db.collection("frota").document(str(frota_id)).get()
        if not frota_doc.exists:
            return None

        frota = dict(frota_doc.to_dict(), id=frota_id)
        escalas_query = self.db.collection("escalas").where("frota_id", "==", frota_id)
        docs = list(escalas_query.stream())

        historico = []
        for d in docs:
            e = d.to_dict()
            data_saida = str(e.get("data_saida", ""))
            if data_inicio and data_saida < data_inicio:
                continue
            if data_fim and data_saida > data_fim:
                continue

            mot_doc = self.db.collection("colaboradores").document(str(e.get("motorista_id"))).get()
            ajud_id = e.get("ajudante_id")
            ajud_doc = self.db.collection("colaboradores").document(str(ajud_id)).get() if ajud_id else None
            rota_doc = self.db.collection("rotas").document(str(e.get("rota_id"))).get()

            historico.append({
                "id": e.get("id"),
                "data_saida": e.get("data_saida"),
                "data_chegada": e.get("data_chegada"),
                "status": e.get("status"),
                "motorista_nome": mot_doc.to_dict().get("nome") if mot_doc.exists else "-",
                "motorista_id": e.get("motorista_id"),
                "ajudante_nome": ajud_doc.to_dict().get("nome") if ajud_doc and ajud_doc.exists else None,
                "ajudante_id": ajud_id,
                "nome_rota": rota_doc.to_dict().get("nome_rota") if rota_doc.exists else "-",
                "rota_id": e.get("rota_id")
            })

        historico.sort(key=lambda x: str(x.get("data_saida", "")), reverse=True)
        if not (data_inicio or data_fim):
            historico = historico[:limite]

        return {
            "frota": frota,
            "historico": historico,
            "total": len(historico)
        }

    # --- ROTAS ---
    def listar_rotas(self) -> List[Dict[str, Any]]:
        docs = self.db.collection("rotas").order_by("nome_rota").stream()
        return [dict(d.to_dict(), id=int(d.id) if d.id.isdigit() else d.id) for d in docs]

    def adicionar_rota(self, nome_rota: str, duracao_media_dias: Optional[int] = None) -> int:
        novo_id = self._obter_proximo_id("rotas")
        doc_data = {
            "id": novo_id,
            "nome_rota": str(nome_rota).strip(),
            "duracao_media_dias": int(duracao_media_dias) if duracao_media_dias else None
        }
        self.db.collection("rotas").document(str(novo_id)).set(doc_data)
        return novo_id

    def atualizar_rota(self, rota_id: int, nome_rota: str, duracao_media_dias: Optional[int] = None) -> bool:
        doc_ref = self.db.collection("rotas").document(str(rota_id))
        if not doc_ref.get().exists:
            return False
        doc_ref.update({
            "nome_rota": str(nome_rota).strip(),
            "duracao_media_dias": int(duracao_media_dias) if duracao_media_dias else None
        })
        return True

    def excluir_rota(self, rota_id: int) -> bool:
        escalas = list(self.db.collection("escalas").where("rota_id", "==", rota_id).limit(1).stream())
        if escalas:
            raise ValueError("Rota possui escalas relacionadas.")
        doc_ref = self.db.collection("rotas").document(str(rota_id))
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    # --- ESCALAS ---
    def listar_escalas(self) -> List[Dict[str, Any]]:
        docs = list(self.db.collection("escalas").order_by("id", direction="DESCENDING").stream())
        resultado = []
        for d in docs:
            e = d.to_dict()
            eid = int(d.id) if d.id.isdigit() else d.id
            mot_doc = self.db.collection("colaboradores").document(str(e.get("motorista_id"))).get()
            ajud_id = e.get("ajudante_id")
            ajud_doc = self.db.collection("colaboradores").document(str(ajud_id)).get() if ajud_id else None
            frota_doc = self.db.collection("frota").document(str(e.get("frota_id"))).get()
            rota_doc = self.db.collection("rotas").document(str(e.get("rota_id"))).get()

            resultado.append({
                "id": eid,
                "motorista_id": e.get("motorista_id"),
                "ajudante_id": ajud_id,
                "frota_id": e.get("frota_id"),
                "rota_id": e.get("rota_id"),
                "motorista": mot_doc.to_dict().get("nome") if mot_doc.exists else "-",
                "ajudante": ajud_doc.to_dict().get("nome") if ajud_doc and ajud_doc.exists else None,
                "numero_frota": frota_doc.to_dict().get("numero_frota") if frota_doc.exists else "-",
                "placa": frota_doc.to_dict().get("placa") if frota_doc.exists else "-",
                "nome_rota": rota_doc.to_dict().get("nome_rota") if rota_doc.exists else "-",
                "duracao_media_dias": rota_doc.to_dict().get("duracao_media_dias") if rota_doc.exists else None,
                "data_saida": e.get("data_saida"),
                "data_chegada": e.get("data_chegada"),
                "status": e.get("status")
            })
        return resultado

    def criar_escala(self, motorista_id: int, frota_id: int, rota_id: int, data_saida: str, ajudante_id: Optional[int] = None) -> int:
        novo_id = self._obter_proximo_id("escalas")
        doc_data = {
            "id": novo_id,
            "motorista_id": int(motorista_id),
            "ajudante_id": int(ajudante_id) if ajudante_id else None,
            "frota_id": int(frota_id),
            "rota_id": int(rota_id),
            "data_saida": data_saida,
            "data_chegada": None,
            "status": "em_rota"
        }
        self.db.collection("escalas").document(str(novo_id)).set(doc_data)

        # Atualiza status dos colaboradores
        self.db.collection("colaboradores").document(str(motorista_id)).update({"status": "em_rota"})
        if ajudante_id:
            self.db.collection("colaboradores").document(str(ajudante_id)).update({"status": "em_rota"})

        self.registrar_historico(
            tipo_alteracao="criacao_escala",
            descricao=f"Nova escala #{novo_id} iniciada para rota {rota_id}.",
            escala_id=novo_id
        )
        return novo_id

    def registrar_chegada(self, escala_id: int, data_chegada: str) -> None:
        doc_ref = self.db.collection("escalas").document(str(escala_id))
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Escala não encontrada.")

        escala = doc.to_dict()
        doc_ref.update({"data_chegada": data_chegada, "status": "chegou"})

        # Libera motorista
        mot_ref = self.db.collection("colaboradores").document(str(escala["motorista_id"]))
        mot = mot_ref.get().to_dict()
        if mot and mot.get("status") != "afastado":
            mot_ref.update({"status": "disponivel"})

        # Libera ajudante
        if escala.get("ajudante_id"):
            ajud_ref = self.db.collection("colaboradores").document(str(escala["ajudante_id"]))
            ajud = ajud_ref.get().to_dict()
            if ajud and ajud.get("status") != "afastado":
                ajud_ref.update({"status": "disponivel"})

        self.registrar_historico(
            tipo_alteracao="chegada_escala",
            descricao=f"Chegada registrada para a escala #{escala_id} em {data_chegada}.",
            escala_id=escala_id
        )

    def trocar_motorista(self, escala_id: int, novo_motorista_id: int, data_troca: str) -> int:
        doc_ref = self.db.collection("escalas").document(str(escala_id))
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Escala não encontrada")

        escala_atual = doc.to_dict()
        doc_ref.update({"status": "substituido", "data_chegada": data_troca})

        # Libera motorista anterior
        antigo_ref = self.db.collection("colaboradores").document(str(escala_atual["motorista_id"]))
        antigo = antigo_ref.get().to_dict()
        if antigo and antigo.get("status") != "afastado":
            antigo_ref.update({"status": "disponivel"})

        # Ocupa novo motorista
        self.db.collection("colaboradores").document(str(novo_motorista_id)).update({"status": "em_rota"})

        # Cria nova escala
        nova_escala_id = self.criar_escala(
            motorista_id=novo_motorista_id,
            frota_id=escala_atual["frota_id"],
            rota_id=escala_atual["rota_id"],
            data_saida=data_troca,
            ajudante_id=escala_atual.get("ajudante_id")
        )

        self.registrar_historico(
            tipo_alteracao="troca_motorista",
            descricao=f"Motorista alterado na escala #{escala_id} para #{novo_motorista_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )
        return nova_escala_id

    def trocar_ajudante(self, escala_id: int, novo_ajudante_id: Optional[int], data_troca: str) -> int:
        doc_ref = self.db.collection("escalas").document(str(escala_id))
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Escala não encontrada")

        escala_atual = doc.to_dict()
        doc_ref.update({"status": "substituido", "data_chegada": data_troca})

        # Libera ajudante anterior
        if escala_atual.get("ajudante_id"):
            antigo_ref = self.db.collection("colaboradores").document(str(escala_atual["ajudante_id"]))
            antigo = antigo_ref.get().to_dict()
            if antigo and antigo.get("status") != "afastado":
                antigo_ref.update({"status": "disponivel"})

        if novo_ajudante_id:
            self.db.collection("colaboradores").document(str(novo_ajudante_id)).update({"status": "em_rota"})

        nova_escala_id = self.criar_escala(
            motorista_id=escala_atual["motorista_id"],
            frota_id=escala_atual["frota_id"],
            rota_id=escala_atual["rota_id"],
            data_saida=data_troca,
            ajudante_id=novo_ajudante_id
        )

        self.registrar_historico(
            tipo_alteracao="troca_ajudante",
            descricao=f"Ajudante alterado na escala #{escala_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )
        return nova_escala_id

    def trocar_frota(self, escala_id: int, nova_frota_id: int, data_troca: str) -> int:
        doc_ref = self.db.collection("escalas").document(str(escala_id))
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Escala não encontrada")

        escala_atual = doc.to_dict()
        doc_ref.update({"status": "substituido", "data_chegada": data_troca})

        nova_escala_id = self.criar_escala(
            motorista_id=escala_atual["motorista_id"],
            frota_id=nova_frota_id,
            rota_id=escala_atual["rota_id"],
            data_saida=data_troca,
            ajudante_id=escala_atual.get("ajudante_id")
        )

        self.registrar_historico(
            tipo_alteracao="troca_frota",
            descricao=f"Frota alterada na escala #{escala_id} para frota #{nova_frota_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )
        return nova_escala_id

    def trocar_rota(self, escala_id: int, nova_rota_id: int, data_troca: str) -> int:
        doc_ref = self.db.collection("escalas").document(str(escala_id))
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Escala não encontrada")

        escala_atual = doc.to_dict()
        doc_ref.update({"status": "substituido", "data_chegada": data_troca})

        nova_escala_id = self.criar_escala(
            motorista_id=escala_atual["motorista_id"],
            frota_id=escala_atual["frota_id"],
            rota_id=nova_rota_id,
            data_saida=data_troca,
            ajudante_id=escala_atual.get("ajudante_id")
        )

        self.registrar_historico(
            tipo_alteracao="troca_rota",
            descricao=f"Rota alterada na escala #{escala_id} para rota #{nova_rota_id}. Nova escala: #{nova_escala_id}",
            escala_id=nova_escala_id
        )
        return nova_escala_id

    # --- AFASTAMENTOS ---
    def listar_afastamentos_ativos(self) -> List[Dict[str, Any]]:
        docs = list(self.db.collection("afastamentos").order_by("id", direction="DESCENDING").stream())
        resultado = []
        for d in docs:
            a = d.to_dict()
            if a.get("data_retorno") is None:
                colab_doc = self.db.collection("colaboradores").document(str(a.get("colaborador_id"))).get()
                colab = colab_doc.to_dict() if colab_doc.exists else {}
                resultado.append({
                    "id": a.get("id"),
                    "colaborador_id": a.get("colaborador_id"),
                    "nome": colab.get("nome", "-"),
                    "funcao": colab.get("funcao", "-"),
                    "motivo": a.get("motivo"),
                    "data_inicio": a.get("data_inicio"),
                    "data_fim_prevista": a.get("data_fim_prevista")
                })
        return resultado

    def registrar_afastamento(self, colaborador_id: int, motivo: str, data_inicio: str, data_fim_prevista: Optional[str] = None) -> int:
        novo_id = self._obter_proximo_id("afastamentos")
        doc_data = {
            "id": novo_id,
            "colaborador_id": int(colaborador_id),
            "motivo": motivo,
            "data_inicio": data_inicio,
            "data_fim_prevista": data_fim_prevista,
            "data_retorno": None
        }
        self.db.collection("afastamentos").document(str(novo_id)).set(doc_data)
        self.db.collection("colaboradores").document(str(colaborador_id)).update({"status": "afastado"})

        self.registrar_historico(
            tipo_alteracao="afastamento",
            descricao=f"Colaborador #{colaborador_id} afastado. Motivo: {motivo}"
        )
        return novo_id

    def registrar_retorno(self, afastamento_id: int, colaborador_id: int, data_retorno: str) -> None:
        doc_ref = self.db.collection("afastamentos").document(str(afastamento_id))
        doc_ref.update({"data_retorno": data_retorno})
        self.db.collection("colaboradores").document(str(colaborador_id)).update({"status": "disponivel"})

        self.registrar_historico(
            tipo_alteracao="retorno_afastamento",
            descricao=f"Colaborador #{colaborador_id} retornou do afastamento #{afastamento_id} em {data_retorno}"
        )

    # --- AUDITORIA & HISTÓRICO ---
    def registrar_historico(self, tipo_alteracao: str, descricao: str, escala_id: Optional[int] = None) -> None:
        novo_id = self._obter_proximo_id("historico_alteracoes")
        doc_data = {
            "id": novo_id,
            "tipo_alteracao": tipo_alteracao,
            "descricao": descricao,
            "escala_id": escala_id,
            "data_alteracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db.collection("historico_alteracoes").document(str(novo_id)).set(doc_data)

    def listar_historico(self) -> List[Dict[str, Any]]:
        docs = self.db.collection("historico_alteracoes").order_by("id", direction="DESCENDING").stream()
        return [dict(d.to_dict(), id=int(d.id) if d.id.isdigit() else d.id) for d in docs]

    # --- DASHBOARD & INDICADORES ---
    def obter_indicadores(self) -> Dict[str, Any]:
        escalas_em_rota = len(list(self.db.collection("escalas").where("status", "==", "em_rota").stream()))
        mot_disp = len(list(self.db.collection("colaboradores").where("status", "==", "disponivel").where("funcao", "==", "motorista").stream()))
        ajud_disp = len(list(self.db.collection("colaboradores").where("status", "==", "disponivel").where("funcao", "==", "ajudante").stream()))
        afastados = len(list(self.db.collection("colaboradores").where("status", "==", "afastado").stream()))
        total_frota = len(list(self.db.collection("frota").stream()))
        total_rotas = len(list(self.db.collection("rotas").stream()))

        # Viagens concluídas e pontualidade
        concluidas_docs = list(self.db.collection("escalas").where("status", "==", "chegou").stream())
        total_concluidas = len(concluidas_docs)
        no_prazo = 0

        # Mapeia rotas para checagem rápida de duração
        rotas_map = {int(r.id): r.to_dict() for r in self.db.collection("rotas").stream()}

        # Frequência de motoristas e rotas
        motoristas_count = {}
        rotas_count = {}

        for doc in concluidas_docs:
            e = doc.to_dict()
            rota_info = rotas_map.get(e.get("rota_id"))
            duracao_media = rota_info.get("duracao_media_dias") if rota_info else None
            saida = e.get("data_saida")
            chegada = e.get("data_chegada")
            if saida and chegada and duracao_media:
                try:
                    d_saida = datetime.strptime(saida[:10], "%Y-%m-%d")
                    d_chegada = datetime.strptime(chegada[:10], "%Y-%m-%d")
                    if (d_chegada - d_saida).days <= duracao_media:
                        no_prazo += 1
                except Exception:
                    pass

        # Ranking geral de viagens
        all_escalas = list(self.db.collection("escalas").stream())
        colabs_map = {int(c.id): c.to_dict() for c in self.db.collection("colaboradores").stream()}

        for doc in all_escalas:
            e = doc.to_dict()
            mid = e.get("motorista_id")
            rid = e.get("rota_id")
            if mid:
                motoristas_count[mid] = motoristas_count.get(mid, 0) + 1
            if rid:
                rotas_count[rid] = rotas_count.get(rid, 0) + 1

        top_motoristas = [
            {"nome": colabs_map.get(mid, {}).get("nome", f"Motorista #{mid}"), "total_viagens": count}
            for mid, count in sorted(motoristas_count.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        top_rotas = [
            {"nome_rota": rotas_map.get(rid, {}).get("nome_rota", f"Rota #{rid}"), "total_escalas": count}
            for rid, count in sorted(rotas_count.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        frotas_com_status = self.listar_frotas_com_status()
        frotas_disponiveis = sum(1 for f in frotas_com_status if f["status_frota"] == "livre")
        total_reservas = len(self.listar_colaboradores_reserva())

        # Transbordos
        escalas_ativas = [e.to_dict() for e in self.db.collection("escalas").where("status", "==", "em_rota").stream()]
        pares = {}
        for e in escalas_ativas:
            par = (e.get("motorista_id"), e.get("frota_id"))
            pares[par] = pares.get(par, 0) + 1
        total_transbordos = sum(1 for count in pares.values() if count > 1)

        taxa_pontualidade = round((no_prazo / total_concluidas * 100), 1) if total_concluidas > 0 else 100.0

        return {
            "escalas_em_rota": escalas_em_rota,
            "motoristas_disponiveis": mot_disp,
            "ajudantes_disponiveis": ajud_disp,
            "colaboradores_afastados": afastados,
            "total_frota": total_frota,
            "total_rotas": total_rotas,
            "total_viagens_concluidas": total_concluidas,
            "taxa_pontualidade": taxa_pontualidade,
            "top_motoristas": top_motoristas,
            "top_rotas": top_rotas,
            "frotas_disponiveis": frotas_disponiveis,
            "total_reservas": total_reservas,
            "total_transbordos": total_transbordos,
        }

    # --- IMPORTAÇÃO & LOTES ---
    def criar_lote_importacao(self, arquivo_nome: str) -> int:
        novo_id = self._obter_proximo_id("lotes_importacao")
        self.db.collection("lotes_importacao").document(str(novo_id)).set({
            "id": novo_id,
            "arquivo_nome": arquivo_nome,
            "data_importacao": datetime.now().isoformat(),
            "observacao": ""
        })
        return novo_id

    def atualizar_observacao_lote(self, lote_id: int, texto: str) -> None:
        doc_ref = self.db.collection("lotes_importacao").document(str(lote_id))
        doc = doc_ref.get()
        if doc.exists:
            obs = doc.to_dict().get("observacao", "")
            nova_obs = (obs + "\n" + texto).strip() if obs else texto
            doc_ref.update({"observacao": nova_obs})

    def listar_lotes_importacao(self) -> List[Dict[str, Any]]:
        docs = self.db.collection("lotes_importacao").order_by("id", direction="DESCENDING").stream()
        return [dict(d.to_dict(), id=int(d.id) if d.id.isdigit() else d.id) for d in docs]

    def processar_linha_importacao(self, dados: Dict[str, Any], data_padrao: Optional[str] = None, motivo_afastamento_padrao: str = "Retirado da escala via importação de planilha") -> Dict[str, Any]:
        # Para Firestore, implementamos a mesma lógica de autocadastro e troca
        motorista_nome = dados.get("motorista")
        frota_identificador = dados.get("frota") or dados.get("veiculo") or dados.get("placa")
        rota_nome = dados.get("rota")
        ajudante_nome = dados.get("ajudante")
        data_saida = dados.get("data_saida") or data_padrao or datetime.now().strftime("%Y-%m-%d")

        if not motorista_nome or not frota_identificador or not rota_nome:
            return {"status": "erro", "motivo": "Linha sem motorista, frota ou rota preenchidos"}

        # Obter ou criar motorista
        mots = list(self.db.collection("colaboradores").where("funcao", "==", "motorista").stream())
        motorista_id = None
        for m in mots:
            if m.to_dict().get("nome", "").strip().lower() == str(motorista_nome).strip().lower():
                motorista_id = int(m.id) if m.id.isdigit() else m.id
                break
        if not motorista_id:
            motorista_id = self.adicionar_colaborador(str(motorista_nome).strip(), "motorista")

        # Obter ou criar frota
        partes = str(frota_identificador).split("-", 1) if "-" in str(frota_identificador) else [str(frota_identificador), str(frota_identificador)]
        num_f, placa_f = partes[0].strip(), partes[1].strip()
        frotas = list(self.db.collection("frota").stream())
        frota_id = None
        for f in frotas:
            f_dict = f.to_dict()
            if f_dict.get("numero_frota", "").upper() == num_f.upper() or f_dict.get("placa", "").upper() == placa_f.upper():
                frota_id = int(f.id) if f.id.isdigit() else f.id
                break
        if not frota_id:
            frota_id = self.adicionar_frota(num_f, placa_f)

        # Obter ou criar rota
        rotas = list(self.db.collection("rotas").stream())
        rota_id = None
        for r in rotas:
            if r.to_dict().get("nome_rota", "").strip().lower() == str(rota_nome).strip().lower():
                rota_id = int(r.id) if r.id.isdigit() else r.id
                break
        if not rota_id:
            rota_id = self.adicionar_rota(str(rota_nome).strip())

        # Obter ou criar ajudante
        ajudante_id = None
        if ajudante_nome and str(ajudante_nome).strip().upper() not in ("VAZIO", "NAN", "-", "--"):
            ajuds = list(self.db.collection("colaboradores").where("funcao", "==", "ajudante").stream())
            for a in ajuds:
                if a.to_dict().get("nome", "").strip().lower() == str(ajudante_nome).strip().lower():
                    ajudante_id = int(a.id) if a.id.isdigit() else a.id
                    break
            if not ajudante_id:
                ajudante_id = self.adicionar_colaborador(str(ajudante_nome).strip(), "ajudante")

        # Checar escala ativa para o veículo ou motorista
        escalas_ativas = list(self.db.collection("escalas").where("status", "==", "em_rota").stream())
        escala_ativa = None
        for ea in escalas_ativas:
            e_dict = ea.to_dict()
            if e_dict.get("frota_id") == frota_id or e_dict.get("motorista_id") == motorista_id:
                escala_ativa = dict(e_dict, id=int(ea.id) if ea.id.isdigit() else ea.id)
                break

        afastamento_gerado = None
        if escala_ativa:
            ajudante_ant = escala_ativa.get("ajudante_id")
            if ajudante_ant is not None and ajudante_id is None:
                afast_id = self.registrar_afastamento(
                    colaborador_id=ajudante_ant,
                    motivo=motivo_afastamento_padrao,
                    data_inicio=data_saida
                )
                afastamento_gerado = {"colaborador_id": ajudante_ant, "afastamento_id": afast_id}

            self.db.collection("escalas").document(str(escala_ativa["id"])).update({
                "status": "substituido",
                "data_chegada": data_saida
            })

            if escala_ativa.get("motorista_id") != motorista_id:
                antigo_mot_ref = self.db.collection("colaboradores").document(str(escala_ativa["motorista_id"]))
                if antigo_mot_ref.get().to_dict().get("status") != "afastado":
                    antigo_mot_ref.update({"status": "disponivel"})

        nova_escala_id = self.criar_escala(
            motorista_id=motorista_id,
            frota_id=frota_id,
            rota_id=rota_id,
            data_saida=data_saida,
            ajudante_id=ajudante_id
        )

        return {
            "status": "sucesso",
            "escala_id": nova_escala_id,
            "motorista_id": motorista_id,
            "frota_id": frota_id,
            "rota_id": rota_id,
            "ajudante_id": ajudante_id,
            "afastamento_gerado": afastamento_gerado
        }

    def processar_linha_rodape(self, texto: str, lote_id: Optional[int] = None) -> Dict[str, Any]:
        if not texto or not str(texto).strip():
            return {"tipo": "vazio"}

        texto_limpo = str(texto).strip()
        upper = texto_limpo.upper()

        if upper.startswith("RESERVAS"):
            return {"tipo": "ignorado", "motivo": "linha RESERVAS"}

        if upper.startswith("MOTORISTAS"):
            conteudo = texto_limpo.split(":", 1)[1] if ":" in texto_limpo else ""
            nomes = [n.strip() for n in conteudo.split(",") if n.strip()]
            ids = []
            for nome in nomes:
                cid = self.adicionar_colaborador(nome, "motorista", status="reserva")
                ids.append(cid)
            return {"tipo": "reserva_motoristas", "colaboradores": ids}

        if upper.startswith("AJUDANTES"):
            conteudo = texto_limpo.split(":", 1)[1] if ":" in texto_limpo else ""
            nomes = [n.strip() for n in conteudo.split(",") if n.strip()]
            ids = []
            for nome in nomes:
                cid = self.adicionar_colaborador(nome, "ajudante", status="reserva")
                ids.append(cid)
            return {"tipo": "reserva_ajudantes", "colaboradores": ids}

        if "INSTRUÇÃO TRANSBORDO" in upper or "INSTRUCAO TRANSBORDO" in upper:
            if lote_id:
                self.atualizar_observacao_lote(lote_id, texto_limpo)
            return {"tipo": "observacao_lote", "texto": texto_limpo}

        return {"tipo": "ignorado", "motivo": "linha de rodapé não reconhecida"}

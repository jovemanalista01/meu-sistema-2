import os
import sys
from typing import List, Dict, Any, Optional

# Garante que o diretório raiz esteja no path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.database import db_manager
from backend.database.repository_interface import DataRepository


class SQLiteRepository(DataRepository):
    """Implementação do repositório utilizando SQLite (escala.db)."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            db_manager.db_PATH = db_path
        db_manager._ensure_db()

    def listar_colaboradores(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_colaboradores()]

    def adicionar_colaborador(self, nome: str, funcao: str, status: str = "disponivel") -> int:
        return db_manager.adicionar_colaborador(nome, funcao, status)

    def atualizar_colaborador(self, colaborador_id: int, nome: str, funcao: str, status: Optional[str] = None) -> bool:
        return db_manager.atualizar_colaborador(colaborador_id, nome, funcao, status)

    def excluir_colaborador(self, colaborador_id: int) -> bool:
        return db_manager.excluir_colaborador(colaborador_id)

    def listar_disponiveis(self, funcao: str) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_disponiveis(funcao)]

    def listar_colaboradores_reserva(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_colaboradores_reserva()]

    def remover_reserva(self, colaborador_id: int) -> int:
        return db_manager.remover_reserva(colaborador_id)

    def obter_historico_colaborador(self, colaborador_id: int) -> Dict[str, Any]:
        return db_manager.obter_historico_colaborador(colaborador_id)

    def listar_frota(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_frota()]

    def adicionar_frota(self, numero_frota: str, placa: str) -> int:
        return db_manager.adicionar_frota(numero_frota, placa)

    def atualizar_frota(self, frota_id: int, numero_frota: str, placa: str) -> bool:
        return db_manager.atualizar_frota(frota_id, numero_frota, placa)

    def excluir_frota(self, frota_id: int) -> bool:
        return db_manager.excluir_frota(frota_id)

    def listar_frotas_com_status(self) -> List[Dict[str, Any]]:
        return db_manager.listar_frotas_com_status()

    def obter_historico_frota(self, frota_id: int, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, limite: int = 3) -> Optional[Dict[str, Any]]:
        return db_manager.obter_historico_frota(frota_id, data_inicio, data_fim, limite)

    def listar_rotas(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_rotas()]

    def adicionar_rota(self, nome_rota: str, duracao_media_dias: Optional[int] = None) -> int:
        return db_manager.adicionar_rota(nome_rota, duracao_media_dias)

    def atualizar_rota(self, rota_id: int, nome_rota: str, duracao_media_dias: Optional[int] = None) -> bool:
        return db_manager.atualizar_rota(rota_id, nome_rota, duracao_media_dias)

    def excluir_rota(self, rota_id: int) -> bool:
        return db_manager.excluir_rota(rota_id)

    def listar_escalas(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_escalas()]

    def criar_escala(self, motorista_id: int, frota_id: int, rota_id: int, data_saida: str, ajudante_id: Optional[int] = None) -> int:
        return db_manager.criar_escala(motorista_id, frota_id, rota_id, data_saida, ajudante_id)

    def registrar_chegada(self, escala_id: int, data_chegada: str) -> None:
        db_manager.registrar_chegada(escala_id, data_chegada)

    def trocar_motorista(self, escala_id: int, novo_motorista_id: int, data_troca: str) -> int:
        return db_manager.trocar_motorista(escala_id, novo_motorista_id, data_troca)

    def trocar_ajudante(self, escala_id: int, novo_ajudante_id: Optional[int], data_troca: str) -> int:
        return db_manager.trocar_ajudante(escala_id, novo_ajudante_id, data_troca)

    def trocar_frota(self, escala_id: int, nova_frota_id: int, data_troca: str) -> int:
        return db_manager.trocar_frota(escala_id, nova_frota_id, data_troca)

    def trocar_rota(self, escala_id: int, nova_rota_id: int, data_troca: str) -> int:
        return db_manager.trocar_rota(escala_id, nova_rota_id, data_troca)

    def listar_afastamentos_ativos(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_afastamentos_ativos()]

    def registrar_afastamento(self, colaborador_id: int, motivo: str, data_inicio: str, data_fim_prevista: Optional[str] = None) -> int:
        return db_manager.registrar_afastamento(colaborador_id, motivo, data_inicio, data_fim_prevista)

    def registrar_retorno(self, afastamento_id: int, colaborador_id: int, data_retorno: str) -> None:
        db_manager.registrar_retorno(afastamento_id, colaborador_id, data_retorno)

    def registrar_historico(self, tipo_alteracao: str, descricao: str, escala_id: Optional[int] = None) -> None:
        db_manager.registrar_historico(tipo_alteracao, descricao, escala_id)

    def listar_historico(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_historico()]

    def obter_indicadores(self) -> Dict[str, Any]:
        return db_manager.obter_indicadores()

    def criar_lote_importacao(self, arquivo_nome: str) -> int:
        return db_manager.criar_lote_importacao(arquivo_nome)

    def atualizar_observacao_lote(self, lote_id: int, texto: str) -> None:
        db_manager.atualizar_observacao_lote(lote_id, texto)

    def listar_lotes_importacao(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in db_manager.listar_lotes_importacao()]

    def processar_linha_importacao(self, dados: Dict[str, Any], data_padrao: Optional[str] = None, motivo_afastamento_padrao: str = "Retirado da escala via importação de planilha") -> Dict[str, Any]:
        return db_manager.processar_linha_importacao(dados, data_padrao, motivo_afastamento_padrao)

    def processar_linha_rodape(self, texto: str, lote_id: Optional[int] = None) -> Dict[str, Any]:
        return db_manager.processar_linha_rodape(texto, lote_id)

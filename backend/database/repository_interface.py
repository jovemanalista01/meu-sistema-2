from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DataRepository(ABC):
    """Interface abstrata da camada de persistência para SQLite e Firestore."""

    # --- COLABORADORES ---
    @abstractmethod
    def listar_colaboradores(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def adicionar_colaborador(self, nome: str, funcao: str, status: str = "disponivel") -> int:
        pass

    @abstractmethod
    def atualizar_colaborador(self, colaborador_id: int, nome: str, funcao: str, status: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def excluir_colaborador(self, colaborador_id: int) -> bool:
        pass

    @abstractmethod
    def listar_disponiveis(self, funcao: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def listar_colaboradores_reserva(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def remover_reserva(self, colaborador_id: int) -> int:
        pass

    @abstractmethod
    def obter_historico_colaborador(self, colaborador_id: int) -> Dict[str, Any]:
        pass

    # --- FROTA ---
    @abstractmethod
    def listar_frota(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def adicionar_frota(self, numero_frota: str, placa: str) -> int:
        pass

    @abstractmethod
    def atualizar_frota(self, frota_id: int, numero_frota: str, placa: str) -> bool:
        pass

    @abstractmethod
    def excluir_frota(self, frota_id: int) -> bool:
        pass

    @abstractmethod
    def listar_frotas_com_status(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def obter_historico_frota(self, frota_id: int, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, limite: int = 3) -> Optional[Dict[str, Any]]:
        pass

    # --- ROTAS ---
    @abstractmethod
    def listar_rotas(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def adicionar_rota(self, nome_rota: str, duracao_media_dias: Optional[int] = None) -> int:
        pass

    @abstractmethod
    def atualizar_rota(self, rota_id: int, nome_rota: str, duracao_media_dias: Optional[int] = None) -> bool:
        pass

    @abstractmethod
    def excluir_rota(self, rota_id: int) -> bool:
        pass

    # --- ESCALAS ---
    @abstractmethod
    def listar_escalas(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def criar_escala(self, motorista_id: int, frota_id: int, rota_id: int, data_saida: str, ajudante_id: Optional[int] = None) -> int:
        pass

    @abstractmethod
    def registrar_chegada(self, escala_id: int, data_chegada: str) -> None:
        pass

    @abstractmethod
    def trocar_motorista(self, escala_id: int, novo_motorista_id: int, data_troca: str) -> int:
        pass

    @abstractmethod
    def trocar_ajudante(self, escala_id: int, novo_ajudante_id: Optional[int], data_troca: str) -> int:
        pass

    @abstractmethod
    def trocar_frota(self, escala_id: int, nova_frota_id: int, data_troca: str) -> int:
        pass

    @abstractmethod
    def trocar_rota(self, escala_id: int, nova_rota_id: int, data_troca: str) -> int:
        pass

    # --- AFASTAMENTOS ---
    @abstractmethod
    def listar_afastamentos_ativos(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def registrar_afastamento(self, colaborador_id: int, motivo: str, data_inicio: str, data_fim_prevista: Optional[str] = None) -> int:
        pass

    @abstractmethod
    def registrar_retorno(self, afastamento_id: int, colaborador_id: int, data_retorno: str) -> None:
        pass

    # --- AUDITORIA & HISTÓRICO ---
    @abstractmethod
    def registrar_historico(self, tipo_alteracao: str, descricao: str, escala_id: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def listar_historico(self) -> List[Dict[str, Any]]:
        pass

    # --- DASHBOARD & INDICADORES ---
    @abstractmethod
    def obter_indicadores(self) -> Dict[str, Any]:
        pass

    # --- IMPORTAÇÃO & LOTES ---
    @abstractmethod
    def criar_lote_importacao(self, arquivo_nome: str) -> int:
        pass

    @abstractmethod
    def atualizar_observacao_lote(self, lote_id: int, texto: str) -> None:
        pass

    @abstractmethod
    def listar_lotes_importacao(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def processar_linha_importacao(self, dados: Dict[str, Any], data_padrao: Optional[str] = None, motivo_afastamento_padrao: str = "Retirado da escala via importação de planilha") -> Dict[str, Any]:
        pass

    @abstractmethod
    def processar_linha_rodape(self, texto: str, lote_id: Optional[int] = None) -> Dict[str, Any]:
        pass

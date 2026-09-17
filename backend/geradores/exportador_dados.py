import io
import pandas as pd
from typing import List, Dict, Any

class ExportadorDadosService:
    """Serviço para geração de relatórios e exportação de dados em formatos Excel e CSV."""

    @staticmethod
    def exportar_escalas_excel(escalas: List[Dict[str, Any]]) -> io.BytesIO:
        """Gera uma planilha Excel estilizada com as escalas fornecidas."""
        df = pd.DataFrame(escalas)
        colunas_map = {
            "id": "ID Escala",
            "motorista": "Motorista",
            "ajudante": "Ajudante",
            "numero_frota": "Nº Frota",
            "placa": "Placa",
            "nome_rota": "Rota de Destino",
            "data_saida": "Data de Saída",
            "data_chegada": "Data de Chegada",
            "status": "Status da Viagem"
        }
        colunas_existentes = [c for c in colunas_map.keys() if c in df.columns]
        df_export = df[colunas_existentes].rename(columns=colunas_map)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Escalas Operacionais")
        output.seek(0)
        return output

    @staticmethod
    def exportar_escalas_csv(escalas: List[Dict[str, Any]]) -> io.BytesIO:
        """Exporta escalas em formato CSV compatível com padrão brasileiro (ponto-e-vírgula e UTF-8 com BOM)."""
        df = pd.DataFrame(escalas)
        output = io.BytesIO()
        csv_text = df.to_csv(index=False, sep=";", encoding="utf-8-sig")
        output.write(csv_text.encode("utf-8-sig"))
        output.seek(0)
        return output

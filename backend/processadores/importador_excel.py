import io
import traceback
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from backend.database.db_factory import get_repository

class ImportadorExcelService:
    """Motor de processamento de planilhas Excel e arquivos CSV para importação de escalas."""

    @staticmethod
    def ler_planilha(bytes_data: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], list]:
        """Lê arquivo em múltiplos formatos com tratamento de exceções e fallback de engines."""
        filename_lower = filename.lower()
        erros_leitura = []
        df = None

        if filename_lower.endswith('.csv'):
            for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(io.BytesIO(bytes_data), encoding=enc, sep=None, engine='python')
                    break
                except Exception as e:
                    erros_leitura.append(str(e))
        else:
            engines_to_try = ['openpyxl', 'xlrd', None] if filename_lower.endswith('.xlsx') else ['xlrd', 'openpyxl', None]
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

        return df, erros_leitura

    @staticmethod
    def normalizar_colunas(df: pd.DataFrame) -> Dict[str, str]:
        """Detecta heuristicamente as colunas correspondentes na planilha."""
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

        return colunas_normalizadas

    @classmethod
    def processar(cls, bytes_data: bytes, filename: str, motivo_afastamento: str = "Retirado da escala via importação de planilha") -> Tuple[Dict[str, Any], int]:
        """Executa o processamento completo do arquivo."""
        repo = get_repository()
        df, erros_leitura = cls.ler_planilha(bytes_data, filename)

        if df is None:
            return {
                "error": f"Não foi possível abrir o arquivo. Detalhes: {'; '.join(erros_leitura)}"
            }, 400

        colunas_normalizadas = cls.normalizar_colunas(df)

        if 'motorista' not in colunas_normalizadas or 'frota' not in colunas_normalizadas or 'rota' not in colunas_normalizadas:
            return {
                "error": "Colunas obrigatórias ('Motorista', 'Veículo' e 'Descrição'/'Rota') não foram encontradas na planilha.",
                "colunas_encontradas_no_arquivo": [str(c) for c in df.columns],
                "colunas_detectadas": colunas_normalizadas,
                "dica": "Renomeie as colunas da planilha para conter: 'Motorista', 'Veículo' ou 'Frota', e 'Descrição' ou 'Rota'"
            }, 400

        lote_id = repo.criar_lote_importacao(filename)

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

            # Linha sem motorista/frota/rota: é rodapé ou vazia
            if pd.isna(raw_motorista) and pd.isna(raw_frota) and pd.isna(raw_rota):
                primeira_coluna = row.iloc[0]
                if pd.notna(primeira_coluna) and str(primeira_coluna).strip():
                    linhas_rodape += 1
                    res_rodape = repo.processar_linha_rodape(str(primeira_coluna), lote_id=lote_id)
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

            try:
                res = repo.processar_linha_importacao(
                    dados_linha,
                    motivo_afastamento_padrao=motivo_afastamento
                )
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

        return {
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
        }, 200

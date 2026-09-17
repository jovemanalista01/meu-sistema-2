"""
Script de Migração: SQLite (escala.db) -> Firebase Firestore
Migra colaboradores, frota, rotas, escalas, afastamentos, historico_alteracoes e lotes_importacao,
além de criar as coleções 'usuarios' e 'configuracoes'.
"""

import os
import sys
import sqlite3
from datetime import datetime

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.config import SQLITE_DB_PATH
from backend.firebase.firebase_admin_client import get_firestore_client

def migrar():
    print("=" * 65)
    print("  MIGRAÇÃO DE DADOS: SQLite -> Firebase Firestore")
    print("=" * 65)

    if not os.path.exists(SQLITE_DB_PATH):
        print(f"[ERRO] Banco SQLite não encontrado em: {SQLITE_DB_PATH}")
        return

    db = get_firestore_client()
    if db is None:
        print("[ERRO] Não foi possível conectar ao Firestore.")
        print("Certifique-se de configurar o arquivo 'config/firebase_credentials.json'.")
        return

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tabelas = [
        ("colaboradores", "colaboradores"),
        ("frota", "frota"),
        ("rotas", "rotas"),
        ("escalas", "escalas"),
        ("afastamentos", "afastamentos"),
        ("historico_alteracoes", "historico_alteracoes"),
        ("lotes_importacao", "lotes_importacao"),
    ]

    total_geral = 0

    for tabela_sql, colecao_fs in tabelas:
        cursor.execute(f"SELECT * FROM {tabela_sql}")
        linhas = cursor.fetchall()
        print(f"\n-> Migrando '{tabela_sql}' ({len(linhas)} registros) para coleção '{colecao_fs}'...")

        batch = db.batch()
        count = 0
        batch_count = 0
        max_id = 0

        for row in linhas:
            dados = dict(row)
            doc_id = str(dados.get("id"))
            if dados.get("id") and isinstance(dados.get("id"), int) and dados.get("id") > max_id:
                max_id = dados.get("id")

            doc_ref = db.collection(colecao_fs).document(doc_id)
            batch.set(doc_ref, dados)
            count += 1
            batch_count += 1

            # Firestore permite até 500 operações por batch commit
            if batch_count >= 400:
                batch.commit()
                batch = db.batch()
                batch_count = 0

        if batch_count > 0:
            batch.commit()

        # Atualiza contador sequencial
        if max_id > 0:
            db.collection("_contadores").document(colecao_fs).set({"ultimo_id": max_id})

        print(f"   [OK] {count} documentos migrados com sucesso para '{colecao_fs}'.")
        total_geral += count

    # Criação da coleção 'usuarios' inicial
    print("\n-> Inicializando coleção de 'usuarios' e permissões...")
    usuarios_iniciais = [
        {
            "uid": "admin-principal",
            "email": "admin@logiscale.com",
            "nome": "Administrador do Sistema",
            "role": "ADMIN",
            "ativo": True,
            "criado_em": datetime.now().isoformat()
        },
        {
            "uid": "operador-principal",
            "email": "operacional@logiscale.com",
            "nome": "Operador da Central",
            "role": "OPERACIONAL",
            "ativo": True,
            "criado_em": datetime.now().isoformat()
        }
    ]
    for u in usuarios_iniciais:
        db.collection("usuarios").document(u["uid"]).set(u)
    print("   [OK] Usuários iniciais configurados (ADMIN e OPERACIONAL).")

    # Criação da coleção 'configuracoes'
    print("\n-> Inicializando coleção 'configuracoes'...")
    db.collection("configuracoes").document("geral").set({
        "nome_sistema": "LogiScale Web",
        "versao": "2.0.0",
        "empresa": "LogiScale Logística e Frotas",
        "motivos_afastamento_permitidos": ["Folga", "Falta", "Licença médica", "Demanda interna"],
        "atualizado_em": datetime.now().isoformat()
    })
    print("   [OK] Configuração geral gravada.")

    conn.close()
    print("\n" + "=" * 65)
    print(f"  MIGRAÇÃO CONCLUÍDA: {total_geral} registros migrados para o Firestore.")
    print("=" * 65)

if __name__ == "__main__":
    migrar()

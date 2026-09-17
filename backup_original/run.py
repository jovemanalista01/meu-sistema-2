"""
Ponto de entrada do LogiScale.exe

Este arquivo é o que o executável realmente roda: ele inicia o servidor
Flask em segundo plano e abre automaticamente o navegador padrão do
Windows (Chrome, Edge, etc.) apontando para o sistema.

Fechar essa janela preta (console) encerra o programa.
"""

import os
import sys
import socket
import threading
import time
import webbrowser

# Garante que "database" seja encontrado tanto rodando como .py quanto
# como .exe empacotado pelo PyInstaller.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app  # noqa: E402  (import depois do sys.path de propósito)

HOST = "127.0.0.1"
PORT = 5000


def _porta_livre(porta):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, porta)) != 0


def _escolher_porta():
    porta = PORT
    while not _porta_livre(porta):
        porta += 1
    return porta


def _abrir_navegador(url):
    # Pequena espera para dar tempo do servidor Flask subir antes de
    # o navegador tentar acessar o endereço.
    time.sleep(1.2)
    webbrowser.open(url)


def main():
    porta = _escolher_porta()
    url = f"http://{HOST}:{porta}"

    print("=" * 60)
    print("  LogiScale - Sistema de Gestão de Escala da Frota")
    print("=" * 60)
    print(f"  Servidor iniciado em: {url}")
    print("  O navegador vai abrir sozinho em instantes...")
    print("  Para ENCERRAR o sistema, feche esta janela.")
    print("=" * 60)

    threading.Thread(target=_abrir_navegador, args=(url,), daemon=True).start()

    # debug=False e use_reloader=False são obrigatórios no .exe: o modo
    # debug tenta reiniciar o processo sozinho, o que não funciona dentro
    # de um executável empacotado.
    app.run(host=HOST, port=porta, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

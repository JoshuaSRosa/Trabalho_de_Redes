import socket
import json
import threading
from . import rede
from .estado import EstadoCliente
from . import ui_terminal as ui
from comum import protocolo as P

HOST = "127.0.0.1"
PORT = 38912

def thread_recebimento(sock, estado):
    buffer = b""
    while estado.ativo:
        try:
            msg, buffer =  rede.receber_linha(sock, buffer)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"\n[erro de protocolo] {e}")
            break
        if msg is None:
            print(f"\n[servidor encerrou]")
            estado.ativo = False
            estado.minha_vez.set()
            break
        estado.processar(msg)
        ui.renderizar(msg, estado)
        if estado.deve_acordar_main(msg):
            estado.minha_vez.set()

def loop_principal(sock, estado):
    try:
        while estado.ativo:
            estado.minha_vez.wait()
            if not estado.ativo:
                break
            estado.minha_vez.clear()
            try:
                linha = int(input(f"{ui.CIANO}Linha (1-3):{ui.R} ")) - 1
                coluna = int(input(f"{ui.CIANO}Coluna (1-3):{ui.R} ")) - 1
            except ValueError:
                print("Digite números de 1 a 3.")
                estado.minha_vez.set() # tenta de novo
                continue
            except (KeyboardInterrupt, EOFError):
                break

            if not ((0 <= linha < 3) and (0 <= coluna < 3)):
                print("Fora do tabuleiro (use 1-3).")
                estado.minha_vez.set() # tenta de novo
                continue

            if not rede.enviar(sock, {P.LINHA: linha, P.COLUNA: coluna}):
                print("[conexão perdida]")
                break
    finally:
        estado.ativo = False

def main():
    while True:
        try:
            melhor_de = int(input("Melhor de (1, 3 ou 5): "))
            if melhor_de in (1, 3, 5):
                break
        except ValueError:
            pass
        print("Valor inválido.")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print(f"Conectado. Entrando na fila (melhor de {melhor_de})...")

    estado = EstadoCliente()
    estado.entrar_na_fila(melhor_de)

    if not rede.enviar(client, {P.TIPO: P.FILA, P.MELHOR_DE: melhor_de}):
        print("[falha ao enviar fila]")
        client.close()
        return

    t = threading.Thread(target=thread_recebimento, args=(client, estado),daemon=True)
    t.start()
    try:
        loop_principal(client, estado)
    finally:
        estado.ativo = False
        estado.minha_vez.set()
        try:
            client.shutdown(socket.SHUT_RDWR) # Destrava o recv da thread
        except OSError:
            pass
        t.join(timeout=2)
        client.close()


if __name__ == "__main__":
    main()
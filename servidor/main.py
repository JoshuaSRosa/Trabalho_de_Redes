# Lógica central do servidor, responsável por aceitar conexões
# criar Sessao, lançar as duas threads de I/O por sessão, e rotear mensagens entre a sessão
# e o matchmaking/partida

# Imports base
import socket
import threading
from .sessoes import Sessao
from .rede import receber_linha, enviar
from .matchmaking import Gerenciador_de_filas
from comum import protocolo as P

# Definições iniciais do servidor
HOST = "127.0.0.1"
PORT = 38912


def thread_leitura(sessao: Sessao):  # Lê dos sockets e enfileira em sessao.fila_entrada
    buffer = b""
    try:
        while sessao.viva:
            msg, buffer = receber_linha(sessao.conn, buffer)
            if msg is None:
                break
            sessao.fila_entrada.put(msg)
    except OSError:
        pass
    finally:
        sessao.encerrar()
        try:
            sessao.conn.close()
        except OSError:
            pass        

def thread_escrita(sessao: Sessao): # Consome sessao.fila_saida e envia para o socket
    while True:
        obj = sessao.fila_saida.get()
        if obj is None:
            break
        if not enviar(sessao.conn. obj):
            break

    try:
        sessao.conn.shutdown(socket.SHUT_WR)
    except OSError:
        pass

def roteador_sessao(sessao: Sessao, filas: Gerenciador_de_filas):
    # Consome sessao.fila_entrada, quando a sessao NÃO está em partida
    while sessao.viva:
        msg = sessao.fila_entrada.get()
        if msg is None:
            break

        # Se a sessão já está em patida, quem consome a fila-entrada
        # é a thread_partida — então esta thread não deveria receber nada.
        # É uma proteção: se chegar aqui, a partida acabou e a sessão
        # voltou a ser "livre".
        if sessao.partida is not None:
            # devolve a fila para a partida consumir
            sessao.fila_entrada.put(msg)
            continue

        tipo = msg.get(P.TIPO)
        if tipo == P.FILA:
            melhor_de = msg.get(P.MELHOR_DE, 3)
            filas.entrar(sessao, melhor_de)
        elif tipo == P.SAIU_FILA:
            filas.sair(sessao)
        else:
            sessao.enviar({P.TIPO: P.ERRO, P.MSG: "esperado 'fila' ou 'saiu_fila'"})

def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"Servidor em {HOST}:{PORT}")

    filas = Gerenciador_de_filas()

    try:
        while True:
            conn, addr = servidor.accept()
            print(f"[+] {addr}")
            sessao = Sessao(conn, addr)

            threading.Thread(target=thread_leitura, args=(sessao,), daemon=True).start()
            threading.Thread(target=thread_escrita, args=(sessao,), daemon=True).start()

            # roteamento de mensagens de "fora de partida"
            # (fila, entrada/saída da partida - tratado na thread da sessão)
            threading.Thread(
                target=roteador_sessao,
                args=(sessao, filas),
                daemon=True,
            ).start()
    except KeyboardInterrupt:
        print("\nEncerrando")
    finally:
        servidor.close()

if __name__ == "__main__":
    main()
import socket
import json
import threading

HOST = "127.0.0.1"
PORT = 38912

# Cria um socket TCP usando IPv4.
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# O endereço é formado por (IP, porta).
client.connect((HOST, PORT)) # Conecta ao servidor. O endereço é formado por (IP, porta).

meu_jogador = None  # Qual jogador o cliente é P1 ou P2
# Controle de concorrênca entre prints das jogadas e impressão do tabuleiro
minha_vez = threading.Event()
jogo_ativo = True

def loop_recebimento(sock):
    global meu_jogador, jogo_ativo
    buffer = b""
    while True:
        msg, buffer = receber_linha(sock, buffer)
        if msg is None:
            print("\n[servidor encerrou]")
            jogo_ativo = False
            minha_vez.set()  # ativa a main para encerrar a conexão 
            break

        tipo = msg.get("tipo")

        if tipo == "welcome":
            meu_jogador = msg["jogador"]
            print(f"\n[Você é o {meu_jogador}]")
            if meu_jogador == "P1":
                print("[Aguardando oponente conectar...]")
        
        elif tipo == "state":
            print(f"\n--- Jogo {msg['partida_numero']+1} ---")
            imprimir_tabuleiro(msg["tabuleiro"])
            print(f"Placar: {msg['placar']}")
            vez = msg["jogador_atual"]
            if vez == meu_jogador:
                print(f">>> SUA VEZ ({vez}) <<<")
                minha_vez.set()  # libera a main para realizar o input corretamente
            else:
                print(f"Aguardando jogada de {vez}")

        elif tipo == "erro":
            print(f"\n[ERRO] {msg['msg']}")
            minha_vez.set()           # libera de novo para o usuário tentar outra

        elif tipo == "fim":
            print(f"\n=== FIM DA SÉRIE ===")
            print(f"Vencedor: {msg['vencedor']}")
            print(f"Placar final: {msg['placar']}")
            jogo_ativo = False      # indica que o jogo terminou
            minha_vez.set()         # libera a main paraa encerrar o jogo
            break

        elif tipo == "desconectou":
            print("\n[oponente desconectou]")

        elif tipo == "cheio":
            print("\n[Servidor cheio — já há uma partida em andamento]")
            jogo_ativo = False
            minha_vez.set()
            break

        else:
            print(f"\n<< mensagem desconhecida: {msg}")

def receber_linha(client, buffer):
    while b"\n" not in buffer:
        data = client.recv(1024)
        if data == b"":
            return None, buffer
        buffer += data
    linha, buffer = buffer.split(b"\n", 1)
    try:
        obj = json.loads(linha.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError): # em caso de erro, devolve msg vazia e atualiza o buffer
        return {"_invalida" : True}, buffer
    return obj, buffer

def enviar(client, obj):
    try:  # controle de execução em caso de erros
        client.sendall((json.dumps(obj) + "\n").encode("utf-8"))
        return True
    except OSError:
        return False

def imprimir_tabuleiro(tabuleiro):  #imprime o tabuleiro 3x3 de forma organizada e legível
    for i, linha in enumerate(tabuleiro):
        print(" " + " | ".join(c if c !=  ' ' else '.' for c in linha))
        if i < 2:
            print("---+---+---")
    print()


def main():

    t = threading.Thread(target=loop_recebimento,args=(client,),daemon=True)
    t.start()

    try:
        while jogo_ativo:
            minha_vez.wait()           # espera até ser sua vez
            if not jogo_ativo:
                break

            try:
                linha  = int(input("Linha (1-3):  ")) - 1
                coluna = int(input("Coluna (1-3): ")) - 1
            except ValueError:
                print("Digite números de 1 a 3.")
                continue

            if not (0 <= linha < 3 and 0 <= coluna < 3):
                print("Fora do tabuleiro (use 1-3).")
                continue

            minha_vez.clear()  # limpa antes de enviar
            if not enviar(client, {"linha": linha, "coluna": coluna}):
                print("[conexão perdida]")
                break
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        client.close()


if __name__ == "__main__":
    main()
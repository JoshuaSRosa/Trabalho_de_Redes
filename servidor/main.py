import socket
import json
import threading
from jogo import PARTIDA_MD # importa classe que estrutura a lógica do jogo

# Definições iniciais do servidor
HOST = "127.0.0.1"
PORT = 38912
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen() # Coloca o socket em modo de escuta.
print("Servidor aguardando conexão...")

# Controle relacionado as threads
conexoes = {} 
lock_conexoes = threading.Lock()

# Controle relacionado ao Jogo
md = None # Partida_MD criada uando dois jgadores conectam
lock_md = threading.Lock() # Proteção do md
jogadores = {} # conn dos jogadores

def comunica(conn,addr):  # Função para thread manter comunicação entre servidor e diferentes clientes
    global md

    with lock_conexoes:
        jogador = jogadores[conn]

    enviar(conn, {"tipo": "welcome", "jogador": jogador})

    if jogador == "P2": # verifica se é o segundo jogador -> cria a partida -> avisa os dois jogadores
        with lock_md:
            md = PARTIDA_MD("P1","P2", 3) # Teste inicial com MD3 fixa
            snap = estado_atual(md)

        with lock_conexoes:
            todas = list(conexoes.keys())

        for c in todas:
            enviar(c, snap)
    
    buffer = b""

    # Avisa a entrada de um novo cliente aos outros
    p = parceiro(conn)
    if p is not None:
        enviar(p, {"tipo": "conectou", "quem": str(addr)})

    try:
        while True:
            if b"\n" not in buffer:
                data = conn.recv(1024)
                if data == b"": break
                buffer += data
                continue
            linha, buffer = buffer.split(b"\n", 1)
            try:
                obj = json.loads(linha.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            # Processa a jogada com o lock de estado
            with lock_md:
                if md is None:
                    erro = "aguardando oponente"
                else:
                    try:
                        md.inserir_jogada(jogador, obj["linha"], obj["coluna"])
                        erro = None
                        snap = estado_atual(md)
                        terminou = md.finished
                        vencedor = md.winner
                        placar_final = dict(md.placar)
                    except (ValueError, KeyError) as e:
                        erro = str(e)

            # Faz o envio fora do lock de estado
            if erro:
                enviar(conn,{"tipo": "erro", "msg": erro})
            else:
                with lock_conexoes:
                    todas = list(conexoes.keys())
                for c in todas:
                    enviar(c, snap)
                if terminou:
                    for c in todas:
                        enviar(c,{"tipo": "fim","vencedor": vencedor, "placar": placar_final})
                    break
            print("Recebido: ", obj) 

            texto = obj.get("text")
            # Cancela a conexão com o servidor
            if texto == "sair":
                break

            p = parceiro(conn)
            if p is None:   # Se não tiver um parceiro, espera até ter um
                enviar(conn, {"tipo": "aviso", "msg": "aguardando parceiro"})
            else: # Tiver parceiro
                enviar(p, {"tipo": "msg", "quem": str(addr), "text": texto}) # Envia mensagem para o parceiro
                enviar(conn, {"tipo": "enviado", "text": texto}) # confirma para o remetent
    
    except (ConnectionResetError, OSError) as e:
        print(f"[!] {addr} erro: {e}")
    finally:
        # Fecha a conexão com o cliente.
        with lock_conexoes:    
            conexoes.pop(conn, None)   # retira o cliente da lista
            jogadores.pop(conn, None)  # retira o jogador que saiu
            restantes = list(conexoes.keys())
        conn.close()   # encerra a conexão com o cliente
        print(f"[-] {addr} desconectado")  # avisa qual cliente foi desconectado
        for c in restantes:
            enviar(c, {"tipo": "desconectou"})

def estado_atual(md): # Função auxiliar para thread ver o estado do jogo
    p = md.partida_atual
    return {
        "tipo": "state",
        "board": p.tabuleiro,
        "jogador_atual": md.jogador_atual(),
        "placar": dict(md.placar),
        "partida_numero": md.partida_numero,
        "finished": md.finished
    }

def enviar(conn, obj):
    # Envia um JSON para uma conn, usando  o lock dela.
    with lock_conexoes:
        lock = conexoes.get(conn)
    if lock is None: # Sem conn retorna falso
        return False
    with lock: # garantia de encerramento ao fim da execução
        try:  # controle de execução em caso de erros
            conn.sendall((json.dumps(obj) + "\n").encode("utf-8"))
            return True
        except OSError:
            return False

def parceiro(conn):
    with lock_conexoes:
        for c in  conexoes:
            if c is not conn:
                return c
    return None


def main():
    while True:
        # Aguarda uma conexão e retorna:
        # conn = socket para comunicação com o cliente
        # addr = endereço IP e porta do cliente 
        conn, addr = server.accept()

        with lock_conexoes:   # adiciona coon ao dicionário depois cria a thread
            if len(conexoes)>=2:
                # já tem dois jogadores; rejeita o terceiro
                conn.sendall((json.dumps({"tipo": "cheio"}) + "\n").encode("utf-8"))
                conn.close()
                continue
            conexoes[conn] = threading.Lock()
            if len(conexoes) == 1:
                jogadores[conn] = "P1"
            else:
                jogadores[conn] = "P2"
        
        t = threading.Thread(target=comunica,args=(conn,addr),daemon=True)
        t.start()



if __name__ == "__main__":
    main()
import socket
import json
import threading

# Definições iniciais do servidor
HOST = "127.0.0.1"
PORT = 38912
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen() # Coloca o socket em modo de escuta.
print("Servidor aguardando conexão...")
conexoes = {} 
lock_conexoes = threading.Lock()

def comunica(conn,addr):  # Função para thread manter comunicação entre servidor e diferentes clientes
    print(f"Cliente conectado: {addr}")
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
            obj = json.loads(linha.decode("utf-8"))
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
        conn.close()   # encerra a conexão com o cliente
        print(f"[-] {addr} desconectado")  # avisa qual cliente foi desconectado

        p = parceiro(conn) # Se houver parceiros conectados, avisa ao parceiro que o outro cliente se desconectou
        if p is not None:
            enviar(p, {"tipo": "desconectou", "quem": str(addr)}) 

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

while True:
    # Aguarda uma conexão e retorna:
    # conn = socket para comunicação com o cliente
    # addr = endereço IP e porta do cliente 
    conn, addr = server.accept()

    with lock_conexoes:   # adiciona coon ao dicionário depois cria a thread
        conexoes[conn] = threading.Lock()
    
    t = threading.Thread(target=comunica,args=(conn,addr),daemon=True)
    t.start()

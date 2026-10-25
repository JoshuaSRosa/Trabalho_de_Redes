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


def comunica(conn,addr):
    print(f"Cliente conectado: {addr}")
    buffer = b""

    while True:
        if b"\n" not in buffer:
            data = conn.recv(1024)
            if data == b"": break
            buffer += data
            continue
        linha, buffer = buffer.split(b"\n", 1)
        obj = json.loads(linha.decode("utf-8"))
        print("Recebido: ", obj) 
        
        if obj.get("text") == "sair":
            conn.sendall((json.dumps({"status": "adeus"}) + "\n").encode("utf-8"))
            break

        conn.sendall((json.dumps({"status": "ok", "eco": obj}) + "\n").encode("utf-8"))

    # Fecha a conexão com o cliente.
    conn.close()

while True:
    # Aguarda uma conexão e retorna:
    # conn = socket para comunicação com o cliente
    # addr = endereço IP e porta do cliente 
    conn, addr = server.accept()
    t = threading.Thread(target=comunica,args=(conn,addr),daemon=True)
    t.start()


# Fecha o socket do servidor.
server.close()


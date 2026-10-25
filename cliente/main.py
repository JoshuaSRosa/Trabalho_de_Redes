import socket
import json

HOST = "127.0.0.1"
PORT = 38912

# Cria um socket TCP usando IPv4.
# AF_INET = IPv4
# SOCK_STREAM = TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conecta ao servidor.
# O endereço é formado por (IP, porta).
client.connect((HOST, PORT))

buffer = b""

while True:
    # Recebe até 1024 bytes do servidor.
    texto = input("Digite sua mensagem: ")
    client.sendall((json.dumps({"text": texto}) + "\n").encode("utf-8"))

    # recebe a resposta (mesmo padrão de buffer do servidor)
    fechou = False
    while b"\n" not in buffer:
        data = client.recv(1024)
        if data == b"":
            fechou = True
            break
        buffer += data

    if fechou:
        print("Servidor encerrou a conexão")
        break

    linha, buffer = buffer.split(b"\n", 1)
    resp = json.loads(linha.decode("utf-8"))
    print("Resposta:", resp)

    if texto == "sair":
        break


# Fecha a conexão.
client.close()

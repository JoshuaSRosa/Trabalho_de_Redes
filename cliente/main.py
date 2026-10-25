import socket
import json
import threading

HOST = "127.0.0.1"
PORT = 38912

# Cria um socket TCP usando IPv4.
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# O endereço é formado por (IP, porta).
client.connect((HOST, PORT)) # Conecta ao servidor. O endereço é formado por (IP, porta).
print("Conectado. Digite 'sair' para encerrar.")

def loop_recebimento(sock):
    buffer = b""
    while True:
        msg, buffer = receber_linha(sock, buffer)
        if msg is None:
            print("\n[servidor encerrou]")
            break
        print(f"\n<< {msg}")

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
    
def main():

    t = threading.Thread(target=loop_recebimento,args=(client,),daemon=True)
    t.start()

    try:
        while True:
            texto = input("> ")
            enviar(client, {"text": texto})
            if texto == "sair":
                break
    except  (KeyboardInterrupt, BrokenPipeError):
        pass
    finally:
        client.close() # Encerra a conexão do cliente com o servidor

if __name__ == "__main__":
    main()
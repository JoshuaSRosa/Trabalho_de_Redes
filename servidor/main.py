import socket
import threading as th
from servidor.rede import tratar_client

HOST = "127.0.0.1" #checar depois um endereço válido
PORT = 5000  #caso de erro trocar a porta

# Cria um socket TCP usando IPv4.
# AF_INET = IPv4
# SOCK_STREAM = TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Associa o socket ao endereço IP e à porta.
server.bind((HOST, PORT))

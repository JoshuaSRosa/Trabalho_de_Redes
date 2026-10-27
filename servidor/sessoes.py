# Parte responsável por controle relacionado a um "cliente conectado":
# a conn, o estado da fila(quando estiver esperando), a partida em que está(após ser pareado com outro player), e as duas filas de comunicação

import queue
import threading

class Sessao:
    def _init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.nickname = None   # Preenchido no login do jogador
        self.fila_entrada = queue.Queue()  # mensagens recebidas do cliente
        self.fila_saida =  queue.Queue()   # mensagens a enviar ao cliente
        self.partida = None    # referência a PartidaThread (None =na fila ou ociosa)
        self.viva = True       # flag para parar as threads
        self.lock_estado = threading.Lock()

    def enviar(self, obj): # método para enfileirar mensagens para o cliente
        self.fila_saida.put(obj)

    def encerrar(self):
        with self.lock_estado:
            self.viva = False
        # controle para destravar threads bloqueadas em get() em caso de perda de conexão
        self.fila_entrada.put(None)
        self.fila_saida.put(None)
    
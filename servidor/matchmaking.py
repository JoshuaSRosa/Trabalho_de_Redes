# Responsável por gerenciar filas de espera, parear dois jogadores com
# o mesmo melhor_de, e lançar a thread_partida

import queue
import threading
from .sessoes import Sessao
from .partida import thread_partida
from comum import protocolo as P

class Gerenciador_de_filas:
    def __init__(self):
        self.lock = threading.Lock()
        # Filas de sessões esperando jogadores com o mesmo melhor-de
        # Listas para facilitar a escolha de pares
        self.filas = {1: [],  3: [], 5: []}

    def entrar(self, sessao: Sessao, melhor_de: int):
        if melhor_de not in self.filas: # Garantia de escolha de MD-n possível
            sessao.enviar({P.TIPO: P.ERRO, P.MSG: f"melhor_de inválido: {melhor_de}"})
            return
        with self.lock:
            self.filas[melhor_de].append(sessao)
            # Se tiver 2 na fila, pareia
            if len(self.filas[melhor_de]) >= 2:
                s1 = self.filas[melhor_de].pop(0)
                s2 = self.filas[melhor_de].pop(0)
                self.parear(s1, s2, melhor_de)

    def sair(self, sessao: Sessao):
        with self.lock:
            for fila in self.filas.values():
                if sessao in fila:
                    fila.remove(sessao)
                    return

    def parear(self, s1, s2, melhor_de):
        # fora do lock de fila, para não bloquer o pareamento
        s1.enviar({P.TIPO: P.PAREADO, P.OPONENTE: str(s2.addr)})
        s2.enviar({P.TIPO: P.PAREADO, P.OPONENTE: str(s1.addr)})
        t = threading.Thread(
           target=thread_partida,
           args=(s1, s2, melhor_de),
           daemon=True,
        )
        t.start()